# NUTSY: PROMPT VEO TỪNG SHOT

Mỗi shot là **một lần gen Veo, 8 giây, tỉ lệ 16:9**. Copy nguyên khối code dán vào Veo.
Cột **Giữ** là số giây nên giữ lại khi dựng (Veo gen 8 giây, cắt bớt cho nhịp nhanh).
**Ref** là ảnh tham chiếu cần gắn (xem `01_thiet-ke-nhan-vat.md`).

> File này được sinh tự động từ `build_prompts.py`. Muốn sửa mô tả nhân vật hay bối cảnh thì sửa ở đó rồi chạy lại.

## Tổng quan

| Shot | Nội dung | Giữ | Ref |
|---|---|---|---|
| | **MỞ MÀN: PHI VỤ HOÀN HẢO** | | |
| S01 | Toàn cảnh sân sau, máy ăn chim lấp lánh | 5s | REF-BIGRED, REF-SPARROWS |
| S02 | Con mắt sau bụi cây | 2s | REF-NUTSY |
| S03 | Nutsy chuẩn bị đồ nghề | 4s | REF-NUTSY |
| S04 | Zipline trên dây phơi | 5s | REF-NUTSY |
| S05 | Slow-motion: chạm mắt với Big Red | 4s | REF-NUTSY, REF-BIGRED |
| S06 | Cướp sạch máy ăn | 5s | REF-NUTSY, REF-BIGRED, REF-SPARROWS |
| S07 | Tẩu thoát kiểu cao bồi | 6s | REF-NUTSY |
| S08 | Trong nhà: tờ note đỏ | 5s | không |
| | **PHẦN 1: CÁI CHUÔNG CẤM** | | |
| S09 | Quả sồi trượt khỏi cành bọc nhựa | 5s | REF-NUTSY |
| S10 | Nutsy nhìn thẳng vào máy quay | 3s | REF-NUTSY |
| S11 | Leo cột thần tốc | 3s | REF-NUTSY |
| S12 | BONG! Đâm đầu vào chuông | 4s | REF-NUTSY |
| S13 | Trượt vòng quanh chuông rồi văng ra | 5s | REF-NUTSY |
| S14 | Dính vào hàng rào hình chữ X | 4s | REF-NUTSY |
| S15 | Ba chim sẻ chấm điểm | 3s | REF-SPARROWS |
| S16 | Hơi cà phê thành mặt cười | 3s | không |
| S17 | Nutsy nghi ngờ nhìn lên cửa sổ | 4s | REF-NUTSY |
| S18 | Kế hoạch B phản chiếu trong mắt | 3s | REF-NUTSY |
| | **PHẦN 2: MONTAGE BẪY** | | |
| S19 | Bẫy 1: lò xo slinky thả xuống từ từ | 6s | REF-NUTSY |
| S20 | Lò xo phóng Nutsy lên trời | 4s | REF-NUTSY |
| S21 | Bẫy 2: rơi trúng máy ăn, cười đắc thắng | 3s | REF-NUTSY |
| S22 | Máy ăn quay tít, ném búa | 7s | REF-NUTSY, REF-BIGRED |
| S23 | Bẫy 3: máy ăn thứ hai quá dễ | 5s | REF-NUTSY |
| S24 | Mặt đổi màu, tai phun khói | 5s | REF-NUTSY |
| S25 | Big Red ăn ớt tỉnh bơ | 4s | REF-NUTSY, REF-BIGRED |
| S26 | Cắm đầu xuống bồn tắm chim | 4s | REF-NUTSY |
| S27 | Bẫy 4: cải trang thành chim | 6s | REF-NUTSY, REF-SPARROWS |
| S28 | Cửa chắn sập, rứt lông giảm cân | 7s | REF-NUTSY |
| S29 | Chấm điểm và mặt cười nháy mắt | 4s | REF-SPARROWS |
| S30 | Iris-out bị kéo mở lại | 5s | REF-NUTSY |
| | **PHẦN 3: PHÒNG CHIẾN LƯỢC** | | |
| S31 | Hang sóc, bảng điều tra chỉ đỏ | 5s | REF-NUTSY |
| S32 | Dàn trận bằng quả sồi | 4s | REF-NUTSY |
| S33 | Chế máy bắn đá bằng thìa | 3s | REF-NUTSY |
| S34 | Dù lượn chiếc tất, kính nắp chai | 3s | REF-NUTSY |
| S35 | Tấm gương bí ẩn, nhìn thẳng máy quay | 4s | REF-NUTSY |
| S36 | Đèn cửa sổ tắt phụt | 3s | không |
| | **PHẦN 4: PHI VỤ CUỐI CÙNG** | | |
| S37 | Thử gió, chào nhà binh | 6s | REF-NUTSY, REF-SPARROWS |
| S38 | Cất cánh slow-motion | 6s | REF-NUTSY |
| S39 | Né chuông gió | 5s | REF-NUTSY |
| S40 | Vòi tưới bật, né kiểu Matrix | 6s | REF-NUTSY |
| S41 | Big Red rượt đuổi trên không | 6s | REF-NUTSY, REF-BIGRED |
| S42 | Tấm gương: Big Red đánh nhau với chính mình | 6s | REF-NUTSY, REF-BIGRED |
| S43 | Hạ cánh. Im lặng. Giọt nước mắt hạnh phúc | 6s | REF-NUTSY |
| S44 | Tay xuyên qua tấm bìa | 6s | REF-NUTSY |
| S45 | Rơi slow-motion vào thùng | 4s | REF-NUTSY |
| | **KẾT: HIỆP ƯỚC HÒA BÌNH** | | |
| S46 | Mở mắt giữa kho báu | 5s | REF-NUTSY |
| S47 | Cửa sổ đáp lời | 4s | không |
| S48 | Nutsy chào lại đối thủ | 4s | REF-NUTSY |
| S49 | Toàn cảnh yên bình | 6s | REF-NUTSY, REF-BIGRED, REF-SPARROWS |
| S50 | …nhưng mà | 7s | REF-NUTSY |
| S51 | KẾ HOẠCH Z | 5s | không |
| | **CẢNH SAU DANH ĐỀ** | | |
| S52 | Chim sẻ trộm hạt của Nutsy | 5s | REF-SPARROWS |
| S53 | Nutsy thành 'con người' | 6s | REF-NUTSY |

