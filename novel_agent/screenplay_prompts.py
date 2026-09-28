"""Lời nhắn cho chế độ kịch bản phim.

Phương pháp (quy trình giai đoạn, bảng nhịp, các bộ câu hỏi chẩn đoán) được chắt lọc và diễn đạt lại
từ bộ skill jtydhr88/screenwriting-skills (MIT) - vốn tổng hợp McKee, Field, Snyder, Egri, Lục Quân...
"""

SYSTEM = """Bạn là xưởng biên kịch điện ảnh tiếng Việt chuyên nghiệp. Nguyên tắc chung:
- Làm theo đúng thứ tự: tiền đề -> cấu trúc -> nhân vật -> danh sách cảnh -> kịch bản -> sửa. Không nhảy thẳng từ ý tưởng sang viết.
- Mọi cảnh phải có giá trị bị đặt cược và giá trị đó phải đảo chiều trong cảnh; cảnh không đảo chiều là cảnh giải thích, bỏ.
- Nhân vật chính phải tự quyết định và hành động, không chỉ phản ứng. Tổng lực đối kháng phải mạnh hơn nhân vật chính.
- Viết cho màn ảnh: chỉ viết thứ máy quay quay được, diễn viên diễn được. Kịch sợ nhất là giải thích.
- Tôn trọng hồ sơ phát triển (nếu có) như quyết định đã chốt; chỉ đổi khi nhiệm vụ yêu cầu.
Viết toàn bộ bằng tiếng Việt."""

BEAT_TABLE = """Bảng nhịp tham khảo (tỷ lệ theo thời lượng {minutes} phút):
- Hình ảnh mở đầu ~1% (phút {m1}) | Nêu chủ đề ~5% ({m5}) | Sự kiện kích động ~11% ({m11})
- Vào hồi 2 ~23% ({m23}) | Tuyến phụ ~27% ({m27}) | Điểm giữa ~50% ({m50}): chiến thắng giả hoặc thất bại giả
- Mất tất cả ~68% ({m68}): phải là mặt trái của điểm giữa | Đêm đen tâm hồn 68-77% | Vào hồi 3 ~77% ({m77})
- Hình ảnh kết ~100% ({minutes}). Phần dạo đầu <= 25%; hồi cuối ngắn nhất.
{short}"""

SHORT_FILM = """Đây là PHIM NGẮN: dùng khởi - thừa - chuyển - hợp làm xương sống thay cho đủ 15 nhịp.
- Khởi: rất ngắn, xung đột nổ ngay, vào truyện gần cao trào (gần chứ không xa, gọn chứ không rườm, động chứ không tĩnh).
- Thừa: ~2/3 phim, từng bước leo thang, có hãm có buông.
- Chuyển: cao trào, tính cách và chủ đề sâu nhất ở đây.
- Hợp: chuyển xong là hợp ngay, ngắn và còn dư vị.
Tối đa 5 nhân vật; lõi kịch phải có trước tiên; khoảng 10-15 cảnh."""

DEVELOP_TASK = """Phát triển dự án phim sau đến hết giai đoạn cấu trúc và nhân vật.

Ý tưởng của tác giả:
{idea}

- Thể loại: {genre}
- Thời lượng: {minutes} phút
- Yêu cầu thêm: {notes}

{beats}

Cách làm:
1. Tiền đề: chỉ MỘT tiền đề (tính cách -> dẫn tới -> kết cục); tư tưởng chủ đạo; lõi kịch; khát vọng và niềm tin sai lầm.
2. Quyết định KẾT PHIM trước, rồi mở đầu, sự kiện kích động, các điểm ngoặt. Cao trào phải "tất yếu mà bất ngờ",
   có hình ảnh chủ đạo. Tránh: không có cao trào, cao trào quá sớm, cao trào trượt, cao trào gượng (quỳ gối, tát, bỏ nhà vô cớ).
   Kết tránh: quá tròn, quá lê thê, nhảy cóc, gượng ép.
3. Nhân vật: bảng ba chiều cho mỗi nhân vật chính; nhân vật chính nhiều chiều nhất; không hai nhân vật cùng kiểu;
   đối thủ có câu chuyện và mục tiêu riêng liên quan chủ đề; cho đối thủ ít nhất một con dao; không có "phép màu cứu nguy".
4. Bảng nhịp theo phút cho đúng thời lượng."""

