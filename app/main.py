import json
import secrets
import shutil
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import config, db
from app.services import ai_writer, catalog, costs, facebook, importer, pipeline, quick_add, studio

BASE = Path(__file__).resolve().parent
PUBLIC_PATHS = ("/login", "/auth/", "/logout")


def require_login(request: Request) -> dict | None:
    """Mọi trang đều cần đăng nhập, trừ trang đăng nhập."""
    if request.url.path.startswith(PUBLIC_PATHS):
        return None
    user = request.session.get("user")
    if not user:
        raise HTTPException(303, headers={"Location": "/login"})
    return user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Quản lý page Facebook", lifespan=lifespan, dependencies=[Depends(require_login)])
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, max_age=30 * 24 * 3600,
                   https_only=config.BASE_URL.startswith("https"))
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def vnd(value) -> str:
    return f"{int(round(value or 0)):,}đ".replace(",", ".")


def num(value) -> str:
    return f"{int(value or 0):,}".replace(",", ".")


def media_url(path: str) -> str:
    """Link xem file media (ảnh/video trên máy chủ) trong app."""
    for root in (config.MEDIA_DIR, config.UPLOAD_DIR):
        try:
            rel = Path(path).resolve().relative_to(Path(root).resolve())
            return f"/media/{'m' if root == config.MEDIA_DIR else 'u'}/{rel.as_posix()}"
        except ValueError:
            continue
    return ""


templates.env.filters.update(vnd=vnd, num=num, loads=json.loads, media=media_url)
templates.env.globals.update(config=config)


def render(request: Request, name: str, **ctx) -> HTMLResponse:
    with db.get_conn() as conn:
        ctx.setdefault("pending_count", conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status = 'pending'").fetchone()[0])
        settings = db.get_settings(conn)
        ctx.setdefault("global_pause", settings["global_pause"])
        ctx.setdefault("veo_auto", settings.get("veo_auto", True))
        ctx.setdefault("veo_style", settings.get("veo_style", "studio"))
        ctx.setdefault("veo_ready", bool(config.GEMINI_API_KEY))
        ctx.setdefault("unassigned_count", conn.execute(
            "SELECT COUNT(*) FROM pages WHERE niche = '' AND status != 'archived'").fetchone()[0])
    ctx.setdefault("user", request.session.get("user"))
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


# ---------------- Đăng nhập ----------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "login.html", {"error": error})


@app.post("/login")
def login_demo(request: Request, password: str = Form(...)):
    """Đăng nhập bằng mật khẩu, chỉ dùng cho bản DEMO (chưa cấu hình Facebook App)."""
    if config.FB_LOGIN_ENABLED:
        return go("/login")
    if not secrets.compare_digest(password.encode(), config.ADMIN_PASSWORD.encode()):
        return go("/login?error=" + quote("Sai mật khẩu"))
    request.session["user"] = {"id": "demo", "name": "Tài khoản demo"}
    with db.get_conn() as conn:
        result = pipeline.sync_pages(conn)
    return _after_login(result)


@app.get("/auth/facebook")
def auth_facebook(request: Request):
    if not config.FB_LOGIN_ENABLED:
        return go("/login")
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    return RedirectResponse(facebook.login_url(state), status_code=303)


@app.get("/auth/facebook/callback")
def auth_facebook_callback(request: Request, code: str = "", state: str = "", error_description: str = ""):
    if error_description or not code:
        return go("/login?error=" + quote(error_description or "Đăng nhập Facebook bị huỷ"))
    if not state or state != request.session.pop("oauth_state", None):
        return go("/login?error=" + quote("Phiên đăng nhập không hợp lệ, hãy thử lại"))
    try:
        account = facebook.exchange_code(code)
    except Exception as e:  # noqa: BLE001
        return go("/login?error=" + quote(f"Không đăng nhập được Facebook: {e}"))
    with db.get_conn() as conn:
        s = db.get_settings(conn)
        owner = s.get("owner_fb_id")
        allowed = config.ALLOWED_FB_USERS or ([owner] if owner else [account["id"]])
        if account["id"] not in allowed:
            return go("/login?error=" + quote(f"Tài khoản {account['name']} không có quyền vào app này"))
        db.set_setting(conn, "owner_fb_id", owner or account["id"])
        db.set_setting(conn, "owner_name", account["name"])
        db.set_setting(conn, "owner_token", account["token"])
        expires = (db.now() + timedelta(seconds=int(account["expires_in"]))).isoformat() \
            if account.get("expires_in") else ""
        db.set_setting(conn, "owner_token_expires", expires)
        try:
            result = pipeline.sync_pages(conn, account["token"])
        except Exception as e:  # noqa: BLE001
            db.log(conn, "error", f"Không lấy được danh sách page: {e}")
            result = {"total": 0, "new": 0, "lost": 0}
    request.session["user"] = {"id": account["id"], "name": account["name"]}
    return _after_login(result)


def _after_login(result: dict) -> RedirectResponse:
    msg = f"Đã nhận diện {result['total']} page."
    with db.get_conn() as conn:
        waiting = conn.execute("SELECT COUNT(*) FROM pages WHERE niche = '' AND status != 'archived'").fetchone()[0]
    if waiting:
        return go("/pages?niche=__none__", msg + f" Có {waiting} page chưa có ngành hàng, hãy chọn ngành cho chúng.")
    return go("/", msg)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return go("/login")


@app.post("/pages/sync")
def pages_sync():
    with db.get_conn() as conn:
        try:
            r = pipeline.sync_pages(conn)
        except Exception as e:  # noqa: BLE001
            return go("/pages", f"Không lấy được danh sách page: {e}. Hãy đăng nhập Facebook lại.", error=True)
    msg = f"Đã nhận diện {r['total']} page: {r['new']} page mới, {r['lost']} page mất quyền quản lý."
    return go("/pages?niche=__none__" if r["new"] else "/pages", msg)


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
            """SELECT id, name FROM pages WHERE status='active' AND niche != '' AND id NOT IN
               (SELECT page_id FROM posts WHERE status='published' AND published_at >= ?)""",
            (_days_ago(2),),
        ).fetchall()
        for p in silent[:5]:
            alerts.append(("warn", f"Page “{p['name']}” không có bài nào trong 2 ngày", f"/pages/{p['id']}"))
        unassigned = q("SELECT COUNT(*) FROM pages WHERE niche = '' AND status != 'archived'")
        if unassigned:
            alerts.append(("warn", f"{unassigned} page chưa được chọn ngành hàng (chưa tạo bài)", "/pages?niche=__none__"))
        for n in niches:
            if n["pages"] < n["target_pages"]:
                alerts.append(("warn", f"Ngành “{n['niche']}” mới có {n['pages']}/{n['target_pages']} page",
                               "/pages?niche=__none__"))
            if n["pages"] and not n["products"]:
                alerts.append(("error", f"Ngành “{n['niche']}” chưa có sản phẩm nào, hãy nhập file sản phẩm",
                               f"/products?niche={quote(n['niche'])}"))
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
    products = grouped("""SELECT niche, COUNT(*), SUM(item_id IN (SELECT item_id FROM videos)) FROM products
                          WHERE blocked = 0 GROUP BY niche""")
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
            "products": products.get(name, (0, 0))[0], "with_video": products.get(name, (0, 0))[1] or 0,
            "posts": posts.get(name, (0,))[0],
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
    per, p = 100, max(p, 1)
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