**53 shot**, sau khi cắt còn khoảng **4 phút 8 giây** chưa tính tiêu đề và danh đề.

---

## MỞ MÀN: PHI VỤ HOÀN HẢO

### S01: Toàn cảnh sân sau, máy ăn chim lấp lánh

**Giữ:** 5s · **Ref:** REF-BIGRED, REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Slow crane shot descending from the apple tree canopy to the bird feeder, which sparkles in the dawn light like a jewel in a museum.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: BIG RED and THE THREE SPARROWS peck sunflower seeds peacefully at the feeder; seeds tinkle as they fall.

SFX: gentle birdsong, seeds tinkling. Ambient: quiet dawn breeze.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc nền: chuỗi đàn dây trầm, hồi hộp kiểu phim điệp viên (thêm khi dựng).

### S02: Con mắt sau bụi cây

**Giữ:** 2s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Extreme close-up, sudden fast snap zoom in.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: Between dark green bush leaves, one huge amber squirrel eye of NUTSY peers out, pupil narrowing with determination.

SFX: a sharp whoosh on the zoom, leaves rustle.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S03: Nutsy chuẩn bị đồ nghề

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Series of tight close-ups, low angle, dramatic side light.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: NUTSY tightens the green leaf bandana on his forehead with a sharp tug, smears two stripes of mud under his eyes with his thumb like a commando, then presses a paw to his ear and chitters secretly as if talking into an earpiece.

SFX: leaf snap, wet mud smear, squirrel chittering whisper.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S04: Zipline trên dây phơi

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Dynamic tracking shot following alongside, fast.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: NUTSY hangs from a wooden clothespin and zips down the clothesline across the backyard at high speed toward the bird feeder, fur and tail streaming in the wind, grinning with confidence.