OUTLINE_TASK = """Lập DANH SÁCH CẢNH (step outline) cho phim ở trên, tổng thời lượng khoảng {minutes} phút ({seconds} giây).

Mỗi cảnh: tiêu đề cảnh, một câu (ai làm gì, kết quả khác dự tính ra sao), giá trị mở -> đóng (phải đảo chiều),
xung đột (ai muốn gì, ai cản, ai thắng), vị trí cấu trúc, thời lượng giây.
- Vào muộn ra sớm; rời cảnh trước khi xung đột được giải quyết hẳn.
- Mỗi cảnh chỉ một xung đột chính; hai cảnh liền nhau có yếu tố chuyển tiếp (đồ vật, âm thanh, hành động, câu nói).
- Chọn bối cảnh làm xung đột khó hơn, nhân vật lộ rõ hơn - "vì sao ở đây, lúc này".
- Hồi cuối không được chỉ có một hai cảnh. Tổng giây gần đúng thời lượng yêu cầu."""

OUTLINE_REVIEW_TASK = """NHIỆM VỤ - BIÊN TẬP CẤU TRÚC: Kiểm tra hồ sơ phát triển và danh sách cảnh ở trên TRƯỚC khi viết kịch bản.
Trả lời từng câu, câu nào không đạt thì ghi thành lỗi (ghi số cảnh liên quan):
1. Nói được phim kể về gì trong 1-2 câu? Biết kết, mở, hai điểm ngoặt? Điểm giữa và "mất tất cả" là mặt trái của nhau?
2. Nhân vật chính TỰ quyết định bước vào hồi 2? Hành động hay chỉ phản ứng?
3. Mỗi cảnh giá trị mở và đóng có khác nhau? Cảnh nào chỉ để giải thích?
4. Hồi 2 có leo thang thật, không lặp quy mô hồi 1? Sau điểm giữa có tăng tốc?
5. Lực đối kháng có mạnh hơn nhân vật chính? Đối thủ có dao?
6. Tuyến phụ quan hệ với tư tưởng chủ đạo thế nào? Không có thì là truyện rời rạc.
7. Hồi cuối ngắn nhất? Cao trào không sớm, không trượt, không gượng? Chuyển biến không nhờ "cấp trên", không bàn tay vô hình, không xử lý sau cánh gà?
8. Có ít nhất 5-6 thay đổi rõ, chủ yếu sinh ra từ tính cách?
9. Tổng thời lượng các cảnh có khớp yêu cầu?
Chấm 0-10 (8 = đủ để viết)."""

OUTLINE_REVISE_TASK = """NHIỆM VỤ - SỬA DANH SÁCH CẢNH theo góp ý dưới đây. Được thêm, bớt, gộp, đổi thứ tự cảnh;
đánh số lại liên tục từ 1. Giữ tiền đề, kết phim và nhân vật đã chốt trừ khi góp ý chỉ ra lỗ hổng ở đó.

{feedback}"""

FORMAT_RULES = """Thể thức kịch bản (đánh số cảnh kiểu Việt Nam, văn bản thuần):
CẢNH 12. NGOẠI. BẾN XE MIỀN TÂY - ĐÊM
Đoạn hành động: thì hiện tại, câu ngắn (<= 15 chữ), động từ cụ thể, không thuật ngữ máy quay, không "chúng ta thấy",
không tả nội tâm không quay được ("cô nhớ lại", "anh nhận ra"). Nhân vật lần đầu xuất hiện: VIẾT HOA TÊN (tuổi) + một hành động đặc trưng.
Thoại: TÊN NHÂN VẬT: lời thoại. Chỉ dẫn diễn xuất trong ngoặc đặt sau tên, tối đa 3 chữ, gần như không dùng: LAN (khẽ): ...
Giọng ngoài khung hình: TÊN (ngoài hình): ... | lời dẫn: TÊN (lời dẫn): ... | chữ trên màn hình: CHỮ: ...
Không viết "CẮT SANG", không ghi chú. Hồi tưởng thêm "(HỒI TƯỞNG)" cuối dòng tiêu đề.
Khoảng 1 trang (~180-220 chữ) cho 1 phút phim."""

