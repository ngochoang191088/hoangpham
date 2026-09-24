"""Shopee Affiliate Open API (GraphQL): tìm sản phẩm, tạo link rút gọn, báo cáo hoa hồng.

Cần tài khoản Shopee Affiliate được cấp Open API (AppID + Secret).
Tên trường / tham số dưới đây theo tài liệu Open API của Shopee Affiliate Việt Nam;
nếu Shopee đổi tài liệu, chỉ cần sửa trong file này.
Khi chưa cấu hình AppID/Secret thì chạy DEMO với dữ liệu mẫu.
"""
import hashlib
import json
import random
import re
import time
from datetime import datetime
from html import unescape
from urllib.parse import unquote

import httpx

from app import config

ENDPOINT = "https://open-api.affiliate.shopee.vn/graphql"

# sortType của productOfferV2: 5 = hoa hồng cao -> thấp
SORT_COMMISSION_DESC = 5


class ShopeeError(Exception):
    pass


def _call(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}, separators=(",", ":"))
    ts = str(int(time.time()))
    sign = hashlib.sha256(
        (config.SHOPEE_APP_ID + ts + payload + config.SHOPEE_APP_SECRET).encode()
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={config.SHOPEE_APP_ID}, Timestamp={ts}, Signature={sign}",
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(ENDPOINT, content=payload, headers=headers)
    data = resp.json()
    if data.get("errors"):
        raise ShopeeError(str(data["errors"]))
    return data["data"]


PRODUCT_QUERY = """
query($keyword: String, $sortType: Int, $page: Int, $limit: Int) {
  productOfferV2(keyword: $keyword, sortType: $sortType, page: $page, limit: $limit) {
    nodes {
      itemId productName commissionRate priceMin priceMax sales ratingStar
      imageUrl shopName productLink offerLink
    }
  }
}
"""


def search_products(keyword: str, limit: int = 20) -> list[dict]:
    """Sản phẩm theo từ khoá, sắp xếp hoa hồng cao nhất trước."""
    if not config.SHOPEE_ENABLED:
        return _demo_products(keyword, limit)
    data = _call(PRODUCT_QUERY, {
        "keyword": keyword, "sortType": SORT_COMMISSION_DESC, "page": 1, "limit": limit,
    })
    result = []
    for n in data["productOfferV2"]["nodes"]:
        result.append({
            "item_id": str(n["itemId"]),
            "name": n["productName"],
            "price": float(n.get("priceMin") or 0),
            "commission_rate": float(n.get("commissionRate") or 0),
            "sales": int(n.get("sales") or 0),
            "rating": float(n.get("ratingStar") or 0),
            "shop_name": n.get("shopName") or "",
            "image_url": n.get("imageUrl") or "",
            "product_link": n.get("productLink") or "",
            "offer_link": n.get("offerLink") or "",
        })
    return result


ITEM_QUERY = """
query($shopId: Int64, $itemId: Int64) {
  productOfferV2(shopId: $shopId, itemId: $itemId, page: 1, limit: 1) {
    nodes {
      itemId productName commissionRate priceMin sales ratingStar imageUrl shopName productLink offerLink
    }
  }
}
"""


def name_from_link(link: str) -> str:
    """Tên tạm lấy từ đường dẫn: shopee.vn/Noi-chien-5L-i.1.2 -> 'Noi chien 5L'."""
    m = re.search(r"shopee\.vn/([^/?#]+?)-i\.\d+\.\d+", link or "")
    return unquote(m.group(1)).replace("-", " ").strip() if m else ""


def lookup_product(product_link: str) -> dict:
    """Lấy tên, giá, ảnh, % hoa hồng từ link sản phẩm.

    Cần Shopee Affiliate Open API; nếu chưa có thì chỉ lấy được tên tạm từ đường dẫn.
    """
    info = {"name": name_from_link(product_link)}
    m = re.search(r"-i\.(\d+)\.(\d+)", product_link or "") or re.search(r"/product/(\d+)/(\d+)", product_link or "")
    if not (config.SHOPEE_ENABLED and m):
        return info
    try:
        nodes = _call(ITEM_QUERY, {"shopId": int(m.group(1)), "itemId": int(m.group(2))})["productOfferV2"]["nodes"]
    except Exception:  # noqa: BLE001 - thiếu thông tin thì người dùng tự bổ sung
        return info
    if nodes:
        n = nodes[0]
        info.update({
            "name": n["productName"], "price": float(n.get("priceMin") or 0),
            "commission_rate": float(n.get("commissionRate") or 0), "sales": int(n.get("sales") or 0),
            "rating": float(n.get("ratingStar") or 0), "shop_name": n.get("shopName") or "",
            "image_url": n.get("imageUrl") or "",
        })
    return info


IMG_CDN = "https://down-vn.img.susercontent.com/file/"
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0 Safari/537.36",
    "Accept": "application/json", "Accept-Language": "vi-VN,vi;q=0.9", "X-Api-Source": "pc",
}