SFX: zipping whirr of the clothespin on the line, wind rush.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S05: Slow-motion: chạm mắt với Big Red

**Giữ:** 4s · **Ref:** REF-NUTSY, REF-BIGRED

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Extreme slow motion, side profile, camera tracking with NUTSY.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: NUTSY flies past right in front of BIG RED's face mid-air. They lock eyes. BIG RED's beak drops open in shock and a single sunflower seed slowly falls from it.

SFX: slowed-down deep whoosh, a single seed drop echoing.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S06: Cướp sạch máy ăn

**Giữ:** 5s · **Ref:** REF-NUTSY, REF-BIGRED, REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot at normal speed, handheld energy.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: NUTSY lands on the bird feeder and stuffs seeds into his cheeks until they bulge like two balloons, while BIG RED and THE THREE SPARROWS scatter in an explosion of feathers.

SFX: rapid chomping, cheeks stretching squeak, panicked bird chirps and wing flaps.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S07: Tẩu thoát kiểu cao bồi

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Low angle on the lawn, then tilt up to the empty feeder.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Early dawn, soft golden-pink backlight, light mist over the grass.

Action: NUTSY drops to the grass, does a stylish roll, stands, blows on his claws like a cowboy blowing on a smoking gun, and dashes off frame. The camera tilts up to the empty feeder swaying gently as a single red cardinal feather drifts down in slow motion.

SFX: roll thump, cheeky blow, zip of a fast exit, feeder creak.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: MATCH CUT từ chiếc lông đỏ đang rơi sang tờ note đỏ đang rơi (S08).

### S08: Trong nhà: tờ note đỏ

**Giữ:** 5s · **Ref:** không

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static close-up at table height.

Setting: interior, camera at table-top height on a warm wooden kitchen table, a pad of red sticky notes, a black marker and a steaming white coffee mug, morning light from a window. The frame is cropped at table height so no person is ever visible.

Action: A single red sticky note flutters down from above and lands softly on the wooden table next to the black marker and the steaming coffee mug. The marker cap pops off by itself with a click.

SFX: paper flutter, marker cap click, off-screen marker scribbling, then a long satisfied off-screen sip of hot coffee.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: chèn chữ viết tay lên tờ note: 'SÓC. KẾ HOẠCH A.' Sau S08 cắt đen và chèn TIÊU ĐỀ 'NUTSY' + SFX 'BOING!' (làm trong CapCut, không cần Veo).

---

## PHẦN 1: CÁI CHUÔNG CẤM

### S09: Quả sồi trượt khỏi cành bọc nhựa

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium wide shot from the lawn.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY fires an acorn tied to a string with a tiny twig slingshot at the feeder branch, but the branch is now wrapped in a shiny slippery plastic tube. The acorn slides straight off and the string falls in loops onto NUTSY's head.

SFX: slingshot twang, plastic squeak, slide, soft plop of string.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S10: Nutsy nhìn thẳng vào máy quay

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static close-up, centered, deadpan comedic framing.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY, with string draped over his head, slowly looks at the string, then turns and stares directly into the camera, blinking twice in silence.

SFX: silence, two tiny blink sounds, a single cricket chirp.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S11: Leo cột thần tốc

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Low angle looking up the green metal pole, fast.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY scrambles up the green metal feeder pole at blurring cartoon speed, claws clicking on metal.

SFX: rapid claw scratching on metal.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S12: BONG! Đâm đầu vào chuông

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Close-up at the top of the pole.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY's head slams into a large clear plastic dome baffle mounted on top of the pole. BONG. His whole body vibrates rapidly like a tuning fork, eyes rattling, teeth chattering.

SFX: a huge resonant church-bell BONG, trembling vibration hum.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S13: Trượt vòng quanh chuông rồi văng ra

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot, camera circling slightly.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY clings to the rim of the clear dome baffle, the baffle tilts, and he slides around and around it like a spinning vinyl record, faster and faster, until he is flung off to the side.

