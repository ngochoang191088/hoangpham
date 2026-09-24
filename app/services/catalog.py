"""Kho sản phẩm do người dùng cung cấp: link sản phẩm + link aff (+ ảnh, video) theo ngành hàng."""
import re
import uuid
from pathlib import Path

from app import config, db
from app.services import facebook, importer, shopee

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}


def save_rows(conn, rows: list[dict], niche: str, source: str = "file") -> dict:
    """Lưu các dòng sản phẩm vào ngành `niche`. Trả về thống kê + danh sách lỗi theo dòng."""
    valid_niches = set(db.niche_names(conn))
    added = updated = videos = 0
    errors: list[str] = []
    for i, row in enumerate(rows, start=1):
        err = importer.validate(row)
        if err:
            errors.append(f"Dòng {i}: {err}")
            continue
        row_niche = row.get("niche") if row.get("niche") in valid_niches else niche
        if row_niche not in valid_niches:
            errors.append(f"Dòng {i}: chưa chọn ngành hàng")
            continue
        item_id = importer.make_item_id(row)
        exists = conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone()

        info = {}
        if row.get("product_link") and not (row.get("name") and row.get("image_url")) and not exists:
            info = shopee.lookup_product(row["product_link"])
        data = {
            "item_id": item_id,
            "name": row.get("name") or info.get("name") or (exists["name"] if exists else ""),
            "niche": row_niche,
            "price": importer.parse_price(row.get("price")) or info.get("price", 0),
            "commission_rate": info.get("commission_rate", 0),
            "sales": info.get("sales", 0), "rating": info.get("rating", 0),
            "shop_name": info.get("shop_name", ""),
            "image_url": row.get("image_url") or info.get("image_url", ""),
            "product_link": row.get("product_link", ""),
            "aff_link": row.get("aff_link", ""),
            "description": row.get("description", ""),
            "source": source,
            "fetched_at": db.now_iso(),
        }
        data["score"] = data["price"] * data["commission_rate"]
        conn.execute(
            """INSERT INTO products(item_id, name, niche, price, commission_rate, sales, rating, shop_name,
                   image_url, product_link, offer_link, aff_link, description, source, score, fetched_at)
               VALUES (:item_id, :name, :niche, :price, :commission_rate, :sales, :rating, :shop_name,
                   :image_url, :product_link, '', :aff_link, :description, :source, :score, :fetched_at)
               ON CONFLICT(item_id) DO UPDATE SET
                   niche = excluded.niche, fetched_at = excluded.fetched_at, blocked = 0,
                   name = CASE WHEN excluded.name != '' THEN excluded.name ELSE name END,
                   price = CASE WHEN excluded.price > 0 THEN excluded.price ELSE price END,
                   image_url = CASE WHEN excluded.image_url != '' THEN excluded.image_url ELSE image_url END,
                   product_link = CASE WHEN excluded.product_link != '' THEN excluded.product_link ELSE product_link END,
                   aff_link = CASE WHEN excluded.aff_link != '' THEN excluded.aff_link ELSE aff_link END,
                   description = CASE WHEN excluded.description != '' THEN excluded.description ELSE description END""",
            data,
        )
        if exists:
            updated += 1
        else:
            added += 1
        if not data["name"]:
            errors.append(f"Dòng {i}: chưa có tên sản phẩm, hãy bổ sung trong trang Sản phẩm")
        if not data["aff_link"] and not (exists and exists["aff_link"]):
            errors.append(f"Dòng {i}: chưa có link aff (lưu sản phẩm nhưng chưa tạo bài được)")
        for url in row.get("images", []):
            add_image(conn, item_id, url=url, source="file")

        if row.get("video_url"):
            if not facebook.direct_video_url(row["video_url"]):
                errors.append(f"Dòng {i}: link video phải là file .mp4 hoặc Google Drive (không dùng link TikTok/YouTube)")
            elif add_video(conn, item_id, url=row["video_url"]):
                videos += 1
    return {"added": added, "updated": updated, "videos": videos, "errors": errors}


