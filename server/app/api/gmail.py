"""Gmail API routes — fetch messages, manage labels, and run the labeling pipeline."""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel

from app.repositories.users import get_user_by_id, update_user_document
from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.session_auth import require_auth
from app.models.label import Label
from ml.pipeline import process_email, update_label_after_confirmation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail")

# Gmail message IDs are alphanumeric — validate to prevent URL manipulation
MESSAGE_ID_PATTERN = r"^[a-zA-Z0-9]+$"


# ------------------------------------------------------------------
# Request bodies
# ------------------------------------------------------------------

class CreateLabelBody(BaseModel):
    name: str


class ApplyLabelBody(BaseModel):
    label_ids: list[str]
    remove_label_ids: list[str] = []


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _gmail_client(session: dict, request: Request) -> GmailClient:
    tokens = session.get("tokens", {})
    return GmailClient(
        access_token=tokens.get("access_token", ""),
        refresh_token=tokens.get("refresh_token"),
        session_id=request.cookies.get(COOKIE_NAME),
    )


async def _get_or_create_suggested_label_id(
    client: GmailClient, label_name: str
) -> str | None:
    """Return the Gmail label ID for 'Suggested: <label_name>', creating it if needed."""
    suggested_name = f"Suggested: {label_name}"
    all_labels = await client.list_labels()
    existing = next((l for l in all_labels if l["name"] == suggested_name), None)
    if existing:
        return existing["id"]
    try:
        created = await client.create_label(suggested_name)
        return created["id"]
    except HTTPException:
        return None


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.get("/messages")
async def get_messages(
    request: Request,
    session: dict = Depends(require_auth),
):
    """Fetch inbox messages since last_checked, run the labeling pipeline, update last_checked.

    For each new message the pipeline result is included under the "pipeline" key:
      - action="label"   → label applied directly in Gmail + centroid updated via EMA
      - action="suggest" → "Suggested: <name>" label applied in Gmail
      - pipeline=None    → no seeded labels yet, or message already labelled
    """
    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)
    last_checked = user_doc.last_checked if user_doc else None
    labels = user_doc.labels if user_doc else {}
    auto_label = user_doc.auto_label if user_doc else False

    client = _gmail_client(session, request)
    raw_messages = await client.list_messages_since(after=last_checked)

    # IDs of labels the user has defined (to skip already-labelled messages)
    user_label_ids = {
        lbl.gmail_label_id
        for lbl in labels.values()
        if lbl.gmail_label_id is not None
    }

    enriched = []
    for msg in raw_messages:
        # Skip messages that already carry one of the user's labels
        if set(msg.get("label_ids", [])) & user_label_ids:
            enriched.append({**msg, "pipeline": None})
            continue

        try:
            full = await client.get_message_body(msg["id"])
            result = process_email(
                subject=full["subject"],
                body=full["body"],
                labels=labels,
                auto_label=auto_label,
            )
        except Exception as e:
            logger.warning("Pipeline failed for message %s: %s", msg["id"], e)
            enriched.append({**msg, "pipeline": None})
            continue

        if result is None:
            enriched.append({**msg, "pipeline": None})
            continue

        pipeline_summary = {
            "label_name": result["label_name"],
            "score": round(result["score"], 4),
            "action": result["action"],
        }

        label = labels.get(result["label_name"])

        if result["action"] == "label" and label and label.gmail_label_id and label.centroid:
            await client.apply_labels(msg["id"], add_label_ids=[label.gmail_label_id])
            new_centroid = update_label_after_confirmation(
                label.centroid, result["vector"]
            )
            await update_user_document(
                user_id,
                {
                    f"labels.{result['label_name']}.centroid": new_centroid,
                    f"labels.{result['label_name']}.count": (label.count or 0) + 1,
                },
            )

        elif result["action"] == "suggest" and label:
            suggested_label_id = await _get_or_create_suggested_label_id(
                client, result["label_name"]
            )
            if suggested_label_id:
                await client.apply_labels(
                    msg["id"], add_label_ids=[suggested_label_id]
                )

        enriched.append({**msg, "pipeline": pipeline_summary})

    await update_user_document(user_id, {"last_checked": datetime.now(UTC)})

    return {"messages": enriched, "count": len(enriched)}


@router.get("/messages/{message_id}/body")
async def get_message_body(
    request: Request,
    session: dict = Depends(require_auth),
    message_id: str = Path(..., pattern=MESSAGE_ID_PATTERN),
):
    """Fetch the full subject + plain-text body of a single message (used for embedding)."""
    client = _gmail_client(session, request)
    return await client.get_message_body(message_id)


@router.get("/labels")
async def get_labels(
    request: Request,
    session: dict = Depends(require_auth),
):
    """List all Gmail labels for the authenticated user."""
    client = _gmail_client(session, request)
    labels = await client.list_labels()
    return {"labels": labels}


@router.post("/labels")
async def create_label(
    body: CreateLabelBody,
    request: Request,
    session: dict = Depends(require_auth),
):
    """Create a Gmail label and register it in the user's label store in MongoDB.

    The label starts with centroid=None. Seed it via POST /api/user/labels/{name}/seed
    before the pipeline can classify against it.
    """
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Label name required")

    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)

    if user_doc and name in user_doc.labels:
        raise HTTPException(status_code=409, detail=f"Label '{name}' already exists")

    client = _gmail_client(session, request)
    gmail_label = await client.create_label(name)

    label = Label(
        name=name,
        type="custom",
        gmail_label_id=gmail_label["id"],
    )
    await update_user_document(user_id, {f"labels.{name}": label.model_dump()})

    return {"label": gmail_label, "stored": label.model_dump()}


@router.post("/messages/{message_id}/label")
async def apply_label(
    body: ApplyLabelBody,
    request: Request,
    session: dict = Depends(require_auth),
    message_id: str = Path(..., pattern=MESSAGE_ID_PATTERN),
):
    """Apply (and optionally remove) labels on a Gmail message."""
    if not body.label_ids:
        raise HTTPException(status_code=422, detail="label_ids required")
    client = _gmail_client(session, request)
    await client.apply_labels(
        message_id,
        add_label_ids=body.label_ids,
        remove_label_ids=body.remove_label_ids,
    )
    return {"ok": True}