def fetch_images(product_link: str, limit: int = 5) -> list[str]:
    """Link ảnh sản phẩm (tối đa `limit`) lấy từ link Shopee.

    Thứ tự thử: Shopee Affiliate Open API (ảnh chính) -> dữ liệu công khai của trang sản phẩm.
    Shopee hay chặn truy cập tự động, nên có thể trả về ít ảnh hoặc rỗng: khi đó hãy dán link ảnh
    vào cột "Link ảnh" của file Excel hoặc tải ảnh lên trong Studio.
    """
    m = re.search(r"-i\.(\d+)\.(\d+)", product_link or "") or re.search(r"/product/(\d+)/(\d+)", product_link or "")
    if not m:
        return []
    shop_id, item_id = m.group(1), m.group(2)
    urls: list[str] = []
    try:
        with httpx.Client(timeout=12, headers={**_BROWSER_HEADERS, "Referer": product_link},
                          follow_redirects=True) as client:
            resp = client.get("https://shopee.vn/api/v4/item/get", params={"itemid": item_id, "shopid": shop_id})
            data = (resp.json() or {}).get("data") or {}
            urls += [IMG_CDN + h for h in data.get("images") or [] if isinstance(h, str)]
    except Exception:  # noqa: BLE001 - bị chặn / đổi API: dùng nguồn khác
        pass
    if not urls:
        info = lookup_product(product_link)
        if info.get("image_url"):
            urls.append(info["image_url"])
    return list(dict.fromkeys(urls))[:limit]


SHORT_LINK = re.compile(r"(s\.shopee\.vn|shope\.ee|shp\.ee|vn\.shp\.ee|/universal-link|an_redir)", re.I)
_CRAWLER_UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"


def parse_ids(link: str) -> tuple[str, str] | None:
    m = re.search(r"-i\.(\d+)\.(\d+)", link or "") or re.search(r"/product/(\d+)/(\d+)", link or "")
    return (m.group(1), m.group(2)) if m else None


def is_short_link(link: str) -> bool:
    return bool(SHORT_LINK.search(link or ""))


def resolve_link(link: str) -> str:
    """Link rút gọn / link aff (s.shopee.vn/...) -> link sản phẩm đầy đủ (theo chuyển hướng)."""
    link = (link or "").strip()
    if parse_ids(link) and not is_short_link(link):
        return link
    try:
        with httpx.Client(timeout=15, headers=_BROWSER_HEADERS, follow_redirects=True) as client:
            resp = client.get(link)
        candidates = [str(r.headers.get("location", "")) for r in resp.history] + [str(resp.url)]
        # link aff thường chuyển qua trang trung gian có tham số chứa link sản phẩm
        candidates += [unquote(c) for c in candidates]
        for url in candidates:
            m = re.search(r"https?://shopee\.vn/[^\s\"'&?]*?-i\.\d+\.\d+|https?://shopee\.vn/product/\d+/\d+", url)
            if m:
                return m.group(0)
    except Exception:  # noqa: BLE001
        pass
    return link


