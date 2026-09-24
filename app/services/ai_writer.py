"""Viết caption bằng Claude API và kiểm duyệt nội dung tự động."""
import random

from app import config

SYSTEM_PROMPT = """Bạn là người viết nội dung cho fanpage Facebook bán hàng tiếp thị liên kết Shopee tại Việt Nam.

Quy tắc bắt buộc:
- Chỉ dùng thông tin sản phẩm được cung cấp. Không bịa công dụng, chứng nhận, khuyến mãi hay giá.
- Không viết như thể page/người viết đã tự dùng sản phẩm ("mình dùng rồi", "review thật") và không tạo đánh giá giả.
- Không hứa hẹn chữa bệnh, giảm cân, hay kết quả chắc chắn.
- Không chèn link (hệ thống tự thêm link sau).
- Viết tiếng Việt tự nhiên, 50–110 chữ, tối đa 4 emoji, có lời kêu gọi xem sản phẩm ở cuối.
- Chỉ trả về nội dung bài đăng, không giải thích thêm."""

ANGLES = [
    "deal hời hôm nay (nhấn vào giá và lượt bán)",
    "giải quyết một vấn đề thường gặp trong cuộc sống",
    "gợi ý quà tặng",
    "mẹo sử dụng / lý do nên cân nhắc",
    "so sánh ngắn với lựa chọn thông thường (không nêu tên thương hiệu khác)",
]


def _n(value) -> str:
    return f"{int(value):,}".replace(",", ".")


def _facts(product: dict) -> str:
    return (
        f"Tên: {product['name']}\n"
        f"Giá từ: {_n(product['price'])}đ\n"
        f"Đã bán: {_n(product['sales'])}\n"
        f"Đánh giá: {product['rating']}/5\n"
        f"Shop: {product['shop_name']}"
    )


def write_caption(page: dict, product: dict, disclosure: str) -> str:
    angle = random.choice(ANGLES)
    if config.AI_ENABLED:
        text = _claude_caption(page, product, angle)
    else:
        text = _template_caption(product, angle)
    return f"{text.strip()}\n\n{disclosure}"


def _claude_caption(page: dict, product: dict, angle: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.beta.messages.create(
        model=config.AI_MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Page: {page['name']} (ngách: {page['niche']}; giọng văn: {page['tone']})\n"
                f"Góc viết: {angle}\n\nThông tin sản phẩm:\n{_facts(product)}"
            ),
        }],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("AI từ chối viết bài cho sản phẩm này")
    return "".join(b.text for b in response.content if b.type == "text")


def _template_caption(product: dict, angle: str) -> str:
    """Caption mẫu dùng khi chưa có ANTHROPIC_API_KEY (chế độ DEMO)."""
    price = f"{_n(product['price'])}đ"
    openers = {
        ANGLES[0]: f"🔥 Deal đang hot: {product['name']} chỉ từ {price}!",
        ANGLES[1]: f"Bạn đang cần một món tiện lợi hơn? Tham khảo {product['name']} nhé.",
        ANGLES[2]: f"🎁 Gợi ý quà tặng dưới {price}: {product['name']}.",
        ANGLES[3]: f"💡 Vài lý do nhiều người chọn {product['name']}:",
        ANGLES[4]: f"So với loại thông thường, {product['name']} là lựa chọn đáng cân nhắc.",
    }
    return (
        f"{openers[angle]}\n"
        f"✅ Đã bán {_n(product['sales'])} sản phẩm, đánh giá {product['rating']}/5\n"
        f"🏪 Shop: {product['shop_name']}\n"
        f"Xem chi tiết và giá mới nhất ở link bên dưới nhé!"
    )


def check_content(caption: str, settings: dict, other_captions: list[str]) -> list[str]:
    """Kiểm duyệt tự động. Trả về danh sách cảnh báo (rỗng = ổn).

    other_captions: các bài khác cùng sản phẩm, để phát hiện nội dung gần trùng giữa các page.
    """
    flags = []
    lower = caption.lower()
    hits = [w for w in settings["blacklist"] if w.lower() in lower]
    if hits:
        flags.append("Có từ cấm: " + ", ".join(hits))
    if settings["disclosure"].lower() not in lower:
        flags.append("Thiếu ghi chú tiếp thị liên kết")
    for phrase in ["mình đã dùng", "mình dùng rồi", "review thật", "cam kết 100%", "khỏi hẳn"]:
        if phrase in lower:
            flags.append(f"Câu dễ gây hiểu lầm: “{phrase}”")
    if len(caption) > 1500:
        flags.append("Bài quá dài")
    words = set(lower.split())
    for other in other_captions:
        other_words = set(other.lower().split())
        if words and len(words & other_words) / len(words | other_words) > 0.8:
            flags.append("Gần trùng nội dung với bài khác")
            break
    return flags