@app.post("/pages/assign")
def pages_assign(request: Request, niche: str = Form(""), action: str = Form("assign"),
                 ids: list[str] = Form(default=[])):
    """Áp ngành hàng (hoặc tạm dừng / bật) cho các page đã chọn."""
    if not ids:
        return back(request)
    marks = ",".join("?" * len(ids))
    with db.get_conn() as conn:
        if action == "assign":
            if niche and niche not in db.niche_names(conn):
                return go("/pages", "Ngành hàng không tồn tại", error=True)
            tone = conn.execute("SELECT default_tone FROM niches WHERE name = ?", (niche,)).fetchone()
            n = conn.execute(f"UPDATE pages SET niche = ? WHERE id IN ({marks})", [niche, *ids]).rowcount
            if tone:
                conn.execute(f"UPDATE pages SET tone = ? WHERE id IN ({marks}) AND tone = 'thân thiện, gần gũi'",
                             [tone[0], *ids])
            msg = f"Đã áp ngành hàng “{niche}” cho {n} page" if niche else f"Đã bỏ ngành hàng của {n} page"
        elif action in ("pause", "resume"):
            old, new = ("active", "paused") if action == "pause" else ("paused", "active")
            n = conn.execute(f"UPDATE pages SET status = ? WHERE status = ? AND id IN ({marks})",
                             [new, old, *ids]).rowcount
            msg = f"Đã {'tạm dừng' if action == 'pause' else 'bật lại'} {n} page"
        else:
            return back(request)
        db.log(conn, "info", msg)
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/pages", msg), status_code=303)


def _with_msg(url: str, msg: str) -> str:
    base = url.split("&msg=")[0].split("?msg=")[0]
    return f"{base}{'&' if '?' in base else '?'}msg={quote(msg)}"


