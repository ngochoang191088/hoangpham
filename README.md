# Aff Pages: quản lý hàng trăm fanpage Facebook chạy affiliate Shopee

Bạn **đăng nhập bằng Facebook cá nhân**, app tự nhận diện tất cả page tài khoản đang quản lý (80, 200, 500 page…).
Bạn chỉ cần: **chọn ngành hàng cho page → nhập file sản phẩm + link aff + video của từng ngành → duyệt bài**.
AI viết bài, app tự đăng **video** (nếu sản phẩm có video) hoặc **ảnh sản phẩm**, và báo cáo kết quả.

## Quy trình

1. **Đăng nhập bằng Facebook**: app lấy danh sách page (kèm quyền đăng bài) của tài khoản. Page mới tạo sau này:
   bấm *Nhận diện lại page từ Facebook* hoặc đăng nhập lại.
2. **Chọn ngành hàng cho page** (trang *Page → Chưa chọn ngành hàng*): tick nhiều page rồi áp 1 ngành,
   hoặc chọn ngay trên từng dòng. Danh sách ngành hàng sửa ở trang *Ngành hàng* (mặc định 16 ngành, mục tiêu 5 page/ngành).
3. **Nhập sản phẩm cho từng ngành** (trang *Sản phẩm & video*): mỗi ngành 1 file Excel riêng
   (`.xlsx`, `.csv`, `.docx`, `.txt`), hoặc thêm từng sản phẩm. Tải file mẫu ngay trong app.

   | Tên sản phẩm | Link sản phẩm | **Link aff** (bắt buộc) | Giá | Mô tả | Link ảnh | Link video |
   |---|---|---|---|---|---|---|

   - **Có link video** (`.mp4` trực tiếp hoặc Google Drive chia sẻ công khai) hoặc tải file video lên app → **đăng video**.
   - **Không có video** → đăng **ảnh sản phẩm** (cột Link ảnh).
   - Một sản phẩm nhiều video: thêm nhiều dòng cùng link aff. Mỗi video không đăng lặp lại trên cùng 1 page.
   - Thiếu tên sản phẩm: app lấy tạm từ link Shopee (hoặc lấy đủ tên/giá/ảnh nếu có Shopee Open API).
4. **AI viết bài** cho từng page, dựa trên tên, giá, mô tả bạn cung cấp, theo giọng văn của page.
   Nội dung được kiểm duyệt tự động (từ cấm, câu gây hiểu lầm, trùng lặp giữa các page).
5. **Bạn duyệt** ở trang *Duyệt bài* (1 nút duyệt tất cả bài sạch), app **tự đăng** đúng giờ,
   link aff đặt trong bài hoặc ở bình luận đầu tiên.
6. **Theo dõi** ở *Tổng quan*: tương tác, hoa hồng theo page / ngành / sản phẩm; cảnh báo page bị hạn chế,
   mất quyền, ngành chưa có sản phẩm, bài lỗi. Có **nút dừng khẩn cấp** toàn bộ.

| Chọn ngành hàng cho page | Sản phẩm, link aff & video |
|---|---|
| ![](docs/pages_unassigned.png) | ![](docs/products.png) |
| **Tổng quan** | **Ngành hàng** |
| ![](docs/dashboard.png) | ![](docs/niches.png) |
| **Duyệt bài** | **Chi tiết một page** |
| ![](docs/review.png) | ![](docs/page.png) |

## Chạy thử ngay (DEMO)

Chưa cần Facebook App: app giả lập 1 tài khoản có 82 page, sản phẩm, video và 30 ngày số liệu.

```bash
pip install -r requirements.txt
cp .env.example .env          # đổi ADMIN_PASSWORD, SECRET_KEY
python -m app.demo            # tạo dữ liệu mẫu
uvicorn app.main:app --port 8000
```

Mở http://localhost:8000 → nhập mật khẩu demo (`ADMIN_PASSWORD`).

## Chạy thật

### 1. Tạo Facebook App (1 lần, khoảng 10 phút)
1. Vào https://developers.facebook.com → **Tạo ứng dụng** → loại *Business* (hoặc *Khác → Doanh nghiệp*).
2. Thêm sản phẩm **Facebook Login for Business** (hoặc Facebook Login).
   Ở phần cài đặt, thêm **Valid OAuth Redirect URI**: `https://<tên-miền-của-bạn>/auth/facebook/callback`.
3. Lấy **App ID** và **App Secret** (Cài đặt → Thông tin cơ bản) điền vào `.env`:
   ```
   FB_APP_ID=...
   FB_APP_SECRET=...
   BASE_URL=https://<tên-miền-của-bạn>
   SECRET_KEY=<chuỗi ngẫu nhiên dài>
   ALLOWED_FB_USERS=<Facebook ID của bạn>   # không bắt buộc
   ```
