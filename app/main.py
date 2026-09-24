import json
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config, db
from app.services import ai_writer, pipeline

BASE = Path(__file__).resolve().parent
security = HTTPBasic()


def require_login(creds: HTTPBasicCredentials = Depends(security)) -> str:
    ok_user = secrets.compare_digest(creds.username.encode(), config.ADMIN_USER.encode())
    ok_pass = secrets.compare_digest(creds.password.encode(), config.ADMIN_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})
    return creds.username


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Quản lý 80 page", lifespan=lifespan, dependencies=[Depends(require_login)])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def vnd(value) -> str:
    return f"{int(round(value or 0)):,}đ".replace(",", ".")


def num(value) -> str:
    return f"{int(value or 0):,}".replace(",", ".")


templates.env.filters.update(vnd=vnd, num=num, loads=json.loads)
templates.env.globals.update(config=config)


def render(request: Request, name: str, **ctx) -> HTMLResponse:
    with db.get_conn() as conn:
        ctx.setdefault("pending_count", conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status = 'pending'").fetchone()[0])
        ctx.setdefault("global_pause", db.get_settings(conn)["global_pause"])
    return templates.TemplateResponse(request, name, ctx)


def back(request: Request, fallback: str = "/") -> RedirectResponse:
    return RedirectResponse(request.headers.get("referer") or fallback, status_code=303)


def _days_ago(n: int) -> str:
    return (db.now() - timedelta(days=n)).isoformat()


# ---------------- Tổng quan ----------------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, days: int = 30):
    days = days if days in (7, 30, 90) else 30
    since = _days_ago(days)
    today = db.now().date().isoformat()
    with db.get_conn() as conn:
        q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
        kpi = {
            "pages": q("SELECT COUNT(*) FROM pages"),
            "active": q("SELECT COUNT(*) FROM pages WHERE status = 'active'"),
            "restricted": q("SELECT COUNT(*) FROM pages WHERE status = 'restricted'"),
            "paused": q("SELECT COUNT(*) FROM pages WHERE status = 'paused'"),
            "published_today": q("SELECT COUNT(*) FROM posts WHERE status='published' AND date(published_at)=?", today),
            "scheduled_today": q("SELECT COUNT(*) FROM posts WHERE status='approved' AND date(scheduled_at)=?", today),
            "commission_today": q("SELECT COALESCE(SUM(commission),0) FROM conversions WHERE date(purchase_time)=?", today),
            "commission": q("SELECT COALESCE(SUM(commission),0) FROM conversions WHERE purchase_time>=?", since),
            "orders": q("SELECT COALESCE(SUM(orders),0) FROM conversions WHERE purchase_time>=?", since),
            "posts": q("SELECT COUNT(*) FROM posts WHERE status='published' AND published_at>=?", since),
            "reactions": q("SELECT COALESCE(SUM(reactions+comments+shares),0) FROM posts WHERE published_at>=?", since),
            "failed": q("SELECT COUNT(*) FROM posts WHERE status='failed' AND scheduled_at>=?", _days_ago(2)),
        }
        daily = conn.execute(
            """WITH RECURSIVE d(day) AS (SELECT date(?) UNION ALL SELECT date(day, '+1 day') FROM d WHERE day < date(?))
               SELECT d.day,
                 (SELECT COALESCE(SUM(commission),0) FROM conversions WHERE date(purchase_time)=d.day) AS commission,
                 (SELECT COALESCE(SUM(orders),0) FROM conversions WHERE date(purchase_time)=d.day) AS orders,
                 (SELECT COUNT(*) FROM posts WHERE status='published' AND date(published_at)=d.day) AS posts
               FROM d""",
            (since, today),
        ).fetchall()
        page_stats = """SELECT pages.id, pages.name, pages.niche, pages.status,
                 COUNT(posts.id) AS posts, COALESCE(SUM(posts.orders),0) AS orders,
                 COALESCE(SUM(posts.commission),0) AS commission,
                 COALESCE(SUM(posts.reactions+posts.comments+posts.shares),0) AS engagement
               FROM pages LEFT JOIN posts ON posts.page_id = pages.id
                 AND posts.status='published' AND posts.published_at >= ?"""
        top_pages = conn.execute(page_stats + " GROUP BY pages.id ORDER BY commission DESC LIMIT 10", (since,)).fetchall()
        weak_pages = conn.execute(page_stats + " WHERE pages.status='active' GROUP BY pages.id ORDER BY commission ASC LIMIT 5", (since,)).fetchall()
        niches = conn.execute(
            """SELECT pages.niche, COUNT(DISTINCT pages.id) AS pages, COALESCE(SUM(conversions.orders),0) AS orders,
                 COALESCE(SUM(conversions.commission),0) AS commission
               FROM pages LEFT JOIN conversions ON conversions.page_id = pages.id AND conversions.purchase_time >= ?
               GROUP BY pages.niche ORDER BY commission DESC""",
            (since,),
        ).fetchall()
        top_products = conn.execute(
            """SELECT products.name, products.commission_rate, COUNT(DISTINCT posts.page_id) AS pages,
                 SUM(posts.orders) AS orders, SUM(posts.commission) AS commission
               FROM posts JOIN products ON products.item_id = posts.item_id
               WHERE posts.published_at >= ? GROUP BY products.item_id ORDER BY commission DESC LIMIT 8""",
            (since,),
        ).fetchall()
        alerts = []
        for p in conn.execute("SELECT id, name FROM pages WHERE status='restricted'"):
            alerts.append(("error", f"Page “{p['name']}” đang bị Facebook hạn chế", f"/pages/{p['id']}"))
        if kpi["failed"]:
            alerts.append(("error", f"{kpi['failed']} bài đăng lỗi trong 48 giờ qua", "/posts?status=failed"))
        silent = conn.execute(
            """SELECT id, name FROM pages WHERE status='active' AND id NOT IN
               (SELECT page_id FROM posts WHERE status='published' AND published_at >= ?)""",
            (_days_ago(2),),
        ).fetchall()
        for p in silent[:5]:
            alerts.append(("warn", f"Page “{p['name']}” không có bài nào trong 2 ngày", f"/pages/{p['id']}"))
        flagged = q("SELECT COUNT(*) FROM posts WHERE status='pending' AND flags != '[]'")
        if flagged:
            alerts.append(("warn", f"{flagged} bài chờ duyệt bị gắn cờ kiểm duyệt", "/review?flagged=1"))
        activity = conn.execute(
            """SELECT activity.*, pages.name AS page_name FROM activity
               LEFT JOIN pages ON pages.id = activity.page_id ORDER BY activity.id DESC LIMIT 12"""
        ).fetchall()
    chart = {
        "labels": [r["day"][5:] for r in daily],
        "commission": [round(r["commission"]) for r in daily],
        "orders": [r["orders"] for r in daily],
        "posts": [r["posts"] for r in daily],
    }
    return render(request, "dashboard.html", kpi=kpi, chart=chart, top_pages=top_pages,
                  weak_pages=weak_pages, niches=niches, top_products=top_products,
                  alerts=alerts, activity=activity, days=days)


# ---------------- Page ----------------

SORTS = {"commission": "commission DESC", "orders": "orders DESC", "engagement": "engagement DESC",
         "posts": "posts DESC", "name": "pages.name", "last": "last_published DESC"}


@app.get("/pages", response_class=HTMLResponse)
def pages_list(request: Request, niche: str = "", status_: str = "", q: str = "", sort: str = "commission"):
    since = _days_ago(30)
    where, args = ["1=1"], [since]
    if niche:
        where.append("pages.niche = ?"); args.append(niche)
    if status_:
        where.append("pages.status = ?"); args.append(status_)
    if q:
        where.append("pages.name LIKE ?"); args.append(f"%{q}%")
    with db.get_conn() as conn:
        rows = conn.execute(
            f"""SELECT pages.*,
                  COUNT(posts.id) AS posts, COALESCE(SUM(posts.orders),0) AS orders,
                  COALESCE(SUM(posts.commission),0) AS commission,
                  COALESCE(SUM(posts.reactions+posts.comments+posts.shares),0) AS engagement,
                  (SELECT MAX(published_at) FROM posts p2 WHERE p2.page_id = pages.id AND p2.status='published') AS last_published,
                  (SELECT COUNT(*) FROM posts p3 WHERE p3.page_id = pages.id AND p3.status='pending') AS pending,
                  (SELECT COUNT(*) FROM posts p4 WHERE p4.page_id = pages.id AND p4.status='failed') AS failed
                FROM pages LEFT JOIN posts ON posts.page_id = pages.id
                  AND posts.status='published' AND posts.published_at >= ?
                WHERE {' AND '.join(where)} GROUP BY pages.id ORDER BY {SORTS.get(sort, SORTS['commission'])}""",
            args,
        ).fetchall()
        niches = [r[0] for r in conn.execute("SELECT DISTINCT niche FROM pages ORDER BY niche")]
    return render(request, "pages.html", rows=rows, niches=niches, niche=niche, status_=status_, q=q, sort=sort)


@app.get("/pages/{page_id}", response_class=HTMLResponse)
def page_detail(request: Request, page_id: str, status_: str = "published", days: int = 30):
    with db.get_conn() as conn:
        page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if not page:
            raise HTTPException(404, "Không tìm thấy page")
        since = _days_ago(days)
        stats = conn.execute(
            """SELECT COUNT(*) AS posts, COALESCE(SUM(orders),0) AS orders, COALESCE(SUM(commission),0) AS commission,
                 COALESCE(SUM(reactions),0) AS reactions, COALESCE(SUM(comments),0) AS comments,
                 COALESCE(SUM(shares),0) AS shares
               FROM posts WHERE page_id = ? AND status='published' AND published_at >= ?""",
            (page_id, since),
        ).fetchone()
        daily = conn.execute(
            """SELECT date(published_at) AS day, COUNT(*) AS posts, SUM(commission) AS commission
               FROM posts WHERE page_id = ? AND status='published' AND published_at >= ?
               GROUP BY day ORDER BY day""",
            (page_id, since),
        ).fetchall()
        counts = dict(conn.execute(
            "SELECT status, COUNT(*) FROM posts WHERE page_id = ? GROUP BY status", (page_id,)).fetchall())
        order = "scheduled_at ASC" if status_ in ("pending", "approved") else "COALESCE(published_at, scheduled_at) DESC"
        posts = conn.execute(
            f"""SELECT posts.*, products.name AS product_name, products.commission_rate
                FROM posts LEFT JOIN products ON products.item_id = posts.item_id
                WHERE page_id = ? AND status = ? ORDER BY {order} LIMIT 30""",
            (page_id, status_),
        ).fetchall()
        niches = list(db.get_settings(conn)["niches"])
        activity = conn.execute(
            "SELECT * FROM activity WHERE page_id = ? ORDER BY id DESC LIMIT 10", (page_id,)).fetchall()
    chart = {"labels": [r["day"][5:] for r in daily], "commission": [round(r["commission"] or 0) for r in daily],
             "posts": [r["posts"] for r in daily]}
    return render(request, "page_detail.html", page=page, stats=stats, chart=chart, posts=posts,
                  counts=counts, status_=status_, niches=niches, activity=activity, days=days)


@app.post("/pages/{page_id}")
def page_update(request: Request, page_id: str, niche: str = Form(...), tone: str = Form(...),
                posts_per_day: int = Form(...), link_mode: str = Form(...), status_: str = Form(...),
                auto_approve: bool = Form(False)):
    with db.get_conn() as conn:
        conn.execute(
            """UPDATE pages SET niche=?, tone=?, posts_per_day=?, link_mode=?, status=?, auto_approve=?
               WHERE id=?""",
            (niche, tone, max(0, min(posts_per_day, 20)), link_mode, status_, int(auto_approve), page_id),
        )
        db.log(conn, "info", "Cập nhật cài đặt page", page_id)
    return back(request)


@app.post("/pages/{page_id}/toggle")
def page_toggle(request: Request, page_id: str):
    with db.get_conn() as conn:
        page = conn.execute("SELECT status FROM pages WHERE id = ?", (page_id,)).fetchone()
        new = "paused" if page["status"] == "active" else "active"
        conn.execute("UPDATE pages SET status = ? WHERE id = ?", (new, page_id))
        db.log(conn, "info", "Bật đăng bài" if new == "active" else "Tạm dừng đăng bài", page_id)
    return back(request)


@app.post("/pages/{page_id}/import")
def page_import(request: Request, page_id: str):
    with db.get_conn() as conn:
        n = pipeline.import_facebook_posts(conn, page_id)
        db.log(conn, "info", f"Kéo {n} bài từ Facebook", page_id)
    return back(request)


# ---------------- Bài đăng ----------------

@app.get("/posts", response_class=HTMLResponse)
def posts_list(request: Request, status: str = "published", page_id: str = "", niche: str = "",
               q: str = "", day: str = "", flagged: int = 0, p: int = 1):
    where, args = ["posts.status = ?"], [status]
    if page_id:
        where.append("posts.page_id = ?"); args.append(page_id)
    if niche:
        where.append("pages.niche = ?"); args.append(niche)
    if q:
        where.append("posts.caption LIKE ?"); args.append(f"%{q}%")
    if day:
        where.append("date(COALESCE(posts.published_at, posts.scheduled_at)) = ?"); args.append(day)
    if flagged:
        where.append("posts.flags != '[]'")
    per = 40
    with db.get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM posts JOIN pages ON pages.id = posts.page_id WHERE {' AND '.join(where)}",
            args).fetchone()[0]
        rows = conn.execute(
            f"""SELECT posts.*, pages.name AS page_name, pages.niche, products.name AS product_name
                FROM posts JOIN pages ON pages.id = posts.page_id
                LEFT JOIN products ON products.item_id = posts.item_id
                WHERE {' AND '.join(where)}
                ORDER BY COALESCE(posts.published_at, posts.scheduled_at) DESC LIMIT ? OFFSET ?""",
            args + [per, (max(p, 1) - 1) * per],
        ).fetchall()
        pages = conn.execute("SELECT id, name FROM pages ORDER BY name").fetchall()
        niches = [r[0] for r in conn.execute("SELECT DISTINCT niche FROM pages ORDER BY niche")]
    return render(request, "posts.html", rows=rows, total=total, pages=pages, niches=niches, status=status,
                  page_id=page_id, niche=niche, q=q, day=day, flagged=flagged, p=max(p, 1), per=per)