@app.post("/pages/{page_id}/niche")
def page_set_niche(request: Request, page_id: str, niche: str = Form("")):
    return pages_assign(request, niche=niche, action="assign", ids=[page_id])


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
        order = "posts.scheduled_at ASC" if status_ in ("pending", "approved") \
        else "COALESCE(posts.published_at, posts.scheduled_at) DESC"
        posts = conn.execute(
            f"""SELECT posts.*, products.name AS product_name, kits.images AS kit_images, kits.video_path AS kit_video, CASE WHEN kits.ai_video_status = 'ready' THEN kits.ai_video_path END AS kit_ai_video, products.commission_rate
                FROM posts LEFT JOIN products ON products.item_id = posts.item_id
                LEFT JOIN media_kits kits ON kits.id = posts.kit_id
                WHERE posts.page_id = ? AND posts.status = ? ORDER BY {order} LIMIT 30""",
            (page_id, status_),
        ).fetchall()
        niches = db.niche_names(conn)
        activity = conn.execute(
            "SELECT * FROM activity WHERE page_id = ? ORDER BY id DESC LIMIT 10", (page_id,)).fetchall()
        kits = _kits_for(conn, posts)
    chart = {"labels": [r["day"][5:] for r in daily], "commission": [round(r["commission"] or 0) for r in daily],
             "posts": [r["posts"] for r in daily]}
    return render(request, "page_detail.html", kits_by_item=kits, media_types=MEDIA_TYPES,
                  rewrite_presets=REWRITE_LABELS, page=page, stats=stats, chart=chart, posts=posts,
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
            f"""SELECT posts.*, pages.name AS page_name, pages.niche, products.name AS product_name, kits.images AS kit_images, kits.video_path AS kit_video, CASE WHEN kits.ai_video_status = 'ready' THEN kits.ai_video_path END AS kit_ai_video
                FROM posts JOIN pages ON pages.id = posts.page_id
                LEFT JOIN products ON products.item_id = posts.item_id
                LEFT JOIN media_kits kits ON kits.id = posts.kit_id
                WHERE {' AND '.join(where)}
                ORDER BY COALESCE(posts.published_at, posts.scheduled_at) DESC LIMIT ? OFFSET ?""",
            args + [per, (max(p, 1) - 1) * per],
        ).fetchall()
        pages = conn.execute("SELECT id, name FROM pages ORDER BY name").fetchall()
        niches = db.niche_names(conn)
        kits = _kits_for(conn, rows)
    return render(request, "posts.html", kits_by_item=kits, media_types=MEDIA_TYPES, rewrite_presets=REWRITE_LABELS, rows=rows, total=total, pages=pages, niches=niches, status=status,
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
            f"""SELECT posts.*, pages.name AS page_name, pages.niche, products.name AS product_name, kits.images AS kit_images, kits.video_path AS kit_video, CASE WHEN kits.ai_video_status = 'ready' THEN kits.ai_video_path END AS kit_ai_video,
                  products.price, products.commission_rate, products.rating, products.sales
                FROM posts JOIN pages ON pages.id = posts.page_id
                LEFT JOIN products ON products.item_id = posts.item_id
                LEFT JOIN media_kits kits ON kits.id = posts.kit_id
                WHERE {' AND '.join(where)} ORDER BY posts.flags != '[]' DESC, posts.scheduled_at LIMIT 200""",
            args,
        ).fetchall()
        clean = conn.execute("SELECT COUNT(*) FROM posts WHERE status='pending' AND flags='[]'").fetchone()[0]
        kits = _kits_for(conn, rows)
    return render(request, "review.html", rows=rows, clean=clean, flagged=flagged, kits_by_item=kits,
                  editor_open=True, media_types=MEDIA_TYPES, rewrite_presets=REWRITE_LABELS)


def _kits_for(conn, rows) -> dict[str, list]:
    """Các bộ media đã xong của những sản phẩm trong danh sách bài (để chọn trong trình sửa bài)."""
    items = sorted({r["item_id"] for r in rows if r["item_id"] and r["status"] in ("pending", "approved")})
    if not items:
        return {}
    marks = ",".join("?" * len(items))
    out: dict[str, list] = {}
    for k in conn.execute(f"""SELECT id, item_id, variant, images, video_path, ai_video_status, ai_video_path
                              FROM media_kits WHERE status = 'ready' AND item_id IN ({marks})
                              ORDER BY variant""", items):
        out.setdefault(k["item_id"], []).append({**dict(k), "images": json.loads(k["images"])})
    return out


MEDIA_TYPES = {"album": "Album ảnh", "kit_video": "Video trình chiếu", "ai_video": "Video AI (Veo)",
               "video": "Video riêng của bạn", "photo": "1 ảnh sản phẩm"}
REWRITE_LABELS = {"shorter": "Ngắn gọn hơn", "fun": "Vui, trẻ trung hơn", "price": "Nhấn mạnh giá",
                  "hook": "Câu mở đầu cuốn hút hơn", "new": "Viết bài mới hoàn toàn"}


@app.post("/posts/{post_id}/edit")
async def post_edit(request: Request, post_id: int):
    """Sửa bài trước khi đăng: nội dung, cách đăng (album / video / ảnh), phiên bản, ảnh trong album,
    giờ đăng, link aff. Nút "Lưu & duyệt" thì duyệt luôn."""
    form = await request.form()
    with db.get_conn() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ? AND status IN ('pending', 'approved')",
                            (post_id,)).fetchone()
        if not post:
            return back(request)
        caption = str(form.get("caption", post["caption"])).strip()
        s = db.get_settings(conn)
        flags = ai_writer.check_content(caption, s, [])
        media_type, kit_id, custom = post["media_type"], post["kit_id"], post["custom_images"]
        if form.get("media_type") in MEDIA_TYPES:
            media_type = str(form["media_type"])
        if form.get("kit_id"):
            kit = conn.execute("SELECT * FROM media_kits WHERE id = ? AND item_id = ? AND status = 'ready'",
                               (int(form["kit_id"]), post["item_id"])).fetchone()
            if kit:
                kit_id = kit["id"]
                allowed = json.loads(kit["images"])
                picked = [p for p in form.getlist(f"img_{kit_id}") if p in allowed]
                custom = json.dumps(picked) if picked and len(picked) < len(allowed) else None
                if media_type == "ai_video" and kit["ai_video_status"] != "ready":
                    media_type = "kit_video"
        if media_type in ("album", "kit_video", "ai_video") and not kit_id:
            media_type = "photo"
        if media_type == "video" and not post["video_id"]:
            media_type = "photo"
        scheduled = post["scheduled_at"]
        if form.get("scheduled_at"):
            try:
                from datetime import datetime
                scheduled = datetime.fromisoformat(str(form["scheduled_at"])).replace(tzinfo=config.TZ).isoformat()
            except ValueError:
                pass
        aff = str(form.get("aff_link", post["aff_link"])).strip()
        status = "approved" if form.get("approve") else post["status"]
        conn.execute(
            """UPDATE posts SET caption=?, flags=?, media_type=?, kit_id=?, custom_images=?, scheduled_at=?,
                   aff_link=?, status=?, updated_at=? WHERE id=?""",
            (caption, json.dumps(flags, ensure_ascii=False), media_type, kit_id, custom, scheduled, aff, status,
             db.now_iso(), post_id))
    msg = "Đã lưu và duyệt bài" if form.get("approve") else "Đã lưu bài"
    if flags:
        msg += " (còn cảnh báo: " + "; ".join(flags) + ")"
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/review", msg) + f"#post-{post_id}", 303)


