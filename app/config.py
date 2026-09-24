import os
from pathlib import Path
from zoneinfo import ZoneInfo


def _load_dotenv() -> None:
    """Đọc file .env ở thư mục gốc (nếu có) mà không cần thư viện ngoài."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

FB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v23.0")

SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-opus-5")
AI_EFFORT = os.getenv("AI_EFFORT", "medium")
# Từ AI_BATCH_MIN bài trở lên thì dùng Message Batches API (giảm 50% chi phí)
AI_BATCH = os.getenv("AI_BATCH", "1") == "1"
AI_BATCH_MIN = int(os.getenv("AI_BATCH_MIN", "20"))
USD_VND = float(os.getenv("USD_VND", "26000"))

DB_PATH = os.getenv("DB_PATH", "data/app.db")
TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"))

FB_ENABLED = bool(FB_SYSTEM_USER_TOKEN)
SHOPEE_ENABLED = bool(SHOPEE_APP_ID and SHOPEE_APP_SECRET)
AI_ENABLED = bool(ANTHROPIC_API_KEY)
DEMO_MODE = not (FB_ENABLED and SHOPEE_ENABLED)