SFX: squeaky spinning, rising whirl, launch whoosh.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S14: Dính vào hàng rào hình chữ X

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Whip pan following NUTSY across the yard, landing on the fence.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY flies across the backyard and splats flat against the white picket fence, spread-eagle in an X shape, then slowly slides down the boards to the grass.

SFX: whip whoosh, cartoon SPLAT, slow wood squeak slide.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S15: Ba chim sẻ chấm điểm

**Giữ:** 3s · **Ref:** REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static medium shot, the three birds perfectly centered in a row on the fence.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: THE THREE SPARROWS on the fence each raise a large green leaf above their heads at the exact same moment, like judges holding up scorecards.

SFX: three synchronized leaf rustles, a tiny chirp in unison.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: chèn số lên 3 chiếc lá: 7 – 8 – 6.

### S16: Hơi cà phê thành mặt cười

**Giữ:** 3s · **Ref:** không

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static close-up on the coffee mug on the windowsill.

Setting: exterior close view of the back window of a cozy house, white curtains behind the glass, a steaming white coffee mug sitting on the outside windowsill. Nobody visible inside, only the curtains.

Action: The steam rising from the coffee mug curls and swirls into the shape of a smiley face, while the white curtain behind the glass sways slightly.

SFX: soft off-screen chuckle behind the glass, a gentle sip.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Đây là running gag, dùng lại ở S29. Nếu Veo không vẽ ra mặt cười thì gen lại 2–3 lần.

### S17: Nutsy nghi ngờ nhìn lên cửa sổ

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up, low angle, then slow push-in on his eye.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY stands up, dusts himself off, and squints suspiciously up toward the house window. The camera pushes slowly into his narrowed eye.

SFX: dust pats, a low suspicious hum.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: zoom xuyên vào mắt để nối sang S18.

### S18: Kế hoạch B phản chiếu trong mắt

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Extreme macro close-up of the squirrel eye.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: In the glossy amber eye of NUTSY, a chalk-drawn blueprint of the bird feeder with arrows and circles appears as a reflection, glowing faintly.

SFX: chalk scratching, a sly musical sting.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

---

## PHẦN 2: MONTAGE BẪY

### S19: Bẫy 1: lò xo slinky thả xuống từ từ

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot of the pole, locked-off camera.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: A metal slinky spring toy now wraps the green feeder pole. NUTSY grabs it and starts climbing, but the slinky stretches and gently lowers him back down to the grass like a slow elevator, boing, boing. He tries again with the same result, his face getting grumpier.

SFX: metallic slinky boing boing, grumpy squirrel grunt.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc nền montage: kèn đồng và trống nhanh, kiểu montage tập luyện (thêm khi dựng).

### S20: Lò xo phóng Nutsy lên trời

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Low angle looking up, camera tilting fast to follow him into the sky.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: On the third attempt the slinky compresses fully and launches NUTSY straight up into the blue sky like a rocket, until he becomes a tiny dot with a twinkle.

SFX: a massive spring BOING, rocket whoosh, tiny twinkle ding.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: MATCH CUT theo chuyển động, bay lên ở S20 rồi rơi xuống ở S21.

### S21: Bẫy 2: rơi trúng máy ăn, cười đắc thắng

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Looking down from above the tube feeder, NUTSY falls from the sky toward camera.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY drops out of the sky and lands perfectly clinging to the tube bird feeder, then flashes a huge triumphant grin.

SFX: falling whistle, clunk landing, confident chuckle-chitter.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S22: Máy ăn quay tít, ném búa

**Giữ:** 7s · **Ref:** REF-NUTSY, REF-BIGRED

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot, camera spinning slightly with the motion.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: The feeder's motorized perch ring suddenly spins at high speed. NUTSY whirls around like an Olympic hammer thrower, cheeks flapping from the force, seeds shooting out of his cheeks like a machine gun at BIG RED who ducks and dodges. NUTSY loses his grip and is flung out of frame to the right.

