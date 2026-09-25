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
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Đăng nhập bằng Facebook cá nhân: app tự nhận diện mọi page tài khoản đang quản lý
FB_APP_ID = os.getenv("FB_APP_ID", "")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")
# Địa chỉ public của app, dùng làm redirect sau khi đăng nhập Facebook
# (Render.com tự cung cấp RENDER_EXTERNAL_URL = link https của app)
BASE_URL = (os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000").rstrip("/")
# (Tuỳ chọn) token System User nếu page nằm trong Meta Business Portfolio
FB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v23.0")

SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")
# Tự đọc thông tin + ảnh sản phẩm từ link Shopee (0 = tắt, dùng khi máy chủ không ra được Internet)
SHOPEE_FETCH = os.getenv("SHOPEE_FETCH", "1") == "1"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-opus-5")
AI_EFFORT = os.getenv("AI_EFFORT", "medium")
# Từ AI_BATCH_MIN bài trở lên thì dùng Message Batches API (giảm 50% chi phí)
AI_BATCH = os.getenv("AI_BATCH", "1") == "1"
AI_BATCH_MIN = int(os.getenv("AI_BATCH_MIN", "20"))
USD_VND = float(os.getenv("USD_VND", "26000"))

# Google Gemini API (aistudio.google.com) để tạo video bằng Veo 3.1. Để trống = giả lập (không tốn tiền).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.1-lite-generate-001")
VEO_RESOLUTION = os.getenv("VEO_RESOLUTION", "720p")
VEO_SECONDS = int(os.getenv("VEO_SECONDS", "8"))
# Ảnh AI (Nano Banana): đặt sản phẩm thật vào bối cảnh mới. Cùng GEMINI_API_KEY với Veo.
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-3.1-flash-image")

DB_PATH = os.getenv("DB_PATH", "data/app.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
MEDIA_DIR = os.getenv("MEDIA_DIR", "data/media")      # ảnh gốc tải về + ảnh/video app tạo
MUSIC_DIR = os.getenv("MUSIC_DIR", "data/music")      # nhạc nền (mp3) bạn có quyền sử dụng, tuỳ chọn
SECRET_KEY = os.getenv("SECRET_KEY", "doi-chuoi-bi-mat-nay")
# Chỉ các tài khoản Facebook này được đăng nhập (ID, cách nhau dấu phẩy).
# Để trống: người đăng nhập đầu tiên thành chủ app, người khác bị chặn.
ALLOWED_FB_USERS = [x.strip() for x in os.getenv("ALLOWED_FB_USERS", "").split(",") if x.strip()]
def _timezone():
    """Giờ Việt Nam. Windows không có sẵn dữ liệu múi giờ (cần gói tzdata): khi thiếu thì dùng UTC+7."""
    try:
        return ZoneInfo(os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh"))
    except Exception:  # noqa: BLE001 - ZoneInfoNotFoundError / thiếu tzdata
        from datetime import timedelta, timezone

        return timezone(timedelta(hours=7), "UTC+07")


TZ = _timezone()

FB_LOGIN_ENABLED = bool(FB_APP_ID and FB_APP_SECRET)
FB_ENABLED = FB_LOGIN_ENABLED or bool(FB_SYSTEM_USER_TOKEN)
SHOPEE_ENABLED = bool(SHOPEE_APP_ID and SHOPEE_APP_SECRET)
AI_ENABLED = bool(ANTHROPIC_API_KEY)
DEMO_MODE = not FB_ENABLED
