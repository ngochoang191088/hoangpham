"""Các việc tự động: săn sản phẩm, tạo bài nháp, đăng bài, đồng bộ số liệu.

Chạy bằng cron (xem README) hoặc bấm nút trong trang Cài đặt.
"""
import json
from datetime import datetime, timedelta

from app import db
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
    for niche, keywords in s["niches"].items():
        for kw in keywords:
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

    pages = conn.execute("SELECT * FROM pages WHERE status = 'active' ORDER BY id").fetchall()
    usage: dict[str, int] = {}          # số page dùng mỗi sản phẩm trong ngày
    day_captions: dict[str, list[str]] = {}  # caption trong ngày theo sản phẩm
    created = 0

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
        candidates = conn.execute(
            "SELECT * FROM products WHERE niche = ? AND blocked = 0 ORDER BY score DESC LIMIT 60",
            (page["niche"],),
        ).fetchall()
        chosen = []
        for p in candidates:
            if p["item_id"] in recent or usage.get(p["item_id"], 0) >= s["max_pages_per_product_per_day"]:
                continue
            chosen.append(p)
            usage[p["item_id"]] = usage.get(p["item_id"], 0) + 1
            if len(chosen) == need:
                break
        if not chosen:
            db.log(conn, "warn", "Không còn sản phẩm phù hợp để tạo bài", page["id"])
            continue

        for p, when in zip(chosen, _slots(day, s["post_hours"], len(chosen), idx * 7)):
            try:
                caption = ai_writer.write_caption(dict(page), dict(p), s["disclosure"])
            except Exception as e:  # noqa: BLE001
                db.log(conn, "error", f"AI lỗi khi viết bài cho '{p['name']}': {e}", page["id"])
                continue
            flags = ai_writer.check_content(caption, s, day_captions.get(p["item_id"], []))
            day_captions.setdefault(p["item_id"], []).append(caption)
            status = "approved" if page["auto_approve"] and not flags else "pending"
            now = db.now_iso()
            cur = conn.execute(
                """INSERT INTO posts(page_id, item_id, caption, image_url, status, flags, scheduled_at,
                       created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page["id"], p["item_id"], caption, p["image_url"], status,
                 json.dumps(flags, ensure_ascii=False), when.isoformat(), now, now),
            )
            post_id = cur.lastrowid
            try:
                link = shopee.make_link(p["offer_link"] or p["product_link"], page["id"], post_id)
            except Exception as e:  # noqa: BLE001
                link = ""
                db.log(conn, "error", f"Không tạo được link aff cho bài #{post_id}: {e}", page["id"])
            conn.execute("UPDATE posts SET aff_link = ? WHERE id = ?", (link, post_id))
            created += 1

    db.log(conn, "info", f"Đã tạo {created} bài nháp cho ngày {day_str}")
    return created


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
        try:
            res = facebook.publish(page, r["caption"], r["image_url"], r["aff_link"])
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


def import_pages(conn) -> int:
    """Nhập / cập nhật danh sách page (và page token) từ Meta Business."""
    pages = facebook.list_managed_pages()
    for p in pages:
        conn.execute(
            """INSERT INTO pages(id, name, access_token, created_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name = excluded.name, access_token = excluded.access_token""",
            (p["id"], p["name"], p.get("access_token", ""), db.now_iso()),
        )
    db.log(conn, "info", f"Đồng bộ {len(pages)} page từ Meta Business")
    return len(pages)


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
