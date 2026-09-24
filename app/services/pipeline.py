"""Các việc tự động: nhận diện page, tạo bài nháp, đăng bài (video / ảnh), đồng bộ số liệu.

Chạy bằng cron (xem README) hoặc bấm nút trong trang Cài đặt.
"""
import json
import zlib
from datetime import datetime, timedelta

from app import config, db
from app.services import ai_writer, facebook, shopee


def score_product(p: dict) -> float:
    """Tiền hoa hồng kỳ vọng mỗi đơn, nhân hệ số độ tin cậy từ lượt bán & đánh giá."""
    per_order = p["price"] * p["commission_rate"]
    trust = min(p["sales"], 20000) ** 0.5 / 141 * (p["rating"] / 5)
    return round(per_order * (0.5 + trust), 1)


def hunt_products(conn) -> int:
    """Tìm sản phẩm hoa hồng cao cho từng ngách và lưu vào kho."""
    s = db.get_settings(conn)
    count = 0
    for n in db.get_niches(conn):
        niche = n["name"]
        for kw in n["keywords"]:
            try:
                items = shopee.search_products(kw)
            except Exception as e:  # noqa: BLE001 - ghi log và chạy tiếp
                db.log(conn, "error", f"Lỗi tìm sản phẩm '{kw}': {e}")
                continue
            for p in items:
                if (p["commission_rate"] < s["min_commission_rate"] or p["rating"] < s["min_rating"]
                        or p["sales"] < s["min_sales"]):
                    continue
                blocked = int(any(w.lower() in p["name"].lower() for w in s["blacklist"]))
                conn.execute(
                    """INSERT INTO products(item_id, name, niche, price, commission_rate, sales, rating,
                           shop_name, image_url, product_link, offer_link, score, blocked, fetched_at)
                       VALUES (:item_id, :name, :niche, :price, :commission_rate, :sales, :rating,
                           :shop_name, :image_url, :product_link, :offer_link, :score, :blocked, :fetched_at)
                       ON CONFLICT(item_id) DO UPDATE SET price=excluded.price,
                           commission_rate=excluded.commission_rate, sales=excluded.sales,
                           rating=excluded.rating, score=excluded.score, fetched_at=excluded.fetched_at""",
                    {**p, "niche": niche, "score": score_product(p), "blocked": blocked,
                     "fetched_at": db.now_iso()},
                )
                count += 1
    db.log(conn, "info", f"Săn sản phẩm: cập nhật {count} sản phẩm đạt tiêu chí")
    return count


