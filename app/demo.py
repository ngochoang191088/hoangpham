"""Tạo dữ liệu mẫu: 80 page chia theo ngành hàng (5 page/ngành), sản phẩm, 30 ngày lịch sử bài đăng và hoa hồng.

    python -m app.demo          # tạo mới (xoá dữ liệu cũ trong DB)
"""
import json
import random
from datetime import timedelta
from pathlib import Path

from app import config, db
from app.services import ai_writer, pipeline

STYLES = ["Săn Deal", "Góc", "Review Nhanh", "Tiệm", "Chợ"]
TONES = ["thân thiện, gần gũi", "vui nhộn, trẻ trung", "ngắn gọn, thực tế", "nhẹ nhàng, tinh tế"]


def seed(n_pages: int = 80, days: int = 30) -> None:
    Path(config.DB_PATH).unlink(missing_ok=True)
    db.init_db()
    rnd = random.Random(42)
    with db.get_conn() as conn:
        niches = list(db.DEFAULT_NICHES)
        # 5 page mỗi ngành; ngành cuối mới có 3 page; 2 page vừa nhập từ Meta chưa phân ngành
        assigned = [n for idx, n in enumerate(niches) for _ in range(5 if idx < len(niches) - 1 else 3)]
        while len(assigned) < n_pages - 2:
            assigned += niches
        assigned = assigned[:max(0, n_pages - 2)] + ["", ""]
        counter: dict[str, int] = {}
        for i, niche in enumerate(assigned[:n_pages]):
            counter[niche] = counter.get(niche, 0) + 1
            k = counter[niche]
            name = (f"{STYLES[(k - 1) % len(STYLES)]} {niche} {(k - 1) // len(STYLES) + 1}" if niche
                    else f"Page mới nhập từ Meta {k}")
            status = "restricted" if i in (13, 57) else "paused" if i == 71 else "active"
            conn.execute(
                """INSERT INTO pages(id, name, niche, tone, status, posts_per_day, link_mode, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(100000000000 + i), name, niche, rnd.choice(TONES), status,
                 rnd.choice([2, 3, 3, 4]), rnd.choice(["comment", "post"]),
                 (db.now() - timedelta(days=90)).isoformat()),
            )
        pipeline.hunt_products(conn)

        s = db.get_settings(conn)
        pages = conn.execute("SELECT * FROM pages").fetchall()
        products = {n: conn.execute("SELECT * FROM products WHERE niche = ? AND blocked = 0",
                                    (n,)).fetchall() for n in niches}
        conv_id = 0
        for d in range(days, 0, -1):
            day = db.now() - timedelta(days=d)
            for idx, page in enumerate(pages):
                if (page["status"] == "paused" and d < 10) or not page["niche"]:
                    continue
                strength = 0.4 + (idx * 37 % 100) / 60      # page mạnh/yếu khác nhau
                for when in pipeline._slots(day, s["post_hours"], page["posts_per_day"], idx * 7):
                    p = rnd.choice(products[page["niche"]])
                    caption = ai_writer.write_caption(dict(page), dict(p), s["disclosure"])
                    failed = rnd.random() < 0.02 or (page["status"] == "restricted" and d < 3)
                    reactions = int(rnd.randint(5, 250) * strength)
                    orders = sum(rnd.random() < 0.01 * strength for _ in range(12)) if not failed else 0
                    commission = round(orders * p["price"] * p["commission_rate"], -2)
                    cur = conn.execute(
                        """INSERT INTO posts(page_id, item_id, caption, image_url, aff_link, status, flags,
                               scheduled_at, published_at, fb_post_id, permalink, error, reactions,
                               comments, shares, orders, commission, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (page["id"], p["item_id"], caption, p["image_url"],
                         f"https://s.shopee.vn/demo?sub=p{page['id']}",
                         "failed" if failed else "published", when.isoformat(),
                         None if failed else when.isoformat(),
                         None if failed else f"{page['id']}_{rnd.getrandbits(40)}",
                         None if failed else f"https://www.facebook.com/{page['id']}",
                         "(#368) The action attempted has been deemed abusive or is otherwise disallowed"
                         if failed else None,
                         reactions, reactions // 6, reactions // 15, orders, commission,
                         when.isoformat(), when.isoformat()),
                    )
                    for _ in range(orders):
                        conv_id += 1
                        conn.execute(
                            """INSERT INTO conversions(conversion_id, page_id, post_id, item_id, orders,
                                   commission, purchase_time) VALUES (?, ?, ?, ?, 1, ?, ?)""",
                            (f"demo{conv_id}", page["id"], cur.lastrowid, p["item_id"],
                             commission / orders, (when + timedelta(hours=rnd.randint(0, 20))).isoformat()),
                        )
        # Bài hôm nay: một phần đã đăng, phần còn lại chờ duyệt / đã duyệt
        pipeline.generate_drafts(conn, db.now())
        conn.execute("UPDATE posts SET status = 'approved' WHERE status = 'pending' AND id % 3 != 0")
        pipeline.publish_due(conn)
        pipeline.generate_drafts(conn)
        # Ví dụ bài bị kiểm duyệt gắn cờ
        conn.execute(
            "UPDATE posts SET caption = caption || ?, flags = ? WHERE id IN "
            "(SELECT id FROM posts WHERE status = 'pending' ORDER BY id LIMIT 3)",
            ("\nMình đã dùng rồi, cam kết 100% hiệu quả!",
             json.dumps(["Câu dễ gây hiểu lầm: “mình đã dùng”", "Câu dễ gây hiểu lầm: “cam kết 100%”"],
                        ensure_ascii=False)),
        )
        for page in pages:
            if page["status"] == "restricted":
                db.log(conn, "warn", "Page bị Facebook hạn chế tính năng đăng bài", page["id"])
    print(f"Đã tạo dữ liệu mẫu tại {config.DB_PATH}")


if __name__ == "__main__":
    seed()
