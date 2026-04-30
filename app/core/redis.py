from app.core.config import Settings
import redis


redis_client = redis.Redis(
    host=Settings.redis_host,
    port=Settings.redis_port,
    username=Settings.redis_username,
    password=Settings.redis_password,
)

TRANSCRIPTION_QUEUE = "transcription_queue"
ANALYSIS_QUEUE = "analysis_queue"



