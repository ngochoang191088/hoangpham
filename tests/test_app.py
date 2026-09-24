import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"
for key in ("FB_SYSTEM_USER_TOKEN", "SHOPEE_APP_ID", "SHOPEE_APP_SECRET", "ANTHROPIC_API_KEY"):
    os.environ[key] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db, demo  # noqa: E402
from app.main import app  # noqa: E402
from app.services import ai_writer, pipeline, shopee  # noqa: E402

AUTH = ("admin", "secret")


@pytest.fixture(scope="module")
def client():
    demo.seed(n_pages=12, days=5)
    with TestClient(app) as c:
        yield c


def test_requires_login(client):
    assert client.get("/").status_code == 401
    assert client.get("/", auth=("admin", "wrong")).status_code == 401


@pytest.mark.parametrize("url", [
    "/", "/?days=7", "/pages", "/pages?sort=orders&niche=Gia%20d%E1%BB%A5ng", "/pages/100000000000",
    "/pages/100000000000?status_=pending", "/posts", "/posts?status=failed&flagged=1", "/review",
    "/review?flagged=1", "/products", "/settings",
])
def test_pages_render(client, url):
    assert client.get(url, auth=AUTH).status_code == 200


def test_unknown_page_404(client):
    assert client.get("/pages/nope", auth=AUTH).status_code == 404


def test_approve_then_publish(client):
    with db.get_conn() as conn:
        post = conn.execute(
            "SELECT posts.id FROM posts JOIN pages ON pages.id = posts.page_id "
            "WHERE posts.status='pending' AND pages.status='active' LIMIT 1").fetchone()
        conn.execute("UPDATE posts SET scheduled_at = ? WHERE id = ?", (db.now_iso(), post["id"]))
    client.post(f"/posts/{post['id']}/approve", auth=AUTH)
    with db.get_conn() as conn:
        assert conn.execute("SELECT status FROM posts WHERE id=?", (post["id"],)).fetchone()[0] == "approved"
        pipeline.publish_due(conn)
        row = conn.execute("SELECT status, fb_post_id FROM posts WHERE id=?", (post["id"],)).fetchone()
    assert row["status"] == "published" and row["fb_post_id"]


def test_global_pause_blocks_publishing(client):
    client.post("/pause", auth=AUTH)
    with db.get_conn() as conn:
        conn.execute("UPDATE posts SET status='approved', scheduled_at=? WHERE status='pending'", (db.now_iso(),))
        assert pipeline.publish_due(conn) == (0, 0)
    client.post("/pause", auth=AUTH)
    with db.get_conn() as conn:
        assert db.get_settings(conn)["global_pause"] is False


def test_bulk_reject(client):
    with db.get_conn() as conn:
        conn.execute("UPDATE posts SET status='pending' WHERE status='approved'")
        ids = [r[0] for r in conn.execute("SELECT id FROM posts WHERE status='pending' LIMIT 3")]
    client.post("/review/bulk", data={"action": "reject", "ids": ids}, auth=AUTH)
    with db.get_conn() as conn:
        marks = ",".join("?" * len(ids))
        statuses = {r[0] for r in conn.execute(f"SELECT status FROM posts WHERE id IN ({marks})", ids)}
    assert statuses == {"rejected"}


def test_check_content_flags():
    s = dict(db.DEFAULT_SETTINGS)
    assert ai_writer.check_content("Sản phẩm tốt #tiepthilienket", s, []) == []
    flags = ai_writer.check_content("Mình đã dùng rồi, thuốc này chữa bệnh", s, [])
    assert any("từ cấm" in f for f in flags)
    assert any("Thiếu ghi chú" in f for f in flags)
    assert any("hiểu lầm" in f for f in flags)
    same = "Deal hot nồi chiên giá tốt #tiepthilienket"
    assert "Gần trùng nội dung với bài khác" in ai_writer.check_content(same, s, [same])


def test_parse_sub_ids():
    assert shopee.parse_sub_ids("p123456-b42") == ("123456", 42)
    assert shopee.parse_sub_ids("") == (None, None)


def test_score_prefers_higher_commission():
    base = {"price": 200000, "commission_rate": 0.05, "sales": 1000, "rating": 4.8}
    assert pipeline.score_product({**base, "commission_rate": 0.15}) > pipeline.score_product(base)
