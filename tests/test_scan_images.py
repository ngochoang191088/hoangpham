import csv
from io import BytesIO

import httpx
from PIL import Image

from app import scan_images
from app.services import shopee

LINK = "https://shopee.vn/Binh-giu-nhiet-500ml-i.123456.7890123"


def _jpeg(size=(800, 800)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, "red").save(buf, "JPEG")
    return buf.getvalue()


def test_find_links_accepts_links_short_links_and_codes():
    assert scan_images.find_links(f"xem {LINK}, rẻ lắm") == [LINK]
    assert scan_images.find_links("https://shopee.vn/product/123456/7890123?sp_atk=x") == [
        "https://shopee.vn/product/123456/7890123?sp_atk=x"]
    assert scan_images.find_links("link aff https://s.shopee.vn/AbC123 nhé") == ["https://s.shopee.vn/AbC123"]
    assert scan_images.find_links("123456.7890123") == ["https://shopee.vn/product/123456/7890123"]
    assert scan_images.find_links("123456/7890123") == ["https://shopee.vn/product/123456/7890123"]
    assert scan_images.find_links("giá 199.000đ, SĐT 0912345678") == []
    assert scan_images.find_links("https://shopee.vn/flash_sale") == []


def test_read_input_txt_and_xlsx(tmp_path):
    txt = tmp_path / "links.txt"
    txt.write_text(f"# ghi chú\n{LINK}\n{LINK}\n\n123456/555555555\n", encoding="utf-8")
    assert scan_images.read_input(txt) == [LINK, "https://shopee.vn/product/123456/555555555"]

    from openpyxl import Workbook

    wb = Workbook()
    wb.active.append(["Tên", "Link"])
    wb.active.append(["Bình giữ nhiệt", LINK])
    wb.active.append(["Quạt", "https://s.shopee.vn/Xyz9"])
    xlsx = tmp_path / "links.xlsx"
    wb.save(xlsx)
    assert scan_images.read_input(xlsx) == [LINK, "https://s.shopee.vn/Xyz9"]


def test_safe_name_is_valid_windows_folder():
    assert scan_images.safe_name('Bình giữ nhiệt 500ml / inox 304: "cao cấp"?') == \
        "Bình giữ nhiệt 500ml inox 304 cao cấp"
    assert scan_images.safe_name("...") == "san-pham"
    assert len(scan_images.safe_name("a" * 200)) == 60


def test_fill_and_find_item_from_shopee_json():
    data = {"data": {"item": {"itemid": 7890123, "name": "Bình giữ nhiệt", "price": 19900000000,
                              "historical_sold": 1200, "item_rating": {"rating_star": 4.87},
                              "images": ["a1", "a2"], "tier_variations": [{"images": ["v1", "a1"]}]}}}
    item = scan_images._find_item(data, "7890123")
    assert item["name"] == "Bình giữ nhiệt"
    assert scan_images._find_item(data, "999") is None
    info = {"images": []}
    scan_images._fill_from_item(info, item)
    assert info["price"] == 199000 and info["sold"] == 1200 and info["rating"] == 4.9
    assert info["images"] == [shopee.IMG_CDN + h for h in ("a1", "a2", "v1")]


def test_scan_downloads_images_into_one_folder_per_product(tmp_path, monkeypatch):
    def fake_collect(link):
        ids = shopee.parse_ids(link)
        return {"input": link, "product_link": link, "shop_id": ids[0], "item_id": ids[1],
                "name": "Bình giữ nhiệt / 500ml", "price": 199000,
                "images": ["https://img/1", "https://img/2", "https://img/tiny", "https://img/3"]}

    def fake_get(self, url, **kw):
        body = _jpeg((50, 50)) if url.endswith("tiny") else _jpeg()
        return httpx.Response(200, content=body, request=httpx.Request("GET", url))

    monkeypatch.setattr(scan_images, "_collect_http", fake_collect)
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    out = tmp_path / "anh_san_pham"
    results = scan_images.scan([LINK, "https://shopee.vn/product/1/22222222"], out, max_images=10,
                               delay=(0, 0), log=lambda *a: None)

    folder = out / "7890123 - Bình giữ nhiệt 500ml"
    assert sorted(p.name for p in folder.glob("*.jpg")) == ["01.jpg", "02.jpg", "03.jpg"]   # bỏ ảnh quá nhỏ
    assert "Giá: 199.000đ" in (folder / "thong_tin.txt").read_text(encoding="utf-8")
    assert [r["downloaded"] for r in results] == [3, 3]
    with (out / "ket_qua.csv").open(encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0] == "Link đưa vào" and len(rows) == 3

    # chạy lại: sản phẩm đã có ảnh thì bỏ qua, không tải lại
    monkeypatch.setattr(scan_images, "_collect_http", lambda link: (_ for _ in ()).throw(AssertionError))
    again = scan_images.scan([LINK], out, delay=(0, 0), log=lambda *a: None)
    assert again[0]["status"] == "đã có" and again[0]["downloaded"] == 3


def test_scan_reports_unreadable_link(tmp_path, monkeypatch):
    monkeypatch.setattr(scan_images, "_collect_http",
                        lambda link: {"input": link, "images": [], "error": "Không đọc được mã sản phẩm"})
    results = scan_images.scan(["https://s.shopee.vn/zzz"], tmp_path, delay=(0, 0), log=lambda *a: None)
    assert results[0]["downloaded"] == 0 and "Không đọc được" in results[0]["status"]


def test_main_creates_input_file_when_missing(tmp_path, capsys):
    target = tmp_path / "danh_sach_link.txt"
    assert scan_images.main([str(target)]) == 1
    assert target.exists() and "Dán link" in target.read_text(encoding="utf-8")
