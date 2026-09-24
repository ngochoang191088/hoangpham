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
MODEL_LABELS = {
    "claude-opus-5": "Claude Opus 5 (viết hay nhất)",
    "claude-sonnet-5": "Claude Sonnet 5 (cân bằng)",
    "claude-haiku-4-5": "Claude Haiku 4.5 (rẻ nhất)",
}

# Token trung bình cho 1 caption tiếng Việt ~100 chữ (ước lượng, sẽ được thay bằng số đo thật khi chạy):
INPUT_TOKENS = 600                 # hướng dẫn + thông tin sản phẩm
OUTPUT_TOKENS_THINKING = 1000      # nội dung (~350) + phần AI suy nghĩ trước khi viết
OUTPUT_TOKENS_NO_THINKING = 400    # Haiku: không bật suy nghĩ

# Máy chủ (VPS) theo quy mô, USD/tháng
def vps_usd(pages: int) -> float:
    return 6 if pages <= 100 else 12 if pages <= 250 else 24


def cost_per_caption(model: str, batch: bool, input_tokens: float | None = None,
                     output_tokens: float | None = None) -> float:
    price_in, price_out = PRICES[model]
    tin = input_tokens if input_tokens is not None else INPUT_TOKENS
    tout = output_tokens if output_tokens is not None else (
        OUTPUT_TOKENS_NO_THINKING if model.startswith("claude-haiku") else OUTPUT_TOKENS_THINKING)
    usd = (tin * price_in + tout * price_out) / 1_000_000
    return usd / 2 if batch else usd


def estimate(pages: int, posts_per_day: float, model: str, batch: bool = True) -> dict:
    captions = round(pages * posts_per_day * 30)
    ai = captions * cost_per_caption(model, batch)
    vps = vps_usd(pages)
    total = ai + vps
    return {"pages": pages, "captions": captions, "ai_usd": ai, "vps_usd": vps,
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