SFX: electric motor whine rising, rapid seed rat-a-tat-tat, BIG RED squawk, launch whoosh.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: bay ra mép phải, sang S23 thì lao vào từ mép trái.

### S23: Bẫy 3: máy ăn thứ hai quá dễ

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot, NUTSY tumbles in from the left edge of frame.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY tumbles into frame from the left and lands on an open wooden tray feeder piled high with seeds that have a faint red coating, with no guards at all. He looks around suspiciously left and right, then shrugs and stuffs his face greedily.

SFX: tumble thuds, suspicious sniffing, greedy chomping.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S24: Mặt đổi màu, tai phun khói

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Close-up on his face, static.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY freezes mid-chew. His face slowly turns from grey to pink to red to deep purple, his eyes water, and jets of steam whistle out of both ears like a boiling kettle.

SFX: rising kettle whistle, sizzle, strained squeak.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyện có thật: chim không cảm nhận được vị cay, còn sóc thì có.

### S25: Big Red ăn ớt tỉnh bơ

**Giữ:** 4s · **Ref:** REF-NUTSY, REF-BIGRED

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Two-shot, medium.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: BIG RED lands next to the steaming NUTSY, calmly crunches the same red-coated seeds with total ease, and gives him a slow pitying look.

SFX: loud calm crunching, NUTSY's whistling ears continue.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S26: Cắm đầu xuống bồn tắm chim

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Wide shot, then the frame fills with white steam.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY rockets across the lawn and dives head-first into the stone bird bath. A giant hiss of steam erupts and fills the entire frame with white.

SFX: rocket whoosh, splash, massive steam HISS.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: màn hơi nước trắng tan ra thành S27.

### S27: Bẫy 4: cải trang thành chim

**Giữ:** 6s · **Ref:** REF-NUTSY, REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

White steam clears to reveal a medium shot on the lawn.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY is now disguised as a bird, with feathers glued all over his body and an acorn cap strapped on as a fake beak, hopping bird-style toward a metal bird feeder with a weight-activated perch. THE THREE SPARROWS tilt their heads at him in perfect unison.

SFX: steam fading, light bird-like hops, three puzzled chirps.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S28: Cửa chắn sập, rứt lông giảm cân

**Giữ:** 7s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up on the feeder perch.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: NUTSY steps onto the perch and a metal shutter slams down over the seed ports. CLACK. He tries tiptoeing, standing on one leg, holding his breath: clack, clack. He plucks off his glued feathers one by one to lose weight until the last one is gone, and the shutter stays shut. He stands there bare, tail drooping.

SFX: metal shutter CLACK repeated, feather plucks, deflated sigh.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S29: Chấm điểm và mặt cười nháy mắt

**Giữ:** 4s · **Ref:** REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static medium shot on the fence, centered.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: THE THREE SPARROWS raise their leaf scorecards in unison, then the third sparrow flips his leaf around to show the other side.

SFX: synchronized leaf rustles, a tiny judging chirp.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: số 2 – 1 – 0, mặt sau lá con thứ ba ghi 'KHÔNG'. Chèn 1 giây S16 với mặt cười NHÁY MẮT (gen lại S16, thay 'smiley face' bằng 'winking smiley face').

### S30: Iris-out bị kéo mở lại

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Close-up on NUTSY's dejected face with a classic cartoon black iris vignette closing in.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Bright sunny morning, crisp shadows, dew on the grass.

Action: A black circular iris closes in around NUTSY's sad face. Just before it shuts, NUTSY frowns with determination, reaches out with both paws, grabs the edge of the black circle and pulls it wide open again.

SFX: cartoon iris swoosh, then a stretching rubber sound as he pulls it open.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nếu Veo làm hỏng: gen Nutsy mặt buồn chuyển sang quyết tâm, rồi làm iris trong CapCut.

---

## PHẦN 3: PHÒNG CHIẾN LƯỢC

