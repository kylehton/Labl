"""Gmail API routes — enqueue labeling jobs, poll status, and manage labels."""
import logging

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel

from app.models.label import Label
from app.repositories.users import get_user_by_id, update_user_document
from config.celery_app import celery_app
from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.limiter import limiter
from dependencies.session_auth import require_auth
from tasks.labeling import run_labeling_pipeline

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
@limiter.limit("2/minute")
async def get_messages(
    request: Request,
    session: dict = Depends(require_auth),
    limit: int | None = Query(default=None, gt=0, description="Cap total messages fetched (for testing)"),
    debug: bool = Query(default=False, description="Include per-label scores in pipeline results"),
    triggered_by: str = Query(default="manual", description="'manual' or 'auto'"),
):
    """Enqueue the email labeling pipeline for the current user.

    Returns a task_id immediately. Poll GET /api/gmail/status/{task_id} for progress
    and results. The pipeline continues running in the background even if the tab is closed.
    """
    tokens = session.get("tokens", {})
    user_id = session["user"]["user_id"]

    task = run_labeling_pipeline.delay(
        user_id=user_id,
        access_token=tokens.get("access_token", ""),
        refresh_token=tokens.get("refresh_token"),
        session_id=request.cookies.get(COOKIE_NAME),
        triggered_by=triggered_by,
        limit=limit,
        debug=debug,
    )

    return {"task_id": task.id}


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    _session: dict = Depends(require_auth),
):
    """Poll the status of a labeling pipeline task.

    States:
      - pending  → task is queued, not yet started
      - running  → task is actively executing
      - done     → task completed; result contains summary + messages
      - failed   → task raised an exception; error contains the message
    """
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return {"status": "pending"}
    if result.state == "STARTED":
        return {"status": "running"}
    if result.state == "SUCCESS":
        return {"status": "done", "result": result.result}
    if result.state == "FAILURE":
        return {"status": "failed", "error": str(result.result)}

    # RETRY or other transient states
    return {"status": "running"}


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
    try:
        await client.apply_labels(
            message_id,
            add_label_ids=body.label_ids,
            remove_label_ids=body.remove_label_ids,
        )
        return {"ok": True}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