@app.get("/review", response_class=HTMLResponse)
def review(request: Request, page_id: str = "", flagged: int = 0):
    where, args = ["posts.status = 'pending'"], []
    if page_id:
        where.append("posts.page_id = ?"); args.append(page_id)
    if flagged:
        where.append("posts.flags != '[]'")
    with db.get_conn() as conn:
        rows = conn.execute(
            f"""SELECT posts.*, pages.name AS page_name, pages.niche, products.name AS product_name,
                  products.price, products.commission_rate, products.rating, products.sales
                FROM posts JOIN pages ON pages.id = posts.page_id
                LEFT JOIN products ON products.item_id = posts.item_id
                WHERE {' AND '.join(where)} ORDER BY posts.flags != '[]' DESC, posts.scheduled_at LIMIT 200""",
            args,
        ).fetchall()
        clean = conn.execute("SELECT COUNT(*) FROM posts WHERE status='pending' AND flags='[]'").fetchone()[0]
    return render(request, "review.html", rows=rows, clean=clean, flagged=flagged)


@app.post("/posts/{post_id}/edit")
def post_edit(request: Request, post_id: int, caption: str = Form(...)):
    with db.get_conn() as conn:
        s = db.get_settings(conn)
        flags = ai_writer.check_content(caption, s, [])
        conn.execute("UPDATE posts SET caption=?, flags=?, updated_at=? WHERE id=? AND status IN ('pending','approved')",
                     (caption, json.dumps(flags, ensure_ascii=False), db.now_iso(), post_id))
    return back(request)


