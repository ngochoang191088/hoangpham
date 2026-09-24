import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    id TEXT PRIMARY KEY,              -- Facebook page id
    name TEXT NOT NULL,
    niche TEXT NOT NULL DEFAULT '',
    tone TEXT NOT NULL DEFAULT 'thân thiện, gần gũi',
    access_token TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',   -- active | paused | restricted | archived
    posts_per_day INTEGER NOT NULL DEFAULT 3,
    link_mode TEXT NOT NULL DEFAULT 'comment', -- post | comment
    auto_approve INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    item_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    niche TEXT NOT NULL DEFAULT '',
    price REAL NOT NULL DEFAULT 0,
    commission_rate REAL NOT NULL DEFAULT 0,  -- 0.12 = 12%
    sales INTEGER NOT NULL DEFAULT 0,
    rating REAL NOT NULL DEFAULT 0,
    shop_name TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    product_link TEXT NOT NULL DEFAULT '',
    offer_link TEXT NOT NULL DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    blocked INTEGER NOT NULL DEFAULT 0,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT NOT NULL REFERENCES pages(id),
    item_id TEXT REFERENCES products(item_id),
    source TEXT NOT NULL DEFAULT 'app',       -- app | facebook (đăng ngoài app)
    caption TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    aff_link TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | rejected | published | failed
    flags TEXT NOT NULL DEFAULT '[]',         -- cảnh báo kiểm duyệt tự động (JSON)
    scheduled_at TEXT,
    published_at TEXT,
    fb_post_id TEXT,
    permalink TEXT,
    error TEXT,
    reactions INTEGER NOT NULL DEFAULT 0,
    comments INTEGER NOT NULL DEFAULT 0,
    shares INTEGER NOT NULL DEFAULT 0,
    orders INTEGER NOT NULL DEFAULT 0,
    commission REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_posts_page ON posts(page_id, status);
CREATE INDEX IF NOT EXISTS idx_posts_sched ON posts(status, scheduled_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_fb ON posts(fb_post_id) WHERE fb_post_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS conversions (
    conversion_id TEXT PRIMARY KEY,
    page_id TEXT,
    post_id INTEGER,
    item_id TEXT,
    orders INTEGER NOT NULL DEFAULT 1,
    commission REAL NOT NULL DEFAULT 0,
    purchase_time TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_time ON conversions(purchase_time);

CREATE TABLE IF NOT EXISTS niches (
    name TEXT PRIMARY KEY,                 -- ngành hàng
    keywords TEXT NOT NULL DEFAULT '[]',   -- từ khoá săn sản phẩm (JSON)
    target_pages INTEGER NOT NULL DEFAULT 5,
    default_tone TEXT NOT NULL DEFAULT 'thân thiện, gần gũi',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    batch INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at);
CREATE INDEX IF NOT EXISTS idx_posts_item ON posts(item_id);
CREATE INDEX IF NOT EXISTS idx_conv_page ON conversions(page_id);
CREATE INDEX IF NOT EXISTS idx_pages_niche ON pages(niche, status);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    level TEXT NOT NULL,     -- info | warn | error
    page_id TEXT,
    message TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "global_pause": False,
    "min_commission_rate": 0.08,
    "min_rating": 4.7,
    "min_sales": 500,
    "max_pages_per_product_per_day": 3,
    "repeat_product_after_days": 14,
    "post_hours": [8, 11, 14, 17, 20, 22],
    "blacklist": [
        "thuốc", "chữa bệnh", "trị bệnh", "giảm cân cấp tốc", "tăng chiều cao",
        "thực phẩm chức năng", "hàng fake", "replica", "super fake", "vape",
    ],
    "disclosure": "#tiepthilienket",
}


# Ngành hàng mặc định: tên -> từ khoá săn sản phẩm trên Shopee
DEFAULT_NICHES = {
    "Mẹ & bé": ["bỉm", "sữa bột", "đồ chơi trẻ em", "xe đẩy"],
    "Gia dụng nhà bếp": ["nồi chiên không dầu", "chảo chống dính", "máy xay sinh tố", "hộp đựng thực phẩm"],
    "Điện gia dụng": ["máy hút bụi", "quạt điều hoà", "máy lọc không khí", "bàn là hơi nước"],
    "Chăm sóc da": ["kem chống nắng", "sữa rửa mặt", "serum", "toner"],
    "Trang điểm": ["son", "phấn nước", "mascara", "kẻ mắt"],
    "Thời trang nữ": ["váy", "áo kiểu nữ", "quần ống rộng", "set đồ nữ"],
    "Thời trang nam": ["áo polo nam", "quần kaki nam", "áo sơ mi nam", "quần short nam"],
    "Giày dép": ["giày sneaker", "dép quai ngang", "sandal", "giày cao gót"],
    "Túi ví & phụ kiện": ["túi xách", "balo", "ví nam", "kính mát"],
    "Phụ kiện điện thoại": ["ốp lưng", "sạc dự phòng", "cáp sạc nhanh", "giá đỡ điện thoại"],
    "Âm thanh": ["tai nghe bluetooth", "loa bluetooth", "micro karaoke", "tai nghe gaming"],
    "Nhà cửa & decor": ["đèn ngủ", "rèm cửa", "thảm trải sàn", "tranh treo tường"],
    "Sắp xếp & lưu trữ": ["kệ để đồ", "hộp đựng đồ", "móc treo", "tủ vải"],
    "Thể thao & dã ngoại": ["thảm tập yoga", "bình nước thể thao", "lều cắm trại", "dây kháng lực"],
    "Thú cưng": ["hạt cho mèo", "cát vệ sinh mèo", "đồ chơi cho chó", "nệm thú cưng"],
    "Văn phòng phẩm": ["bút bi", "sổ tay", "balo học sinh", "đèn học"],
}


def now() -> datetime:
    return datetime.now(config.TZ).replace(microsecond=0)


def now_iso() -> str:
    return now().isoformat()


def connect() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        if not conn.execute("SELECT 1 FROM niches LIMIT 1").fetchone():
            for name, keywords in DEFAULT_NICHES.items():
                conn.execute("INSERT INTO niches(name, keywords, created_at) VALUES (?, ?, ?)",
                             (name, json.dumps(keywords, ensure_ascii=False), now_iso()))
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )


def get_settings(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    settings = dict(DEFAULT_SETTINGS)
    settings.update({r["key"]: json.loads(r["value"]) for r in rows})
    return settings


def set_setting(conn: sqlite3.Connection, key: str, value) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, json.dumps(value, ensure_ascii=False)),
    )


def get_niches(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM niches ORDER BY name").fetchall()
    return [{**dict(r), "keywords": json.loads(r["keywords"])} for r in rows]


def niche_names(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT name FROM niches ORDER BY name")]


def log(conn: sqlite3.Connection, level: str, message: str, page_id: str | None = None) -> None:
    conn.execute(
        "INSERT INTO activity(ts, level, page_id, message) VALUES (?, ?, ?, ?)",
        (now_iso(), level, page_id, message),
    )
