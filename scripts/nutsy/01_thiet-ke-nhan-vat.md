# NUTSY: THIẾT KẾ NHÂN VẬT VÀ QUY TRÌNH GEN

## 1. Concept tổng thể

**Một câu:** một chú sóc tự coi mình là James Bond, đấu trí với một đối thủ vô hình trong nhà, trên chiến trường là cái máy ăn chim.

**Hình ảnh:** hoạt hình 3D chất lượng phim chiếu rạp Hollywood, lông mềm, màu bão hòa, ánh sáng điện ảnh. Chuyển động co giãn (squash and stretch) cường điệu, nhịp hài dứt khoát.

**Ngôn ngữ hình khối (shape language):** mỗi nhân vật đọc được ngay chỉ từ bóng đen (silhouette).

| Nhân vật | Hình khối chủ đạo | Ý nghĩa |
|---|---|---|
| Nutsy | **Tam giác + chữ S** (tai nhọn, thân gầy, đuôi chữ S khổng lồ) | Lanh lợi, liều lĩnh, luôn chuyển động |
| Big Red | **Hình tròn / quả lê** (thân tròn, mào nhọn trên đỉnh) | Nặng nề, lì lợm, "bảo vệ hộp đêm" |
| Ba chim sẻ | **Ba quả cầu nhỏ giống hệt nhau** | Một khối đồng thanh, khán giả của phim |
| "Con người" | **Không có hình**, chỉ có đồ vật: ly cà phê trắng, giấy note đỏ, rèm trắng | Phản diện vô hình, tỉnh bơ, thật ra tử tế |

**Bảng màu toàn phim:**

| Màu | Mã | Dùng cho |
|---|---|---|
| Xám sóc | `#8C8F96` | Lông Nutsy |
| Kem bụng | `#F2E6D0` | Bụng Nutsy, lông chim sẻ |
| Xanh lá băng đô | `#5DBB3F` | Chiếc lá, điểm nhận diện của Nutsy |
| Hổ phách | `#E39B2D` | Mắt Nutsy |
| Đỏ hồng y | `#D7263D` | Big Red, **đồng thời là màu giấy note của "con người"** (cố ý: màu đỏ = đối thủ) |
| Nâu sẻ | `#8A5A3B` | Ba chim sẻ |
| Trắng sứ | `#FAFAF7` | Ly cà phê, rèm cửa |
| Xanh trời bình minh | `#FFC8A2` → `#9CD3F0` | Nền sân sau |

---

## 2. Nhân vật

### NUTSY (nhân vật chính)
- **Loài:** sóc xám. **Tính cách:** tự tin thái quá, sĩ diện, thua là cay, nhưng không bao giờ bỏ cuộc.
- **Tỉ lệ:** đầu to, chiếm khoảng 1/3 chiều cao. Thân gầy, tay chân mảnh. Đuôi to bằng cả thân, uốn chữ S, chóp màu bạc.
- **Điểm nhận diện (không bao giờ thay đổi):**
  1. **Băng đô lá xanh** buộc ngang trán.
  2. **Vết khuyết** ở chóp tai trái.
  3. Mắt hổ phách to, bóng.
  4. Hai răng cửa to.
- **Biểu cảm chủ lực:** cười đắc thắng · nheo mắt nghi ngờ · nhìn thẳng máy quay vẻ tỉnh bơ (deadpan) · mặt đỏ tím vì cay · quyết tâm nghiến răng.
- **Động tác đặc trưng:** chạm tay vào tai và "chít chít" như gọi tổng đài · thổi móng tay như cao bồi · chào kiểu nhà binh.
- **Âm thanh:** chỉ có tiếng chít chít, thở, cười. **Không nói tiếng người.**

### BIG RED (đối thủ phụ)
- **Loài:** chim hồng y đỏ (northern cardinal) đực. **Tính cách:** "trùm" máy ăn, lì, chán đời, khinh Nutsy.
- **Tỉ lệ:** gần như hình cầu, béo tròn, mào nhọn cao, mỏ nón màu cam dày.
- **Điểm nhận diện:** mặt nạ đen quanh mắt và mỏ · mí mắt sụp nửa chừng (vẻ mặt "tao không ấn tượng") · ngực ưỡn.

### BA CHIM SẺ (dàn đồng ca)
- **Loài:** chim sẻ nhà, **giống hệt nhau**, bé xíu, tròn.
- **Luật diễn:** luôn đứng thành hàng, **phản ứng cùng lúc**: nghiêng đầu cùng lúc, giơ bảng điểm cùng lúc, chào cùng lúc. Riêng con thứ ba đôi khi làm lệch nhịp để gây cười.

### "CON NGƯỜI" (phản diện vô hình)
- **Tuyệt đối không xuất hiện:** không mặt, không tay, không bóng.
- **Bộ nhận diện:** ly cà phê trắng bốc khói (hơi nước biến thành mặt cười hoặc trái tim) · giấy note đỏ · bút lông đen tự bật nắp · rèm trắng khẽ lay · tiếng nhấp cà phê *xìiii* và tiếng cười khẽ.

---

## 3. Prompt tạo ảnh tham chiếu

Gen ảnh **trước** bằng công cụ tạo ảnh (Gemini / Nano Banana, Imagen, Midjourney…). Chọn ảnh đẹp nhất rồi dùng làm **Ingredients** (ảnh tham chiếu) trong Google Flow, để Veo giữ đúng mặt nhân vật qua 53 shot.