@app.post("/posts/{post_id}/{action}")
def post_action(request: Request, post_id: int, action: str):
    transitions = {"approve": ("pending", "approved"), "reject": ("pending", "rejected"),
                   "unapprove": ("approved", "pending"), "retry": ("failed", "approved")}
    if action not in transitions:
        raise HTTPException(404)
    old, new = transitions[action]
    with db.get_conn() as conn:
        conn.execute("UPDATE posts SET status=?, updated_at=? WHERE id=? AND status=?",
                     (new, db.now_iso(), post_id, old))
    return back(request)


@app.post("/review/bulk")
def review_bulk(request: Request, action: str = Form(...), ids: list[int] = Form(default=[])):
    new = {"approve": "approved", "reject": "rejected"}.get(action)
    with db.get_conn() as conn:
        if action == "approve_clean":
            n = conn.execute("UPDATE posts SET status='approved', updated_at=? WHERE status='pending' AND flags='[]'",
                             (db.now_iso(),)).rowcount
        elif new and ids:
            marks = ",".join("?" * len(ids))
            n = conn.execute(f"UPDATE posts SET status=?, updated_at=? WHERE status='pending' AND id IN ({marks})",
                             [new, db.now_iso(), *ids]).rowcount
        else:
            n = 0
        if n:
            db.log(conn, "info", f"Duyệt hàng loạt: {n} bài → {'từ chối' if action == 'reject' else 'đã duyệt'}")
    return back(request, "/review")