def _og_meta(url: str) -> dict:
    """Thẻ og:title / og:image / og:description Shopee trả cho trình thu thập của Facebook."""
    try:
        with httpx.Client(timeout=15, headers={"User-Agent": _CRAWLER_UA}, follow_redirects=True) as client:
            html = client.get(url).text
    except Exception:  # noqa: BLE001
        return {}
    meta = {}
    for key in ("og:title", "og:image", "og:description"):
        m = re.search(rf'<meta[^>]+property=["\']{key}["\'][^>]+content=["\']([^"\']+)', html) or \
            re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{key}["\']', html)
        if m:
            meta[key] = unescape(m.group(1)).strip()
    return meta


def _public_item(shop_id: str, item_id: str, referer: str) -> dict:
    """Dữ liệu công khai của trang sản phẩm (Shopee có thể chặn: khi đó trả về {})."""
    try:
        with httpx.Client(timeout=12, headers={**_BROWSER_HEADERS, "Referer": referer}, follow_redirects=True) as client:
            data = client.get("https://shopee.vn/api/v4/item/get", params={"itemid": item_id, "shopid": shop_id}).json()
        return (data or {}).get("data") or {}
    except Exception:  # noqa: BLE001
        return {}


def detect_product(link: str) -> dict:
    """Nhận diện sản phẩm từ link Shopee (link sản phẩm, link rút gọn hoặc link aff).

    Trả về: product_link, aff_link (nếu link đưa vào là link aff), name, price, images, description,
    sales, rating, shop_name, categories, commission_rate, sources (nguồn dữ liệu đã dùng).
    Thử lần lượt: Shopee Affiliate Open API -> dữ liệu công khai trang sản phẩm -> thẻ chia sẻ (og:) -> đường dẫn.
    """
    link = (link or "").strip()
    info: dict = {"aff_link": link if is_short_link(link) else "", "images": [], "categories": [], "sources": []}
    product_link = resolve_link(link) if config.SHOPEE_FETCH else link
    info["product_link"] = product_link
    ids = parse_ids(product_link)
    if not config.SHOPEE_FETCH:
        return _demo_detect(info, product_link, ids)
    if not ids:
        info["error"] = "Không đọc được mã sản phẩm từ link (cần link dạng shopee.vn/...-i.<shop>.<item>)"
        return info

    api = lookup_product(product_link)
    if api.get("image_url"):
        info["sources"].append("Shopee Open API")
        info.update({k: v for k, v in api.items() if k != "image_url" and v})
        info["images"].append(api["image_url"])

    item = _public_item(ids[0], ids[1], product_link)
    if item:
        info["sources"].append("trang sản phẩm")
        info.setdefault("name", item.get("name") or "")
        if not info.get("price") and item.get("price"):
            info["price"] = item["price"] / 100000                    # Shopee lưu giá x100000
        info["images"] += [IMG_CDN + h for h in item.get("images") or [] if isinstance(h, str)]
        info["description"] = (item.get("description") or "")[:3000]
        info.setdefault("sales", item.get("historical_sold") or item.get("sold") or 0)
        rating = (item.get("item_rating") or {}).get("rating_star")
        if rating:
            info.setdefault("rating", round(float(rating), 1))
        info["categories"] = [c.get("display_name", "") for c in item.get("categories") or [] if c.get("display_name")]

    if not info.get("name") or not info["images"]:
        og = _og_meta(product_link)
        if og:
            info["sources"].append("thẻ chia sẻ")
            title = re.sub(r"\s*\|\s*Shopee.*$", "", og.get("og:title", "")).strip()
            info["name"] = info.get("name") or title
            if og.get("og:image"):
                info["images"].append(og["og:image"])
            info["description"] = info.get("description") or og.get("og:description", "")
    if not info.get("name"):
        info["name"] = name_from_link(product_link)
        if info["name"]:
            info["sources"].append("đường dẫn")
    info["images"] = list(dict.fromkeys(info["images"]))[:8]
    if config.DEMO_MODE and not info["images"] and not info.get("description"):
        return _demo_detect(info, product_link, ids)          # demo: Shopee chặn thì giả lập để xem thử
    return info


def _demo_detect(info: dict, product_link: str, ids) -> dict:
    """DEMO: giả lập kết quả nhận diện từ đường dẫn (không gọi Shopee)."""
    name = name_from_link(product_link) or "Sản phẩm demo"
    seed = int(ids[1]) if ids else len(product_link)
    rnd = random.Random(seed)
    info.update({
        "product_link": product_link, "name": name,
        "price": float(rnd.choice([89, 159, 249, 399, 599, 899]) * 1000),
        "description": f"{name}. Thiết kế tiện dụng, chất liệu bền, dễ vệ sinh.",
        "sales": rnd.randint(200, 20000), "rating": round(rnd.uniform(4.6, 5.0), 1),
        "categories": [], "sources": ["demo"],
    })
    return info


LINK_MUTATION = """
mutation($url: String!, $subIds: [String]) {
  generateShortLink(input: {originUrl: $url, subIds: $subIds}) { shortLink }
}
"""


def make_link(product_link: str, page_id: str, post_id: int) -> str:
    """Link aff gắn subId = page + bài, để biết đơn đến từ page/bài nào."""
    sub_ids = [f"p{page_id}", f"b{post_id}"]
    if not config.SHOPEE_ENABLED:
        return f"https://s.shopee.vn/demo{post_id}?sub={'-'.join(sub_ids)}"
    data = _call(LINK_MUTATION, {"url": product_link, "subIds": sub_ids})
    return data["generateShortLink"]["shortLink"]


REPORT_QUERY = """
query($start: Int64, $end: Int64, $scrollId: String) {
  conversionReport(purchaseTimeStart: $start, purchaseTimeEnd: $end, limit: 500, scrollId: $scrollId) {
    nodes {
      conversionId purchaseTime utmContent totalCommission
      orders { items { itemId } }
    }
    pageInfo { hasNextPage scrollId }
  }
}
"""


def parse_sub_ids(utm_content: str) -> tuple[str | None, int | None]:
    """utmContent dạng 'p123-b45-...' -> (page_id, post_id)."""
    page_id, post_id = None, None
    for part in (utm_content or "").split("-"):
        if part.startswith("p") and len(part) > 1:
            page_id = part[1:]
        elif part.startswith("b") and part[1:].isdigit():
            post_id = int(part[1:])
    return page_id, post_id


def conversions(start: datetime, end: datetime) -> list[dict]:
    """Đơn hàng phát sinh trong khoảng thời gian (chỉ dùng khi có Open API)."""
    if not config.SHOPEE_ENABLED:
        return []
    result, scroll_id = [], None
    while True:
        data = _call(REPORT_QUERY, {
            "start": int(start.timestamp()), "end": int(end.timestamp()), "scrollId": scroll_id,
        })["conversionReport"]
        for n in data["nodes"]:
            page_id, post_id = parse_sub_ids(n.get("utmContent", ""))
            items = [i for o in n.get("orders") or [] for i in o.get("items") or []]
            result.append({
                "conversion_id": str(n["conversionId"]),
                "page_id": page_id,
                "post_id": post_id,
                "item_id": str(items[0]["itemId"]) if items else None,
                "orders": max(1, len(n.get("orders") or [])),
                "commission": float(n.get("totalCommission") or 0),
                "purchase_time": datetime.fromtimestamp(int(n["purchaseTime"]), config.TZ).isoformat(),
            })
        if not data["pageInfo"]["hasNextPage"]:
            return result
        scroll_id = data["pageInfo"]["scrollId"]


# ---------- dữ liệu DEMO ----------

_ADJ = ["cao cấp", "chính hãng", "mini", "đa năng", "siêu bền", "chống nước", "size lớn", "phiên bản 2026"]


def _demo_products(keyword: str, limit: int) -> list[dict]:
    rnd = random.Random(keyword)
    items = []
    for i in range(limit):
        item_id = str(int(hashlib.md5(f"{keyword}|{i}".encode()).hexdigest()[:9], 16))
        items.append({
            "item_id": item_id,
            "name": f"{keyword.capitalize()} {rnd.choice(_ADJ)} {rnd.choice(['A1', 'Pro', 'Plus', 'X', 'Lite'])}",
            "price": float(rnd.choice([49, 89, 129, 199, 259, 349, 499, 799, 1290]) * 1000),
            "commission_rate": round(rnd.uniform(0.03, 0.22), 3),
            "sales": rnd.randint(50, 30000),
            "rating": round(rnd.uniform(4.3, 5.0), 1),
            "shop_name": rnd.choice(["Shop Mall Official", "Tiệm Nhà Mơ", "Gia Dụng Xanh", "Bé Yêu Store"]),
            "image_url": f"https://picsum.photos/seed/{item_id}/600/600",
            "product_link": f"https://shopee.vn/product/{item_id}",
            "offer_link": f"https://shopee.vn/product/{item_id}",
        })
    return items
