"""Cấu hình đọc từ biến môi trường (hoặc file .env ở thư mục gốc)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# Model cho kiến trúc sư, nhà văn, biên tập viên sửa, thủ thư
MODEL = os.getenv("NOVEL_MODEL", "claude-opus-5")
# Model cho hội đồng phê bình (có thể đặt model khác để có "góc nhìn" khác)
CRITIC_MODEL = os.getenv("NOVEL_CRITIC_MODEL", MODEL)
# Mức suy nghĩ: low | medium | high | xhigh | max
WRITER_EFFORT = os.getenv("NOVEL_WRITER_EFFORT", "high")
CRITIC_EFFORT = os.getenv("NOVEL_CRITIC_EFFORT", "medium")
# 1 = khi model chính từ chối (refusal) thì API tự chạy lại trên model dự phòng
FALLBACKS = os.getenv("NOVEL_FALLBACKS", "1") == "1"

# Vòng phản biện: chương đạt khi MỌI nhà phê bình chấm >= PASS_SCORE và không còn lỗi nghiêm trọng
PASS_SCORE = float(os.getenv("NOVEL_PASS_SCORE", "8"))
MAX_REVISIONS = int(os.getenv("NOVEL_MAX_REVISIONS", "3"))
# Số chương gần nhất được tóm tắt chi tiết trong ngữ cảnh (chương cũ hơn gộp theo phần)
RECENT_CHAPTERS = int(os.getenv("NOVEL_RECENT_CHAPTERS", "5"))
# Số ký tự cuối chương trước đưa nguyên văn cho nhà văn để nối mạch câu chữ
TAIL_CHARS = int(os.getenv("NOVEL_TAIL_CHARS", "3000"))

NOVEL_DIR = Path(os.getenv("NOVEL_DIR", str(ROOT / "data" / "novels")))
SCRIPT_DIR = Path(os.getenv("SCRIPT_DIR", str(ROOT / "data" / "scripts")))

# 1 = chạy giả lập (không gọi API, không tốn tiền) để thử quy trình
MOCK = os.getenv("NOVEL_MOCK", "0") == "1"