# ---------------- Sản phẩm ----------------

@app.get("/products", response_class=HTMLResponse)
def products(request: Request, niche: str = "", q: str = ""):
    where, args = ["1=1"], []
    if niche:
        where.append("niche = ?"); args.append(niche)
    if q:
        where.append("name LIKE ?"); args.append(f"%{q}%")
    with db.get_conn() as conn:
        rows = conn.execute(
            f"""SELECT products.*,
                  (SELECT COUNT(*) FROM posts WHERE posts.item_id = products.item_id AND status='published') AS used,
                  (SELECT COALESCE(SUM(commission),0) FROM posts WHERE posts.item_id = products.item_id) AS earned
                FROM products WHERE {' AND '.join(where)} ORDER BY score DESC LIMIT 300""",
            args,
        ).fetchall()
        niches = list(db.get_settings(conn)["niches"])
    return render(request, "products.html", rows=rows, niches=niches, niche=niche, q=q)


@app.post("/products/{item_id}/toggle")
def product_toggle(request: Request, item_id: str):
    with db.get_conn() as conn:
        conn.execute("UPDATE products SET blocked = 1 - blocked WHERE item_id = ?", (item_id,))
    return back(request)


# ---------------- Cài đặt & chạy việc ----------------

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    with db.get_conn() as conn:
        s = db.get_settings(conn)
        activity = conn.execute(
            """SELECT activity.*, pages.name AS page_name FROM activity
               LEFT JOIN pages ON pages.id = activity.page_id ORDER BY activity.id DESC LIMIT 50"""
        ).fetchall()
    return render(request, "settings.html", s=s, activity=activity)