DIALOGUE_RULES = """Thoại:
- Dưới mỗi câu thoại là một hành động (nhân vật muốn gì, dùng chiến thuật gì). Không trả lời được thì bỏ câu đó.
- Che tên vẫn đoán ra ai nói. Không nhân vật nào kể cho người kia điều cả hai đã biết, trừ khi dùng làm vũ khí.
- Không nói thẳng ẩn ý ("anh yêu em" dưới ánh nến là không diễn được). Hai người không bao giờ đồng ý hoàn toàn.
- Không "này", "à", "ừm" vô nghĩa, không dấu chấm than, không phiên âm giọng địa phương; giữ xưng hô tiếng Việt nhất quán theo quan hệ.
- Hỏi trước: cảnh này có thể KHÔNG cần thoại không? Một cái tháo nhẫn thay cả trang thoại."""

DRAFT_TASK = """NHIỆM VỤ - BIÊN KỊCH: Viết kịch bản cho các cảnh {first}-{last} theo danh sách cảnh ở trên
(giữ đúng số cảnh và tiêu đề; chi tiết có thể tinh chỉnh nếu làm cảnh mạnh hơn).

{format_rules}

{dialogue_rules}

Mỗi cảnh: vào muộn ra sớm; giá trị phải đảo chiều qua hành động hoặc phát hiện; kết cảnh bằng một hành động
hoặc một chữ đắt. Độ dài theo số giây ghi ở từng cảnh.
Chỉ trả về văn bản kịch bản của các cảnh {first}-{last}, mỗi cảnh bắt đầu bằng dòng "CẢNH <số>. ..."."""

