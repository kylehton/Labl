"""Celery task: run the full email labeling pipeline for a user.

The task is enqueued by GET /api/gmail/messages with the user's credentials
extracted from the session before the HTTP response is returned. It runs the
same logic that previously lived in the route handler, but in a background
worker process — so the user doesn't need to keep the tab open.

Async/sync bridging: the task function is synchronous (Celery workers are sync)
but the internal logic uses async motor/httpx. asyncio.run() creates a fresh
event loop per task invocation.
"""
import asyncio
import logging
from datetime import UTC, datetime

from config.celery_app import celery_app
from config.db import reconnect_for_worker

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.labeling.run_labeling_pipeline")
def run_labeling_pipeline(
    self,
    user_id: str,
    access_token: str,
    refresh_token: str | None,
    session_id: str | None,
    triggered_by: str = "manual",
    limit: int | None = None,
    debug: bool = False,
) -> dict:
    """Run the full email sync + labeling pipeline for one user.

    Args:
        user_id: Google user ID.
        access_token: Current Gmail OAuth access token.
        refresh_token: Gmail OAuth refresh token (may be None).
        session_id: Session cookie value, used by GmailClient for token refresh writes.
        triggered_by: "manual" or "auto" — recorded on the job result.
        limit: Optional cap on messages fetched (for testing).
        debug: If True, include per-label scores in results.

    Returns:
        {"summary": {...}, "count": int, "messages": [...]}
    """
    return asyncio.run(
        _run_async(
            task=self,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            triggered_by=triggered_by,
            limit=limit,
            debug=debug,
        )
    )