### S31: Hang sóc, bảng điều tra chỉ đỏ

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Slow dolly along the evidence wall, moody noir lighting from the swinging firefly lamp.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped under an upturned bottle cap swinging from a string like an interrogation lamp, the curved wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a detective's evidence board, a dirt floor map of the backyard with acorns on it.

Action: NUTSY paces back and forth in front of the wall of feeder photos and red strings, stroking his chin, the firefly lamp swinging and throwing moving shadows.

SFX: creaking string of the swinging lamp, soft footsteps, firefly buzz.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: trầm, bí ẩn kiểu phim trinh thám.

### S32: Dàn trận bằng quả sồi

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

High angle over the dirt floor map.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped under an upturned bottle cap swinging from a string like an interrogation lamp, the curved wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a detective's evidence board, a dirt floor map of the backyard with acorns on it.

Action: NUTSY moves acorns across the dirt map of the backyard with a twig like a war general, then draws a big swooping flight arrow in the dirt.

SFX: acorns clicking, twig scraping dirt.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S33: Chế máy bắn đá bằng thìa

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Quick close-up, energetic.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped under an upturned bottle cap swinging from a string like an interrogation lamp, the curved wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a detective's evidence board, a dirt floor map of the backyard with acorns on it.

Action: NUTSY ties a white plastic spoon to a bent green sapling with grass string, pulls it back and tests the spring.

SFX: grass knot tightening, woody creak, springy twang.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: trống nhanh kiểu montage chế tạo. Cắt S33, S34, S35 thật nhanh, mỗi đoạn 2–3 giây.

### S34: Dù lượn chiếc tất, kính nắp chai

**Giữ:** 3s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Quick close-up, energetic.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped under an upturned bottle cap swinging from a string like an interrogation lamp, the curved wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a detective's evidence board, a dirt floor map of the backyard with acorns on it.

Action: NUTSY stretches an old striped sock over a frame of crossed twigs to make a tiny hang glider, then puts on goggles made of two bottle caps.

SFX: fabric stretch, twig snaps into place, goggle strap snap.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S35: Tấm gương bí ẩn, nhìn thẳng máy quay

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up, then he looks straight into the lens.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped under an upturned bottle cap swinging from a string like an interrogation lamp, the curved wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a detective's evidence board, a dirt floor map of the backyard with acorns on it.

Action: NUTSY holds up a small round mirror, taps it knowingly and nods mysteriously. Then he pulls the bottle-cap goggles down over his eyes with a snap and stares directly into the camera.

SFX: mirror tap ting, goggle SNAP.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Chuyển cảnh: MATCH CUT bằng âm thanh, tiếng tách của kính thành tiếng tách công tắc đèn (S36).

### S36: Đèn cửa sổ tắt phụt

**Giữ:** 3s · **Ref:** không

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static wide shot.

Setting: exterior of the house at night seen from the apple tree, one warm glowing window among dark blue night tones, crickets, fireflies.

Action: The single glowing window of the house clicks off, leaving the house dark under the night sky.

SFX: a crisp light switch CLICK, crickets.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

---

## PHẦN 4: PHI VỤ CUỐI CÙNG

### S37: Thử gió, chào nhà binh

**Giữ:** 6s · **Ref:** REF-NUTSY, REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Heroic low angle on NUTSY standing on the plastic spoon catapult.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: Wearing the bottle-cap goggles with the sock glider strapped on his back, NUTSY licks a finger and holds it up to test the wind, then gives a crisp military salute to THE THREE SPARROWS on the fence. The sparrows salute back by reflex in unison, then awkwardly lower their wings.

SFX: finger lick, wind gust, crisp salute swish, embarrassed tiny chirps.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: chủ đề điệp viên quay lại, dàn nhạc đầy đủ, nhịp gấp đôi.

### S38: Cất cánh slow-motion

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Extreme slow motion, camera rising with him against the sun.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY bites through the grass string, the spoon catapult snaps and launches him into the air. In slow motion the striped sock glider unfurls above him and he soars heroically, backlit by the rising sun with a lens flare.