@app.post("/posts/{post_id}/rewrite")
def post_rewrite(request: Request, post_id: int, preset: str = Form("new"), instruction: str = Form("")):
    """AI sửa lại nội dung bài theo yêu cầu (ngắn hơn, vui hơn, nhấn giá...)."""
    with db.get_conn() as conn:
        post = conn.execute("""SELECT posts.*, pages.name AS page_name, pages.niche, pages.tone FROM posts
                               JOIN pages ON pages.id = posts.page_id
                               WHERE posts.id = ? AND posts.status IN ('pending', 'approved')""", (post_id,)).fetchone()
        if not post:
            return back(request)
        product = conn.execute("SELECT * FROM products WHERE item_id = ?", (post["item_id"],)).fetchone()
        page = {"name": post["page_name"], "niche": post["niche"], "tone": post["tone"]}
        s = db.get_settings(conn)
        wish = "; ".join(x for x in (ai_writer.REWRITE_PRESETS.get(preset, ""), instruction.strip()) if x)
        caption, error = ai_writer.rewrite_caption(page, dict(product) if product else {"name": ""}, post["caption"],
                                                   wish or ai_writer.REWRITE_PRESETS["new"], s["disclosure"],
                                                   pipeline.usage_recorder(conn))
        if error:
            return RedirectResponse(_with_msg(request.headers.get("referer") or "/review", error) + "&err=1", 303)
        flags = ai_writer.check_content(caption, s, [])
        conn.execute("UPDATE posts SET caption=?, flags=?, updated_at=? WHERE id=?",
                     (caption, json.dumps(flags, ensure_ascii=False), db.now_iso(), post_id))
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/review", "AI đã viết lại bài")
                            + f"#post-{post_id}", 303)


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
def products(request: Request, niche: str = "", q: str = "", only: str = "", p: int = 1):
    where, args = ["1=1"], []
    if niche:
        where.append("niche = ?"); args.append(niche)
    if q:
        where.append("(name LIKE ? OR aff_link LIKE ? OR product_link LIKE ?)"); args += [f"%{q}%"] * 3
    if only == "video":
        where.append("item_id IN (SELECT item_id FROM videos)")
    elif only == "novideo":
        where.append("item_id NOT IN (SELECT item_id FROM videos)")
    elif only == "incomplete":
        where.append("(name = '' OR aff_link = '' OR (image_url = '' AND item_id NOT IN (SELECT item_id FROM videos)))")
    per, p = 50, max(p, 1)
    with db.get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM products WHERE {' AND '.join(where)}", args).fetchone()[0]
        rows = conn.execute(
            f"""SELECT products.*,
                  (SELECT COUNT(*) FROM posts WHERE posts.item_id = products.item_id AND status='published') AS used,
                  (SELECT COALESCE(SUM(commission),0) FROM posts WHERE posts.item_id = products.item_id) AS earned,
                  (SELECT COALESCE(NULLIF(file_path, ''), url) FROM product_images i
                     WHERE i.item_id = products.item_id ORDER BY position, id LIMIT 1) AS src_first,
                  (SELECT status FROM media_kits k WHERE k.item_id = products.item_id AND k.variant = 0) AS kit_status
                FROM products WHERE {' AND '.join(where)}
                ORDER BY blocked, fetched_at DESC, score DESC LIMIT ? OFFSET ?""",
            args + [per, (p - 1) * per],
        ).fetchall()
        videos: dict[str, list] = {}
        if rows:
            marks = ",".join("?" * len(rows))
            for v in conn.execute(f"SELECT * FROM videos WHERE item_id IN ({marks}) ORDER BY id",
                                  [r["item_id"] for r in rows]):
                videos.setdefault(v["item_id"], []).append(v)
        counts = {r[0]: (r[1], r[2]) for r in conn.execute(
            """SELECT niche, COUNT(*), SUM(item_id IN (SELECT item_id FROM videos)) FROM products
               WHERE blocked = 0 GROUP BY niche""")}
        niches = db.niche_names(conn)
        jobs = _recent_jobs(conn)
    return render(request, "products.html", jobs=jobs, rows=rows, videos=videos, niches=niches, niche=niche, q=q,
                  only=only, total=total, p=p, per=per, counts=counts)


@app.get("/products/template.xlsx")
def product_template(niche: str = ""):
    data = importer.template_xlsx(niche)
    filename = quote(f"mau-san-pham-{niche or 'nganh-hang'}.xlsx")
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@app.post("/products/import")
async def product_import(niche: str = Form(""), file: UploadFile = File(...)):
    """Nhập sản phẩm + link aff + video từ file Excel / CSV / Word / text của 1 ngành hàng."""
    data = await file.read()
    try:
        rows = importer.read_file(file.filename or "", data)
    except Exception as e:  # noqa: BLE001
        return go(f"/products?niche={quote(niche)}", f"Không đọc được file: {e}", error=True)
    if not rows:
        return go(f"/products?niche={quote(niche)}", "File không có dòng sản phẩm nào", error=True)
    with db.get_conn() as conn:
        r = catalog.save_rows(conn, rows, niche, source="file")
        db.log(conn, "info", f"Nhập file “{file.filename}” vào ngành “{niche}”: {r['added']} mới, "
                             f"{r['updated']} cập nhật, {r['videos']} video")
    return _catalog_result(niche, r)


