"""Ảnh AI: đặt sản phẩm THẬT (ảnh gốc Shopee) vào bối cảnh mới bằng Nano Banana (Gemini image, Gemini API).

Quy trình cho 1 sản phẩm:
  1. Claude xem ảnh gốc + thông tin sản phẩm, nghĩ 3 ý tưởng bối cảnh riêng cho sản phẩm đó (creative.py, "scenes").
  2. Gửi 1-2 ảnh gốc sạch nhất + ý tưởng cho Nano Banana: giữ nguyên sản phẩm, chỉ đổi bối cảnh, không chữ.
  3. Claude Haiku so ảnh AI với ảnh gốc, chấm điểm "có đúng sản phẩm không" (check). Ảnh kém -> tạo lại 1 lần,
     vẫn kém -> đưa vào hàng chờ "Ảnh AI cần xem" (không tự dùng). Bạn chỉ xem ảnh bị gắn cờ, không cần xem hết.
  4. Ảnh đạt được dùng cho bộ ảnh 4:5, video trình chiếu và làm khung đầu cho Veo (bản 9:16).

Chưa có GEMINI_API_KEY: giả lập (ghép ảnh gốc lên nền) để xem thử luồng, không tốn tiền.
"""
import base64
import io
import json
import zlib
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageOps

from app import config

MODELS = {
    "gemini-3.1-flash-image": "Nano Banana 2 (rẻ, khuyên dùng)",
    "gemini-3-pro-image": "Nano Banana Pro (đẹp nhất, đắt ~3 lần)",
}
# Giá tham khảo USD / ảnh 1K (kiểm tra lại bảng giá Gemini API trước khi chạy nhiều)
PRICE_PER_IMAGE = {"gemini-3.1-flash-image": 0.045, "gemini-3-pro-image": 0.134, "gemini-2.5-flash-image": 0.039}
SIZES = {"4:5": (1080, 1350), "9:16": (1080, 1920)}
QC_PASS = 7            # điểm tối thiểu (0-10) để tự dùng ảnh AI

PRODUCT_RULES = ("The product must stay EXACTLY as in the reference photo(s): same shape, proportions, colors, "
                 "materials, pattern, packaging, printed text and logo. Do not redesign, recolor or simplify it. "
                 "Show only this one product (unless it comes as a set in the reference). "
                 "Do not add any text, captions, prices, stickers, watermarks or other brand logos. "
                 "No faces; hands are allowed only if they look natural. "
                 "Photorealistic commercial photo, product sharp and in focus, occupying a large part of the frame.")


def enabled() -> bool:
    return bool(config.GEMINI_API_KEY)


def price_per_image(model: str | None = None) -> float:
    model = model or config.IMAGE_MODEL
    return next((v for k, v in sorted(PRICE_PER_IMAGE.items(), key=lambda kv: -len(kv[0]))
                 if model.startswith(k)), 0.134)


def build_prompt(product: dict, scene: dict, aspect: str = "4:5") -> str:
    name = product.get("name") or "the product"
    return (f"Create a {aspect} vertical advertising photo of this product: {name}. "
            f"Scene: {scene['setting']}. {PRODUCT_RULES}")


def generate(ref_paths: list[str], prompt: str, out_path: str, aspect: str = "4:5", model: str | None = None,
             seed: int = 0) -> dict:
    """Ảnh gốc + mô tả bối cảnh -> ảnh mới (JPEG). Trả về {"model", "simulated"}."""
    model = model or config.IMAGE_MODEL
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if not enabled():
        simulate(ref_paths[0], out_path, aspect, seed)
        return {"model": model, "simulated": True}

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    refs = []
    for p in ref_paths[:3]:
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        im.thumbnail((1536, 1536))
        refs.append(im)
    response = client.models.generate_content(
        model=model,
        contents=[*refs, prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"],
                                           image_config=types.ImageConfig(aspect_ratio=aspect)),
    )
    for cand in response.candidates or []:
        for part in (cand.content.parts if cand.content else None) or []:
            data = getattr(part, "inline_data", None)
            if data and data.data:
                raw = data.data if isinstance(data.data, bytes) else base64.b64decode(data.data)
                im = Image.open(io.BytesIO(raw)).convert("RGB")
                ImageOps.fit(im, SIZES.get(aspect, im.size), Image.LANCZOS).save(out_path, "JPEG", quality=92)
                return {"model": model, "simulated": False}
    reason = ""
    if response.candidates:
        reason = str(response.candidates[0].finish_reason or "")
    raise RuntimeError(f"AI không trả ảnh (bị bộ lọc an toàn chặn?) {reason}".strip())