CRITICS = {
    "structure": {
        "name": "Biên tập cấu trúc",
        "checklist": """1. Mười phút đầu đã giới thiệu nhân vật chính, tiền đề, tình thế? Sự kiện kích động có đến quá muộn?
2. Nhân vật chính tự quyết bước vào hồi 2? Hành động hay chỉ phản ứng?
3. Hồi 2 leo thang thật? Điểm giữa và "mất tất cả" là mặt trái nhau? Sau điểm giữa có tăng tốc?
4. Cao trào tất yếu mà bất ngờ, có hình ảnh chủ đạo? Không sớm, không trượt, không gượng?
5. Chuyển biến không nhờ "cấp trên", phép màu, xử lý sau cánh gà, tình cờ phát hiện huyết thống?
6. Kết không quá tròn, không lê thê, không nhảy cóc, không gượng? Hồi cuối ngắn nhất?
7. Điều được báo trước ở đầu phim, cuối phim có được trả (hoặc cố ý không trả)?"""},
    "character": {
        "name": "Biên tập nhân vật",
        "checklist": """1. Nhân vật chính có khát vọng lớn hơn cả mạng sống, đang ở thời khắc nguy cấp? Hành động hay chỉ hỏi han?
2. Nhân vật chính và đối thủ bị trói vào nhau không thể thoả hiệp? Đối thủ mạnh hơn, có câu chuyện riêng?
3. Xung đột leo thang (tấn công - phản công - leo thang), không đứng yên, không nhảy cóc?
4. Mỗi nhân vật có cách làm riêng? Lần đầu xuất hiện đúng lúc tính cách và xung đột cần?
5. Chuyển biến có quá trình, không "thử một lần là tỉnh ngộ"? Nhân vật chính tự tay thắng (hoặc thua)?
6. Có hiểu lầm tuỳ tiện, né tránh, đánh trống bỏ dùi không?
7. Cuối phim thấy được đời nhân vật chính sẽ khác?"""},
    "scene": {
        "name": "Biên tập cảnh",
        "checklist": """1. Vì sao ở đây, lúc này? Bối cảnh khác có làm xung đột khó hơn không?
2. Giá trị mở - đóng của từng cảnh có đảo chiều? Cảnh nào không đổi là cảnh giải thích.
3. Mỗi người muốn gì, dùng chiến thuật gì? Đối kháng trực diện hay lướt qua nhau?
4. Có nhịp (beat) lặp lại không? Điểm ngoặt là hành động hay phát hiện, đến đúng lúc?
5. Vào đủ muộn, ra đủ sớm? Có đoạn "không có gì xảy ra" (cạo râu, tán gẫu, gọi món)?
6. Có đạo cụ/chi tiết đắt, nhìn thấy được, lặp lại có phát triển? Cảnh liền nhau có yếu tố chuyển tiếp?
7. Hồi hộp: khán giả biết nhiều hay ít hơn nhân vật, có trao "chìa khoá" cho khán giả? Gần cao trào cảnh có ngắn dần?"""},
    "dialogue": {
        "name": "Biên tập thoại",
        "checklist": """1. Dưới mỗi câu thoại là hành động gì? Câu không có hành động thì bỏ.
2. Che tên có đoán ra ai nói? Xưng hô tiếng Việt đúng quan hệ và nhất quán?
3. Có ai kể cho người kia điều cả hai đã biết (không dùng làm vũ khí)?
4. Có nói thẳng ẩn ý không? Hai người có lúc nào đồng ý hoàn toàn (nhàm)?
5. Cùng một nhịp lặp mấy lần? Diễn văn dài có câu nào không mang thông tin mới?
6. Có từ đệm vô nghĩa, dấu chấm than, phiên âm giọng địa phương, chỉ dẫn diễn xuất thừa?
7. Cảnh này có thể không cần thoại? Câu sáo rỗng có phải lựa chọn đầu tiên?"""},
    "format": {
        "name": "Biên tập thể thức",
        "checklist": """1. Dòng tiêu đề cảnh đủ: CẢNH số. NỘI/NGOẠI. ĐỊA ĐIỂM - NGÀY/ĐÊM, thống nhất toàn kịch bản?
2. Hành động: thì hiện tại, câu ngắn, động từ cụ thể, không thuật ngữ máy quay, không "chúng ta thấy", không nội tâm không quay được, không câu phủ định kiểu "không trả lời"?
3. Mỗi đoạn hành động chiếm bao nhiêu giây trên màn hình, có đáng tiền không?
4. Nhân vật lần đầu: tên viết hoa, tuổi, một hành động đặc trưng; không tiểu sử dài?
5. Thoại đúng dạng TÊN: lời; chỉ dẫn trong ngoặc <= 3 chữ; ngoài hình / lời dẫn dùng nhất quán?
6. Không "CẮT SANG", không ghi chú, không lẫn hai thể thức? Tổng độ dài khớp thời lượng?"""},
}

CRITIC_TASK = """NHIỆM VỤ - {name}: Đọc toàn bộ KỊCH BẢN ở trên và chẩn đoán theo bộ câu hỏi:
{checklist}

Mỗi câu không đạt ghi thành một lỗi: số cảnh liên quan, câu hỏi nào, vấn đề, cách sửa cụ thể.
critical = phá cấu trúc / logic phim, bắt buộc sửa; major = ảnh hưởng rõ; minor = nên sửa.
Chấm 0-10 (8 = đủ đem đi quay thử). Công tâm, không khen xã giao, không bới lỗi vụn."""

REVISE_TASK = """NHIỆM VỤ - SỬA KỊCH BẢN theo góp ý của hội đồng:

{feedback}

- Chỉ trả về các cảnh cần sửa, mỗi cảnh viết lại TOÀN VĂN (giữ số cảnh). Sửa hết critical và major.
- Nếu góp ý mâu thuẫn: ưu tiên cấu trúc, rồi nhân vật, rồi cảnh, rồi thoại, cuối cùng thể thức.
- Giữ tiền đề, kết phim và những gì đang tốt.

{format_rules}"""
