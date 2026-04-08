from contextlib import asynccontextmanager

import os
import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import gmail, auth, user as user_api, label_records as label_records_api
from app.repositories.users import ensure_user_indexes
from app.repositories.presets import seed_preset_collection
from app.repositories.label_records import ensure_indexes as ensure_label_record_indexes
from config.db import connect_to_mongo, close_mongo_connection
from config.session import ensure_session_indexes
from dependencies.limiter import limiter

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_session_indexes()
    await ensure_user_indexes()
    await ensure_label_record_indexes()
    await seed_preset_collection()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key="SUPER_SECRET_SESSION_KEY",
    same_site="lax",    # Value='none' REQUIRED for prod.
    https_only=False,    # Value=True REQUIRED for cross-origin
)

app.include_router(auth.router)
app.include_router(user_api.router)
app.include_router(gmail.router)
app.include_router(label_records_api.router)

@app.get("/")
def read_root():
    return {"message": "Labl Server Connected!"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 