@app.post("/settings")
def settings_save(request: Request, min_commission_rate: float = Form(...), min_rating: float = Form(...),
                  min_sales: int = Form(...), max_pages_per_product_per_day: int = Form(...),
                  repeat_product_after_days: int = Form(...), post_hours: str = Form(...),
                  blacklist: str = Form(""), disclosure: str = Form(...), niches: str = Form(...)):
    try:
        niches_val = json.loads(niches)
        hours = sorted({int(h) for h in post_hours.replace(" ", "").split(",") if h})
        assert isinstance(niches_val, dict) and all(0 <= h <= 23 for h in hours)
    except (ValueError, AssertionError):
        raise HTTPException(400, "Khung giờ hoặc danh sách ngách không hợp lệ")
    with db.get_conn() as conn:
        for key, value in {
            "min_commission_rate": min_commission_rate / 100, "min_rating": min_rating, "min_sales": min_sales,
            "max_pages_per_product_per_day": max_pages_per_product_per_day,
            "repeat_product_after_days": repeat_product_after_days, "post_hours": hours,
            "blacklist": [w.strip() for w in blacklist.splitlines() if w.strip()],
            "disclosure": disclosure.strip(), "niches": niches_val,
        }.items():
            db.set_setting(conn, key, value)
        db.log(conn, "info", "Cập nhật cài đặt chung")
    return back(request, "/settings")


@app.post("/pause")
def toggle_pause(request: Request):
    with db.get_conn() as conn:
        paused = not db.get_settings(conn)["global_pause"]
        db.set_setting(conn, "global_pause", paused)
        db.log(conn, "warn" if paused else "info",
               "DỪNG KHẨN CẤP: tạm dừng đăng bài trên tất cả page" if paused else "Bật lại đăng bài")
    return back(request)


@app.post("/jobs/{name}")
def run_job(request: Request, name: str):
    jobs = {"hunt": pipeline.hunt_products, "drafts": pipeline.generate_drafts, "publish": pipeline.publish_due,
            "sync": pipeline.sync_metrics, "pages": pipeline.import_pages}
    if name not in jobs:
        raise HTTPException(404)
    with db.get_conn() as conn:
        jobs[name](conn)
    return back(request, "/settings")