def _catalog_result(niche: str, r: dict) -> RedirectResponse:
    msg = f"Đã thêm {r['added']} sản phẩm, cập nhật {r['updated']}, gắn {r['videos']} video."
    if r["errors"]:
        msg += f" {len(r['errors'])} lưu ý: " + "; ".join(r["errors"][:6])
    return go(f"/products?niche={quote(niche)}", msg, error=bool(r["errors"]) and not (r["added"] or r["updated"]))


@app.post("/products/add")
async def product_add(niche: str = Form(...), product_link: str = Form(...), aff_link: str = Form(""),
                      name: str = Form(""), price: str = Form(""), description: str = Form(""),
                      image_url: str = Form(""), video_url: str = Form(""),
                      video_file: UploadFile | None = File(None)):
    row = {k: v.strip() for k, v in dict(aff_link=aff_link, product_link=product_link, name=name, price=price,
                                          description=description, image_url=image_url,
                                          video_url=video_url).items() if v and v.strip()}
    with db.get_conn() as conn:
        r = catalog.save_rows(conn, [row], niche, source="manual")
        if video_file is not None and video_file.filename and (r["added"] or r["updated"]):
            try:
                path = _store_upload(video_file)
                catalog.add_video(conn, importer.make_item_id(row), file_path=path, title=video_file.filename)
                r["videos"] += 1
            except ValueError as e:
                r["errors"].append(str(e))
    return _catalog_result(niche, r)


def _store_upload(upload: UploadFile) -> str:
    """Lưu video tải lên xuống đĩa theo từng khối (không đọc cả file vào RAM)."""
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in catalog.VIDEO_EXTS:
        raise ValueError("Chỉ nhận video .mp4, .mov, .m4v, .webm")
    path = Path(catalog.save_upload(upload.filename, b""))
    with path.open("wb") as fh:
        shutil.copyfileobj(upload.file, fh, length=1024 * 1024)
    return str(path)


@app.post("/products/{item_id}/edit")
def product_edit(request: Request, item_id: str, name: str = Form(""), niche: str = Form(...),
                 aff_link: str = Form(""), product_link: str = Form(""), price: str = Form(""),
                 description: str = Form(""), image_url: str = Form("")):
    with db.get_conn() as conn:
        if niche not in db.niche_names(conn):
            return back(request)
        conn.execute(
            """UPDATE products SET name=?, niche=?, aff_link=?, product_link=?, price=?, description=?, image_url=?
               WHERE item_id=?""",
            (name.strip(), niche, aff_link.strip(), product_link.strip(), importer.parse_price(price),
             description.strip(), image_url.strip(), item_id),
        )
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/products", "Đã lưu sản phẩm"), 303)


@app.post("/products/{item_id}/videos")
async def product_video_add(request: Request, item_id: str, video_url: str = Form(""),
                            video_file: UploadFile | None = File(None)):
    with db.get_conn() as conn:
        if not conn.execute("SELECT 1 FROM products WHERE item_id = ?", (item_id,)).fetchone():
            raise HTTPException(404)
        try:
            if video_file is not None and video_file.filename:
                catalog.add_video(conn, item_id, file_path=_store_upload(video_file), title=video_file.filename)
            elif facebook.direct_video_url(video_url):
                catalog.add_video(conn, item_id, url=video_url.strip())
            else:
                raise ValueError("Link video phải là file .mp4 hoặc Google Drive")
        except ValueError as e:
            return RedirectResponse(_with_msg(request.headers.get("referer") or "/products", str(e)) + "&err=1", 303)
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/products", "Đã thêm video"), 303)


@app.post("/videos/{video_id}/delete")
def video_delete(request: Request, video_id: int):
    with db.get_conn() as conn:
        v = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        if v:
            conn.execute("UPDATE posts SET media_type='photo', video_id=NULL WHERE video_id=? AND status IN "
                         "('pending','approved')", (video_id,))
            conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
            if v["file_path"] and not conn.execute("SELECT 1 FROM posts WHERE video_id = ?", (video_id,)).fetchone():
                Path(v["file_path"]).unlink(missing_ok=True)
    return back(request, "/products")


@app.post("/products/{item_id}/toggle")
def product_toggle(request: Request, item_id: str):
    with db.get_conn() as conn:
        conn.execute("UPDATE products SET blocked = 1 - blocked WHERE item_id = ?", (item_id,))
    return back(request)


@app.post("/products/{item_id}/delete")
def product_delete(request: Request, item_id: str):
    with db.get_conn() as conn:
        used = conn.execute("SELECT COUNT(*) FROM posts WHERE item_id = ?", (item_id,)).fetchone()[0]
        if used:
            conn.execute("UPDATE products SET blocked = 1 WHERE item_id = ?", (item_id,))
            msg = "Sản phẩm đã có bài đăng nên được chuyển sang “Chặn” thay vì xoá"
        else:
            for v in conn.execute("SELECT file_path FROM videos WHERE item_id = ?", (item_id,)):
                if v[0]:
                    Path(v[0]).unlink(missing_ok=True)
            conn.execute("DELETE FROM videos WHERE item_id = ?", (item_id,))
            conn.execute("DELETE FROM products WHERE item_id = ?", (item_id,))
            msg = "Đã xoá sản phẩm"
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/products", msg), 303)


# ---------------- Dán link Shopee: tự nhận diện sản phẩm ----------------

