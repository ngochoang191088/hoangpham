import json
import secrets
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config, db
from urllib.parse import quote

from app.services import ai_writer, costs, pipeline

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


def go(url: str, msg: str = "", error: bool = False) -> RedirectResponse:
    """Chuyển trang, kèm thông báo hiển thị ở đầu trang."""
    if not msg:
        return RedirectResponse(url, status_code=303)
    sep = "&" if "?" in url else "?"
    return RedirectResponse(f"{url}{sep}msg={quote(msg)}{'&err=1' if error else ''}", status_code=303)


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
        daily = _daily(conn, since, today)
        page_stats = """SELECT pages.id, pages.name, pages.niche, pages.status,
                 COUNT(posts.id) AS posts, COALESCE(SUM(posts.orders),0) AS orders,
                 COALESCE(SUM(posts.commission),0) AS commission,
                 COALESCE(SUM(posts.reactions+posts.comments+posts.shares),0) AS engagement
               FROM pages LEFT JOIN posts ON posts.page_id = pages.id
                 AND posts.status='published' AND posts.published_at >= ?"""
        top_pages = conn.execute(page_stats + " GROUP BY pages.id ORDER BY commission DESC LIMIT 10", (since,)).fetchall()
        weak_pages = conn.execute(page_stats + " WHERE pages.status='active' GROUP BY pages.id ORDER BY commission ASC LIMIT 5", (since,)).fetchall()
        niches = _niche_stats(conn, since)
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
        unassigned = q("SELECT COUNT(*) FROM pages WHERE niche = '' AND status != 'archived'")
        if unassigned:
            alerts.append(("warn", f"{unassigned} page chưa được phân ngành hàng (chưa tạo bài)", "/pages/new"))
        for n in niches:
            if n["pages"] < n["target_pages"]:
                alerts.append(("warn", f"Ngành “{n['niche']}” mới có {n['pages']}/{n['target_pages']} page",
                               f"/pages/new?niche={quote(n['niche'])}"))
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


def _daily(conn, since: str, today: str) -> list[dict]:
    """Hoa hồng, đơn, số bài theo từng ngày (kể cả ngày bằng 0)."""
    conv = {r[0]: (r[1], r[2]) for r in conn.execute(
        """SELECT date(purchase_time), SUM(commission), SUM(orders) FROM conversions
           WHERE purchase_time >= ? GROUP BY 1""", (since,))}
    posts = dict(conn.execute(
        """SELECT date(published_at), COUNT(*) FROM posts WHERE status = 'published' AND published_at >= ?
           GROUP BY 1""", (since,)).fetchall())
    day, end, out = date.fromisoformat(since[:10]), date.fromisoformat(today), []
    while day <= end:
        key = day.isoformat()
        commission, orders = conv.get(key, (0, 0))
        out.append({"day": key, "commission": commission, "orders": orders, "posts": posts.get(key, 0)})
        day += timedelta(days=1)
    return out


def _niche_stats(conn, since: str) -> list[dict]:
    """Số liệu theo ngành hàng (gộp bằng vài truy vấn GROUP BY để chạy nhanh với hàng trăm page)."""
    def grouped(sql, *args):
        return {r[0]: r[1:] for r in conn.execute(sql, args)}

    pages = grouped("""SELECT niche, SUM(status != 'archived'), SUM(status = 'active') FROM pages GROUP BY niche""")
    products = grouped("SELECT niche, COUNT(*) FROM products WHERE blocked = 0 GROUP BY niche")
    posts = grouped("""SELECT pages.niche, COUNT(*) FROM posts JOIN pages ON pages.id = posts.page_id
                       WHERE posts.status = 'published' AND posts.published_at >= ? GROUP BY pages.niche""", since)
    conv = grouped("""SELECT pages.niche, SUM(c.orders), SUM(c.commission) FROM conversions c
                      JOIN pages ON pages.id = c.page_id WHERE c.purchase_time >= ? GROUP BY pages.niche""", since)
    rows = []
    for n in conn.execute("SELECT * FROM niches"):
        name = n["name"]
        rows.append({
            "niche": name, "target_pages": n["target_pages"], "keywords": n["keywords"],
            "default_tone": n["default_tone"],
            "pages": pages.get(name, (0, 0))[0], "active": pages.get(name, (0, 0))[1],
            "products": products.get(name, (0,))[0], "posts": posts.get(name, (0,))[0],
            "orders": conv.get(name, (0, 0))[0], "commission": conv.get(name, (0, 0))[1],
        })
    return sorted(rows, key=lambda r: (-r["commission"], r["niche"]))