SFX: string snap, catapult THWACK, slowed epic wind.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: hợp xướng hùng tráng (thêm khi dựng).

### S39: Né chuông gió

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Tracking shot flying with NUTSY, alternating slow motion and normal speed.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY glides through a hanging set of metal wind chimes, twisting and dodging as each chime tube swings past just millimeters from his nose.

SFX: wind chimes clinking, near-miss whooshes.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S40: Vòi tưới bật, né kiểu Matrix

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Dynamic slow-motion orbiting camera.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: Lawn sprinklers suddenly burst on beneath him. NUTSY twists and rolls in mid-air to dodge each glittering jet of water like laser beams, finishing with an extreme backward bend as a jet passes over him in bullet-time slow motion.

SFX: sprinkler hiss bursts, slowed water whoosh, bullet-time bass drop.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S41: Big Red rượt đuổi trên không

**Giữ:** 6s · **Ref:** REF-NUTSY, REF-BIGRED

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Fast aerial dogfight chase shot weaving through apple tree branches.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: BIG RED takes off in anger and chases the gliding NUTSY between the branches like a fighter jet dogfight, both banking and weaving through leaves.

SFX: flapping wings like a jet engine, angry squawks, leaves whipping.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S42: Tấm gương: Big Red đánh nhau với chính mình

**Giữ:** 6s · **Ref:** REF-NUTSY, REF-BIGRED

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot, mid-air.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY whips out the small round mirror and holds it toward BIG RED. BIG RED sees his own reflection, puffs up furiously and starts pecking and fighting the mirror, while NUTSY glides away smugly.

SFX: mirror flash ting, furious flapping and pecking on glass, smug chitter.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S43: Hạ cánh. Im lặng. Giọt nước mắt hạnh phúc

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Slow push-in on NUTSY at the main feeder.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY lands perfectly on the perch of the main tube feeder. No baffle, no spring, no motor. Everything goes silent. He slowly reaches toward the glowing golden seeds, eyes sparkling, a single happy tear rolling down his cheek.

SFX: complete silence except a single soft heartbeat.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: TẮT hẳn.

### S44: Tay xuyên qua tấm bìa

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot from the side, revealing the feeder is flat.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY's paw pokes straight through the feeder: it is only a flat cardboard cutout printed with a photo of a bird feeder. The cardboard wobbles. NUTSY looks at the hole, then slowly turns to stare into the camera, then the cutout tips over and he falls with it.

SFX: cardboard poke, papery wobble, a tiny sad squeak, fall whoosh.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S45: Rơi slow-motion vào thùng

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Slow-motion overhead shot looking down.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.

Action: NUTSY falls in slow motion with a flat deadpan face, down toward an open cardboard box on the lawn, and disappears into it. POOF, a puff of peanut shells bursts up.

SFX: slowed falling wind, a soft POOF.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

---

## KẾT: HIỆP ƯỚC HÒA BÌNH

### S46: Mở mắt giữa kho báu

**Giữ:** 5s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up inside the box, looking down at him.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: inside an open cardboard box sitting on the lawn below the apple tree, filled to the brim with peanuts, chestnuts and dried corn, a blank red sticky note taped to the inner wall, warm morning light spilling in from above.

Action: NUTSY slowly opens his eyes, lying in a soft pile of peanuts, chestnuts and corn. He sits up in total wonder, looks around, and notices the red sticky note taped to the box wall.

SFX: soft crunchy shifting of nuts, amazed gasp-squeak.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: chèn chữ lên note: 'CỦA MÀY. ĐỂ YÊN CHO CHIM ĂN.'

### S47: Cửa sổ đáp lời

**Giữ:** 4s · **Ref:** không

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static medium shot of the window from a low angle, as seen from the box.

Setting: exterior close view of the back window of a cozy house, white curtains behind the glass, a steaming white coffee mug sitting on the outside windowsill. Nobody visible inside, only the curtains.

Action: The white curtain behind the glass parts slightly for a moment then falls back, and the steam from the coffee mug on the sill curls into a small heart shape.

