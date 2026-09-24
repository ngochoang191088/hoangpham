"""Dán link Shopee -> app tự nhận diện sản phẩm, xếp ngành hàng, tạo bộ ảnh + video.

Mỗi link là 1 "việc" (link_jobs) chạy nền; trang Sản phẩm / Studio hiển thị tiến độ.
Mỗi dòng dán vào: "link"  hoặc  "link sản phẩm | link aff".
"""
import json

from app import db
from app.services import catalog, importer, pipeline, shopee, studio


def parse_lines(text: str) -> list[tuple[str, str]]:
    """-> [(link, link aff)]. Link aff là link rút gọn s.shopee.vn nằm cùng dòng (nếu có)."""
    out = []
    for line in text.splitlines():
        urls = importer.URL_LIST_RE.findall(line)
        if not urls:
            continue
        main = next((u for u in urls if shopee.parse_ids(u)), urls[0])
        aff = next((u for u in urls if u != main and shopee.is_short_link(u)), "")
        out.append((main, aff))
    return list(dict.fromkeys(out))


def create_jobs(conn, text: str, niche: str = "", auto_media: bool = True, ai_video: bool = False) -> list[int]:
    now = db.now_iso()
    ids = []
    for link, aff in parse_lines(text)[:200]:
        cur = conn.execute(
            "INSERT INTO link_jobs(input, aff_link, niche, auto_media, ai_video, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (link, aff, niche, int(auto_media), int(auto_media and ai_video), now, now))
        ids.append(cur.lastrowid)
    return ids


def _step(conn, job_id: int, status: str, step: str = "", **extra) -> None:
    sets = ", ".join(f"{k} = ?" for k in extra)
    conn.execute(f"UPDATE link_jobs SET status = ?, step = ?, updated_at = ?{', ' + sets if sets else ''} WHERE id = ?",
                 (status, step, db.now_iso(), *extra.values(), job_id))
    conn.commit()


def run_job(job_id: int) -> None:
    """Xử lý 1 link: nhận diện -> xếp ngành -> lưu sản phẩm -> tạo ảnh + video."""
    with db.get_conn() as conn:
        job = conn.execute("SELECT * FROM link_jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return
        record = pipeline.usage_recorder(conn)
        try:
            info = json.loads(job["detected"]) if job["detected"] != "{}" else None
            if not info:
                _step(conn, job_id, "running", "Đang đọc thông tin sản phẩm từ Shopee…")
                info = shopee.detect_product(job["input"])
                _step(conn, job_id, "running", "Đã đọc sản phẩm", detected=json.dumps(info, ensure_ascii=False))
            if not shopee.parse_ids(info.get("product_link", "")) and not info.get("name"):
                raise RuntimeError(info.get("error") or "Không nhận diện được sản phẩm từ link này")

            niche, how = job["niche"], "bạn chọn"
            if not niche:
                niche, how = catalog.guess_niche(conn, info.get("name", ""), info.get("categories"),
                                                 info.get("description", ""), record)
            if not niche:
                _step(conn, job_id, "need_niche", "Chưa đoán được ngành hàng, hãy chọn ngành")
                return

            row = {
                "product_link": info["product_link"], "aff_link": job["aff_link"] or info.get("aff_link", ""),
                "name": info.get("name", ""), "price": info.get("price") or "",
                "description": info.get("description", ""), "images": info.get("images", []),
                "image_url": (info.get("images") or [""])[0],
            }
            catalog.save_rows(conn, [row], niche, source="link")
            item_id = importer.make_item_id(row)
            conn.execute(
                """UPDATE products SET sales = MAX(sales, ?), rating = CASE WHEN ? > 0 THEN ? ELSE rating END,
                     shop_name = CASE WHEN ? != '' THEN ? ELSE shop_name END,
                     commission_rate = CASE WHEN ? > 0 THEN ? ELSE commission_rate END WHERE item_id = ?""",
                (int(info.get("sales") or 0), info.get("rating") or 0, info.get("rating") or 0,
                 info.get("shop_name", ""), info.get("shop_name", ""), info.get("commission_rate") or 0,
                 info.get("commission_rate") or 0, item_id))
            conn.execute("UPDATE link_jobs SET niche = ?, item_id = ? WHERE id = ?", (niche, item_id, job_id))
            if job["auto_media"]:
                _step(conn, job_id, "running", f"Ngành “{niche}” ({how}). Đang tạo ảnh + video…")
                studio.build_all_variants(conn, item_id, new_brief=True, record_usage=record)
                kit = conn.execute("SELECT status, error FROM media_kits WHERE item_id = ? AND variant = 0",
                                   (item_id,)).fetchone()
                if kit and kit["status"] == "error":
                    _step(conn, job_id, "error", "Đã lưu sản phẩm, tạo ảnh lỗi", error=kit["error"])
                    return
                if job["ai_video"]:
                    _step(conn, job_id, "running", "Đã có ảnh. Đang tạo video AI bằng Veo 3.1 (1-3 phút)…")
                    studio.build_ai_video(conn, item_id, 0)
                    kit = conn.execute("SELECT ai_video_status, ai_video_error FROM media_kits WHERE item_id = ? "
                                       "AND variant = 0", (item_id,)).fetchone()
                    if kit["ai_video_status"] == "error":
                        _step(conn, job_id, "error", "Đã có ảnh, video AI lỗi", error=kit["ai_video_error"])
                        return
            _step(conn, job_id, "done", f"Xong · ngành “{niche}” ({how})")
        except Exception as e:  # noqa: BLE001
            _step(conn, job_id, "error", "Lỗi", error=str(e)[:500])


def set_niche_and_resume(conn, job_id: int, niche: str) -> bool:
    if niche not in db.niche_names(conn):
        return False
    conn.execute("UPDATE link_jobs SET niche = ?, status = 'queued', step = '' WHERE id = ? AND status = 'need_niche'",
                 (niche, job_id))
    return True


def run_pending(conn=None, limit: int = 50) -> int:
    """Chạy các việc còn chờ (dùng cho cron nếu app khởi động lại giữa chừng)."""
    with db.get_conn() as c:
        ids = [r[0] for r in c.execute(
            "SELECT id FROM link_jobs WHERE status IN ('queued', 'running') ORDER BY id LIMIT ?", (limit,))]
    for job_id in ids:
        run_job(job_id)
    return len(ids)
