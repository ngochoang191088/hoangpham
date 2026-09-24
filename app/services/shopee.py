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