SFX: soft curtain swish, a gentle off-screen chuckle.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S48: Nutsy chào lại đối thủ

**Giữ:** 4s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up, low angle looking up at him in the box.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: inside an open cardboard box sitting on the lawn below the apple tree, filled to the brim with peanuts, chestnuts and dried corn, a blank red sticky note taped to the inner wall, warm morning light spilling in from above.

Action: NUTSY looks up toward the house window, pauses, then gives a respectful two-finger salute from his forehead with a small knowing smile.

SFX: soft salute swish.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Nhạc: ấm áp, nhẹ nhàng.

### S49: Toàn cảnh yên bình

**Giữ:** 6s · **Ref:** REF-NUTSY, REF-BIGRED, REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Wide crane shot rising up and away over the backyard.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded unimpressed eyes, chest puffed out like a nightclub bouncer.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Warm golden late-morning light, peaceful and cozy.

Action: NUTSY sits cross-legged in his cardboard box of nuts munching happily, while BIG RED and THE THREE SPARROWS eat peacefully at the real bird feeder nearby. A peaceful harmonious backyard.

SFX: happy munching, gentle birdsong. Ambient: soft breeze.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S50: …nhưng mà

**Giữ:** 7s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium close-up on NUTSY in the box.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird bath, a white wooden picket fence, a clothesline across the yard, and the back window of a cozy house with white curtains and a steaming white coffee mug on the windowsill. Warm golden late-morning light, peaceful and cozy.

Action: NUTSY glances at the bird feeder, then at his own pile of nuts, then back at the feeder. He wipes his mouth, slowly pulls the green leaf bandana down over his eyes like a mask, presses a paw to his ear and chitters secretly, then grins slyly at the camera.

SFX: glance whooshes, sneaky chittering whisper.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S51: KẾ HOẠCH Z

**Giữ:** 5s · **Ref:** không

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Static close-up at table height.

Setting: interior, camera at table-top height on a warm wooden kitchen table, a pad of red sticky notes, a black marker and a steaming white coffee mug, morning light from a window. The frame is cropped at table height so no person is ever visible.

Action: The black marker cap pops off by itself with a click, and a fresh red sticky note slides into frame next to the steaming coffee mug.

SFX: marker cap CLICK, off-screen scribbling, a long satisfied off-screen sip of coffee.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: chèn chữ 'KẾ HOẠCH Z.' lên note, rồi CẮT ĐEN. Danh đề cuối.

---

## CẢNH SAU DANH ĐỀ

### S52: Chim sẻ trộm hạt của Nutsy

**Giữ:** 5s · **Ref:** REF-SPARROWS

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Medium shot from the rim of the box.

THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in perfect unison like sports fans in a stadium.

Setting: inside an open cardboard box sitting on the lawn below the apple tree, filled to the brim with peanuts, chestnuts and dried corn, a blank red sticky note taped to the inner wall, warm morning light spilling in from above.

Action: THE THREE SPARROWS tiptoe sneakily into the cardboard box of nuts in a single-file row, each grabs one peanut in its beak, and they tiptoe away in perfect unison.

SFX: sneaky tiptoe plinks, tiny muffled chirps.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

### S53: Nutsy thành 'con người'

**Giữ:** 6s · **Ref:** REF-NUTSY

```
Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, anamorphic lens look, 24fps with natural motion blur.

Close-up, slow push-in.

NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead like a bandana. Cocky wannabe secret agent, very expressive face.

Setting: inside an open cardboard box sitting on the lawn below the apple tree, filled to the brim with peanuts, chestnuts and dried corn, a blank red sticky note taped to the inner wall, warm morning light spilling in from above.

Action: NUTSY returns, notices a few peanuts missing, slowly turns to stare into the camera with narrowed unimpressed eyes, then pulls out a tiny red sticky note and a stub of pencil.

SFX: suspicious sniff, paper rustle, pencil click.

Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo.
```

📝 Hậu kỳ: CẮT ĐEN. HẾT.
