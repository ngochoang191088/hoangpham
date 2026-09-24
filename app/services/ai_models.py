"""Chọn model Claude theo từng việc, theo "chế độ AI" trong Cài đặt.

Mỗi việc cần mức thông minh khác nhau, nên không cần dùng model đắt cho mọi việc:
  - classify: xếp sản phẩm vào ngành hàng (việc rất dễ)
  - creative: xem ảnh sản phẩm, soạn chữ ngắn in lên ảnh / video
  - caption:  viết bài đăng Facebook

Chế độ:
  save      Tiết kiệm nhất: Claude Haiku 4.5 cho mọi việc (không bật suy nghĩ, ảnh gửi AI thu nhỏ).
  balanced  Cân bằng: bài đăng dùng Claude Sonnet 5 (effort thấp), còn lại Haiku 4.5.
  quality   Chất lượng cao: bài đăng + chữ trên ảnh dùng model AI_MODEL (mặc định Claude Opus 5).
"""
from app import config, db

TIERS = {
    "save": {"classify": "claude-haiku-4-5", "creative": "claude-haiku-4-5", "caption": "claude-haiku-4-5"},
    "balanced": {"classify": "claude-haiku-4-5", "creative": "claude-haiku-4-5", "caption": "claude-sonnet-5"},
    "quality": {"classify": "claude-haiku-4-5", "creative": None, "caption": None},   # None = config.AI_MODEL
}
TIER_LABELS = {
    "save": "Tiết kiệm nhất: Claude Haiku 4.5 cho mọi việc",
    "balanced": "Cân bằng: bài đăng Claude Sonnet 5, còn lại Haiku 4.5",
    "quality": "Chất lượng cao: bài đăng + chữ trên ảnh dùng Claude Opus 5",
}
# Cạnh dài tối đa của ảnh gửi cho AI. Chi phí ảnh ≈ (rộng x cao) / 750 token: 512px ≈ 350 token, 768px ≈ 790 token.
IMAGE_SIDE = {"save": 512, "balanced": 512, "quality": 768}


def tier() -> str:
    with db.get_conn() as conn:
        value = db.get_settings(conn).get("ai_tier", "save")
    return value if value in TIERS else "save"


def model_for(task: str, current_tier: str | None = None) -> str:
    return TIERS[current_tier or tier()][task] or config.AI_MODEL


def request_options(model: str) -> dict:
    """Tham số theo model: Haiku không bật suy nghĩ; Sonnet/Opus giới hạn effort để tiết kiệm token."""
    if model.startswith("claude-haiku"):
        return {}
    effort = "low" if model.startswith("claude-sonnet") else config.AI_EFFORT
    return {"output_config": {"effort": effort}}