# ---------------- Ngành hàng ----------------

@app.get("/niches", response_class=HTMLResponse)
def niches_page(request: Request, days: int = 30):
    with db.get_conn() as conn:
        rows = _niche_stats(conn, _days_ago(days))
        pages = conn.execute(
            "SELECT id, name, niche, status FROM pages WHERE status != 'archived' AND niche != '' ORDER BY name"
        ).fetchall()
    by_niche: dict[str, list] = {}
    for pg in pages:
        by_niche.setdefault(pg["niche"], []).append(pg)
    return render(request, "niches.html", rows=rows, by_niche=by_niche, days=days)


def _keywords(text: str) -> str:
    words = [w.strip() for w in text.replace("\n", ",").split(",") if w.strip()]
    return json.dumps(list(dict.fromkeys(words)), ensure_ascii=False)


@app.post("/niches")
def niche_add(name: str = Form(...), keywords: str = Form(""), target_pages: int = Form(5),
              default_tone: str = Form("thân thiện, gần gũi")):
    name = name.strip()
    if not name:
        return go("/niches", "Tên ngành hàng không được để trống", error=True)
    with db.get_conn() as conn:
        if conn.execute("SELECT 1 FROM niches WHERE name = ?", (name,)).fetchone():
            return go("/niches", f"Ngành hàng “{name}” đã có", error=True)
        conn.execute("INSERT INTO niches(name, keywords, target_pages, default_tone, created_at) VALUES (?, ?, ?, ?, ?)",
                     (name, _keywords(keywords), max(0, target_pages), default_tone.strip(), db.now_iso()))
        db.log(conn, "info", f"Tạo ngành hàng “{name}”")
    return go("/niches", f"Đã tạo ngành hàng “{name}”. Bấm “Thêm page” để gán page vào ngành này.")


@app.post("/niches/update")
def niche_update(old_name: str = Form(...), name: str = Form(...), keywords: str = Form(""),
                 target_pages: int = Form(5), default_tone: str = Form("")):
    name = name.strip()
    with db.get_conn() as conn:
        if name != old_name and conn.execute("SELECT 1 FROM niches WHERE name = ?", (name,)).fetchone():
            return go("/niches", f"Ngành hàng “{name}” đã có", error=True)
        conn.execute("UPDATE niches SET name=?, keywords=?, target_pages=?, default_tone=? WHERE name=?",
                     (name, _keywords(keywords), max(0, target_pages), default_tone.strip(), old_name))
        if name != old_name:
            conn.execute("UPDATE pages SET niche = ? WHERE niche = ?", (name, old_name))
            conn.execute("UPDATE products SET niche = ? WHERE niche = ?", (name, old_name))
    return go("/niches", f"Đã lưu ngành hàng “{name}”")


@app.post("/niches/delete")
def niche_delete(name: str = Form(...)):
    with db.get_conn() as conn:
        used = conn.execute("SELECT COUNT(*) FROM pages WHERE niche = ? AND status != 'archived'", (name,)).fetchone()[0]
        if used:
            return go("/niches", f"Không xoá được: ngành “{name}” còn {used} page. Chuyển page sang ngành khác trước.", error=True)
        conn.execute("DELETE FROM niches WHERE name = ?", (name,))
        db.log(conn, "warn", f"Xoá ngành hàng “{name}”")
    return go("/niches", f"Đã xoá ngành hàng “{name}”")


# ---------------- Page ----------------

SORTS = {"commission": "commission DESC", "orders": "orders DESC", "engagement": "engagement DESC",
         "posts": "posts DESC", "name": "pages.name", "last": "last_published DESC"}


