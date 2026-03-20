# Labl

Automated Gmail inbox management using centroid-based semantic labeling. Users define custom labels by selecting seed emails; incoming mail is embedded and matched against label centroids to auto-label or suggest labels directly in Gmail.

---

## Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI (Python 3.14) |
| Database | MongoDB (via motor — async) |
| Embeddings | `BAAI/bge-small-en-v1.5` (local, via sentence-transformers) |
| Auth | Google OAuth 2.0 (Gmail scopes) |
| Sessions | MongoDB `sessions` collection (TTL index, encrypted refresh token) |
| Frontend | Next.js 16 (App Router, Tailwind, Radix UI) |

---

## Server Setup

### Environment variables

Create `server/.env`:

```env
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net
MONGO_DB_NAME=labl

GOOGLE_OAUTH_CLIENT_ID=<your-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/user/auth/login/callback

FRONTEND_URL=http://localhost:3000
SESSION_COOKIE_NAME=labl_session
SESSION_TTL_SECONDS=2592000

FERNET_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

SECURE_COOKIE=false
```

### Install dependencies

```bash
cd server

# Create venv if not already done
python3 -m venv .venv
source .venv/bin/activate

# CPU-only torch (smaller install — ~500MB vs ~2GB)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# All other dependencies
pip install -r requirements.txt
```

> On first server start, `bge-small-en-v1.5` (~130MB) is downloaded and cached automatically.

### Run the server

```bash
cd server
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Run tests

```bash
cd server
source .venv/bin/activate
pytest tests/ -v
```

---

## API Endpoints

Base URL: `http://localhost:8000`

All endpoints except `/api/user/auth/login` and `/api/user/auth/login/callback` require an active session cookie (`labl_session`).

---

### Auth

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/user/auth/login` | Redirect to Google OAuth consent screen |
| `GET` | `/api/user/auth/login/callback` | OAuth callback — creates session, sets cookie, redirects to frontend |
| `GET` | `/api/user/auth/status` | Returns `{ authenticated: bool, user? }` |
| `POST` | `/api/user/auth/logout` | Deletes session, clears cookie |

---

### User

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/user` | Returns full user document (profile, labels, settings) |
| `PATCH` | `/api/user` | Update user document. Allowed fields: `auto_label` (bool), `labels` |

**PATCH `/api/user` example:**

```json
{ "auto_label": true }
```

---

### Labels — Seeding

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/user/labels/{label_name}/seed` | Compute centroid from seed emails. Label must exist first (create via `POST /api/gmail/labels`). |

**POST `/api/user/labels/Work/seed` body:**

```json
{ "message_ids": ["abc123", "def456", "ghi789"] }
```

**Response:**

```json
{ "label_name": "Work", "seeded_with": 3, "centroid_dim": 384 }
```

> `label_name` in the path must match exactly what was used when creating the label.

---

### Gmail — Messages

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/gmail/messages` | Fetch inbox messages since `last_checked`, run labeling pipeline, update `last_checked` |
| `GET` | `/api/gmail/messages/{message_id}/body` | Fetch full subject + plain-text body of a single message |
| `POST` | `/api/gmail/messages/{message_id}/label` | Manually apply/remove Gmail labels on a message |

**GET `/api/gmail/messages` response shape:**

```json
{
  "messages": [
    {
      "id": "abc123",
      "thread_id": "xyz",
      "subject": "Q3 budget review",
      "from": "alice@company.com",
      "date": "Mon, 17 Mar 2026 10:00:00 +0000",
      "snippet": "Hi, please review the attached...",
      "label_ids": ["INBOX"],
      "pipeline": {
        "label_name": "Work",
        "score": 0.8821,
        "action": "label"
      }
    }
  ],
  "count": 1
}
```

`pipeline` is `null` if no labels are seeded yet or the message was already labelled.

`action` values:

- `"label"` — confidence above threshold; Gmail label applied, centroid updated via EMA
- `"suggest"` — below threshold or `auto_label=false`; `"Suggested: <name>"` Gmail label applied

**POST `/api/gmail/messages/{message_id}/label` body:**

```json
{ "label_ids": ["Label_42"], "remove_label_ids": ["INBOX"] }
```

---

### Gmail — Labels

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/gmail/labels` | List all Gmail labels for the user |
| `POST` | `/api/gmail/labels` | Create a Gmail label and register it in MongoDB (centroid=null until seeded) |

**POST `/api/gmail/labels` body:**

```json
{ "name": "Work" }
```

**Response:**

```json
{
  "label": { "id": "Label_42", "name": "Work", "type": "user" },
  "stored": {
    "name": "Work",
    "type": "custom",
    "gmail_label_id": "Label_42",
    "centroid": null,
    "count": 0,
    "confidence": 0.0
  }
}
```

---

## Live Testing Workflow

Suggested sequence for testing with a real Gmail account:

1. **Login** — `GET /api/user/auth/login` in browser → complete OAuth → confirm `labl_session` cookie is set
2. **Check auth** — `GET /api/user/auth/status` → should return `{ authenticated: true, user: {...} }`
3. **Check user doc** — `GET /api/user` → confirm user document in MongoDB
4. **Create a label** — `POST /api/gmail/labels` `{ "name": "Work" }` → confirm label appears in Gmail sidebar and MongoDB
5. **Seed the label** — find 3–5 email message IDs in Gmail that belong to that label, then `POST /api/user/labels/Work/seed` `{ "message_ids": [...] }` → confirm `centroid_dim: 384` in response
6. **Verify centroid stored** — `GET /api/user` → `labels.Work.centroid` should be a 384-element float array
7. **Run the pipeline** — `GET /api/gmail/messages` → inspect `pipeline` field on each message; check Gmail inbox for applied / suggested labels
8. **Toggle auto-label** — `PATCH /api/user` `{ "auto_label": true }` → re-run `GET /api/gmail/messages` and verify direct labels are applied (not `Suggested:`)

---

## How to Find Gmail Message IDs

Message IDs are not shown in the Gmail UI. Options:

- **`GET /api/gmail/messages`** — the `id` field in each returned message is the Gmail message ID; use these for seeding
- **Gmail API Explorer** — `GET /gmail/v1/users/me/messages` at [developers.google.com/gmail/api/reference/rest](https://developers.google.com/gmail/api/reference/rest)

---

## MongoDB Collections

| Collection | Purpose |
| --- | --- |
| `users` | User profile, label store (with centroids), `auto_label` flag, `last_checked` timestamp |
| `sessions` | Active sessions with encrypted refresh tokens; TTL index auto-expires stale sessions |

**`users` document shape:**

```json
{
  "user": { "user_id": "...", "email": "...", "name": "..." },
  "auto_label": false,
  "last_checked": "2026-03-19T10:00:00Z",
  "labels": {
    "Work": {
      "name": "Work",
      "type": "custom",
      "gmail_label_id": "Label_42",
      "centroid": [0.021, -0.043, "..."],
      "count": 5,
      "confidence": 0.0
    }
  },
  "updated_at": "2026-03-19T10:00:00Z"
}
```
