"""Studio: tạo bộ media cho từng sản phẩm từ link Shopee.

Quy trình cho 1 sản phẩm:
  1. Lấy ảnh gốc (link trong file Excel, ảnh tải lên, hoặc tự lấy từ link Shopee) và tải về máy chủ.
  2. Claude xem ảnh + thông tin, soạn chữ (tiêu đề, điểm nổi bật, lời kêu gọi) và chọn thứ tự ảnh.
  3. Dựng 3-5 ảnh 4:5 đã chỉnh + 1 video ngắn 9:16.
  4. Làm thêm phiên bản khác màu / bố cục để mỗi page trong ngành đăng một kiểu riêng.
"""
import json
import shutil
import zlib
from datetime import timedelta
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from app import config, db
from app.services import catalog, creative, designer, shopee, video_maker

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
            "Referer": "https://shopee.vn/"}


def _dir(*parts) -> Path:
    path = Path(config.MEDIA_DIR).joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe(item_id: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in item_id)


def download_image(url: str, dest: Path) -> bool:
    """Tải ảnh về, kiểm tra đúng là ảnh, lưu JPEG. Trả về False nếu lỗi."""
    try:
        with httpx.Client(timeout=20, headers=_HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
        resp.raise_for_status()
        from io import BytesIO

        im = Image.open(BytesIO(resp.content))
        im.load()
        im.convert("RGB").save(dest, "JPEG", quality=92)
        return True
    except Exception:  # noqa: BLE001
        return False


def placeholder_image(product: dict, idx: int, dest: Path) -> None:
    """Ảnh giả lập cho chế độ DEMO (khi không tải được ảnh thật)."""
    colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"]
    seed = zlib.crc32(product["item_id"].encode())
    c = colors[(seed + idx) % len(colors)]
    im = Image.new("RGB", (900, 900), "white")
    d = ImageDraw.Draw(im)
    shape = (seed + idx) % 3
    if shape == 0:
        d.rounded_rectangle((250, 170, 650, 700), 70, fill=c)
        d.ellipse((380, 280, 520, 420), fill="white")
    elif shape == 1:
        d.ellipse((190, 190, 710, 710), fill=c)
        d.ellipse((330, 330, 570, 570), fill="white")
    else:
        d.polygon([(450, 150), (740, 700), (160, 700)], fill=c)
    d.rectangle((0, 820, 900, 900), fill="#F3F4F6")
    im.save(dest, "JPEG", quality=90)


def source_images(conn, item_id: str, fetch: bool = True) -> list[str]:
    """Đường dẫn ảnh gốc đã tải về của sản phẩm (tự lấy thêm từ link Shopee khi thiếu)."""
    product = conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone()
    if not product:
        return []
    have = conn.execute("SELECT COUNT(*) FROM product_images WHERE item_id = ?", (item_id,)).fetchone()[0]
    if product["image_url"]:
        catalog.add_image(conn, item_id, url=product["image_url"], source="file")
    if fetch and have < 3 and product["product_link"] and not config.DEMO_MODE:
        for url in shopee.fetch_images(product["product_link"]):
            catalog.add_image(conn, item_id, url=url, source="shopee")

    folder = _dir("src", _safe(item_id))
    paths = []
    rows = conn.execute("SELECT * FROM product_images WHERE item_id = ? ORDER BY position, id", (item_id,)).fetchall()
    for r in rows:
        if r["file_path"] and Path(r["file_path"]).exists():
            paths.append(r["file_path"])
            continue
        dest = folder / f"{r['id']}.jpg"
        ok = download_image(r["url"], dest) if r["url"] else False
        if not ok and config.DEMO_MODE:
            placeholder_image(dict(product), len(paths), dest)
            ok = True
        if ok:
            conn.execute("UPDATE product_images SET file_path = ? WHERE id = ?", (str(dest), r["id"]))
            paths.append(str(dest))
    if not paths and config.DEMO_MODE:                    # demo: sản phẩm chưa có ảnh nào
        for i in range(3):
            dest = folder / f"demo{i}.jpg"
            placeholder_image(dict(product), i, dest)
            catalog.add_image(conn, item_id, file_path=str(dest), source="upload")
            paths.append(str(dest))
    return paths


def get_brief(conn, item_id: str) -> dict | None:
    row = conn.execute("SELECT brief FROM media_kits WHERE item_id = ? AND brief != '{}' ORDER BY variant LIMIT 1",
                       (item_id,)).fetchone()
    return json.loads(row[0]) if row else None


def build_kit(conn, item_id: str, variant: int = 0, brief: dict | None = None, new_brief: bool = False,
              record_usage=None) -> int:
    """Tạo (hoặc làm lại) 1 phiên bản bộ media. Trả về id của media_kits."""
    now = db.now_iso()
    conn.execute(
        """INSERT INTO media_kits(item_id, variant, status, created_at, updated_at) VALUES (?, ?, 'processing', ?, ?)
           ON CONFLICT(item_id, variant) DO UPDATE SET status = 'processing', error = NULL, updated_at = excluded.updated_at""",
        (item_id, variant, now, now),
    )
    kit_id = conn.execute("SELECT id FROM media_kits WHERE item_id = ? AND variant = ?", (item_id, variant)).fetchone()[0]
    conn.commit()
    try:
        product = dict(conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone())
        paths = source_images(conn, item_id)
        if not paths:
            raise RuntimeError("Chưa có ảnh sản phẩm: dán link ảnh trong file Excel hoặc tải ảnh lên Studio")
        paths = paths[:6]
        if brief is None and not new_brief:
            brief = get_brief(conn, item_id)
        if brief is None:
            brief = creative.make_brief(product, paths, record_usage)
        brief = creative.clean_brief(brief, len(paths))

        theme = (zlib.crc32(item_id.encode()) + variant) % len(designer.THEMES)
        photos = [designer.enhance(p) for p in paths]
        out = _dir("kits", _safe(item_id), f"v{variant}")
        for old in out.glob("*"):
            old.unlink()
        feed_paths = []
        for i, im in enumerate(designer.render_set(photos, brief, product, variant, designer.FEED, theme)):
            path = out / f"anh_{i + 1}.jpg"
            im.save(path, "JPEG", quality=90, optimize=True)
            feed_paths.append(str(path))
        video_brief = {**brief, "points": brief["video_lines"][1:-1] or brief["points"]}
        story_paths = []
        for i, im in enumerate(designer.render_set(photos, video_brief, product, variant, designer.STORY, theme)):
            path = out / f"story_{i + 1}.jpg"
            im.save(path, "JPEG", quality=92)
            story_paths.append(str(path))
        video = video_maker.make_video(story_paths, str(out / "video.mp4"), variant,
                                       music=video_maker.pick_music(zlib.crc32(item_id.encode()) + variant))
        conn.execute(
            """UPDATE media_kits SET status = 'ready', brief = ?, images = ?, video_path = ?, error = NULL, updated_at = ?
               WHERE id = ?""",
            (json.dumps(brief, ensure_ascii=False), json.dumps(feed_paths), video, db.now_iso(), kit_id),
        )
    except Exception as e:  # noqa: BLE001
        conn.execute("UPDATE media_kits SET status = 'error', error = ?, updated_at = ? WHERE id = ?",
                     (str(e)[:500], db.now_iso(), kit_id))
        db.log(conn, "error", f"Tạo bộ media lỗi cho sản phẩm {item_id}: {e}")
    return kit_id


def build_ai_video(conn, item_id: str, variant: int = 0, style: str | None = None) -> None:
    """Video AI bằng Veo 3.1 cho 1 phiên bản: ảnh sản phẩm -> clip Veo -> chèn chữ + cảnh cuối."""
    from app.services import veo

    kit = conn.execute("SELECT * FROM media_kits WHERE item_id = ? AND variant = ?", (item_id, variant)).fetchone()
    if not kit or kit["status"] != "ready":
        raise RuntimeError("Hãy tạo bộ ảnh cho sản phẩm trước")
    settings = db.get_settings(conn)
    conn.execute("UPDATE media_kits SET ai_video_status = 'processing', ai_video_error = NULL WHERE id = ?", (kit["id"],))
    conn.commit()
    try:
        product = dict(conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone())
        brief = json.loads(kit["brief"])
        paths = source_images(conn, item_id, fetch=False)
        if not paths:
            raise RuntimeError("Chưa có ảnh sản phẩm")
        order = [i for i in brief.get("image_order") or [] if i < len(paths)] or [0]
        photo = designer.enhance(paths[order[variant % len(order)]])
        theme = designer.THEMES[(zlib.crc32(item_id.encode()) + variant) % len(designer.THEMES)]
        out = _dir("kits", _safe(item_id), f"v{variant}")
        frame = out / "veo_frame.jpg"
        designer.veo_frame(photo, theme).save(frame, "JPEG", quality=92)
        overlay = out / "veo_overlay.png"
        designer.video_overlay(brief, product, theme).save(overlay)
        stories = sorted(out.glob("story_*.jpg"), key=lambda p: int(p.stem.split("_")[1]))
        if not stories:
            raise RuntimeError("Thiếu cảnh cuối, hãy dựng lại bộ ảnh")
        clip = out / "veo_clip.mp4"
        info = veo.generate(str(frame), veo.build_prompt(product, style or settings.get("veo_style", "studio")),
                            str(clip))
        conn.execute("INSERT INTO video_usage(ts, model, seconds, simulated) VALUES (?, ?, ?, ?)",
                     (db.now_iso(), info["model"], info["seconds"], int(info["simulated"])))
        final = out / "video_ai.mp4"
        video_maker.compose_ad(str(clip), str(overlay), str(stories[-1]), str(final),
                               keep_audio=settings.get("veo_audio") == "keep",
                               music=video_maker.pick_music(zlib.crc32(item_id.encode()) + variant))
        conn.execute("""UPDATE media_kits SET ai_video_status = 'ready', ai_video_path = ?, ai_video_model = ?,
                        ai_video_error = NULL WHERE id = ?""",
                     (str(final), info["model"] + (" (giả lập)" if info["simulated"] else ""), kit["id"]))
    except Exception as e:  # noqa: BLE001
        conn.execute("UPDATE media_kits SET ai_video_status = 'error', ai_video_error = ? WHERE id = ?",
                     (str(e)[:500], kit["id"]))
        db.log(conn, "error", f"Tạo video AI lỗi cho sản phẩm {item_id}: {e}")


def build_all_variants(conn, item_id: str, new_brief: bool = False, brief: dict | None = None,
                       record_usage=None) -> None:
    """Làm (lại) đủ số phiên bản theo cài đặt. Phiên bản 0 soạn chữ, các phiên bản sau dùng lại."""
    n = max(1, int(db.get_settings(conn).get("media_variants", 2)))
    build_kit(conn, item_id, 0, brief=brief, new_brief=new_brief, record_usage=record_usage)
    for v in range(1, n):
        build_kit(conn, item_id, v, record_usage=record_usage)


def build_missing(conn, limit: int = 30, record_usage=None) -> int:
    """Tạo bộ media cho các sản phẩm chưa có (ưu tiên sản phẩm có link aff). Dùng cho cron."""
    n = max(1, int(db.get_settings(conn).get("media_variants", 2)))
    rows = conn.execute(
        """SELECT item_id FROM products WHERE blocked = 0 AND product_link != ''
             AND (SELECT COUNT(*) FROM media_kits k WHERE k.item_id = products.item_id AND k.status = 'ready') < ?
             AND NOT EXISTS (SELECT 1 FROM media_kits k WHERE k.item_id = products.item_id AND k.status = 'error'
                             AND k.updated_at > ?)
           ORDER BY aff_link != '' DESC, fetched_at DESC LIMIT ?""",
        (n, (db.now() - timedelta(days=1)).isoformat(), limit),
    ).fetchall()
    for (item_id,) in rows:
        build_all_variants(conn, item_id, record_usage=record_usage)
        conn.commit()
    if rows:
        db.log(conn, "info", f"Studio: tạo bộ ảnh + video cho {len(rows)} sản phẩm")
    return len(rows)


def ready_kits(conn, item_id: str) -> list:
    return conn.execute("SELECT * FROM media_kits WHERE item_id = ? AND status = 'ready' ORDER BY variant",
                        (item_id,)).fetchall()


def delete_media(item_id: str) -> None:
    for sub in ("kits", "src"):
        shutil.rmtree(Path(config.MEDIA_DIR) / sub / _safe(item_id), ignore_errors=True)
