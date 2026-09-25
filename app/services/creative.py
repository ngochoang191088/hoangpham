"""AI soạn nội dung chữ cho bộ ảnh + video của 1 sản phẩm (Claude đọc ảnh + thông tin sản phẩm).

Claude không vẽ ảnh: Claude xem ảnh gốc, chọn thứ tự ảnh đẹp nhất và viết tiêu đề, điểm nổi bật,
lời kêu gọi. Phần thiết kế (chỉnh màu, bố cục, chữ) do designer.py làm, video do video_maker.py làm.
Claude cũng nghĩ 3 ý tưởng bối cảnh RIÊNG cho từng sản phẩm ("scenes"): dùng để tạo ảnh AI (imagegen.py)
và làm kịch bản chuyển động cho video Veo, thay cho vài kiểu chuyển động cố định.
"""
import base64
import io
import json

from app import config
from app.services import ai_models

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "Tiêu đề ảnh bìa, tối đa 38 ký tự"},
        "subheadline": {"type": "string", "description": "Dòng phụ ngắn, tối đa 48 ký tự"},
        "points": {"type": "array", "items": {"type": "string"},
                   "description": "3-4 điểm nổi bật, mỗi điểm tối đa 32 ký tự"},
        "cta": {"type": "string", "description": "Lời kêu gọi cuối, tối đa 36 ký tự"},
        "badge": {"type": "string", "description": "Nhãn nhỏ tối đa 14 ký tự, rỗng nếu không có căn cứ"},
        "image_order": {"type": "array", "items": {"type": "integer"},
                        "description": "Số thứ tự ảnh gốc (từ 0) theo thứ tự nên dùng, ảnh đẹp nhất trước; "
                                       "bỏ ảnh xấu / ảnh bảng size / ảnh nhiều chữ"},
        "video_lines": {"type": "array", "items": {"type": "string"},
                        "description": "4-6 câu rất ngắn (tối đa 30 ký tự) hiện lần lượt trong video"},
        "scenes": {
            "type": "array",
            "description": "3 ý tưởng bối cảnh khác nhau cho ảnh quảng cáo + video của RIÊNG sản phẩm này",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Tên ý tưởng, tiếng Việt, tối đa 30 ký tự"},
                    "setting": {"type": "string",
                                "description": "Tiếng Anh: sản phẩm đặt ở đâu, xung quanh có gì, ánh sáng, góc chụp"},
                    "motion": {"type": "string",
                               "description": "Tiếng Anh: chuyển động máy quay / hành động trong video 8 giây"},
                },
                "required": ["label", "setting", "motion"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["headline", "subheadline", "points", "cta", "badge", "image_order", "video_lines", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """Bạn là designer nội dung cho fanpage bán hàng tiếp thị liên kết Shopee tại Việt Nam.
Nhiệm vụ: xem ảnh sản phẩm và thông tin được cung cấp, soạn chữ ngắn gọn để in lên bộ ảnh quảng cáo và video ngắn.

Quy tắc:
- Chỉ nói điều có trong thông tin sản phẩm hoặc nhìn thấy rõ trong ảnh. Không bịa công dụng, chứng nhận, % giảm giá, quà tặng.
- Không hứa hẹn chữa bệnh, giảm cân, kết quả chắc chắn. Không viết như người đã dùng thử.
- Tiếng Việt tự nhiên, câu cực ngắn, dễ đọc trên điện thoại, không dùng emoji, không dùng hashtag.
- Badge chỉ ghi khi có căn cứ (ví dụ "Bán chạy" khi lượt bán cao); không có thì để rỗng.
- Chọn thứ tự ảnh: ảnh sản phẩm rõ, đẹp, nền sạch lên trước; bỏ ảnh mờ, ảnh bảng kích thước, ảnh chứa nhiều chữ.

Ý tưởng bối cảnh (scenes), dùng để AI đặt đúng sản phẩm này vào ảnh / video mới:
- Nghĩ riêng cho sản phẩm: ai dùng, dùng ở đâu, lúc nào, điều gì khiến người xem muốn mua. Không chung chung.
- 3 ý tưởng khác hẳn nhau, ví dụ: 1 ảnh "hero" nền đẹp làm nổi sản phẩm; 1 cảnh đang được dùng thật;
  1 cảnh đời sống / quà tặng / trước-sau. Bối cảnh gần gũi người Việt (nhà ở, bếp, phòng ngủ, văn phòng, xe máy...).
- Sản phẩm phải nhìn rõ, là trung tâm. Không mô tả thay đổi sản phẩm. Không chữ, không bảng giá trong cảnh.
- Không mặt người (có thể có bàn tay). Không cảnh nguy hiểm, không trẻ em một mình với sản phẩm không an toàn.
- motion: 1 chuyển động đơn giản, mượt (push-in, orbit chậm, trượt ngang, tay cầm lên...), hợp 8 giây."""


def _encode(path: str, max_side: int = 768) -> dict:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                        "data": base64.standard_b64encode(buf.getvalue()).decode()}}


def _facts(product: dict) -> str:
    from app.services.ai_writer import _facts as facts

    return facts(product)


