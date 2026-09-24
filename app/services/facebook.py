"""Facebook Graph API: đăng nhập, nhận diện page, đăng bài (ảnh / video), lấy số liệu tương tác.

Khi chưa cấu hình Facebook App (FB_APP_ID/FB_APP_SECRET) hoặc FB_SYSTEM_USER_TOKEN
thì mọi hàm chạy ở chế độ DEMO (giả lập kết quả, không gọi Facebook).
"""
import random
import re
import uuid
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app import config


class FacebookError(Exception):
    pass


def _url(path: str) -> str:
    return f"https://graph.facebook.com/{config.FB_GRAPH_VERSION}/{path.lstrip('/')}"


def _request(method: str, path: str, token: str, **params) -> dict:
    params["access_token"] = token
    with httpx.Client(timeout=60) as client:
        if method == "GET":
            resp = client.get(_url(path), params=params)
        else:
            resp = client.post(_url(path), data=params)
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error", {})
        raise FacebookError(f"{err.get('code', resp.status_code)}: {err.get('message', resp.text)}")
    return data


# Quyền cần xin khi đăng nhập: xem danh sách page, đăng bài, đọc tương tác, trả lời bình luận
SCOPES = ["pages_show_list", "pages_manage_posts", "pages_read_engagement", "pages_manage_engagement",
          "business_management"]


def login_url(state: str) -> str:
    """Link mở hộp thoại "Đăng nhập bằng Facebook"."""
    query = urlencode({
        "client_id": config.FB_APP_ID, "redirect_uri": f"{config.BASE_URL}/auth/facebook/callback",
        "state": state, "scope": ",".join(SCOPES), "response_type": "code",
    })
    return f"https://www.facebook.com/{config.FB_GRAPH_VERSION}/dialog/oauth?{query}"


def exchange_code(code: str) -> dict:
    """Đổi mã đăng nhập lấy token dài hạn (~60 ngày) + thông tin tài khoản.

    Page token lấy từ user token dài hạn thì không hết hạn (trừ khi đổi mật khẩu / gỡ quyền).
    """
    with httpx.Client(timeout=60) as client:
        short = client.get(_url("oauth/access_token"), params={
            "client_id": config.FB_APP_ID, "client_secret": config.FB_APP_SECRET,
            "redirect_uri": f"{config.BASE_URL}/auth/facebook/callback", "code": code,
        }).json()
        if "access_token" not in short:
            raise FacebookError(str(short.get("error", short)))
        long = client.get(_url("oauth/access_token"), params={
            "grant_type": "fb_exchange_token", "client_id": config.FB_APP_ID,
            "client_secret": config.FB_APP_SECRET, "fb_exchange_token": short["access_token"],
        }).json()
    token = long.get("access_token", short["access_token"])
    me = _request("GET", "me", token, fields="id,name")
    return {"id": me["id"], "name": me["name"], "token": token, "expires_in": long.get("expires_in")}


def list_managed_pages(user_token: str = "") -> list[dict]:
    """Tất cả page mà tài khoản đang quản lý, kèm page access token."""
    token = user_token or config.FB_SYSTEM_USER_TOKEN
    if not config.FB_ENABLED or not token:
        return demo_pages()
    pages, after = [], None
    while True:
        params = {"fields": "id,name,access_token,category,fan_count,picture{url}", "limit": 100}
        if after:
            params["after"] = after
        data = _request("GET", "me/accounts", token, **params)
        pages.extend(data.get("data", []))
        after = data.get("paging", {}).get("cursors", {}).get("after")
        if not data.get("paging", {}).get("next"):
            return pages


_DEMO_TOPICS = ["Săn Deal", "Góc Review", "Tiệm Nhà", "Chợ Online", "Nhà Mình", "Đồ Hay", "Giá Tốt", "Mua Gì"]
DEMO_PAGE_COUNT = 82


def demo_pages(n: int | None = None) -> list[dict]:
    """Danh sách page giả lập cho chế độ DEMO (như 1 tài khoản cá nhân quản lý 82 page)."""
    n = DEMO_PAGE_COUNT if n is None else n
    return [{
        "id": str(100000000000 + i), "name": f"{_DEMO_TOPICS[i % len(_DEMO_TOPICS)]} {i + 1:02d}",
        "access_token": "", "category": "Shopping & Retail", "fan_count": 1000 + (i * 7919) % 50000,
    } for i in range(n)]