def _slots(day: datetime, hours: list[int], n: int, offset_min: int) -> list[datetime]:
    """Chia n bài vào các khung giờ, lệch vài phút giữa các page để không đăng cùng lúc."""
    hours = sorted(hours)
    step = max(1, len(hours) // max(n, 1))
    picked = hours[::step][:n]
    return [day.replace(hour=h, minute=offset_min % 50, second=0) for h in picked]


def generate_drafts(conn, day: datetime | None = None) -> int:
    """Tạo bài nháp cho ngày `day` (mặc định: ngày mai) cho mọi page đang hoạt động."""
    s = db.get_settings(conn)
    day = (day or db.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    day_str = day.date().isoformat()
    since = (day - timedelta(days=s["repeat_product_after_days"])).isoformat()

    pages = conn.execute(
        "SELECT * FROM pages WHERE status = 'active' AND niche != '' ORDER BY niche, id").fetchall()
    usage: dict[str, int] = {}          # số page dùng mỗi sản phẩm trong ngày
    candidates_by_niche: dict[str, list] = {}
    jobs = []                           # (page, product, giờ đăng)

    # Bước 1: chọn sản phẩm + giờ đăng cho từng page
    for idx, page in enumerate(pages):
        have = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE page_id = ? AND date(scheduled_at) = ?",
            (page["id"], day_str),
        ).fetchone()[0]
        need = page["posts_per_day"] - have
        if need <= 0:
            continue
        recent = {r[0] for r in conn.execute(
            "SELECT item_id FROM posts WHERE page_id = ? AND created_at >= ? AND item_id IS NOT NULL",
            (page["id"], since),
        )}
        if page["niche"] not in candidates_by_niche:
            # Sản phẩm bạn nhập cho ngành này, đủ tên + link aff (hoặc tự tạo link khi có Shopee Open API)
            candidates_by_niche[page["niche"]] = conn.execute(
                """SELECT products.*, (SELECT COUNT(*) FROM videos WHERE videos.item_id = products.item_id) AS n_videos
                   FROM products WHERE niche = ? AND blocked = 0 AND name != ''
                     AND (aff_link != '' OR ?)
                   ORDER BY n_videos > 0 DESC, score DESC, fetched_at DESC LIMIT 500""",
                (page["niche"], int(config.SHOPEE_ENABLED)),
            ).fetchall()
        chosen = []
        for p in candidates_by_niche[page["niche"]]:
            if p["item_id"] in recent or usage.get(p["item_id"], 0) >= s["max_pages_per_product_per_day"]:
                continue
            chosen.append(p)
            usage[p["item_id"]] = usage.get(p["item_id"], 0) + 1
            if len(chosen) == need:
                break
        if not chosen:
            db.log(conn, "warn", f"Ngành “{page['niche']}” hết sản phẩm chưa đăng, hãy nhập thêm sản phẩm", page["id"])
            continue
        jobs += [(page, p, when) for p, when in zip(chosen, _slots(day, s["post_hours"], len(chosen), idx * 7))]

    # Bước 2: AI viết toàn bộ caption một lần (Batch API khi số lượng lớn)
    record_usage = usage_recorder(conn)
    captions = ai_writer.write_captions(
        [{"page": dict(pg), "product": dict(p)} for pg, p, _ in jobs], s["disclosure"], record_usage)

    # Bước 3: kiểm duyệt, lưu bài, tạo link aff
    day_captions: dict[str, list[str]] = {}  # caption trong ngày theo sản phẩm
    created = 0
    for (page, p, when), (caption, error) in zip(jobs, captions):
        if error:
            db.log(conn, "error", f"AI lỗi khi viết bài cho '{p['name']}': {error}", page["id"])
            continue
        flags = ai_writer.check_content(caption, s, day_captions.get(p["item_id"], []))
        day_captions.setdefault(p["item_id"], []).append(caption)
        status = "approved" if page["auto_approve"] and not flags else "pending"
        media_type, video_id, kit_id = pick_media(conn, p["item_id"], page["id"], s.get("kit_media", "alternate"),
                                                  created)
        if media_type == "photo" and not p["image_url"]:
            flags.append("Sản phẩm chưa có ảnh / video, hãy tạo bộ media trong Studio")
        now = db.now_iso()
        cur = conn.execute(
            """INSERT INTO posts(page_id, item_id, caption, image_url, media_type, video_id, kit_id, status, flags,
                   scheduled_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (page["id"], p["item_id"], caption, p["image_url"], media_type, video_id, kit_id, status,
             json.dumps(flags, ensure_ascii=False), when.isoformat(), now, now),
        )
        post_id = cur.lastrowid
        link = p["aff_link"]
        if not link and config.SHOPEE_ENABLED:
            try:
                link = shopee.make_link(p["offer_link"] or p["product_link"], page["id"], post_id)
            except Exception as e:  # noqa: BLE001
                db.log(conn, "error", f"Không tạo được link aff cho bài #{post_id}: {e}", page["id"])
        conn.execute("UPDATE posts SET aff_link = ? WHERE id = ?", (link, post_id))
        created += 1

    db.log(conn, "info", f"Đã tạo {created} bài nháp cho ngày {day_str}")
    return created


def usage_recorder(conn):
    """Hàm ghi lại token Claude đã dùng (để tính chi phí thật)."""
    def record(model, tin, tout, batch):
        conn.execute("INSERT INTO ai_usage(ts, model, input_tokens, output_tokens, batch) VALUES (?, ?, ?, ?, ?)",
                     (db.now_iso(), model, tin, tout, int(batch)))
    return record


def build_media(conn, limit: int = 30) -> int:
    """Tạo bộ ảnh + video cho sản phẩm chưa có (chạy trước khi tạo bài nháp)."""
    from app.services import studio

    return studio.build_missing(conn, limit, usage_recorder(conn))


def pick_media(conn, item_id: str, page_id: str, kit_media: str = "alternate", seq: int = 0):
    """Chọn nội dung đăng cho 1 bài. Trả về (media_type, video_id, kit_id).

    1. Video riêng bạn cung cấp (chưa đăng trên page này) -> "video".
    2. Bộ media app tạo: mỗi page dùng 1 phiên bản cố định (khác màu/bố cục với page khác);
       đăng album 3-5 ảnh hoặc video ngắn (xen kẽ theo cài đặt).
    3. Không có gì -> 1 ảnh sản phẩm ("photo").
    """
    video = pick_video(conn, item_id, page_id)
    if video:
        return "video", video["id"], None
    kits = conn.execute("""SELECT id, video_path, ai_video_status FROM media_kits
                           WHERE item_id = ? AND status = 'ready' ORDER BY variant""", (item_id,)).fetchall()
    if kits:
        kit = kits[zlib.crc32(page_id.encode()) % len(kits)]
        if kit["ai_video_status"] == "ready" and kit_media != "album":
            return "kit_video", None, kit["id"]                   # có video AI (Veo): ưu tiên video
        if kit_media == "video" or (kit_media == "alternate" and (seq + zlib.crc32(page_id.encode())) % 2):
            return ("kit_video", None, kit["id"]) if kit["video_path"] else ("album", None, kit["id"])
        return "album", None, kit["id"]
    return "photo", None, None


def pick_video(conn, item_id: str, page_id: str):
    """Video của sản phẩm chưa từng đăng trên page này, ưu tiên video ít được dùng nhất."""
    return conn.execute(
        """SELECT videos.* FROM videos WHERE item_id = ?
             AND id NOT IN (SELECT video_id FROM posts WHERE page_id = ? AND video_id IS NOT NULL
                            AND status NOT IN ('rejected', 'failed'))
           ORDER BY (SELECT COUNT(*) FROM posts WHERE posts.video_id = videos.id), id LIMIT 1""",
        (item_id, page_id),
    ).fetchone()


def publish_due(conn) -> tuple[int, int]:
    """Đăng các bài đã duyệt đến giờ. Trả về (thành công, lỗi)."""
    s = db.get_settings(conn)
    if s["global_pause"]:
        return 0, 0
    rows = conn.execute(
        """SELECT posts.*, pages.name AS page_name, pages.access_token, pages.link_mode
           FROM posts JOIN pages ON pages.id = posts.page_id
           WHERE posts.status = 'approved' AND pages.status = 'active' AND posts.scheduled_at <= ?
           ORDER BY posts.scheduled_at LIMIT 200""",
        (db.now_iso(),),
    ).fetchall()
    ok = fail = 0
    for r in rows:
        if not r["aff_link"]:
            conn.execute("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?",
                         ("Thiếu link aff", db.now_iso(), r["id"]))
            fail += 1
            continue
        page = {"id": r["page_id"], "access_token": r["access_token"], "link_mode": r["link_mode"]}
        video, images = None, None
        if r["media_type"] == "video" and r["video_id"]:
            row = conn.execute("SELECT * FROM videos WHERE id = ?", (r["video_id"],)).fetchone()
            video = dict(row) if row else None
        elif r["media_type"] in ("album", "kit_video") and r["kit_id"]:
            kit = conn.execute("SELECT * FROM media_kits WHERE id = ? AND status = 'ready'", (r["kit_id"],)).fetchone()
            if kit and r["media_type"] == "kit_video":
                ai_ready = kit["ai_video_status"] == "ready" and kit["ai_video_path"]
                video = {"file_path": kit["ai_video_path"] if ai_ready else kit["video_path"]}
            elif kit:
                images = json.loads(kit["images"])
        try:
            res = facebook.publish(page, r["caption"], r["aff_link"], r["image_url"], video, images)
        except Exception as e:  # noqa: BLE001
            conn.execute("UPDATE posts SET status='failed', error=?, updated_at=? WHERE id=?",
                         (str(e)[:500], db.now_iso(), r["id"]))
            db.log(conn, "error", f"Đăng bài #{r['id']} thất bại: {e}", r["page_id"])
            fail += 1
            continue
        conn.execute(
            """UPDATE posts SET status='published', fb_post_id=?, permalink=?, published_at=?,
                   error=NULL, updated_at=? WHERE id=?""",
            (res["fb_post_id"], res["permalink"], db.now_iso(), db.now_iso(), r["id"]),
        )
        ok += 1
    if rows:
        db.log(conn, "info" if not fail else "warn", f"Đăng bài: {ok} thành công, {fail} lỗi")
    return ok, fail


def sync_metrics(conn, days: int = 7) -> int:
    """Cập nhật tương tác Facebook + hoa hồng Shopee cho các bài gần đây."""
    since = (db.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """SELECT posts.id, posts.fb_post_id, posts.page_id, pages.access_token FROM posts
           JOIN pages ON pages.id = posts.page_id
           WHERE posts.status = 'published' AND posts.published_at >= ?""",
        (since,),
    ).fetchall()
    for r in rows:
        try:
            m = facebook.post_metrics({"access_token": r["access_token"]}, r["fb_post_id"])
        except Exception as e:  # noqa: BLE001
            db.log(conn, "warn", f"Không lấy được số liệu bài #{r['id']}: {e}", r["page_id"])
            continue
        conn.execute("UPDATE posts SET reactions=?, comments=?, shares=? WHERE id=?",
                     (m["reactions"], m["comments"], m["shares"], r["id"]))

    for c in shopee.conversions(db.now() - timedelta(days=days), db.now()):
        conn.execute(
            """INSERT OR REPLACE INTO conversions(conversion_id, page_id, post_id, item_id, orders,
                   commission, purchase_time) VALUES (:conversion_id, :page_id, :post_id, :item_id,
                   :orders, :commission, :purchase_time)""",
            c,
        )
    conn.execute(
        """UPDATE posts SET
             orders = (SELECT COALESCE(SUM(orders), 0) FROM conversions WHERE post_id = posts.id),
             commission = (SELECT COALESCE(SUM(commission), 0) FROM conversions WHERE post_id = posts.id)
           WHERE id IN (SELECT DISTINCT post_id FROM conversions WHERE post_id IS NOT NULL)"""
    )
    db.log(conn, "info", f"Đồng bộ số liệu: {len(rows)} bài")
    return len(rows)


def sync_pages(conn, user_token: str = "") -> dict:
    """Nhận diện toàn bộ page của tài khoản Facebook đang đăng nhập.

    Page mới: thêm vào app, chờ bạn chọn ngành hàng. Page cũ: cập nhật tên + token.
    Page không còn quyền quản lý: chuyển sang "bị hạn chế" để ngừng đăng.
    """
    user_token = user_token or db.get_settings(conn).get("owner_token", "")
    pages = facebook.list_managed_pages(user_token)
    before = {r[0] for r in conn.execute("SELECT id FROM pages WHERE status != 'archived'")}
    for p in pages:
        conn.execute(
            """INSERT INTO pages(id, name, access_token, created_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name = excluded.name, access_token = excluded.access_token""",
            (p["id"], p["name"], p.get("access_token", ""), db.now_iso()),
        )
    seen = {p["id"] for p in pages}
    new = seen - before
    lost = before - seen if pages else set()
    for page_id in lost:
        conn.execute("UPDATE pages SET status = 'restricted' WHERE id = ? AND status != 'archived'", (page_id,))
        db.log(conn, "warn", "Tài khoản không còn quyền quản lý page này", page_id)
    db.log(conn, "info", f"Nhận diện {len(pages)} page ({len(new)} page mới cần chọn ngành hàng)")
    return {"total": len(pages), "new": len(new), "lost": len(lost)}


def import_pages(conn) -> int:
    return sync_pages(conn)["total"]


def import_facebook_posts(conn, page_id: str) -> int:
    """Kéo các bài đang có trên page (kể cả bài đăng tay ngoài app) để kiểm tra."""
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if not page:
        return 0
    added = 0
    for p in facebook.recent_posts(dict(page)):
        now = db.now_iso()
        created = datetime.strptime(p["created_time"], "%Y-%m-%dT%H:%M:%S%z").astimezone(db.now().tzinfo)
        cur = conn.execute(
            """INSERT OR IGNORE INTO posts(page_id, source, caption, image_url, status, fb_post_id,
                   permalink, published_at, scheduled_at, created_at, updated_at)
               VALUES (?, 'facebook', ?, ?, 'published', ?, ?, ?, ?, ?, ?)""",
            (page_id, p.get("message", ""), p.get("full_picture", ""), p["id"],
             p.get("permalink_url", ""), created.isoformat(), created.isoformat(), now, now),
        )
        added += cur.rowcount
    return added
