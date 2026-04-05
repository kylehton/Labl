"""Current user document API: get/update profile, labels, settings, and label seeding."""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel

from app.repositories.users import get_user_by_id, update_user_document
from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.session_auth import require_auth
from ml.pipeline import seed_label as compute_seed_label

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])

MESSAGE_ID_PATTERN = r"^[a-zA-Z0-9]+$"


# ------------------------------------------------------------------
# Request bodies
# ------------------------------------------------------------------

class SeedLabelBody(BaseModel):
    message_ids: list[str]


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.get("")
async def get_user(session: dict = Depends(require_auth)):
    """Return the current user's document (user, auto_label, labels)."""
    user_id = (session.get("user") or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user in session")
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User document not found")
    return user_doc.model_dump()


@router.patch("")
async def update_user(session: dict = Depends(require_auth), body: dict | None = None):
    """Update current user document. Allowed keys: auto_label, labels (partial merge)."""
    user_id = (session.get("user") or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user in session")
    if not body:
        body = {}
    allowed = {"auto_label", "labels"}
    update = {key: value for key, value in body.items() if key in allowed}
    if not update:
        raise HTTPException(status_code=400, detail="No allowed fields to update")
    updated = await update_user_document(user_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="User document not found")
    return updated.model_dump()


@router.post("/labels/{label_name}/seed")
async def seed_label(
    body: SeedLabelBody,
    request: Request,
    session: dict = Depends(require_auth),
    label_name: str = Path(..., min_length=5, max_length=20),
):
    """Seed a label's medoid from a set of example emails.

    Fetches the full body of each provided message_id from Gmail, embeds them,
    computes a medoid, and stores it in MongoDB. The label must already
    exist in the user's label store (created via POST /api/gmail/labels).

    Body:
        message_ids: list of Gmail message IDs to use as seed examples (min 1).
    """
    if not body.message_ids:
        raise HTTPException(status_code=422, detail="At least one message_id required")

    # Validate message IDs (same pattern as gmail routes)
    import re
    pattern = re.compile(MESSAGE_ID_PATTERN)
    for mid in body.message_ids:
        if not pattern.match(mid):
            raise HTTPException(status_code=422, detail=f"Invalid message_id: {mid!r}")

    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    if label_name not in user_doc.labels:
        raise HTTPException(
            status_code=404,
            detail=f"Label '{label_name}' not found. Create it first via POST /api/gmail/labels.",
        )

    # Fetch full message bodies from Gmail for embedding
    tokens = session.get("tokens", {})
    gmail = GmailClient(
        access_token=tokens.get("access_token", ""),
        refresh_token=tokens.get("refresh_token"),
        session_id=request.cookies.get(COOKIE_NAME),
    )

    msgs = await asyncio.gather(*[gmail.get_message_body(mid) for mid in body.message_ids])
    seed_texts = [(m.get("subject", ""), m.get("body", "")) for m in msgs]

    # Compute medoid and persist
    fields = compute_seed_label(seed_texts)
    await update_user_document(
        user_id,
        {f"labels.{label_name}.{k}": v for k, v in fields.items()},
    )

    return {
        "label_name": label_name,
        "seeded_with": len(seed_texts),
        "centroid_dim": len(fields["medoid"]),
    }