def _recent_jobs(conn) -> list:
    return conn.execute(
        """SELECT link_jobs.*, products.name AS product_name FROM link_jobs
           LEFT JOIN products ON products.item_id = link_jobs.item_id
           ORDER BY link_jobs.id DESC LIMIT 15""").fetchall()


@app.post("/links")
def links_add(request: Request, background: BackgroundTasks, links: str = Form(...), niche: str = Form(""),
              auto_media: str = Form(""), ai_video: str = Form("")):
    with db.get_conn() as conn:
        if niche and niche not in db.niche_names(conn):
            niche = ""
        ids = quick_add.create_jobs(conn, links, niche, bool(auto_media), bool(ai_video))
    for job_id in ids:
        background.add_task(quick_add.run_job, job_id)
    url = request.headers.get("referer") or "/products"
    if not ids:
        return RedirectResponse(_with_msg(url, "Không thấy link Shopee nào") + "&err=1", 303)
    msg = f"Đã nhận {len(ids)} link. App đang đọc sản phẩm, xếp ngành và tạo ảnh + video (xem tiến độ bên dưới)."
    return RedirectResponse(_with_msg(url, msg), 303)


@app.post("/links/{job_id}/niche")
def links_set_niche(request: Request, job_id: int, background: BackgroundTasks, niche: str = Form(...)):
    with db.get_conn() as conn:
        ok = quick_add.set_niche_and_resume(conn, job_id, niche)
    if ok:
        background.add_task(quick_add.run_job, job_id)
    return back(request, "/products")


@app.post("/links/{job_id}/retry")
def links_retry(request: Request, job_id: int, background: BackgroundTasks):
    with db.get_conn() as conn:
        conn.execute("UPDATE link_jobs SET status = 'queued', error = NULL, detected = '{}' WHERE id = ?", (job_id,))
    background.add_task(quick_add.run_job, job_id)
    return back(request, "/products")


# ---------------- Studio: ảnh + video cho sản phẩm ----------------

@app.get("/media/{kind}/{path:path}")
def media_file(kind: str, path: str):
    root = Path(config.MEDIA_DIR if kind == "m" else config.UPLOAD_DIR).resolve()
    target = (root / path).resolve()
    if kind not in ("m", "u") or root not in target.parents or not target.is_file():
        raise HTTPException(404)
    return FileResponse(target)


def _bg_build(item_id: str, new_brief: bool = False, brief: dict | None = None) -> None:
    with db.get_conn() as conn:
        studio.build_all_variants(conn, item_id, new_brief=new_brief, brief=brief,
                                  record_usage=pipeline.usage_recorder(conn))


def _mark_processing(conn, item_ids: list[str]) -> None:
    now = db.now_iso()
    for item_id in item_ids:
        conn.execute("""INSERT INTO media_kits(item_id, variant, status, created_at, updated_at)
                        VALUES (?, 0, 'processing', ?, ?)
                        ON CONFLICT(item_id, variant) DO UPDATE SET status = 'processing', error = NULL""",
                     (item_id, now, now))


@app.get("/studio", response_class=HTMLResponse)
def studio_list(request: Request, niche: str = "", status: str = "", q: str = "", p: int = 1):
    where, args = ["products.blocked = 0"], []
    if niche:
        where.append("products.niche = ?"); args.append(niche)
    if q:
        where.append("products.name LIKE ?"); args.append(f"%{q}%")
    kit_status = "(SELECT status FROM media_kits k WHERE k.item_id = products.item_id AND k.variant = 0)"
    if status == "none":
        where.append(f"{kit_status} IS NULL")
    elif status:
        where.append(f"{kit_status} = ?"); args.append(status)
    per, p = 40, max(p, 1)
    with db.get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM products WHERE {' AND '.join(where)}", args).fetchone()[0]
        rows = conn.execute(
            f"""SELECT products.*, {kit_status} AS kit_status,
                  (SELECT images FROM media_kits k WHERE k.item_id = products.item_id AND k.variant = 0) AS kit_images,
                  (SELECT COUNT(*) FROM media_kits k WHERE k.item_id = products.item_id AND k.status = 'ready') AS n_ready,
                  (SELECT COUNT(*) FROM product_images i WHERE i.item_id = products.item_id) AS n_src,
                  (SELECT COALESCE(NULLIF(file_path, ''), url) FROM product_images i
                     WHERE i.item_id = products.item_id ORDER BY position, id LIMIT 1) AS src_first
                FROM products WHERE {' AND '.join(where)}
                ORDER BY (kit_status = 'processing') DESC, kit_status IS NULL DESC, fetched_at DESC
                LIMIT ? OFFSET ?""",
            args + [per, (p - 1) * per],
        ).fetchall()
        stats = dict(conn.execute(
            """SELECT COALESCE(k.status, 'none'), COUNT(*) FROM products
               LEFT JOIN media_kits k ON k.item_id = products.item_id AND k.variant = 0
               WHERE products.blocked = 0 GROUP BY 1""").fetchall())
        niches = db.niche_names(conn)
        jobs = _recent_jobs(conn)
    return render(request, "studio_list.html", jobs=jobs, rows=rows, niches=niches, niche=niche, status=status, q=q,
                  total=total, p=p, per=per, stats=stats)