def make_brief(product: dict, image_paths: list[str], record_usage=None) -> dict:
    """Nội dung chữ cho bộ media. Không có ANTHROPIC_API_KEY thì dùng mẫu có sẵn."""
    if not config.AI_ENABLED:
        return template_brief(product, len(image_paths))
    import anthropic

    current = ai_models.tier()
    model = ai_models.model_for("creative", current)
    side = ai_models.IMAGE_SIDE[current]
    content = []
    for i, path in enumerate(image_paths[:5]):          # tối đa 5 ảnh, thu nhỏ để giảm token
        content += [{"type": "text", "text": f"Ảnh {i}:"}, _encode(path, side)]
    content.append({"type": "text", "text": f"Thông tin sản phẩm:\n{_facts(product)}"})
    params = {
        "model": model, "max_tokens": 4000, "system": SYSTEM,
        "messages": [{"role": "user", "content": content}],
        "output_config": {"format": {"type": "json_schema", "schema": BRIEF_SCHEMA}},
    }
    params["output_config"].update(ai_models.request_options(model).get("output_config", {}))
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = client.messages.create(**params)
    if record_usage:
        record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, False)
    if msg.stop_reason == "refusal":
        raise RuntimeError("AI từ chối xử lý sản phẩm này")
    text = next(b.text for b in msg.content if b.type == "text")
    return clean_brief(json.loads(text), len(image_paths))


# Ý tưởng dự phòng (chưa có Claude API key / AI trả thiếu)
DEFAULT_SCENES = [
    {"label": "Ảnh studio nổi bật",
     "setting": "on a clean seamless studio backdrop in a soft color that complements the product, soft diffused "
                "light, subtle reflection on the surface, premium e-commerce hero shot",
     "motion": "slow cinematic orbit around the product while soft light sweeps across it"},
    {"label": "Đang được sử dụng",
     "setting": "being used naturally in a bright, tidy, realistic Vietnamese home where this kind of product is "
                "normally used, a user's hands may appear but no faces, natural daylight",
     "motion": "slow push-in towards the product while it is being used naturally"},
    {"label": "Góc sống đẹp",
     "setting": "styled tabletop lifestyle scene with a few tasteful props related to how the product is used, "
                "warm window light, shallow depth of field",
     "motion": "gentle sideways camera slide with soft parallax, light shifting slightly"},
]


def clean_scenes(scenes) -> list[dict]:
    out = []
    for sc in scenes or []:
        if not isinstance(sc, dict) or not str(sc.get("setting") or "").strip():
            continue
        label = " ".join(str(sc.get("label") or "").split())[:34] or f"Ý tưởng {len(out) + 1}"
        setting = " ".join(str(sc["setting"]).split())[:400]
        motion = " ".join(str(sc.get("motion") or "").split())[:240] or DEFAULT_SCENES[len(out) % 3]["motion"]
        out.append({"label": label, "setting": setting, "motion": motion})
    for d in DEFAULT_SCENES:                    # luôn đủ 3 ý tưởng
        if len(out) >= 3:
            break
        if all(d["setting"] != sc["setting"] for sc in out):
            out.append(dict(d))
    return out[:3]


def clean_brief(brief: dict, n_images: int) -> dict:
    """Cắt độ dài, loại chỉ số ảnh sai, đảm bảo đủ trường."""
    def cut(text, n):
        text = " ".join(str(text or "").split())
        text = text[:1].upper() + text[1:]
        return text if len(text) <= n else text[: n - 1].rstrip() + "…"

    order = [i for i in brief.get("image_order", []) if isinstance(i, int) and 0 <= i < n_images]
    order = list(dict.fromkeys(order)) or list(range(n_images))
    return {
        "headline": cut(brief.get("headline"), 42),
        "subheadline": cut(brief.get("subheadline"), 52),
        "points": [cut(p, 36) for p in brief.get("points", []) if str(p).strip()][:4],
        "cta": cut(brief.get("cta") or "Xem giá & mua ngay ở link bên dưới", 40),
        "badge": cut(brief.get("badge"), 16),
        "image_order": order,
        "video_lines": [cut(v, 34) for v in brief.get("video_lines", []) if str(v).strip()][:6],
        "scenes": clean_scenes(brief.get("scenes")),
    }


def template_brief(product: dict, n_images: int) -> dict:
    """Nội dung mẫu (chế độ DEMO / chưa có API key), chỉ dùng dữ liệu có sẵn."""
    name = product.get("name") or "Sản phẩm hot"
    desc = [x.strip() for x in (product.get("description") or "").replace(";", ",").split(",") if x.strip()]
    points = desc[:3]
    if product.get("sales"):
        points.append(f"Đã bán {int(product['sales']):,}".replace(",", "."))
    if product.get("rating"):
        points.append(f"Đánh giá {product['rating']}/5")
    if product.get("price") and len(points) < 3:
        points.append(f"Giá chỉ từ {int(product['price']):,}đ".replace(",", "."))
    points = (points or ["Thiết kế tiện dụng", "Dễ sử dụng hằng ngày", "Giao hàng toàn quốc"])[:4]
    return clean_brief({
        "headline": name,
        "subheadline": product.get("niche") or "Gợi ý hay trên Shopee",
        "points": points,
        "cta": "Xem giá & mua ở link bên dưới",
        "badge": "Bán chạy" if (product.get("sales") or 0) >= 1000 else "",
        "image_order": list(range(n_images)),
        "video_lines": [name, *points[:3], "Link mua ở bên dưới"],
    }, n_images)
