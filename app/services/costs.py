"""Ước tính chi phí vận hành mỗi tháng.

Giá Claude API (USD / 1 triệu token) theo bảng giá công bố của Anthropic, cập nhật 06/2026.
Kiểm tra lại tại https://www.anthropic.com/pricing trước khi chốt ngân sách.
"""
from app import config, db

PRICES = {
    # model: (input, output)
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Token trung bình (ước lượng, được thay bằng số đo thật khi chạy):
INPUT_TOKENS = 600                 # 1 bài viết: hướng dẫn + thông tin sản phẩm
CAPTION_OUT = 400                  # ~100 chữ tiếng Việt
THINKING_OUT = {"claude-haiku": 0, "claude-sonnet": 300, "claude-opus": 650}   # phần AI "suy nghĩ" thêm
BRIEF_TEXT_IN, BRIEF_OUT = 700, 350  # soạn chữ cho bộ ảnh + video (1 lần / sản phẩm, dùng lại cho mọi phiên bản)
IMAGES_PER_BRIEF = 5
POSTS_PER_PRODUCT = 10             # giả định: mỗi sản phẩm được đăng ~10 lần trên các page -> số sản phẩm mới/tháng


def _thinking(model: str) -> int:
    return next((v for k, v in THINKING_OUT.items() if model.startswith(k)), 0)


def _price(model: str) -> tuple[float, float]:
    return PRICES[next(m for m in sorted(PRICES, key=len, reverse=True) if model.startswith(m))]


def vps_usd(pages: int) -> float:
    """Máy chủ (VPS) theo quy mô, USD/tháng (dựng video cần CPU hơn)."""
    return 8 if pages <= 100 else 16 if pages <= 250 else 32


def cost_per_caption(model: str, batch: bool = True) -> float:
    price_in, price_out = _price(model)
    usd = (INPUT_TOKENS * price_in + (CAPTION_OUT + _thinking(model)) * price_out) / 1_000_000
    return usd / 2 if batch else usd


def cost_per_kit(model: str, image_side: int) -> float:
    """Chi phí AI soạn chữ cho bộ ảnh + video của 1 sản phẩm (ảnh + dựng video chạy trên máy chủ, không tốn token)."""
    price_in, price_out = _price(model)
    image_tokens = IMAGES_PER_BRIEF * (image_side * image_side / 750)
    return ((BRIEF_TEXT_IN + image_tokens) * price_in + (BRIEF_OUT + _thinking(model)) * price_out) / 1_000_000


def estimate(pages: int, posts_per_day: float, tier: str) -> dict:
    from app.services import ai_models

    caption_model = ai_models.model_for("caption", tier)
    creative_model = ai_models.model_for("creative", tier)
    captions = round(pages * posts_per_day * 30)
    products = max(1, round(captions / POSTS_PER_PRODUCT))
    ai = captions * cost_per_caption(caption_model) + products * cost_per_kit(creative_model, ai_models.IMAGE_SIDE[tier])
    vps = vps_usd(pages)
    total = ai + vps
    return {"pages": pages, "captions": captions, "products": products, "ai_usd": ai, "vps_usd": vps,
            "total_usd": total, "total_vnd": total * config.USD_VND}


def actual_this_month(conn) -> dict:
    """Chi phí AI thật đã phát sinh trong tháng (từ số token Claude trả về)."""
    month = db.now().strftime("%Y-%m")
    rows = conn.execute(
        """SELECT model, batch, COUNT(*) AS calls, SUM(input_tokens) AS tin, SUM(output_tokens) AS tout
           FROM ai_usage WHERE substr(ts, 1, 7) = ? GROUP BY model, batch""",
        (month,),
    ).fetchall()
    usd, calls = 0.0, 0
    for r in rows:
        base = next((m for m in sorted(PRICES, key=len, reverse=True) if r["model"].startswith(m)), None)
        if not base:
            continue
        price_in, price_out = PRICES[base]
        cost = (r["tin"] * price_in + r["tout"] * price_out) / 1_000_000
        usd += cost / 2 if r["batch"] else cost
        calls += r["calls"]
    return {"calls": calls, "usd": usd, "vnd": usd * config.USD_VND,
            "per_caption_usd": usd / calls if calls else 0}