def simulate(src_path: str, out_path: str, aspect: str = "4:5", seed: int = 0) -> None:
    """Ảnh giả lập (chưa có key): sản phẩm trên nền màu mờ lấy từ chính ảnh, có bóng đổ. Không chữ."""
    W, H = SIZES.get(aspect, SIZES["4:5"])
    photo = ImageOps.exif_transpose(Image.open(src_path)).convert("RGB")
    tints = ["#F6E7D8", "#DDEFE6", "#E3E8F7", "#F7E1EA", "#EFEFEA"]
    tint = ImageColor.getrgb(tints[(zlib.crc32(src_path.encode()) + seed) % len(tints)])
    bg = ImageOps.fit(photo, (W // 8, H // 8)).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    bg = Image.blend(bg, Image.new("RGB", (W, H), tint), 0.65).convert("RGBA")
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((W * 0.18, H * 0.74, W * 0.82, H * 0.8), fill=(0, 0, 0, 70))
    bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
    fitted = ImageOps.contain(photo, (int(W * 0.8), int(H * 0.62)), Image.LANCZOS).convert("RGBA")
    mask = fitted.convert("L").point(lambda v: 0 if v > 243 else 255).filter(ImageFilter.GaussianBlur(1.5))
    fitted.putalpha(mask)
    bg.alpha_composite(fitted, ((W - fitted.width) // 2, int(H * 0.77) - fitted.height))
    bg.convert("RGB").save(out_path, "JPEG", quality=90)


# ---------------- Kiểm tra chất lượng (Claude Haiku so ảnh AI với ảnh gốc) ----------------

QC_SCHEMA = {
    "type": "object",
    "properties": {
        "same_product": {"type": "boolean",
                         "description": "Sản phẩm trong ảnh AI có đúng là sản phẩm ở ảnh gốc không (hình dáng, màu, chi tiết)"},
        "score": {"type": "integer", "description": "0-10: độ giống sản phẩm + độ đẹp, tự nhiên của ảnh để đăng quảng cáo"},
        "note": {"type": "string", "description": "Lỗi chính nếu có (tiếng Việt, tối đa 80 ký tự), rỗng nếu tốt"},
    },
    "required": ["same_product", "score", "note"],
    "additionalProperties": False,
}
QC_SYSTEM = """Bạn kiểm tra ảnh quảng cáo do AI tạo cho sản phẩm bán trên Shopee.
Ảnh 1 là ảnh gốc của sản phẩm thật, ảnh 2 là ảnh AI đặt sản phẩm vào bối cảnh mới.
Chấm nghiêm: khách mua về phải nhận đúng món trong ảnh.
- same_product = false nếu sản phẩm bị đổi hình dáng, màu, số lượng, chi tiết, chữ/logo trên sản phẩm, hoặc là món khác.
- Trừ điểm mạnh: chữ lạ, logo lạ, sản phẩm méo, tay/người dị dạng, nhiều bản sao sản phẩm, ảnh giả tạo.
- 9-10: đẹp, đúng sản phẩm, đăng được ngay. 7-8: ổn. 5-6: có lỗi nhỏ đáng xem lại. 0-4: không dùng được."""


def _encode(path: str, side: int = 512) -> dict:
    im = Image.open(path).convert("RGB")
    im.thumbnail((side, side))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                        "data": base64.standard_b64encode(buf.getvalue()).decode()}}


def check(src_path: str, gen_path: str, product: dict, record_usage=None) -> dict:
    """{"score": 0-10 | None, "same_product": bool, "note": str}. Chưa có Claude API key: không chấm (score None)."""
    if not config.AI_ENABLED:
        return {"score": None, "same_product": True, "note": "Chưa kiểm tra tự động (chưa có Claude API key)"}
    import anthropic

    from app.services import ai_models

    model = ai_models.model_for("qc")
    msg = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
        model=model, max_tokens=400, system=QC_SYSTEM,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "Ảnh 1 (ảnh gốc):"}, _encode(src_path),
            {"type": "text", "text": "Ảnh 2 (ảnh AI):"}, _encode(gen_path),
            {"type": "text", "text": f"Sản phẩm: {product.get('name') or ''}"}]}],
        output_config={"format": {"type": "json_schema", "schema": QC_SCHEMA}},
    )
    if record_usage:
        record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, False)
    if msg.stop_reason == "refusal":
        return {"score": 0, "same_product": False, "note": "AI từ chối kiểm tra ảnh này"}
    data = json.loads(next(b.text for b in msg.content if b.type == "text"))
    return {"score": max(0, min(10, int(data.get("score", 0)))), "same_product": bool(data.get("same_product")),
            "note": " ".join(str(data.get("note") or "").split())[:120]}


def passed(result: dict) -> bool:
    return result["same_product"] and (result["score"] is None or result["score"] >= QC_PASS)
