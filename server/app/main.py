from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
import uvicorn
from api import google_auth

app = FastAPI()

app.include_router(google_auth.router)

@app.get("/")
def read_root():
    return {"message": "GSort Server Connected!"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)