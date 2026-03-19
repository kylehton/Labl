"""Gmail API routes — fetch messages, manage labels."""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel

from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.session_auth import require_auth
from app.models.label import Label
from app.repositories.users import get_user_by_id, update_user_document

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


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.get("/messages")
async def get_messages(
    request: Request,
    session: dict = Depends(require_auth),
):
    """Fetch inbox messages since last_checked. Updates last_checked on success."""
    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)
    last_checked = user_doc.last_checked if user_doc else None

    client = _gmail_client(session, request)
    messages = await client.list_messages_since(after=last_checked)

    await update_user_document(user_id, {"last_checked": datetime.now(UTC)})

    return {"messages": messages, "count": len(messages)}


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

    The label is stored with centroid=None and count=0. The centroid is computed
    in Phase 2 once the user selects seed emails.
    """
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Label name required")

    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)

    # Prevent duplicate labels
    if user_doc and name in user_doc.labels:
        raise HTTPException(status_code=409, detail=f"Label '{name}' already exists")

    client = _gmail_client(session, request)
    gmail_label = await client.create_label(name)

    # Persist label to MongoDB (centroid filled later during seed phase)
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