async def _run_async(
    task,
    user_id: str,
    access_token: str,
    refresh_token: str | None,
    session_id: str | None,
    triggered_by: str,
    limit: int | None,
    debug: bool,
) -> dict:
    # Each worker process needs its own MongoDB connection.
    await reconnect_for_worker()

    # Late imports — avoid loading the embedding model at Celery import time.
    from app.models.label_record import LabelRecord
    from app.repositories.label_records import insert_record
    from app.repositories.users import get_user_by_id, update_user_document
    from config.db import get_db
    from config.gmail import GmailClient
    from fastapi import HTTPException
    from ml.embeddings import load_model
    from ml.pipeline import batch_process_emails, confirm_label_batch

    load_model()

    client = GmailClient(
        access_token=access_token,
        refresh_token=refresh_token,
        session_id=session_id,
    )

    task_id = task.request.id

    # ------------------------------------------------------------------
    # Load user document
    # ------------------------------------------------------------------
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise RuntimeError(f"User {user_id} not found")

    last_checked = user_doc.last_checked
    labels = user_doc.labels
    auto_label = user_doc.auto_label

    # ------------------------------------------------------------------
    # Bootstrap Gmail label IDs for labels that don't have one yet
    # ------------------------------------------------------------------
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
            gmail_label_cache.update(gmail_by_name)
            cache_populated[0] = True
        except HTTPException as exc:
            logger.warning("Could not bootstrap Gmail label IDs: %s", exc)

    # ------------------------------------------------------------------
    # Fetch raw messages since last_checked
    # ------------------------------------------------------------------
    raw_messages = await client.list_messages_since(after=last_checked, limit=limit)

    user_label_ids = {
        lbl.gmail_label_id
        for lbl in labels.values()
        if lbl.gmail_label_id is not None
    }

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
    body_map: dict[str, dict] = {b["id"]: b for b in bodies if b is not None}

    pipeline_inputs = []
    pipeline_msg_refs = []
    already_labelled = []

    for msg in raw_messages:
        if set(msg.get("label_ids", [])) & user_label_ids:
            already_labelled.append(msg)
            continue
        full = body_map.get(msg["id"])
        if full is None:
            logger.warning("Skipping %s — body fetch failed", msg["id"])
            continue
        pipeline_inputs.append({
            "subject": full["subject"],
            "body": full["body"],
            "list_unsubscribe": full.get("list_unsubscribe", False),
        })
        pipeline_msg_refs.append((msg, full))

    # ------------------------------------------------------------------
    # Run pipeline
    # ------------------------------------------------------------------
    try:
        pipeline_results = batch_process_emails(
            pipeline_inputs, labels, auto_label=auto_label, debug=debug
        )
    except Exception as e:
        logger.error("Batch pipeline failed: %s", e, exc_info=True)
        raise

    # ------------------------------------------------------------------
    # Bucket results
    # ------------------------------------------------------------------
    direct_labels: list[tuple[str, str]] = []
    label_actions: dict[str, list[tuple[str, list[float], str]]] = {}
    suggest_tasks: list[tuple[str, str]] = []
    enriched = [{**m, "pipeline": None} for m in already_labelled]

    # (msg_id, label_name, action, source, score, vector) — collected for record writes
    record_queue: list[tuple[str, str, str, str, float | None, list[float] | None, str]] = []

    def _bucket_label(
        label_name: str,
        msg_id: str,
        vector: list[float] | None,
        text: str,
        action: str,
        source: str,
        score: float | None,
        subject: str,
    ) -> None:
        lbl = labels.get(label_name)
        if action == "label" and lbl and lbl.gmail_label_id:
            if vector is not None and (lbl.medoid is not None or lbl.clusters is not None):
                label_actions.setdefault(label_name, []).append((msg_id, vector, text))
            else:
                direct_labels.append((msg_id, lbl.gmail_label_id))
            record_queue.append((msg_id, label_name, "label", source, score, vector, subject))
        elif action == "suggest" and lbl:
            suggest_tasks.append((msg_id, label_name))
            record_queue.append((msg_id, label_name, "suggest", source, score, vector, subject))

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

        subject = full.get("subject", "")
        source = "rule" if result.get("score") == 1.0 and result["action"] in ("label", "suggest") and not result.get("vector") else "ml"
        # Refine: rule matches have score=1.0 and no vector in rule path
        is_rule = result.get("score") == 1.0 and result.get("vector") is not None and False
        source = "rule" if (result.get("score") == 1.0 and result.get("vector") is None) else "ml"

        _bucket_label(
            result["label_name"],
            msg["id"],
            result.get("vector"),
            result.get("text", ""),
            result["action"],
            source,
            result.get("score"),
            subject,
        )
        if ml:
            _bucket_label(
                ml["label_name"],
                msg["id"],
                result.get("vector"),
                result.get("text", ""),
                ml["action"],
                "ml",
                ml.get("score"),
                subject,
            )

        enriched.append({**msg, "pipeline": pipeline_summary})

    # ------------------------------------------------------------------
    # Apply labels — three passes
    # ------------------------------------------------------------------
    apply_sem = asyncio.Semaphore(5)

    if direct_labels:
        async def _apply_direct(mid: str, gid: str) -> None:
            async with apply_sem:
                await client.apply_labels(mid, add_label_ids=[gid])

        await asyncio.gather(*[_apply_direct(mid, gid) for mid, gid in direct_labels])

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

        mongo_updates: dict[str, object] = {}
        for label_name, items in label_actions.items():
            label = labels[label_name]
            new_items = [(vec, txt) for _, vec, txt in items]
            fields = confirm_label_batch(label, new_items)
            labels[label_name] = label.model_copy(update=fields)
            for k, v in fields.items():
                mongo_updates[f"labels.{label_name}.{k}"] = v

        await update_user_document(user_id, mongo_updates)

    if suggest_tasks:
        if not cache_populated[0]:
            try:
                all_labels = await client.list_labels()
                gmail_label_cache.update({l["name"]: l["id"] for l in all_labels})
                cache_populated[0] = True
            except HTTPException as e:
                logger.warning("Failed to populate label cache: %s", e)

        unique_suggest_names = dict.fromkeys(ln for _, ln in suggest_tasks)
        for ln in unique_suggest_names:
            suggested_name = f"Suggested: {ln}"
            if suggested_name not in gmail_label_cache:
                if not cache_populated[0]:
                    try:
                        all_labels = await client.list_labels()
                        gmail_label_cache.update({l["name"]: l["id"] for l in all_labels})
                        cache_populated[0] = True
                    except HTTPException:
                        pass
                if suggested_name not in gmail_label_cache:
                    try:
                        created = await client.create_label(suggested_name)
                        gmail_label_cache[suggested_name] = created["id"]
                    except HTTPException:
                        pass

        async def apply_suggestion(message_id: str, label_name: str) -> None:
            label_id = gmail_label_cache.get(f"Suggested: {label_name}")
            if label_id:
                async with apply_sem:
                    await client.apply_labels(message_id, add_label_ids=[label_id])

        await asyncio.gather(*[apply_suggestion(mid, ln) for mid, ln in suggest_tasks])

    # ------------------------------------------------------------------
    # Update last_checked
    # ------------------------------------------------------------------
    now = datetime.now(UTC)
    await update_user_document(user_id, {"last_checked": now})

    # ------------------------------------------------------------------
    # Write label records
    # ------------------------------------------------------------------
    for msg_id, label_name, action, source, score, vector, subject in record_queue:
        lbl = labels.get(label_name)
        status = "applied" if action == "label" else "suggested"
        record = LabelRecord(
            record_id="",  # assigned by insert_record
            user_id=user_id,
            task_id=task_id,
            gmail_message_id=msg_id,
            subject=subject,
            label_name=label_name,
            gmail_label_id=lbl.gmail_label_id if lbl else None,
            action=action,
            source=source,
            score=score,
            vector=vector,
            status=status,
            applied_at=now,
        )
        try:
            await insert_record(record)
        except Exception as e:
            logger.warning("Failed to write label record for %s/%s: %s", msg_id, label_name, e)

    # ------------------------------------------------------------------
    # Persist job result
    # ------------------------------------------------------------------
    actions = [m["pipeline"]["action"] for m in enriched if m.get("pipeline")]
    summary = {
        "total": len(enriched),
        "already_labelled": len(already_labelled),
        "labeled": actions.count("label"),
        "suggested": actions.count("suggest"),
        "no_match": (
            len(enriched) - len(already_labelled) - actions.count("label") - actions.count("suggest")
        ),
    }

    await get_db()["job_results"].insert_one({
        "task_id": task_id,
        "user_id": user_id,
        "triggered_by": triggered_by,
        "status": "done",
        "created_at": now,
        "completed_at": datetime.now(UTC),
        "summary": summary,
        "error": None,
    })

    return {"summary": summary, "count": len(enriched), "messages": enriched}