def add_image(conn, item_id: str, url: str = "", file_path: str = "", source: str = "file") -> bool:
    """Thêm ảnh gốc cho sản phẩm (bỏ qua nếu trùng), tối đa 10 ảnh."""
    if conn.execute("SELECT 1 FROM product_images WHERE item_id = ? AND url = ? AND file_path = ?",
                    (item_id, url, file_path)).fetchone():
        return False
    n = conn.execute("SELECT COUNT(*) FROM product_images WHERE item_id = ?", (item_id,)).fetchone()[0]
    if n >= 10:
        return False
    conn.execute("INSERT INTO product_images(item_id, url, file_path, position, source, created_at) "
                 "VALUES (?, ?, ?, ?, ?, ?)", (item_id, url, file_path, n, source, db.now_iso()))
    return True


def add_video(conn, item_id: str, url: str = "", file_path: str = "", title: str = "") -> bool:
    """Gắn video cho sản phẩm (bỏ qua nếu trùng)."""
    if conn.execute("SELECT 1 FROM videos WHERE item_id = ? AND url = ? AND file_path = ?",
                    (item_id, url, file_path)).fetchone():
        return False
    conn.execute("INSERT INTO videos(item_id, url, file_path, title, created_at) VALUES (?, ?, ?, ?, ?)",
                 (item_id, url, file_path, title, db.now_iso()))
    return True


def save_upload(filename: str, data: bytes) -> str:
    """Lưu file video tải lên máy chủ app, trả về đường dẫn."""
    ext = Path(filename).suffix.lower()
    if ext not in VIDEO_EXTS:
        raise ValueError("Chỉ nhận video .mp4, .mov, .m4v, .webm")
    folder = Path(config.UPLOAD_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]", "_", Path(filename).stem)[:40]
    path = folder / f"{uuid.uuid4().hex[:8]}_{safe}{ext}"
    path.write_bytes(data)
    return str(path)


def guess_niche(conn, name: str, categories: list[str] | None = None, description: str = "",
                record_usage=None) -> tuple[str, str]:
    """Đoán ngành hàng cho sản phẩm. Trả về (ngành, cách đoán).

    1. Miễn phí: so từ khoá của từng ngành (và tên ngành) với tên sản phẩm + danh mục Shopee.
    2. Chỉ khi không đoán được mới hỏi AI (model rẻ nhất, trả lời 1 lựa chọn trong danh sách).
    """
    niches = db.get_niches(conn)
    if not niches:
        return "", ""
    text = importer.strip_accents(" ".join([name, *(categories or [])]))
    best, best_score = "", 0.0
    for n in niches:
        score = 0.0
        for kw in n["keywords"]:
            k = importer.strip_accents(kw)
            if k and k in text:
                score += 2 + len(k.split())                # từ khoá nhiều chữ khớp -> chắc chắn hơn
        for word in importer.strip_accents(n["name"]).replace("&", " ").split():
            if len(word) > 2 and f" {word} " in f" {text} ":
                score += 0.5
        if score > best_score:
            best, best_score = n["name"], score
    if best_score >= 2:
        return best, "từ khoá"
    if not config.AI_ENABLED:
        return "", ""
    return _ai_niche(name, categories or [], description, [n["name"] for n in niches], record_usage), "AI"


def _ai_niche(name: str, categories: list[str], description: str, options: list[str], record_usage=None) -> str:
    import json

    import anthropic

    from app.services import ai_models

    model = ai_models.model_for("classify")
    msg = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
        model=model, max_tokens=200,
        messages=[{"role": "user", "content": (
            f"Xếp sản phẩm Shopee vào 1 ngành hàng.\nSản phẩm: {name}\nDanh mục: {', '.join(categories) or '-'}\n"
            f"Mô tả: {description[:400]}")}],
        output_config={"format": {"type": "json_schema", "schema": {
            "type": "object", "properties": {"niche": {"type": "string", "enum": [*options, "Khác"]}},
            "required": ["niche"], "additionalProperties": False}}},
    )
    if record_usage:
        record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, False)
    if msg.stop_reason == "refusal":
        return ""
    niche = json.loads(next(b.text for b in msg.content if b.type == "text"))["niche"]
    return niche if niche in options else ""
