from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dependencies.session_auth import require_auth
from urllib.parse import urlencode
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail")

### add all routes for gmail operations after storage + token system is fully concrete