@app.post("/studio/build")
def studio_build_many(request: Request, background: BackgroundTasks, ids: list[str] = Form(default=[]),
                      niche: str = Form(""), missing: str = Form("")):
    with db.get_conn() as conn:
        if missing:
            where, args = ["blocked = 0",
                           "item_id NOT IN (SELECT item_id FROM media_kits WHERE status IN ('ready', 'processing'))"], []
            if niche:
                where.append("niche = ?"); args.append(niche)
            ids = [r[0] for r in conn.execute(f"SELECT item_id FROM products WHERE {' AND '.join(where)} LIMIT 200",
                                              args)]
        _mark_processing(conn, ids)
    for item_id in ids:
        background.add_task(_bg_build, item_id)
    msg = f"Đang tạo bộ ảnh + video cho {len(ids)} sản phẩm (mỗi sản phẩm ~10-20 giây). Tải lại trang để xem."
    return RedirectResponse(_with_msg(request.headers.get("referer") or "/studio", msg), 303)


@app.get("/studio/{item_id}", response_class=HTMLResponse)
def studio_detail(request: Request, item_id: str):
    with db.get_conn() as conn:
        product = conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone()
        if not product:
            raise HTTPException(404)
        images = conn.execute("SELECT * FROM product_images WHERE item_id = ? ORDER BY position, id",
                              (item_id,)).fetchall()
        kits = conn.execute("SELECT * FROM media_kits WHERE item_id = ? ORDER BY variant", (item_id,)).fetchall()
        brief = studio.get_brief(conn, item_id)
        videos = conn.execute("SELECT * FROM videos WHERE item_id = ?", (item_id,)).fetchall()
        used = conn.execute("""SELECT posts.media_type, COUNT(*) FROM posts WHERE item_id = ? AND status = 'published'
                               GROUP BY 1""", (item_id,)).fetchall()
    from app.services import veo

    return render(request, "studio.html", product=product, images=images, kits=kits, brief=brief,
                  videos=videos, used=dict(used), themes=studio.designer.THEMES, veo_styles=veo.VEO_STYLES,
                  veo_enabled=veo.enabled(), veo_cost_vnd=veo.cost_per_video(config.VEO_MODEL) * config.USD_VND)


@app.post("/studio/{item_id}/build")
def studio_build(request: Request, item_id: str, background: BackgroundTasks, new_brief: str = Form("")):
    with db.get_conn() as conn:
        _mark_processing(conn, [item_id])
    background.add_task(_bg_build, item_id, bool(new_brief))
    return go(f"/studio/{quote(item_id)}", "Đang tạo bộ ảnh + video, tải lại trang sau vài giây")


def _bg_ai_video(item_id: str, variant: int, style: str) -> None:
    with db.get_conn() as conn:
        studio.build_ai_video(conn, item_id, variant, style or None)


@app.post("/studio/{item_id}/ai-video")
def studio_ai_video(item_id: str, background: BackgroundTasks, variant: int = Form(0), style: str = Form("")):
    """Tạo video AI bằng Veo 3.1 cho 1 phiên bản (tốn phí theo giây video)."""
    with db.get_conn() as conn:
        kit = conn.execute("SELECT id, status FROM media_kits WHERE item_id = ? AND variant = ?",
                           (item_id, variant)).fetchone()
        if not kit or kit["status"] != "ready":
            return go(f"/studio/{quote(item_id)}", "Hãy tạo bộ ảnh trước khi làm video AI", error=True)
        conn.execute("UPDATE media_kits SET ai_video_status = 'processing', ai_video_error = NULL WHERE id = ?",
                     (kit["id"],))
    background.add_task(_bg_ai_video, item_id, variant, style)
    return go(f"/studio/{quote(item_id)}", "Đang tạo video AI bằng Veo 3.1 (thường 1-3 phút), trang tự tải lại")


@app.post("/studio/{item_id}/brief")
def studio_brief(item_id: str, background: BackgroundTasks, headline: str = Form(""), subheadline: str = Form(""),
                 points: str = Form(""), cta: str = Form(""), badge: str = Form(""), video_lines: str = Form(""),
                 image_order: str = Form("")):
    """Sửa chữ trên ảnh/video rồi dựng lại (không gọi AI)."""
    order = [int(x) for x in image_order.replace(" ", "").split(",") if x.strip().isdigit()]
    brief = {"headline": headline, "subheadline": subheadline, "cta": cta, "badge": badge,
             "points": [x for x in points.splitlines() if x.strip()],
             "video_lines": [x for x in video_lines.splitlines() if x.strip()], "image_order": order}
    with db.get_conn() as conn:
        _mark_processing(conn, [item_id])
    background.add_task(_bg_build, item_id, False, brief)
    return go(f"/studio/{quote(item_id)}", "Đã lưu nội dung, đang dựng lại ảnh + video")


@app.post("/studio/{item_id}/images")
async def studio_add_images(item_id: str, urls: str = Form(""), files: list[UploadFile] = File(default=[]),
                            fetch: str = Form("")):
    added = 0
    with db.get_conn() as conn:
        if not conn.execute("SELECT 1 FROM products WHERE item_id = ?", (item_id,)).fetchone():
            raise HTTPException(404)
        if fetch:
            link = conn.execute("SELECT product_link FROM products WHERE item_id = ?", (item_id,)).fetchone()[0]
            got = studio.shopee.fetch_images(link)
            for url in got:
                added += catalog.add_image(conn, item_id, url=url, source="shopee")
            if not got:
                return go(f"/studio/{quote(item_id)}", "Shopee chặn lấy ảnh tự động. Hãy dán link ảnh hoặc tải ảnh lên.",
                          error=True)
        for url in importer.URL_LIST_RE.findall(urls):
            added += catalog.add_image(conn, item_id, url=url, source="file")
        for f in files:
            if not f.filename:
                continue
            if Path(f.filename).suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            folder = studio._dir("src", studio._safe(item_id))
            dest = folder / f"up_{db.now().strftime('%H%M%S%f')}{Path(f.filename).suffix.lower()}"
            with dest.open("wb") as fh:
                shutil.copyfileobj(f.file, fh)
            added += catalog.add_image(conn, item_id, file_path=str(dest), source="upload")
        studio.source_images(conn, item_id, fetch=False)          # tải ảnh về máy chủ
    return go(f"/studio/{quote(item_id)}", f"Đã thêm {added} ảnh. Bấm “Tạo lại” để dựng bộ media mới.")


