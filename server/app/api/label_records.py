"""Label record endpoints — history, undo, confirm, reject."""
import asyncio
import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.models.label_record import LabelRecord
from app.repositories.label_records import (
    delete_resolved_records_before,
    get_record,
    get_recent_grouped_emails,
    get_records_for_user,
    insert_record,
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
GMAIL_MESSAGE_ID_PATTERN = r"^[a-zA-Z0-9]+$"

# Per-(user, label) locks to serialize concurrent confirm requests and prevent
# read-modify-write races on the label's embedding corpus and medoid/clusters.
_confirm_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class ManualLabelBody(BaseModel):
    gmail_message_id: str
    label_name: str


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

    On each visit (debounced to 60s), deletes terminal-status records from before the
    previous visit timestamp so the dashboard acts as a sliding "since last visit" window.
    Suggested records are left intact to avoid orphaning Gmail shadow labels.
    """
    user_id = session["user"]["user_id"]
    now = datetime.now(UTC)

    user = await get_user_by_id(user_id)
    last_visit = user.last_dashboard_visit if user else None

    if last_visit is not None:
        if last_visit.tzinfo is None:
            last_visit = last_visit.replace(tzinfo=UTC)
        if (now - last_visit).total_seconds() >= 60:
            deleted = await delete_resolved_records_before(user_id, last_visit)
            logger.info("Cleaned %d resolved records for user %s (before %s)", deleted, user_id, last_visit)
            await update_user_document(user_id, {"last_dashboard_visit": now})
    else:
        await update_user_document(user_id, {"last_dashboard_visit": now})

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
                add_label_ids=[],
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
                add_label_ids=[],
                remove_label_ids=[suggested_id],
            )
    except HTTPException as e:
        logger.warning("Failed to remove suggested label for %s: %s", record_id, e)

    # Serialize concurrent confirmations on the same label to prevent read-modify-write
    # races on the embedding corpus and medoid/cluster state.
    async with _confirm_locks[f"{user_id}:{record.label_name}"]:
        user_doc = await get_user_by_id(user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        label = user_doc.labels.get(record.label_name)
        if not label:
            raise HTTPException(status_code=404, detail=f"Label '{record.label_name}' not found")

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
                add_label_ids=[],
                remove_label_ids=[suggested_id],
            )
    except HTTPException as e:
        logger.warning("Failed to remove suggested label for %s: %s", record_id, e)

    updated = await update_record_status(record_id, "rejected", resolved_at=datetime.now(UTC))
    return {"record": updated.model_dump()}


@router.post("/manual")
async def apply_manual_label(
    body: ManualLabelBody,
    request: Request,
    session: dict = Depends(require_auth),
):
    """Manually apply a label to a message from the dashboard.

    Applies the Gmail label, creates a label_record with status 'applied' and
    source 'manual'. Safe to call for any email visible in the dashboard.
    """
    import re
    if not re.match(GMAIL_MESSAGE_ID_PATTERN, body.gmail_message_id):
        raise HTTPException(status_code=422, detail="Invalid gmail_message_id")

    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    label = user_doc.labels.get(body.label_name)
    if not label:
        raise HTTPException(status_code=404, detail=f"Label '{body.label_name}' not found")

    client = _gmail_client(session, request)

    # Fetch subject so the record can display it without a Gmail round-trip later.
    try:
        msg = await client.get_message_body(body.gmail_message_id)
        subject = msg.get("subject", "(no subject)")
    except Exception:
        subject = "(no subject)"

    if label.gmail_label_id:
        try:
            await client.apply_labels(
                body.gmail_message_id,
                add_label_ids=[label.gmail_label_id],
            )
        except HTTPException as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail)

    record = LabelRecord(
        record_id="",
        user_id=user_id,
        task_id="manual",
        gmail_message_id=body.gmail_message_id,
        subject=subject,
        label_name=body.label_name,
        gmail_label_id=label.gmail_label_id,
        action="label",
        source="manual",
        score=None,
        vector=None,
        status="applied",
    )
    record_id = await insert_record(record)
    record.record_id = record_id

    return {"record": record.model_dump()}
