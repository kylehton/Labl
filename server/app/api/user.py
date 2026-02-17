"""Current user document API: get/update profile, labels, settings."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.repositories.users import get_user_by_id, update_user_document
from dependencies.session_auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


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
