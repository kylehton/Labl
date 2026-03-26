"""Gmail API routes — fetch messages, manage labels, and run the labeling pipeline."""
import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel

from app.repositories.users import get_user_by_id, update_user_document
from config.gmail import GmailClient
from config.session import COOKIE_NAME
from dependencies.session_auth import require_auth
from app.models.label import Label
from ml.pipeline import batch_process_emails, confirm_label_batch

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
    client: GmailClient,
    label_name: str,
    gmail_label_cache: dict[str, str],
    cache_populated: list[bool],
) -> str | None:
    """Return the Gmail label ID for 'Suggested: <label_name>', creating it if needed.

    `gmail_label_cache` is a name→id dict populated lazily on the first suggestion so
    that list_labels() is never called when there are no suggest actions in a batch.
    `cache_populated` is a 1-element list used as a mutable boolean flag.
    """
    suggested_name = f"Suggested: {label_name}"
    if suggested_name in gmail_label_cache:
        return gmail_label_cache[suggested_name]

    # Populate cache from Gmail on first miss (lazy).
    if not cache_populated[0]:
        try:
            all_labels = await client.list_labels()
            gmail_label_cache.update({l["name"]: l["id"] for l in all_labels})
            cache_populated[0] = True
        except HTTPException as e:
            logger.warning("Failed to fetch Gmail labels for suggestion cache: %s", e)

    if suggested_name in gmail_label_cache:
        return gmail_label_cache[suggested_name]

    try:
        created = await client.create_label(suggested_name)
        gmail_label_cache[suggested_name] = created["id"]
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
    limit: int | None = Query(default=None, gt=0, description="Cap total messages fetched (for testing)"),
    debug: bool = Query(default=False, description="Include per-label scores in pipeline results, even for unmatched emails"),
):
    """Fetch inbox messages since last_checked, run the labeling pipeline, update last_checked.

    For each new message the pipeline result is included under the "pipeline" key:
      - action="label"   → label applied directly in Gmail + medoid/clusters updated
      - action="suggest" → "Suggested: <name>" label applied in Gmail
      - action="none"    → best match was below suggest_threshold (debug=true only)
      - pipeline=None    → no seeded labels yet, or message already labelled
      - ml_label         → secondary ML match for rule-matched emails (e.g. Subscription List
                           emails also scored against category labels like Promotions & Deals)

    Pass ?limit=N to cap the number of messages fetched — useful for testing against a large inbox.
    Pass ?debug=true to see per-label scores on every message, including those that didn't match.
    """
    user_id = session["user"]["user_id"]
    user_doc = await get_user_by_id(user_id)
    last_checked = user_doc.last_checked if user_doc else None
    labels = user_doc.labels if user_doc else {}
    auto_label = user_doc.auto_label if user_doc else False

    client = _gmail_client(session, request)

    # Bootstrap Gmail label IDs for any label that doesn't have one yet.
    # Preset labels are seeded from MongoDB with gmail_label_id=None; this step
    # looks them up (or creates them) in Gmail once, then persists the IDs so
    # subsequent requests skip this block entirely.
    labels_needing_ids = [n for n, lbl in labels.items() if not lbl.gmail_label_id]
    gmail_label_cache: dict[str, str] = {}
    cache_populated = [False]

    if labels_needing_ids:
        try:
            all_gmail = await client.list_labels()
            gmail_by_name = {l["name"]: l["id"] for l in all_gmail}
            gmail_id_updates: dict[str, str] = {}
            for name in labels_needing_ids:
                if name in gmail_by_name:
                    gmail_id_updates[name] = gmail_by_name[name]
                else:
                    try:
                        created = await client.create_label(name)
                        gmail_id_updates[name] = created["id"]
                        gmail_by_name[name] = created["id"]
                    except HTTPException as exc:
                        logger.warning("Could not create Gmail label '%s': %s", name, exc)
            if gmail_id_updates:
                id_mongo = {f"labels.{n}.gmail_label_id": gid for n, gid in gmail_id_updates.items()}
                await update_user_document(user_id, id_mongo)
                for name, gid in gmail_id_updates.items():
                    labels[name] = labels[name].model_copy(update={"gmail_label_id": gid})
            # Cache is already populated — avoid a second list_labels() call later.
            gmail_label_cache.update(gmail_by_name)
            cache_populated[0] = True
        except HTTPException as exc:
            logger.warning("Could not bootstrap Gmail label IDs: %s", exc)

    raw_messages = await client.list_messages_since(after=last_checked, limit=limit)

    # IDs of labels the user has defined (to skip already-labelled messages)
    user_label_ids = {
        lbl.gmail_label_id
        for lbl in labels.values()
        if lbl.gmail_label_id is not None
    }

    # Pre-fetch full bodies for all unlabelled messages concurrently.
    sem = asyncio.Semaphore(5)

    async def fetch_body(msg: dict) -> dict | None:
        if set(msg.get("label_ids", [])) & user_label_ids:
            return None
        async with sem:
            try:
                return await client.get_message_body(msg["id"])
            except Exception as e:
                logger.warning("Failed to fetch body for %s: %s", msg["id"], e)
                return None

    bodies = await asyncio.gather(*[fetch_body(m) for m in raw_messages])
    body_map: dict[str, dict] = {
        b["id"]: b for b in bodies if b is not None
    }

    # Build input list for batch pipeline — only messages whose bodies were fetched.
    pipeline_inputs = []
    pipeline_msg_refs = []
    already_labelled = []

    for msg in raw_messages:
        if set(msg.get("label_ids", [])) & user_label_ids:
            already_labelled.append(msg)
            continue
        full = body_map.get(msg["id"])
        if full is None:
            # Body fetch failed — skip silently so the message is retried next sync.
            # Do NOT add to already_labelled; last_checked will not advance past it.
            logger.warning("Skipping message %s — body fetch failed, will retry next sync", msg["id"])
            continue
        pipeline_inputs.append({
            "subject": full["subject"],
            "body": full["body"],
            "list_unsubscribe": full.get("list_unsubscribe", False),
        })
        pipeline_msg_refs.append((msg, full))

    # Run all embeddings in one batched encode() call.
    try:
        pipeline_results = batch_process_emails(
            pipeline_inputs, labels, auto_label=auto_label, debug=debug
        )
    except Exception as e:
        logger.error("Batch pipeline failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Email classification pipeline failed")

    # --- Apply labels ---
    # Pass 1: scan results, bucket into three lists:
    #   direct_labels  — apply Gmail label only, no medoid update (rule-matched or unseeded)
    #   label_actions  — apply Gmail label + update medoid/clusters (seeded ML match)
    #   suggest_tasks  — create/apply "Suggested: X" label
    # Rule-matched results also carry an "ml_label" secondary match (a category label);
    # that secondary label is routed through the same buckets independently.

    direct_labels: list[tuple[str, str]] = []          # (msg_id, gmail_label_id)
    label_actions: dict[str, list[tuple[str, list[float], str]]] = {}
    suggest_tasks: list[tuple[str, str]] = []           # (msg_id, label_name)
    enriched = [{**m, "pipeline": None} for m in already_labelled]

    def _bucket_label(
        label_name: str,
        msg_id: str,
        vector: list[float] | None,
        text: str,
        action: str,
    ) -> None:
        """Route a single (label, msg) pair into the appropriate bucket."""
        lbl = labels.get(label_name)
        if action == "label" and lbl and lbl.gmail_label_id:
            if vector is not None and (lbl.medoid is not None or lbl.clusters is not None):
                label_actions.setdefault(label_name, []).append((msg_id, vector, text))
            else:
                direct_labels.append((msg_id, lbl.gmail_label_id))
        elif action == "suggest" and lbl:
            suggest_tasks.append((msg_id, label_name))

    for (msg, full), result in zip(pipeline_msg_refs, pipeline_results):
        if result is None:
            enriched.append({**msg, "pipeline": None})
            continue

        pipeline_summary: dict = {
            "label_name": result["label_name"],
            "score": round(result["score"], 4),
            "action": result["action"],
        }
        ml = result.get("ml_label")
        if ml:
            pipeline_summary["ml_label"] = {
                "label_name": ml["label_name"],
                "score": round(ml["score"], 4),
                "action": ml["action"],
            }
        if debug and result.get("all_scores"):
            pipeline_summary["all_scores"] = result["all_scores"]

        _bucket_label(
            result["label_name"],
            msg["id"],
            result.get("vector"),
            result.get("text", ""),
            result["action"],
        )
        if ml:
            _bucket_label(
                ml["label_name"],
                msg["id"],
                result.get("vector"),
                result.get("text", ""),
                ml["action"],
            )

        enriched.append({**msg, "pipeline": pipeline_summary})

    # Shared semaphore for all label-apply passes — keeps concurrent Gmail
    # modify requests under the per-user rate limit across all three phases.
    apply_sem = asyncio.Semaphore(5)

    # Pass 2a: apply rule-matched labels concurrently (no medoid update needed).
    if direct_labels:
        async def _apply_direct(mid: str, gid: str) -> None:
            async with apply_sem:
                await client.apply_labels(mid, add_label_ids=[gid])

        await asyncio.gather(*[_apply_direct(mid, gid) for mid, gid in direct_labels])

    # Pass 2b: apply ML-matched labels concurrently, then batch-update medoids.
    if label_actions:
        async def _apply_ml(msg_id: str, gmail_label_id: str) -> None:
            async with apply_sem:
                await client.apply_labels(msg_id, add_label_ids=[gmail_label_id])

        apply_label_tasks = [
            _apply_ml(msg_id, labels[ln].gmail_label_id)
            for ln, items in label_actions.items()
            for msg_id, _, _ in items
            if labels[ln].gmail_label_id
        ]
        await asyncio.gather(*apply_label_tasks)

        # One medoid/cluster recomputation + one DB write per label (not per email).
        mongo_updates: dict[str, object] = {}
        for label_name, items in label_actions.items():
            label = labels[label_name]
            new_items = [(vec, txt) for _, vec, txt in items]
            fields = confirm_label_batch(label, new_items)
            labels[label_name] = label.model_copy(update=fields)
            for k, v in fields.items():
                mongo_updates[f"labels.{label_name}.{k}"] = v

        await update_user_document(user_id, mongo_updates)

    # Pass 3: apply suggested labels.
    # Two-step to avoid a race condition: if we ran all apply_suggestion coroutines
    # concurrently, every one of them would see cache_populated=False and call
    # list_labels() simultaneously (13+ concurrent GET /labels → 429).
    # Instead: populate cache once, create each unique "Suggested: X" label
    # sequentially, then stamp messages concurrently (different endpoints, safe).
    if suggest_tasks:
        # Ensure cache is populated before anything else touches it.
        if not cache_populated[0]:
            try:
                all_labels = await client.list_labels()
                gmail_label_cache.update({l["name"]: l["id"] for l in all_labels})
                cache_populated[0] = True
            except HTTPException as e:
                logger.warning("Failed to populate label cache for suggestions: %s", e)

        # Create any missing "Suggested: X" labels sequentially (avoids duplicate creates).
        unique_suggest_names = dict.fromkeys(ln for _, ln in suggest_tasks)
        for ln in unique_suggest_names:
            await _get_or_create_suggested_label_id(client, ln, gmail_label_cache, cache_populated)

        # All IDs are now in cache — apply to messages concurrently.
        async def apply_suggestion(message_id: str, label_name: str) -> None:
            label_id = gmail_label_cache.get(f"Suggested: {label_name}")
            if label_id:
                async with apply_sem:
                    await client.apply_labels(message_id, add_label_ids=[label_id])

        await asyncio.gather(*[apply_suggestion(mid, ln) for mid, ln in suggest_tasks])

    await update_user_document(user_id, {"last_checked": datetime.now(UTC)})

    actions = [m["pipeline"]["action"] for m in enriched if m.get("pipeline")]
    summary = {
        "total": len(enriched),
        "already_labelled": len(already_labelled),
        "labeled": actions.count("label"),
        "suggested": actions.count("suggest"),
        "no_match": actions.count("none") if debug else (
            len(enriched) - len(already_labelled) - actions.count("label") - actions.count("suggest")
        ),
    }

    return {"summary": summary,"count": len(enriched), "messages": enriched }


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
