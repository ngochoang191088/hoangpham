"""Facebook Graph API: lấy danh sách page, đăng bài, lấy số liệu tương tác.

Khi chưa cấu hình FB_SYSTEM_USER_TOKEN thì mọi hàm chạy ở chế độ DEMO
(giả lập kết quả, không gọi Facebook).
"""
import random
import uuid

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


def list_managed_pages() -> list[dict]:
    """Các page mà System User quản lý, kèm page access token."""
    if not config.FB_ENABLED:
        return []
    pages, after = [], None
    while True:
        params = {"fields": "id,name,access_token,category", "limit": 100}
        if after:
            params["after"] = after
        data = _request("GET", "me/accounts", config.FB_SYSTEM_USER_TOKEN, **params)
        pages.extend(data.get("data", []))
        after = data.get("paging", {}).get("cursors", {}).get("after")
        if not data.get("paging", {}).get("next"):
            return pages


def publish(page: dict, caption: str, image_url: str, link: str) -> dict:
    """Đăng bài lên page. Trả về {"fb_post_id", "permalink"}.

    link_mode = "post": link nằm trong nội dung bài.
    link_mode = "comment": đăng ảnh + caption, rồi bình luận link ngay dưới bài.
    """
    message = caption if page["link_mode"] == "comment" else f"{caption}\n\n👉 {link}"

    if not config.FB_ENABLED:
        fake_id = f"{page['id']}_{uuid.uuid4().hex[:12]}"
        return {"fb_post_id": fake_id, "permalink": f"https://www.facebook.com/{fake_id}"}

    token = page["access_token"]
    if image_url:
        data = _request("POST", f"{page['id']}/photos", token, url=image_url, caption=message)
        post_id = data.get("post_id") or data["id"]
    else:
        data = _request("POST", f"{page['id']}/feed", token, message=message, link=link)
        post_id = data["id"]

    if page["link_mode"] == "comment":
        _request("POST", f"{post_id}/comments", token, message=f"👉 Link sản phẩm: {link}")

    info = _request("GET", post_id, token, fields="permalink_url")
    return {"fb_post_id": post_id, "permalink": info.get("permalink_url", "")}


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
