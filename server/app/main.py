from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
import uvicorn
from app.api import user_auth

from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

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


app.include_router(user_auth.router)

@app.get("/")
def read_root():
    return {"message": "GSort Server Connected!"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)