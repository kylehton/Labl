"""Async Gmail REST API client with automatic access-token refresh."""
import base64
import logging
import os

import httpx
from datetime import datetime
from fastapi import HTTPException

from config.db import update_one

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")


class GmailClient:
    def __init__(
        self,
        access_token: str,
        refresh_token: str | None = None,
        session_id: str | None = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.session_id = session_id

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    async def _refresh_access_token(self) -> None:
        """Exchange refresh token for a new access token, persist to session."""
        if not self.refresh_token:
            raise HTTPException(
                status_code=401, detail="Session expired — please log in again"
            )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        if resp.status_code != 200:
            logger.error("Token refresh failed: %s", resp.text)
            raise HTTPException(
                status_code=401, detail="Token refresh failed — please log in again"
            )
        self.access_token = resp.json()["access_token"]
        if self.session_id:
            await update_one(
                "sessions",
                {"session_id": self.session_id},
                {"$set": {"access_token": self.access_token}},
            )

    # ------------------------------------------------------------------
    # Low-level HTTP helpers (auto-refresh on 401)
    # ------------------------------------------------------------------

    async def _get(self, url: str, params: dict | None = None) -> dict:
        for attempt in range(2):
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
            if resp.status_code == 401 and attempt == 0:
                await self._refresh_access_token()
                continue
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Gmail API error: {resp.text}",
                )
            return resp.json()
        raise HTTPException(status_code=401, detail="Gmail API authentication failed")

    async def _post(self, url: str, json: dict) -> dict:
        for attempt in range(2):
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json=json,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
            if resp.status_code == 401 and attempt == 0:
                await self._refresh_access_token()
                continue
            if resp.status_code not in (200, 201):
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Gmail API error: {resp.text}",
                )
            return resp.json()
        raise HTTPException(status_code=401, detail="Gmail API authentication failed")

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def list_messages_since(
        self, after: datetime | None = None, max_results: int = 50
    ) -> list[dict]:
        """Return message metadata (id, snippet, subject, from, date) for inbox messages since `after`."""
        params: dict = {"maxResults": max_results, "labelIds": "INBOX"}
        if after:
            params["q"] = f"after:{int(after.timestamp())}"

        data = await self._get(f"{GMAIL_API_BASE}/messages", params=params)
        raw_messages = data.get("messages", [])

        results = []
        for msg in raw_messages:
            meta = await self._get(
                f"{GMAIL_API_BASE}/messages/{msg['id']}",
                params={
                    "format": "metadata",
                    "metadataHeaders": ["Subject", "From", "Date"],
                },
            )
            headers = {
                h["name"]: h["value"]
                for h in meta.get("payload", {}).get("headers", [])
            }
            results.append(
                {
                    "id": msg["id"],
                    "thread_id": meta.get("threadId"),
                    "snippet": meta.get("snippet", ""),
                    "subject": headers.get("Subject", "(no subject)"),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "label_ids": meta.get("labelIds", []),
                }
            )
        return results

    async def get_message_body(self, message_id: str) -> dict:
        """Fetch subject + decoded plain-text body for embedding."""
        data = await self._get(
            f"{GMAIL_API_BASE}/messages/{message_id}", params={"format": "full"}
        )
        payload = data.get("payload", {})
        headers = {
            h["name"]: h["value"] for h in payload.get("headers", [])
        }
        return {
            "id": message_id,
            "subject": headers.get("Subject", ""),
            "body": _extract_body(payload),
        }

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    async def list_labels(self) -> list[dict]:
        """Return all Gmail labels for the user."""
        data = await self._get(f"{GMAIL_API_BASE}/labels")
        return data.get("labels", [])

    async def create_label(self, name: str) -> dict:
        """Create a Gmail label. Returns the created label object (includes id)."""
        return await self._post(
            f"{GMAIL_API_BASE}/labels",
            json={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )

    async def apply_labels(
        self,
        message_id: str,
        add_label_ids: list[str],
        remove_label_ids: list[str] | None = None,
    ) -> None:
        """Add and/or remove labels on a message."""
        await self._post(
            f"{GMAIL_API_BASE}/messages/{message_id}/modify",
            json={
                "addLabelIds": add_label_ids,
                "removeLabelIds": remove_label_ids or [],
            },
        )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        body = _extract_body(part)
        if body:
            return body
    return ""
