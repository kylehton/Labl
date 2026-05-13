"""Async Gmail REST API client with automatic access-token refresh."""
import asyncio
import base64
import logging
import os

import httpx
from datetime import datetime
from fastapi import HTTPException

from config.db import update_one

_MAX_RATE_LIMIT_RETRIES = 4

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
        self._http = httpx.AsyncClient()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    async def _refresh_access_token(self) -> None:
        """Exchange refresh token for a new access token, persist to session."""
        if not self.refresh_token:
            raise HTTPException(
                status_code=401, detail="Session expired — please log in again"
            )
        resp = await self._http.post(
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
    # Low-level HTTP helpers (auto-refresh on 401, backoff on 429)
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        ok_statuses: tuple[int, ...] = (200,),
    ) -> dict:
        """Send an authenticated request, handling token refresh and rate-limit backoff.

        - 401 on first attempt → refresh token, retry once.
        - 429 → honour Retry-After header if present, otherwise exponential backoff
          (2 ** attempt seconds); retries up to _MAX_RATE_LIMIT_RETRIES times.
        """
        if not self.access_token:
            await self._refresh_access_token()

        refreshed = False
        rate_attempts = 0

        while True:
            resp = await self._http.request(
                method,
                url,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if resp.status_code == 401 and not refreshed:
                await self._refresh_access_token()
                refreshed = True
                continue

            if resp.status_code == 429 and rate_attempts < _MAX_RATE_LIMIT_RETRIES:
                retry_after = resp.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = 2 ** rate_attempts
                else:
                    wait = 2 ** rate_attempts
                logger.warning(
                    "Gmail API rate limited (429). Waiting %.1fs before retry %d/%d.",
                    wait, rate_attempts + 1, _MAX_RATE_LIMIT_RETRIES,
                )
                await asyncio.sleep(wait)
                rate_attempts += 1
                continue

            if resp.status_code not in ok_statuses:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Gmail API error: {resp.text}",
                )
            return resp.json()

    async def _get(self, url: str, params: dict | None = None) -> dict:
        return await self._request("GET", url, params=params, ok_statuses=(200,))

    async def _post(self, url: str, json: dict) -> dict:
        return await self._request("POST", url, json=json, ok_statuses=(200, 201))

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def list_messages_since(
        self,
        after: datetime | None = None,
        max_results: int = 50,
        limit: int | None = None,
    ) -> list[dict]:
        """Return message metadata (id, snippet, subject, from, date) for inbox messages since `after`.

        When `after` is None (first-time full sync), paginates through all inbox messages
        using nextPageToken until exhausted, fetching 500 per page (Gmail's max).
        When `after` is set (incremental sync), fetches a single page up to `max_results`.

        `limit` caps the total number of messages returned regardless of sync mode.
        Useful for testing against a large inbox without waiting for a full sync.
        """
        full_sync = after is None
        if limit is not None:
            page_size = min(limit, 500)
        elif full_sync:
            page_size = 500
        else:
            page_size = max_results
        params: dict = {
            "maxResults": page_size,
            "labelIds": "INBOX",
        }
        if after:
            params["q"] = f"after:{int(after.timestamp())}"

        raw_messages: list[dict] = []
        while True:
            data = await self._get(f"{GMAIL_API_BASE}/messages", params=params)
            raw_messages.extend(data.get("messages", []))
            if limit is not None and len(raw_messages) >= limit:
                raw_messages = raw_messages[:limit]
                break
            next_page_token = data.get("nextPageToken")
            if not full_sync or not next_page_token:
                break
            params["pageToken"] = next_page_token

        # Fetch metadata for all messages concurrently, bounded to avoid rate limits.
        semaphore = asyncio.Semaphore(5)

        async def fetch_meta(msg: dict) -> dict:
            async with semaphore:
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
            return {
                "id": msg["id"],
                "thread_id": meta.get("threadId"),
                "snippet": meta.get("snippet", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "label_ids": meta.get("labelIds", []),
            }

        return list(await asyncio.gather(*[fetch_meta(m) for m in raw_messages]))

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
            "list_unsubscribe": headers.get("List-Unsubscribe") is not None,
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