@app.get("/pages", response_class=HTMLResponse)
def pages_list(request: Request, niche: str = "", status_: str = "", q: str = "", sort: str = "commission",
               p: int = 1):
    since = _days_ago(30)
    where, args = ["1=1"], [since]
    if niche == "__none__":
        where.append("pages.niche = ''")
    elif niche:
        where.append("pages.niche = ?"); args.append(niche)
    if status_:
        where.append("pages.status = ?"); args.append(status_)
    else:
        where.append("pages.status != 'archived'")
    if q:
        where.append("(pages.name LIKE ? OR pages.id = ?)"); args += [f"%{q}%", q]
    per, p = 50, max(p, 1)
    with db.get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM pages WHERE {' AND '.join(where)}", args[1:]).fetchone()[0]
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
                WHERE {' AND '.join(where)} GROUP BY pages.id ORDER BY {SORTS.get(sort, SORTS['commission'])}
                LIMIT ? OFFSET ?""",
            args + [per, (p - 1) * per],
        ).fetchall()
        niches = db.niche_names(conn)
    return render(request, "pages.html", rows=rows, niches=niches, niche=niche, status_=status_, q=q, sort=sort,
                  total=total, p=p, per=per)


# ---------------- Thêm page ----------------

def _add_page(conn, page_id: str, name: str, niche: str, tone: str = "", posts_per_day: int = 3,
              link_mode: str = "comment", access_token: str = "") -> str | None:
    """Thêm 1 page. Trả về thông báo lỗi, hoặc None nếu thành công."""
    page_id, name, niche = page_id.strip(), name.strip(), niche.strip()
    if not page_id.isdigit():
        return f"ID page “{page_id}” không hợp lệ (ID page chỉ gồm chữ số)"
    if not name:
        return f"Page {page_id} thiếu tên"
    nrow = conn.execute("SELECT * FROM niches WHERE name = ?", (niche,)).fetchone() if niche else None
    if niche and not nrow:
        return f"Ngành hàng “{niche}” chưa có, hãy tạo ở trang Ngành hàng trước"
    old = conn.execute("SELECT status FROM pages WHERE id = ?", (page_id,)).fetchone()
    if old and old["status"] != "archived":
        return f"Page {page_id} đã có trong app"
    conn.execute(
        """INSERT INTO pages(id, name, niche, tone, access_token, posts_per_day, link_mode, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET name=excluded.name, niche=excluded.niche, tone=excluded.tone,
             posts_per_day=excluded.posts_per_day, link_mode=excluded.link_mode, status='active',
             access_token=CASE WHEN excluded.access_token != '' THEN excluded.access_token ELSE access_token END""",
        (page_id, name, niche, tone.strip() or (nrow["default_tone"] if nrow else "thân thiện, gần gũi"),
         access_token.strip(), max(0, min(posts_per_day, 20)), link_mode, db.now_iso()),
    )
    db.log(conn, "info", f"Thêm page vào ngành hàng “{niche or 'chưa phân ngành'}”", page_id)
    return None


@app.get("/pages/new", response_class=HTMLResponse)
def page_new(request: Request, niche: str = ""):
    with db.get_conn() as conn:
        niches = conn.execute(
            """SELECT niches.name, niches.target_pages,
                 (SELECT COUNT(*) FROM pages WHERE pages.niche = niches.name AND pages.status != 'archived') AS pages
               FROM niches ORDER BY niches.name""").fetchall()
        unassigned = conn.execute(
            "SELECT * FROM pages WHERE niche = '' AND status != 'archived' ORDER BY name").fetchall()
    return render(request, "page_new.html", niches=niches, unassigned=unassigned, niche=niche)


@app.post("/pages/add")
def page_add(page_id: str = Form(...), name: str = Form(...), niche: str = Form(""), tone: str = Form(""),
             posts_per_day: int = Form(3), link_mode: str = Form("comment"), access_token: str = Form("")):
    with db.get_conn() as conn:
        err = _add_page(conn, page_id, name, niche, tone, posts_per_day, link_mode, access_token)
    return go("/pages/new", err or f"Đã thêm page “{name.strip()}”", error=bool(err))


@app.post("/pages/bulk")
def page_bulk(lines: str = Form(...), niche: str = Form(""), posts_per_day: int = Form(3)):
    """Mỗi dòng: ID page | Tên page | Ngành hàng (ngành hàng có thể bỏ trống để dùng ngành đã chọn)."""
    added, errors = 0, []
    with db.get_conn() as conn:
        for line in lines.splitlines():
            if not line.strip():
                continue
            parts = [x.strip() for x in line.split("|")]
            if len(parts) < 2:
                errors.append(f"Dòng “{line.strip()[:40]}” thiếu dấu |")
                continue
            err = _add_page(conn, parts[0], parts[1], parts[2] if len(parts) > 2 and parts[2] else niche,
                            posts_per_day=posts_per_day)
            if err:
                errors.append(err)
            else:
                added += 1
    msg = f"Đã thêm {added} page." + (f" {len(errors)} dòng lỗi: " + "; ".join(errors[:5]) if errors else "")
    return go("/pages/new", msg, error=bool(errors))


@app.post("/pages/assign")
async def page_assign(request: Request):
    """Phân ngành hàng cho các page chưa có ngành (form gửi niche_<page_id>=<ngành>)."""
    form = await request.form()
    n = 0
    with db.get_conn() as conn:
        valid = set(db.niche_names(conn))
        for key, value in form.items():
            if key.startswith("niche_") and value in valid:
                n += conn.execute("UPDATE pages SET niche = ? WHERE id = ? AND niche = ''",
                                  (value, key[6:])).rowcount
        if n:
            db.log(conn, "info", f"Phân ngành hàng cho {n} page")
    return go("/pages/new", f"Đã phân ngành hàng cho {n} page")


@app.post("/pages/import-meta")
def page_import_meta():
    with db.get_conn() as conn:
        n = pipeline.import_pages(conn)
    msg = f"Đã đồng bộ {n} page từ Meta" if config.FB_ENABLED else "Chưa có FB_SYSTEM_USER_TOKEN nên chưa nhập được từ Meta"
    return go("/pages/new", msg, error=not config.FB_ENABLED)


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
        niches = db.niche_names(conn)
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
        if page["status"] not in ("active", "paused"):
            return back(request)
        new = "paused" if page["status"] == "active" else "active"
        conn.execute("UPDATE pages SET status = ? WHERE id = ?", (new, page_id))
        db.log(conn, "info", "Bật đăng bài" if new == "active" else "Tạm dừng đăng bài", page_id)
    return back(request)


@app.post("/pages/{page_id}/archive")
def page_archive(page_id: str):
    with db.get_conn() as conn:
        conn.execute("UPDATE pages SET status = 'archived' WHERE id = ?", (page_id,))
        conn.execute("UPDATE posts SET status = 'rejected' WHERE page_id = ? AND status IN ('pending','approved')",
                     (page_id,))
        db.log(conn, "warn", "Gỡ page khỏi app (lịch sử vẫn được giữ)", page_id)
    return go("/pages", "Đã gỡ page khỏi app")


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
        niches = db.niche_names(conn)
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
        niches = db.niche_names(conn)
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
        cur = conn.execute(
            "SELECT COUNT(*), COALESCE(AVG(posts_per_day), 3) FROM pages WHERE status = 'active'").fetchone()
        actual = costs.actual_this_month(conn)
    return render(request, "settings.html", s=s, activity=activity, cost=_cost_table(cur[0], cur[1]),
                  actual=actual, posts_per_day=cur[1])


def _cost_table(active_pages: int, posts_per_day: float) -> list[dict]:
    sizes = sorted({active_pages, 100, 250, 500} - {0})
    return [{"model": m, "label": costs.MODEL_LABELS[m], "current": m == config.AI_MODEL,
             "rows": [costs.estimate(n, posts_per_day, m, batch=True) for n in sizes],
             "per_caption_vnd": costs.cost_per_caption(m, True) * config.USD_VND}
            for m in costs.MODEL_LABELS]


@app.post("/settings")
def settings_save(request: Request, min_commission_rate: float = Form(...), min_rating: float = Form(...),
                  min_sales: int = Form(...), max_pages_per_product_per_day: int = Form(...),
                  repeat_product_after_days: int = Form(...), post_hours: str = Form(...),
                  blacklist: str = Form(""), disclosure: str = Form(...)):
    try:
        hours = sorted({int(h) for h in post_hours.replace(" ", "").split(",") if h})
        assert hours and all(0 <= h <= 23 for h in hours)
    except (ValueError, AssertionError):
        return go("/settings", "Khung giờ không hợp lệ (ví dụ đúng: 8, 11, 14, 20)", error=True)
    with db.get_conn() as conn:
        for key, value in {
            "min_commission_rate": min_commission_rate / 100, "min_rating": min_rating, "min_sales": min_sales,
            "max_pages_per_product_per_day": max_pages_per_product_per_day,
            "repeat_product_after_days": repeat_product_after_days, "post_hours": hours,
            "blacklist": [w.strip() for w in blacklist.splitlines() if w.strip()],
            "disclosure": disclosure.strip(),
        }.items():
            db.set_setting(conn, key, value)
        db.log(conn, "info", "Cập nhật cài đặt chung")
    return go("/settings", "Đã lưu cài đặt")


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