@app.post("/studio/images/{image_id}/{action}")
def studio_image_action(request: Request, image_id: int, action: str):
    with db.get_conn() as conn:
        img = conn.execute("SELECT * FROM product_images WHERE id = ?", (image_id,)).fetchone()
        if not img:
            raise HTTPException(404)
        if action == "delete":
            conn.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        elif action in ("first", "up"):
            rows = [r[0] for r in conn.execute(
                "SELECT id FROM product_images WHERE item_id = ? ORDER BY position, id", (img["item_id"],))]
            i = rows.index(image_id)
            rows.pop(i)
            rows.insert(0 if action == "first" else max(0, i - 1), image_id)
            for pos, rid in enumerate(rows):
                conn.execute("UPDATE product_images SET position = ? WHERE id = ?", (pos, rid))
    return back(request, "/studio")


@app.post("/studio/{item_id}/caption")
def studio_caption(item_id: str):
    """AI viết thử 1 bài đăng cho sản phẩm (không lưu thành bài)."""
    with db.get_conn() as conn:
        product = conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone()
        page = conn.execute("SELECT * FROM pages WHERE niche = ? AND status = 'active' ORDER BY RANDOM() LIMIT 1",
                            (product["niche"],)).fetchone()
        page = dict(page) if page else {"name": "Page mẫu", "niche": product["niche"], "tone": "thân thiện, gần gũi"}
        s = db.get_settings(conn)
        (caption, error), = ai_writer.write_captions([{"page": page, "product": dict(product)}], s["disclosure"],
                                                     pipeline.usage_recorder(conn))
        if error:
            return go(f"/studio/{quote(item_id)}", error, error=True)
        conn.execute("UPDATE products SET sample_caption = ? WHERE item_id = ?",
                     (f"[Viết cho page: {page['name']}]\n\n{caption}", item_id))
    return go(f"/studio/{quote(item_id)}#bai-viet", "AI đã viết thử bài đăng")


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
    from app.services import veo

    with db.get_conn() as c2:
        row = c2.execute("""SELECT COALESCE(SUM(seconds), 0), model FROM video_usage WHERE simulated = 0
                            AND substr(ts, 1, 7) = ? GROUP BY model""", (db.now().strftime("%Y-%m"),)).fetchall()
        veo_month_usd = sum(r[0] * veo.price_per_second(r[1]) for r in row)
    return render(request, "settings.html", s=s, activity=activity, veo_styles=veo.VEO_STYLES, veo_enabled=veo.enabled(),
                  veo_models=veo.MODELS, veo_video_vnd=veo.cost_per_video(config.VEO_MODEL) * config.USD_VND,
                  veo_month_vnd=veo_month_usd * config.USD_VND, cost=_cost_table(cur[0], cur[1], s.get("ai_tier", "save")),
                  actual=actual, posts_per_day=cur[1])


def _cost_table(active_pages: int, posts_per_day: float, current_tier: str) -> list[dict]:
    from app.services import ai_models

    sizes = sorted({active_pages, 100, 250, 500} - {0})
    return [{"tier": t, "label": ai_models.TIER_LABELS[t], "current": t == current_tier,
             "rows": [costs.estimate(n, posts_per_day, t) for n in sizes],
             "per_caption_vnd": costs.cost_per_caption(ai_models.model_for("caption", t)) * config.USD_VND,
             "per_kit_vnd": costs.cost_per_kit(ai_models.model_for("creative", t), ai_models.IMAGE_SIDE[t])
             * config.USD_VND}
            for t in ai_models.TIERS]


@app.post("/settings")
def settings_save(request: Request, min_commission_rate: float = Form(...), min_rating: float = Form(...),
                  min_sales: int = Form(...), max_pages_per_product_per_day: int = Form(...),
                  repeat_product_after_days: int = Form(...), post_hours: str = Form(...),
                  blacklist: str = Form(""), disclosure: str = Form(...), media_variants: int = Form(2),
                  kit_media: str = Form("alternate"), ai_tier: str = Form("save"), veo_style: str = Form("studio"),
                  veo_audio: str = Form("mute"), veo_auto: bool = Form(False)):
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
            "disclosure": disclosure.strip(), "media_variants": max(1, min(media_variants, 6)),
            "kit_media": kit_media if kit_media in ("alternate", "album", "video") else "alternate",
            "ai_tier": ai_tier if ai_tier in ("save", "balanced", "quality") else "save",
            "veo_style": veo_style, "veo_audio": "keep" if veo_audio == "keep" else "mute", "veo_auto": veo_auto,
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
    jobs = {"hunt": pipeline.hunt_products, "media": pipeline.build_media, "drafts": pipeline.generate_drafts,
            "publish": pipeline.publish_due,
            "sync": pipeline.sync_metrics, "pages": pipeline.import_pages}
    if name not in jobs:
        raise HTTPException(404)
    with db.get_conn() as conn:
        jobs[name](conn)
    return back(request, "/settings")
