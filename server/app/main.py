from contextlib import asynccontextmanager

import os
import uvicorn
from fastapi import FastAPI

from app.api import gmail, auth, user as user_api
from app.repositories.users import ensure_user_indexes
from app.repositories.presets import seed_preset_collection
from config.db import connect_to_mongo, close_mongo_connection
from config.session import ensure_session_indexes
from ml.embeddings import load_model

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await ensure_session_indexes()
    await ensure_user_indexes()
    load_model()
    await seed_preset_collection()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)

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

@app.get("/")
def read_root():
    return {"message": "Labl Server Connected!"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 