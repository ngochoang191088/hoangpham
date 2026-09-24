"""Viết caption bằng Claude API và kiểm duyệt nội dung tự động."""
import random
import time

from app import config
from app.services import ai_models

SYSTEM_PROMPT = """Bạn là người viết nội dung bán hàng cho fanpage Facebook tiếp thị liên kết Shopee tại Việt Nam.
Mục tiêu: bài đọc tự nhiên, dừng được người đang lướt, khiến họ muốn bấm xem sản phẩm.

Cấu trúc bài (60-120 chữ):
1. Câu mở đầu gây chú ý (1 dòng): nêu đúng nỗi bất tiện hoặc mong muốn của người mua, hoặc một con số có thật trong dữ liệu (giá, lượt bán, đánh giá).
2. 2-4 dòng lợi ích, mỗi dòng bắt đầu bằng 1 emoji, nói "được gì" chứ không chỉ liệt kê thông số.
3. Bằng chứng xã hội nếu có trong dữ liệu (lượt bán, số sao). Không có thì bỏ qua.
4. Lời kêu gọi ngắn ở cuối, nhắc xem giá / chọn phân loại ở link bên dưới.
5. Tối đa 3 hashtag ngắn liên quan sản phẩm.

Quy tắc bắt buộc:
- Chỉ dùng thông tin được cung cấp. Không bịa công dụng, chứng nhận, khuyến mãi, % giảm giá, quà tặng hay giá.
- Không viết như thể page đã tự dùng sản phẩm ("mình dùng rồi", "review thật"), không tạo đánh giá giả.
- Không hứa chữa bệnh, giảm cân hay kết quả chắc chắn. Không tạo khan hiếm giả ("chỉ còn 2 suất").
- Không chèn link (hệ thống tự thêm). Tối đa 5 emoji cả bài. Viết đúng giọng văn của page.
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
    """Thông tin sản phẩm đưa cho AI; chỉ gồm các trường bạn đã nhập."""
    lines = [f"Tên: {product['name']}"]
    if product.get("price"):
        lines.append(f"Giá từ: {_n(product['price'])}đ")
    if product.get("sales"):
        lines.append(f"Đã bán: {_n(product['sales'])}")
    if product.get("rating"):
        lines.append(f"Đánh giá: {product['rating']}/5")
    if product.get("shop_name"):
        lines.append(f"Shop: {product['shop_name']}")
    if product.get("description"):
        lines.append(f"Mô tả / điểm nổi bật (do chủ page cung cấp): {product['description'][:1500]}")
    return "\n".join(lines)


def write_caption(page: dict, product: dict, disclosure: str) -> str:
    """Viết 1 caption (dùng cho dữ liệu mẫu / trường hợp lẻ)."""
    (caption, error), = write_captions([{"page": page, "product": product}], disclosure)
    if error:
        raise RuntimeError(error)
    return caption


def write_captions(jobs: list[dict], disclosure: str, record_usage=None) -> list[tuple[str | None, str | None]]:
    """Viết caption cho nhiều bài. Mỗi job: {"page": dict, "product": dict}.

    Trả về danh sách (caption, lỗi) theo đúng thứ tự jobs.
    Nhiều bài (>= AI_BATCH_MIN) thì gửi qua Message Batches API: rẻ hơn 50%, thường xong trong < 1 giờ.
    record_usage(model, input_tokens, output_tokens, batch) được gọi để ghi lại chi phí thật.
    """
    prompts = [_user_prompt(j["page"], j["product"], random.choice(ANGLES)) for j in jobs]
    if not config.AI_ENABLED:
        texts = [(_template_caption(j["product"], p["angle"]), None) for j, p in zip(jobs, prompts)]
    elif config.AI_BATCH and len(jobs) >= config.AI_BATCH_MIN:
        texts = _claude_batch([p["text"] for p in prompts], record_usage)
    else:
        texts = [_claude_one(p["text"], record_usage) for p in prompts]
    return [(f"{t.strip()}\n\n{disclosure}" if t else None, err) for t, err in texts]


def _user_prompt(page: dict, product: dict, angle: str) -> dict:
    text = (
        f"Page: {page['name']} (ngành hàng: {page['niche']}; giọng văn: {page['tone']})\n"
        f"Góc viết: {angle}\n\nThông tin sản phẩm:\n{_facts(product)}"
    )
    return {"angle": angle, "text": text}


# Model hỗ trợ tự chuyển sang model dự phòng khi bị từ chối (chỉ khi gọi lẻ, Batch API không hỗ trợ)
FALLBACK_MODELS = {"claude-opus-5", "claude-fable-5-1"}


def _params(text: str, model: str) -> dict:
    params = {
        "model": model,
        "max_tokens": 2000 if model.startswith("claude-haiku") else 16000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text}],
    }
    params.update(ai_models.request_options(model))
    return params


def _text_of(message) -> tuple[str | None, str | None]:
    if message.stop_reason == "refusal":
        return None, "AI từ chối viết bài cho sản phẩm này"
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    return (text, None) if text else (None, "AI không trả về nội dung")


def _client():
    import anthropic

    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _claude_one(text: str, record_usage) -> tuple[str | None, str | None]:
    import anthropic

    model = ai_models.model_for("caption")
    params = _params(text, model)
    try:
        if model in FALLBACK_MODELS:
            msg = _client().beta.messages.create(
                **params, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            msg = _client().messages.create(**params)
    except anthropic.APIError as e:
        return None, f"Lỗi Claude API: {e}"
    if record_usage:
        record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, False)
    return _text_of(msg)


def _claude_batch(texts: list[str], record_usage, poll_seconds: int = 30,
                  max_wait_seconds: int = 6 * 3600) -> list[tuple[str | None, str | None]]:
    client = _client()
    model = ai_models.model_for("caption")
    batch = client.messages.batches.create(
        requests=[{"custom_id": str(i), "params": _params(t, model)} for i, t in enumerate(texts)])
    waited = 0
    while batch.processing_status != "ended":
        if waited >= max_wait_seconds:
            client.messages.batches.cancel(batch.id)
            return [(None, "Batch quá thời gian chờ")] * len(texts)
        time.sleep(poll_seconds)
        waited += poll_seconds
        batch = client.messages.batches.retrieve(batch.id)

    results: list[tuple[str | None, str | None]] = [(None, "Không có kết quả")] * len(texts)
    for item in client.messages.batches.results(batch.id):
        idx = int(item.custom_id)
        if item.result.type == "succeeded":
            msg = item.result.message
            if record_usage:
                record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, True)
            results[idx] = _text_of(msg)
        else:
            results[idx] = (None, f"Batch: {item.result.type}")
    return results


def _template_caption(product: dict, angle: str) -> str:
    """Caption mẫu dùng khi chưa có ANTHROPIC_API_KEY (chế độ DEMO)."""
    price = f"{_n(product['price'])}đ" if product.get("price") else "giá tốt"
    openers = {
        ANGLES[0]: f"🔥 Deal đang hot: {product['name']} chỉ từ {price}!",
        ANGLES[1]: f"Bạn đang cần một món tiện lợi hơn? Tham khảo {product['name']} nhé.",
        ANGLES[2]: f"🎁 Gợi ý quà tặng: {product['name']} ({price}).",
        ANGLES[3]: f"💡 Vài lý do nhiều người chọn {product['name']}:",
        ANGLES[4]: f"So với loại thông thường, {product['name']} là lựa chọn đáng cân nhắc.",
    }
    lines = [openers[angle]]
    if product.get("description"):
        lines.append(f"✨ {product['description'].strip().splitlines()[0][:200]}")
    if product.get("sales"):
        lines.append(f"✅ Đã bán {_n(product['sales'])} sản phẩm" +
                     (f", đánh giá {product['rating']}/5" if product.get("rating") else ""))
    lines.append("Xem chi tiết và giá mới nhất ở link bên dưới nhé!")
    return "\n".join(lines)


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