Mỗi nhân vật gen **2 loại ảnh**:
- **(a) Ảnh tham chiếu:** một nhân vật, nền trơn, toàn thân. Đây là ảnh gắn vào Veo.
- **(b) Model sheet:** nhiều góc nhìn và biểu cảm, để mày duyệt thiết kế và làm tài liệu.

### REF-NUTSY (a): ảnh gắn vào Veo
```
A single cartoon character on a plain light grey studio background, full body, three-quarter front view, standing in a confident heroic pose with one paw on hip. NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face, smug grin. High-end Hollywood 3D animated feature film style, soft detailed fur, soft studio lighting, clean and sharp, no text.
```

### Nutsy (b): model sheet
```
Professional character model sheet for a 3D animated feature film, plain white background. The same character shown in a turnaround: front view, three-quarter view, side view, back view, plus a row of six facial expressions: smug grin, suspicious squint, deadpan stare, face red and steaming from spicy food, determined gritted teeth, happy tear. NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Consistent design across all views, soft detailed fur, clean studio lighting, no text labels.
```

### REF-BIGRED (a)
```
A single cartoon character on a plain light grey studio background, full body, three-quarter front view, perched on a short branch with chest puffed out. BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer. High-end Hollywood 3D animated feature film style, soft detailed feathers, soft studio lighting, clean and sharp, no text.
```

### Big Red (b): model sheet
```
Professional character model sheet for a 3D animated feature film, plain white background. The same bird shown front, three-quarter, side and back views, plus four expressions: bored unimpressed, shocked beak wide open, furious puffed up, pitying look. BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes. Consistent design across all views, clean studio lighting, no text labels.
```

### REF-SPARROWS (a)
```
Three identical tiny round cartoon house sparrows standing shoulder to shoulder in a straight row on a plain light grey studio background, full body, front view, heads tilted in the same direction at the same angle. Brown and cream feathers, big curious glossy eyes, round like little balls. High-end Hollywood 3D animated feature film style, soft detailed feathers, soft studio lighting, clean and sharp, no text.
```

### REF-YARD: bối cảnh (tùy chọn, gắn thêm nếu Flow cho phép 3 ảnh)
```
Wide establishing shot of a small suburban backyard for a 3D animated feature film, no characters. An old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, warm cinematic lighting, rich saturated colors, no people, no text.
```

---

## 4. Quy trình làm video (từng bước)

1. **Gen ảnh tham chiếu** (mục 3). Chọn **1 ảnh (a) đẹp nhất cho mỗi nhân vật**, lưu tên `REF-NUTSY.png`, `REF-BIGRED.png`, `REF-SPARROWS.png`.
2. **Mở Google Flow** → chọn **Veo 3.1** → chế độ **Ingredients to Video** → tỉ lệ **16:9**.
   - Muốn đăng Reels/TikTok thì chọn **9:16**. Prompt vẫn dùng được, nhưng nên thêm `vertical 9:16 framing` vào dòng máy quay.
3. **Với từng shot** trong `02_prompt-veo-tung-shot.md`:
   - Gắn các ảnh ở cột **Ref** (shot "Ref: không" thì không gắn ảnh nào, hoặc dùng chế độ Text to Video).
   - Dán nguyên khối prompt → gen **2 phiên bản** → chọn bản tốt nhất.
   - Tải về, đặt tên `S01.mp4`, `S02.mp4`… để dựng theo thứ tự.
4. **Shot khó** (S16, S29 mặt cười bằng hơi nước; S30 iris; S40 né kiểu Matrix): cứ gen 3–4 lần, chọn bản đạt. Nếu vẫn không được thì làm theo ghi chú 📝 bên dưới shot đó.
5. **Dựng trong CapCut / Premiere:**
   - Cắt mỗi clip còn đúng số giây ở cột **Giữ**. Đây là bí quyết nhịp nhanh: thà cắt sớm còn hơn để thừa.
   - **Giữ tiếng SFX của Veo**, tắt mọi nhạc Veo tự thêm. **Nhạc nền mày tự thêm** theo ghi chú 📝 để nhạc liền mạch cả tập.
   - Chèn chữ lên giấy note và bảng điểm lá (Veo viết chữ, nhất là tiếng Việt, rất hay sai).
   - Chèn **tiêu đề NUTSY** sau S08 và **danh đề** sau S51.
6. **Kiểm tra liên tục:** xem lại cả tập, chỗ nào nhân vật lệch thiết kế quá (mất băng đô lá, sai màu) thì gen lại shot đó.

### Mẹo giữ nhân vật đồng nhất
- **Không sửa mô tả nhân vật trong từng prompt.** Nếu muốn đổi thiết kế thì sửa trong `build_prompts.py` rồi chạy lại để mọi prompt đổi cùng lúc.
- Nếu Veo làm mất băng đô lá của Nutsy: thêm câu `He always wears the green leaf bandana.` vào dòng Action.
- Nếu Veo vẫn vẽ ra bàn tay người ở các shot trong nhà (S08, S51): gen lại. Câu "Avoid" đã có sẵn, nếu công cụ có ô **Negative prompt** riêng thì dán dòng Avoid vào đó.
