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

---

# 🎬 Chế độ viết kịch bản phim (`script`)

Phương pháp chắt lọc từ bộ skill [jtydhr88/screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills) (MIT),
vốn tổng hợp McKee, Syd Field, Blake Snyder, Egri, Lục Quân...: **không nhảy thẳng từ ý tưởng sang viết**, mà đi đúng thứ tự
tiền đề → kết phim → cấu trúc → nhân vật → danh sách cảnh → kịch bản → sửa theo bộ câu hỏi chẩn đoán.

| Giai đoạn | Việc làm |
|---|---|
| 1-3. Phát triển | Logline, tiền đề (tính cách → dẫn tới → kết cục), tư tưởng chủ đạo, lõi kịch, **kết phim chốt trước**, bảng nhịp theo phút (phim ngắn ≤ 40 phút dùng khởi-thừa-chuyển-hợp), nhân vật ba chiều + giọng nói riêng, con dao của đối thủ, thứ trói buộc hai bên. |
| 4. Danh sách cảnh | Mỗi cảnh: tiêu đề, một câu, **giá trị mở → đóng (phải đảo chiều)**, ai muốn gì / ai cản / ai thắng, số giây. AI biên tập cấu trúc chấm và bắt sửa (tối đa 2 vòng). **Dừng lại để bạn duyệt.** |
| 5. Viết | Viết theo từng đợt ~5 phút phim, thể thức đánh số cảnh kiểu Việt Nam (`CẢNH 3. NGOẠI. BẾN XE - ĐÊM`, `LAN: ...`), ~1 trang / 1 phút. |
| 6. Hội đồng 5 AI | Biên tập **cấu trúc**, **nhân vật**, **cảnh**, **thoại**, **thể thức** - mỗi người chạy bộ câu hỏi chẩn đoán riêng, chỉ ra số cảnh lỗi. Biên tập viên sửa viết lại đúng các cảnh bị góp ý, lặp tới khi cả 5 chấm ≥ 8. |

```bash
# 1. Phát triển tới danh sách cảnh (phim 15 phút), rồi DỪNG để bạn đọc
python -m novel_agent script new "Cô bé bán vé số ở Sài Gòn phát hiện người mua vé mỗi ngày là cha mình" \
    --minutes 15 --genre "tâm lý gia đình" --notes "quay được với 3 diễn viên, 4 bối cảnh, ngân sách thấp"

# 2. Chưa ưng thì bảo AI sửa danh sách cảnh (lặp lại bao nhiêu lần cũng được)
python -m novel_agent script plan co-be-ban-ve-so --note "kết mở hơn, bỏ cảnh bệnh viện, thêm một cảnh không lời ở chợ"

# 3. Ưng rồi thì viết + hội đồng chấm + sửa -> xuất .txt và .docx
python -m novel_agent script write co-be-ban-ve-so

# Chấm/sửa thêm (sau khi bạn tự sửa tay trong project.json), xem trạng thái, xuất lại
python -m novel_agent script revise co-be-ban-ve-so --rounds 1     # --rounds 0 = chỉ chấm, không sửa
python -m novel_agent script status co-be-ban-ve-so
python -m novel_agent script export co-be-ban-ve-so
python -m novel_agent script list

# --auto: không dừng duyệt, viết luôn tới cuối.   --mock: chạy giả lập, không tốn tiền.
```

Mỗi kịch bản nằm trong `data/scripts/<tên>/`: `project.json` (toàn bộ dữ liệu, góp ý từng vòng),
`<tên>.txt` / `.docx` (kịch bản), và **`story-bible.md`** theo đúng mẫu của skill `sw-workflow` -
mở repo bằng Claude Code có plugin screenwriting là có thể nói "làm tiếp kịch bản của tao" và nó đọc được tiến độ.

Mẹo để có kịch bản quay được:
- Ghi rõ ràng buộc sản xuất trong `--notes` (số diễn viên, bối cảnh, ngày quay, ngân sách) - AI sẽ viết cho vừa.
- Dành thời gian ở bước 2 (danh sách cảnh): sửa ở đây rẻ và hiệu quả hơn nhiều so với sửa kịch bản.
- Sau khi có bản cuối, **đọc to cùng diễn viên** trước khi quay - thoại nghe khác hẳn khi đọc thầm.
