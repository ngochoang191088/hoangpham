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


def test_niche_and_page_management(client):
    r = client.post("/niches", data={"name": "Đồ ăn vặt", "keywords": "khô gà, bánh tráng, khô gà",
                                     "target_pages": 5}, auth=AUTH)
    assert r.status_code == 200 and "Đã tạo" in r.text
    with db.get_conn() as conn:
        assert [n["keywords"] for n in db.get_niches(conn) if n["name"] == "Đồ ăn vặt"] == [["khô gà", "bánh tráng"]]

    client.post("/pages/add", data={"page_id": "555000111", "name": "Ăn Vặt 1", "niche": "Đồ ăn vặt"}, auth=AUTH)
    r = client.post("/pages/bulk", data={
        "lines": "555000112 | Ăn Vặt 2\n555000113 | Ăn Vặt 3 | Đồ ăn vặt\nabc | Sai ID\n555000111 | Trùng",
        "niche": "Đồ ăn vặt"}, auth=AUTH)
    assert "Đã thêm 2 page" in r.text and "2 dòng lỗi" in r.text
    with db.get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) FROM pages WHERE niche = 'Đồ ăn vặt'").fetchone()[0] == 3
        assert conn.execute("SELECT tone FROM pages WHERE id = '555000111'").fetchone()[0] == "thân thiện, gần gũi"

    # Không xoá được ngành còn page
    r = client.post("/niches/delete", data={"name": "Đồ ăn vặt"}, auth=AUTH)
    assert "Không xoá được" in r.text

    # Đổi tên ngành -> page đi theo
    client.post("/niches/update", data={"old_name": "Đồ ăn vặt", "name": "Ăn vặt", "keywords": "khô gà",
                                        "target_pages": 4, "default_tone": "vui"}, auth=AUTH)
    with db.get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) FROM pages WHERE niche = 'Ăn vặt'").fetchone()[0] == 3

    # Page chưa phân ngành -> phân ngành
    with db.get_conn() as conn:
        conn.execute("INSERT INTO pages(id, name, created_at) VALUES ('777', 'Mới từ Meta', ?)", (db.now_iso(),))
    assert "Mới từ Meta" in client.get("/pages/new", auth=AUTH).text
    client.post("/pages/assign", data={"niche_777": "Ăn vặt"}, auth=AUTH)
    with db.get_conn() as conn:
        assert conn.execute("SELECT niche FROM pages WHERE id = '777'").fetchone()[0] == "Ăn vặt"

    # Gỡ page: ẩn khỏi danh sách, có thể thêm lại
    client.post("/pages/777/archive", auth=AUTH)
    assert "Mới từ Meta" not in client.get("/pages?q=777", auth=AUTH).text
    r = client.post("/pages/add", data={"page_id": "777", "name": "Mới từ Meta", "niche": "Ăn vặt"}, auth=AUTH)
    assert "Đã thêm" in r.text

    for url in ("/niches", "/pages/new", "/pages?niche=__none__", "/pages?p=2", "/settings"):
        assert client.get(url, auth=AUTH).status_code == 200


def test_cost_estimate():
    from app.services import costs
    small = costs.estimate(80, 3, "claude-opus-5")
    big = costs.estimate(500, 3, "claude-opus-5")
    assert small["captions"] == 7200 and big["captions"] == 45000
    assert big["total_usd"] > small["total_usd"]
    assert costs.cost_per_caption("claude-opus-5", batch=True) == costs.cost_per_caption("claude-opus-5", False) / 2
    assert costs.cost_per_caption("claude-haiku-4-5", True) < costs.cost_per_caption("claude-sonnet-5", True)


def test_batch_captions(monkeypatch):
    """Batch API: kết quả trả về không theo thứ tự, lỗi/refusal được báo đúng bài, token được ghi lại."""
    from types import SimpleNamespace as NS

    from app import config

    def message(text, stop="end_turn"):
        return NS(stop_reason=stop, model="claude-opus-5", content=[NS(type="text", text=text)],
                  usage=NS(input_tokens=600, output_tokens=900))

    class FakeBatches:
        def create(self, requests):
            self.n = len(requests)
            assert "fallbacks" not in requests[0]["params"]
            return NS(id="b1", processing_status="in_progress")

        def retrieve(self, _id):
            return NS(id="b1", processing_status="ended")

        def results(self, _id):
            return [
                NS(custom_id="2", result=NS(type="errored")),
                NS(custom_id="0", result=NS(type="succeeded", message=message("Bài số 0"))),
                NS(custom_id="1", result=NS(type="succeeded", message=message("", stop="refusal"))),
            ]

    fake = NS(messages=NS(batches=FakeBatches()))
    monkeypatch.setattr(config, "AI_ENABLED", True)
    monkeypatch.setattr(config, "AI_BATCH_MIN", 2)
    monkeypatch.setattr(ai_writer, "_client", lambda: fake)
    monkeypatch.setattr(ai_writer.time, "sleep", lambda _s: None)

    page = {"name": "P", "niche": "N", "tone": "vui"}
    product = {"name": "X", "price": 100000, "sales": 10, "rating": 5, "shop_name": "S"}
    usage = []
    out = ai_writer.write_captions([{"page": page, "product": product}] * 3, "#tag",
                                   lambda *a: usage.append(a))
    assert out[0] == ("Bài số 0\n\n#tag", None)
    assert out[1][0] is None and "từ chối" in out[1][1]
    assert out[2][0] is None and "errored" in out[2][1]
    assert usage == [("claude-opus-5", 600, 900, True), ("claude-opus-5", 600, 900, True)]
