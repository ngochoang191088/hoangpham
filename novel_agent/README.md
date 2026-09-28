# AI viết tiểu thuyết (novel_agent)

Một nhóm AI (Claude) cùng viết một cuốn tiểu thuyết dài, nhiều phần, các chương nối mạch với nhau.
Mỗi chương đều được **nhiều AI khác đọc lại, chấm điểm, chỉ lỗi**, rồi được **sửa lại** tới khi đạt.

## Các agent

| Agent | Việc làm |
|---|---|
| 🏛️ **Kiến trúc sư** | Từ ý tưởng của bạn, dựng *kinh thánh truyện*: thể loại, bối cảnh, nhân vật (mục tiêu, hành trình), hướng dẫn văn phong, mạch từng phần, kết cục. Tới mỗi phần mới lập dàn ý chi tiết từng chương, **dựa trên những gì thật sự đã viết** ở các phần trước. |
| ✍️ **Nhà văn** | Viết chương theo dàn ý chương + toàn bộ hồ sơ truyện + đoạn cuối chương trước (để câu chữ liền mạch). |
| 🔎 **Hội đồng biên tập** (3 AI) | Đọc lại bản thảo, chấm 0-10 và liệt kê lỗi (critical / major / minor) kèm vị trí và cách sửa:<br>• *Biên tập viên logic & nhất quán*: mâu thuẫn với chương trước, nhân vật, dòng thời gian, sai dàn ý.<br>• *Biên tập viên văn chương*: văn phong, nhịp, thoại, tả/kể, chính tả.<br>• *Độc giả khó tính*: độ cuốn, cảm xúc, kết chương có kéo đọc tiếp không. |
| 🛠️ **Biên tập viên sửa** | Viết lại chương theo toàn bộ góp ý. Lặp *phê bình → sửa* tới khi **mọi** nhà phê bình chấm ≥ 8 và không còn lỗi critical (tối đa 3 vòng; không đạt thì giữ bản điểm cao nhất). |
| 📚 **Thủ thư** | Sau khi chương được duyệt: tóm tắt, cập nhật **trạng thái hiện tại của từng nhân vật**, thêm nhân vật mới, ghi **sự thật phải giữ nhất quán**, mở/khép **tuyến truyện** (bí ẩn, chi tiết cài cắm). Hết mỗi phần thì nén cả phần thành 1 bản tóm tắt. |

## Truyện dài vẫn nối mạch thế nào?

Mỗi lần viết / phê bình, AI nhận một "hồ sơ truyện" nén theo tầng để không vượt giới hạn ngữ cảnh:

```
Kinh thánh truyện (nhân vật + TRẠNG THÁI HIỆN TẠI, văn phong, thế giới, mạch các phần)
+ Sự thật đã thiết lập (phải giữ nhất quán)
+ Phần đã xong       -> tóm tắt phần
+ Chương cũ phần này -> sự kiện chính
+ 5 chương gần nhất  -> tóm tắt đầy đủ + chương dừng ở đâu
+ Tuyến truyện đang mở
+ Dàn ý phần hiện tại + dàn ý chương cần viết
+ 3000 ký tự cuối chương trước (nguyên văn)
```

Hồ sơ này được cache (prompt caching) giữa nhà văn, 3 nhà phê bình và biên tập viên sửa của cùng một chương nên rẻ hơn nhiều.

## Cài đặt

```bash
pip install -r requirements.txt
# Đặt ANTHROPIC_API_KEY trong file .env (xem .env.example, các biến NOVEL_*)
```

## Sử dụng

```bash
# 1. Tạo truyện mới (3 phần x 8 chương, ~3000 chữ/chương) và viết luôn 2 chương đầu
python -m novel_agent new "Một cô gái ở Huế nhận được lá thư do người mẹ đã mất 10 năm gửi" \
    --genre "trinh thám tâm lý" --parts 3 --chapters 8 --words 3000 \
    --notes "ngôi thứ nhất, giọng trầm, có yếu tố ẩm thực Huế" --write 2
#    Ý tưởng dài thì để trong file:  python -m novel_agent new @y_tuong.txt

# 2. Viết tiếp (mặc định 1 chương; --count N; --all = tới hết truyện). Bị ngắt thì chạy lại, tự viết tiếp.
python -m novel_agent write co-gai-o-hue --count 3

# 3. Xem tiến độ, xuất file .md + .docx
python -m novel_agent status co-gai-o-hue
python -m novel_agent export co-gai-o-hue

# 4. Bạn tự sửa tay 1 chương (data/novels/<truyện>/chapters/chuong-005.md) rồi nhờ hội đồng đọc lại
python -m novel_agent review co-gai-o-hue 5

python -m novel_agent list          # các truyện đã tạo
python -m novel_agent --mock new "thử"  # chạy giả lập, không gọi API, không tốn tiền
```

Mỗi truyện nằm trong `data/novels/<tên-truyện>/`:

- `project.json`: kinh thánh truyện, dàn ý, ghi chép từng chương, tuyến truyện, sự thật (sửa tay được, ví dụ đổi dàn ý phần chưa viết).
- `chapters/chuong-001.md`: văn bản từng chương.
- `reviews/chuong-001.json`: điểm và góp ý của hội đồng qua từng vòng sửa.

## Chi phí & tuỳ chỉnh

- Mỗi chương ~ 1 lần viết + 3 lần phê bình mỗi vòng + 0-3 lần sửa + 1 lần ghi chép. Cuối mỗi lệnh app in số token đã dùng.
- Giảm chi phí: `NOVEL_MAX_REVISIONS=1`, `NOVEL_CRITIC_EFFORT=low`, hoặc đặt `NOVEL_CRITIC_MODEL=claude-sonnet-5` cho hội đồng.
- Khắt khe hơn: `NOVEL_PASS_SCORE=8.5`.
- Thêm / bớt nhà phê bình: sửa `CRITICS` trong `novel_agent/prompts.py` (ví dụ thêm "chuyên gia lịch sử" cho truyện lịch sử).