_DRIVE_ID = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=download&)?id=)([\w-]+)")


def direct_video_url(url: str) -> str | None:
    """Chuẩn hoá link video thành link tải trực tiếp mà Facebook tự tải được.

    Hỗ trợ: link .mp4/.mov trực tiếp, Google Drive (file chia sẻ "Bất kỳ ai có đường liên kết").
    Trả về None nếu là link trang xem video (TikTok, YouTube...) vì Facebook không tải được.
    """
    url = (url or "").strip()
    m = _DRIVE_ID.search(url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    if re.search(r"\.(mp4|mov|m4v|webm)(\?|$)", url, re.I) and url.startswith("http"):
        return url
    return None


def publish(page: dict, caption: str, link: str, image_url: str = "", video: dict | None = None) -> dict:
    """Đăng bài lên page. Trả về {"fb_post_id", "permalink"}.

    video = {"url": ..., "file_path": ...}: đăng video (ưu tiên). Không có video thì đăng ảnh sản phẩm.
    link_mode = "post": link aff nằm trong nội dung bài.
    link_mode = "comment": link aff nằm ở bình luận đầu tiên dưới bài.
    """
    message = caption if page["link_mode"] == "comment" else f"{caption}\n\n👉 {link}"

    if not config.FB_ENABLED:
        fake_id = f"{page['id']}_{uuid.uuid4().hex[:12]}"
        return {"fb_post_id": fake_id, "permalink": f"https://www.facebook.com/{fake_id}"}

    token = page["access_token"]
    if video:
        post_id = _upload_video(page["id"], token, message, video)
    elif image_url:
        data = _request("POST", f"{page['id']}/photos", token, url=image_url, caption=message)
        post_id = data.get("post_id") or data["id"]
    else:
        data = _request("POST", f"{page['id']}/feed", token, message=message, link=link)
        post_id = data["id"]

    if page["link_mode"] == "comment":
        _request("POST", f"{post_id}/comments", token, message=f"👉 Link sản phẩm: {link}")

    info = _request("GET", post_id, token, fields="permalink_url")
    permalink = info.get("permalink_url", "")
    if permalink.startswith("/"):
        permalink = "https://www.facebook.com" + permalink
    return {"fb_post_id": post_id, "permalink": permalink}


def _upload_video(page_id: str, token: str, message: str, video: dict) -> str:
    """Tải video lên page: từ file trên máy chủ app, hoặc để Facebook tự tải từ link."""
    url = f"https://graph-video.facebook.com/{config.FB_GRAPH_VERSION}/{page_id}/videos"
    data = {"access_token": token, "description": message}
    with httpx.Client(timeout=900) as client:
        if video.get("file_path"):
            path = Path(video["file_path"])
            with path.open("rb") as fh:
                resp = client.post(url, data=data, files={"source": (path.name, fh, "video/mp4")})
        else:
            file_url = direct_video_url(video.get("url", ""))
            if not file_url:
                raise FacebookError("Link video không tải trực tiếp được (cần link .mp4 hoặc Google Drive)")
            resp = client.post(url, data={**data, "file_url": file_url})
    result = resp.json()
    if resp.status_code >= 400 or "error" in result:
        err = result.get("error", {})
        raise FacebookError(f"Tải video lỗi {err.get('code', resp.status_code)}: {err.get('message', resp.text)}")
    return result["id"]


def post_metrics(page: dict, fb_post_id: str) -> dict:
    """Số reaction, comment, share của một bài."""
    if not config.FB_ENABLED:
        return {
            "reactions": random.randint(5, 400),
            "comments": random.randint(0, 60),
            "shares": random.randint(0, 30),
        }
    data = _request(
        "GET", fb_post_id, page["access_token"],
        fields="reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0),shares",
    )
    return {
        "reactions": data.get("reactions", {}).get("summary", {}).get("total_count", 0),
        "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
        "shares": data.get("shares", {}).get("count", 0),
    }


def recent_posts(page: dict, limit: int = 25) -> list[dict]:
    """Các bài đã đăng gần đây trên page, kể cả bài đăng ngoài app."""
    if not config.FB_ENABLED:
        return []
    data = _request(
        "GET", f"{page['id']}/published_posts", page["access_token"],
        fields="id,message,created_time,permalink_url,full_picture", limit=limit,
    )
    return data.get("data", [])
