"""Label record endpoints — history, undo, confirm, reject."""
import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.repositories.label_records import (
    get_record,
    get_recent_grouped_emails,
    get_records_for_user,
    update_record_status,
)
from app.repositories.users import get_user_by_id, update_user_document
from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.session_auth import require_auth
from fastapi import Request
from ml.pipeline import confirm_label

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/label-records", tags=["label-records"])

RECORD_ID_PATTERN = r"^[a-f0-9]{24}$"  # MongoDB ObjectId hex


def _gmail_client(session: dict, request: Request) -> GmailClient:
    tokens = session.get("tokens", {})
    return GmailClient(
        access_token=tokens.get("access_token", ""),
        refresh_token=tokens.get("refresh_token"),
        session_id=request.cookies.get(COOKIE_NAME),
    )


@router.get("/recent")
async def get_recent_emails(
    session: dict = Depends(require_auth),
    limit: Optional[int] = Query(default=None, gt=0),
):
    """Return recent emails grouped by message, with confirmed and suggested label arrays.

    Delegates grouping and filtering to a MongoDB aggregation — no Python heuristics.
    """
    user_id = session["user"]["user_id"]
    emails = await get_recent_grouped_emails(user_id, limit=limit)
    return {"emails": emails}


@router.get("")
async def list_label_records(
    session: dict = Depends(require_auth),
    limit: int = Query(default=50, gt=0, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, description="Filter by status: applied, suggested, confirmed, rejected, undone"),
):
    """Return label records for the current user, newest first.

    Used by the frontend to render the label history view.
    """
    user_id = session["user"]["user_id"]
    records = await get_records_for_user(user_id, limit=limit, offset=offset, status=status)
    return {"records": [r.model_dump() for r in records], "count": len(records)}


@router.post("/{record_id}/undo")
async def undo_label_record(
    request: Request,
    session: dict = Depends(require_auth),
    record_id: str = Path(..., pattern=RECORD_ID_PATTERN),
):
    """Undo an applied label — removes it from Gmail and marks the record as undone.

    Only valid for records with status 'applied' or 'confirmed'.
    Does not reverse the ML model update.
    """
    user_id = session["user"]["user_id"]
    record = await get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if record.status not in ("applied", "confirmed"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot undo a record with status '{record.status}'",
        )

    client = _gmail_client(session, request)

    if record.gmail_label_id:
        try:
            await client.apply_labels(
                record.gmail_message_id,
                remove_label_ids=[record.gmail_label_id],
            )
        except HTTPException as e:
            # Label may already be absent in Gmail — log and continue.
            logger.warning("Gmail remove label failed for %s: %s", record_id, e)

    updated = await update_record_status(record_id, "undone", resolved_at=datetime.now(UTC))
    return {"record": updated.model_dump()}


@router.post("/{record_id}/confirm")
async def confirm_label_record(
    request: Request,
    session: dict = Depends(require_auth),
    record_id: str = Path(..., pattern=RECORD_ID_PATTERN),
):
    """Confirm a suggested label — applies it in Gmail, updates the ML model, marks confirmed.

    Only valid for records with status 'suggested'.
    The stored embedding vector is used to update the label's corpus so the model
    learns from the user's confirmation without needing to re-fetch or re-embed.
    """
    user_id = session["user"]["user_id"]
    record = await get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if record.status != "suggested":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot confirm a record with status '{record.status}'",
        )

    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    label = user_doc.labels.get(record.label_name)
    if not label:
        raise HTTPException(status_code=404, detail=f"Label '{record.label_name}' not found")

    client = _gmail_client(session, request)

    # Apply the real label in Gmail.
    if record.gmail_label_id:
        try:
            await client.apply_labels(
                record.gmail_message_id,
                add_label_ids=[record.gmail_label_id],
            )
        except HTTPException as e:
            logger.warning("Gmail apply label failed for %s: %s", record_id, e)

    # Remove the "Suggested: X" shadow label if it exists.
    try:
        all_gmail_labels = await client.list_labels()
        suggested_name = f"Suggested: {record.label_name}"
        suggested_id = next(
            (l["id"] for l in all_gmail_labels if l["name"] == suggested_name), None
        )
        if suggested_id:
            await client.apply_labels(
                record.gmail_message_id,
                remove_label_ids=[suggested_id],
            )
    except HTTPException as e:
        logger.warning("Failed to remove suggested label for %s: %s", record_id, e)

    # Update the ML model if we have the stored vector and text.
    if record.vector and record.subject:
        fields = confirm_label(label, record.vector, record.subject)
        await update_user_document(
            user_id,
            {f"labels.{record.label_name}.{k}": v for k, v in fields.items()},
        )

    updated = await update_record_status(record_id, "confirmed", resolved_at=datetime.now(UTC))
    return {"record": updated.model_dump()}


@router.post("/{record_id}/reject")
async def reject_label_record(
    request: Request,
    session: dict = Depends(require_auth),
    record_id: str = Path(..., pattern=RECORD_ID_PATTERN),
):
    """Reject a suggested label — removes the 'Suggested: X' Gmail label, marks rejected.

    Only valid for records with status 'suggested'.
    """
    user_id = session["user"]["user_id"]
    record = await get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if record.status != "suggested":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject a record with status '{record.status}'",
        )

    client = _gmail_client(session, request)

    # Remove the "Suggested: X" shadow label from Gmail.
    try:
        all_gmail_labels = await client.list_labels()
        suggested_name = f"Suggested: {record.label_name}"
        suggested_id = next(
            (l["id"] for l in all_gmail_labels if l["name"] == suggested_name), None
        )
        if suggested_id:
            await client.apply_labels(
                record.gmail_message_id,
                remove_label_ids=[suggested_id],
            )
    except HTTPException as e:
        logger.warning("Failed to remove suggested label for %s: %s", record_id, e)

    updated = await update_record_status(record_id, "rejected", resolved_at=datetime.now(UTC))
    return {"record": updated.model_dump()}
