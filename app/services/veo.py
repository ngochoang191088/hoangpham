"""Tạo video sản phẩm bằng Google Veo 3.1 (Gemini API, thư viện chính thức google-genai).

Quy trình cho 1 sản phẩm:
  1. Lấy ảnh sản phẩm đẹp nhất (AI đã chọn trong Studio), đặt lên khung 9:16 sạch, không chữ.
  2. Gửi khung đó + mô tả chuyển động cho Veo (image-to-video): Veo làm clip ~8 giây giữ nguyên sản phẩm.
  3. Chèn lại chữ (tiêu đề, giá) lên clip và nối cảnh cuối kêu gọi mua -> video quảng cáo ~10 giây.

Chưa có GEMINI_API_KEY: chạy giả lập (chuyển động ảnh tĩnh) để xem thử luồng, không tốn tiền.
Kiểu "scene" (mặc định): dùng ý tưởng bối cảnh + chuyển động Claude nghĩ riêng cho từng sản phẩm, khung đầu là
ảnh AI (Nano Banana) của ý tưởng đó -> mỗi sản phẩm / phiên bản có video khác nhau. Giọng đọc: bổ sung sau.
"""
import time
from pathlib import Path

from app import config
from app.services import video_maker

# Kiểu chuyển động (prompt tiếng Anh cho Veo hiểu tốt nhất). "scene" = theo ý tưởng riêng của sản phẩm.
VEO_STYLES = {
    "scene": ("Theo ý tưởng AI nghĩ riêng cho sản phẩm (khuyên dùng)", ""),
    "studio": ("Quay sản phẩm trong studio",
               "Slow cinematic orbit around the product on a clean studio background, soft diffused lighting, "
               "gentle reflections, subtle depth of field, premium commercial look."),
    "reveal": ("Cận cảnh rồi lùi ra",
               "Start with a smooth macro close-up on the product details, then slowly pull back to reveal the whole "
               "product, soft studio lighting, clean background, premium product commercial."),
    "lifestyle": ("Sản phẩm trong bối cảnh sử dụng",
                  "The product sits in a bright, tidy, realistic setting where it is naturally used; slow camera push-in, "
                  "warm natural light, shallow depth of field, lifestyle commercial."),
}
PRODUCT_RULES = ("Keep the product exactly as in the input image: same shape, proportions, colors, materials, "
                 "printed text and logo. Do not add any text, captions, subtitles, watermarks or new logos. "
                 "No people. Smooth, stable motion.")
NEGATIVE = "text, captions, subtitles, watermark, logo change, deformed product, extra products, people, hands, blur"
SCENE_RULES = ("Keep the product exactly as in the input image: same shape, proportions, colors, materials, "
               "printed text and logo. Keep the scene consistent with the first frame. Do not add any text, "
               "captions, subtitles, watermarks or new logos. No faces; hands only if natural. Smooth, stable motion.")
NEGATIVE_SCENE = "text, captions, subtitles, watermark, logo change, deformed product, extra products, faces, " \
                 "deformed hands, blur"

# Giá tham khảo USD / giây video (kiểm tra lại bảng giá Gemini API trước khi chạy nhiều)
PRICE_PER_SECOND = {"veo-3.1-lite": 0.05, "veo-3.1-fast": 0.15, "veo-3.1-generate": 0.40, "veo-3": 0.40}
MODELS = {
    "veo-3.1-lite-generate-001": "Veo 3.1 Lite (rẻ nhất)",
    "veo-3.1-generate-preview": "Veo 3.1 (chất lượng cao nhất)",
}


def enabled() -> bool:
    return bool(config.GEMINI_API_KEY)


def price_per_second(model: str) -> float:
    return next((v for k, v in sorted(PRICE_PER_SECOND.items(), key=lambda kv: -len(kv[0]))
                 if model.startswith(k)), 0.40)


def cost_per_video(model: str, seconds: int | None = None) -> float:
    return price_per_second(model) * (seconds or config.VEO_SECONDS)


def build_prompt(product: dict, style: str = "studio") -> str:
    """Mô tả chuyển động gửi Veo. Tên sản phẩm giúp AI hiểu vật thể, không in ra video."""
    motion = VEO_STYLES.get(style, VEO_STYLES["studio"])[1] or VEO_STYLES["studio"][1]
    name = product.get("name") or "the product"
    return f"Vertical 9:16 product video of: {name}. {motion} {PRODUCT_RULES}"


def build_scene_prompt(product: dict, scene: dict, in_frame: bool = True) -> str:
    """Prompt theo ý tưởng riêng của sản phẩm. in_frame: khung đầu đã là ảnh bối cảnh (ảnh AI)."""
    name = product.get("name") or "the product"
    if in_frame:
        return f"Vertical 9:16 product commercial of: {name}. Camera and action: {scene['motion']}. {SCENE_RULES}"
    return (f"Vertical 9:16 product commercial of: {name}. {scene['motion']}. Soft, clean lighting. "
            f"{PRODUCT_RULES}")


def generate(frame_path: str, prompt: str, out_path: str, model: str | None = None,
             poll_seconds: int = 10, timeout: int = 900, negative: str = NEGATIVE) -> dict:
    """Image-to-video bằng Veo. Trả về {"seconds", "model", "simulated"}."""
    model = model or config.VEO_MODEL
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if not enabled():
        video_maker.animate_still(frame_path, out_path, float(config.VEO_SECONDS))
        return {"seconds": config.VEO_SECONDS, "model": model, "simulated": True}

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    operation = client.models.generate_videos(
        model=model,
        source=types.GenerateVideosSource(prompt=prompt, image=types.Image.from_file(location=frame_path)),
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16", resolution=config.VEO_RESOLUTION, duration_seconds=config.VEO_SECONDS,
            number_of_videos=1, negative_prompt=negative,
        ),
    )
    waited = 0
    while not operation.done:
        if waited >= timeout:
            raise RuntimeError("Veo tạo video quá lâu, hãy thử lại sau")
        time.sleep(poll_seconds)
        waited += poll_seconds
        operation = client.operations.get(operation)
    if operation.error:
        raise RuntimeError(f"Veo lỗi: {operation.error}")
    result = operation.result or operation.response
    if not result or not result.generated_videos:
        reasons = "; ".join(getattr(result, "rai_media_filtered_reasons", None) or []) if result else ""
        raise RuntimeError(f"Veo không trả video (bị bộ lọc an toàn chặn?) {reasons}".strip())
    client.files.download(file=result.generated_videos[0].video, destination=out_path)
    return {"seconds": config.VEO_SECONDS, "model": model, "simulated": False}
