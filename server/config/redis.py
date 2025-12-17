import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# Create a global Redis client
redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,  # Redis returns strings instead of bytes
)