4. Tài khoản Facebook tạo app là **quản trị viên của app** nên dùng được ngay ở chế độ Development,
   **không cần Facebook duyệt app**, vì bạn chỉ quản lý page của chính mình.
5. Khi đăng nhập, Facebook hỏi quyền: chọn **tất cả page** và đồng ý các quyền
   `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `pages_manage_engagement`, `business_management`.

Token đăng nhập có hạn khoảng 60 ngày (app hiển thị ngày hết hạn trong *Cài đặt*); token của từng page
không hết hạn nên việc đăng bài vẫn chạy. Chỉ cần đăng nhập lại khi muốn nhận diện page mới sau ngày hết hạn.

> Chỉ dùng API chính thức của Facebook. Không dùng tool đăng nhập bằng cookie hay nick clone, vì đó là cách nhanh nhất để mất page.
> Chỉ đăng video/ảnh bạn có quyền sử dụng.

### 2. Claude AI (viết bài)
Dán `ANTHROPIC_API_KEY`. Nếu để trống, app dùng caption mẫu.
- `AI_MODEL`: mặc định `claude-opus-5` (viết hay nhất); tiết kiệm hơn: `claude-sonnet-5`, `claude-haiku-4-5`.
- `AI_BATCH=1` (mặc định): bài ngày mai được viết qua **Message Batches API**, giảm 50% chi phí.

### 3. (Tuỳ chọn) Shopee Affiliate Open API
Điền `SHOPEE_APP_ID`, `SHOPEE_APP_SECRET` nếu muốn app tự lấy tên / giá / ảnh / % hoa hồng từ link sản phẩm
và đồng bộ hoa hồng thật. Không bắt buộc: bạn tự nhập link aff là đủ.

### 4. Chạy tự động (cron trên VPS)

```cron
# AI viết bài cho ngày mai lúc 6h sáng (bạn duyệt trong ngày)
0 6 * * *    cd /opt/aff-pages && python -m app.jobs drafts
# Đăng bài đến giờ, 5 phút một lần
*/5 * * * *  cd /opt/aff-pages && python -m app.jobs publish
# Cập nhật tương tác (+ hoa hồng nếu có Shopee Open API), 2 giờ một lần
0 */2 * * *  cd /opt/aff-pages && python -m app.jobs sync
# Nhận diện page mới mỗi ngày
30 5 * * *   cd /opt/aff-pages && python -m app.jobs pages
```

Web app: `uvicorn app.main:app --host 127.0.0.1 --port 8000` đặt sau Nginx + HTTPS (Facebook Login bắt buộc HTTPS).
Video tải lên được lưu trong `data/uploads/`, nên để ổ đĩa VPS đủ lớn (video 50–100 MB/cái).

## Chi phí mỗi tháng (ước tính, 3 bài/page/ngày, dùng Batch API)

| Model | 80 page | 100 page | 250 page | 500 page |
|---|---|---|---|---|
| Claude Opus 5 | ~2,8 triệu đ | ~3,4 triệu đ | ~8,5 triệu đ | ~17 triệu đ |
| Claude Sonnet 5 | ~1,2 triệu đ | ~1,5 triệu đ | ~3,6 triệu đ | ~7,2 triệu đ |
| Claude Haiku 4.5 | ~0,4 triệu đ | ~0,5 triệu đ | ~1,1 triệu đ | ~2,2 triệu đ |

Đã gồm VPS (6–24 USD). Facebook API miễn phí. Bảng theo số page thật và **chi phí AI thật đo từ token**
nằm trong *Cài đặt → Chi phí*.

## Cấu trúc

```
app/
  main.py              web app (đăng nhập, các trang, thao tác)
  jobs.py              chạy việc tự động từ cron
  demo.py              dữ liệu mẫu
  db.py                SQLite, tự nâng cấp cấu trúc khi cập nhật
  services/
    facebook.py        đăng nhập Facebook, nhận diện page, đăng video / ảnh
    importer.py        đọc file Excel / CSV / Word / text, file mẫu
    catalog.py         kho sản phẩm + video theo ngành hàng
    ai_writer.py       viết caption (Claude, Batch API) + kiểm duyệt
    pipeline.py        nhận diện page → tạo bài → đăng → đồng bộ số liệu
    shopee.py          (tuỳ chọn) Shopee Affiliate Open API
    costs.py           ước tính chi phí
tests/                 python -m pytest
```
