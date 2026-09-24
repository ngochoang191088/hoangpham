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

        if row.get("video_url"):
            if not facebook.direct_video_url(row["video_url"]):
                errors.append(f"Dòng {i}: link video phải là file .mp4 hoặc Google Drive (không dùng link TikTok/YouTube)")
            elif add_video(conn, item_id, url=row["video_url"]):
                videos += 1
    return {"added": added, "updated": updated, "videos": videos, "errors": errors}


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
