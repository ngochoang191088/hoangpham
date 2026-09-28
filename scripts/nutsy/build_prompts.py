"""Sinh file prompt Veo cho tập phim NUTSY.

Mọi mô tả nhân vật, bối cảnh, phong cách được khai báo MỘT lần ở đây rồi ghép
nguyên văn vào từng prompt. Như vậy Veo luôn nhận đúng một mô tả, giúp nhân vật
giữ hình dạng ổn định giữa các clip. Sửa mô tả thì sửa ở đây rồi chạy lại:

    python scripts/nutsy/build_prompts.py
"""
from pathlib import Path

OUT = Path(__file__).with_name("02_prompt-veo-tung-shot.md")

STYLE = (
    "Style: high-end Hollywood 3D animated feature film, stylized cartoon characters with "
    "exaggerated squash-and-stretch animation and snappy comedic timing, soft detailed fur and "
    "feathers, rich saturated colors, warm cinematic lighting, shallow depth of field, "
    "anamorphic lens look, 24fps with natural motion blur."
)

NEGATIVE = (
    "Avoid: humans, people, human hands or arms, human silhouettes or shadows, talking mouths, "
    "dialogue, voiceover, background music, on-screen text, subtitles, captions, watermark, logo."
)

CHARS = {
    "nutsy": (
        "NUTSY: a small cartoon grey squirrel, lean and wiry, oversized glossy amber eyes, two big "
        "front teeth, cream-white belly, a tiny notch in the tip of his left ear, a huge fluffy "
        "S-shaped grey tail with a pale silver tip, and a bright green leaf tied around his forehead "
        "like a bandana. Cocky wannabe secret agent, very expressive face."
    ),
    "red": (
        "BIG RED: a very plump round cartoon male northern cardinal, bright crimson feathers, tall "
        "pointed crest, black mask around the eyes and beak, thick orange cone beak, heavy-lidded "
        "unimpressed eyes, chest puffed out like a nightclub bouncer."
    ),
    "sparrows": (
        "THE THREE SPARROWS: three identical tiny round cartoon house sparrows, brown and cream "
        "feathers, big curious eyes, always standing shoulder to shoulder in a row and moving in "
        "perfect unison like sports fans in a stadium."
    ),
}

YARD = (
    "a small suburban backyard: an old apple tree with a clear tube bird feeder full of sunflower "
    "seeds hanging from a low branch, a green metal feeder pole in the lawn, a round stone bird "
    "bath, a white wooden picket fence, a clothesline across the yard, and the back window of a "
    "cozy house with white curtains and a steaming white coffee mug on the windowsill"
)

SETTINGS = {
    "yard_dawn": f"Setting: {YARD}. Early dawn, soft golden-pink backlight, light mist over the grass.",
    "yard_day": f"Setting: {YARD}. Bright sunny morning, crisp shadows, dew on the grass.",
    "yard_sunrise": f"Setting: {YARD}. Sunrise, dramatic golden backlight and long shadows, epic atmosphere.",
    "yard_golden": f"Setting: {YARD}. Warm golden late-morning light, peaceful and cozy.",
    "window": (
        "Setting: exterior close view of the back window of a cozy house, white curtains behind the "
        "glass, a steaming white coffee mug sitting on the outside windowsill. Nobody visible "
        "inside, only the curtains."
    ),
    "table": (
        "Setting: interior, camera at table-top height on a warm wooden kitchen table, a pad of red "
        "sticky notes, a black marker and a steaming white coffee mug, morning light from a window. "
        "The frame is cropped at table height so no person is ever visible."
    ),
    "house_night": (
        "Setting: exterior of the house at night seen from the apple tree, one warm glowing window "
        "among dark blue night tones, crickets, fireflies."
    ),
    "hollow": (
        "Setting: interior of a squirrel's hollow inside a tree trunk at night, a firefly trapped "
        "under an upturned bottle cap swinging from a string like an interrogation lamp, the curved "
        "wooden wall covered in hand-drawn photos of the bird feeder connected with red strings like a "
        "detective's evidence board, a dirt floor map of the backyard with acorns on it."
    ),
    "box": (
        "Setting: inside an open cardboard box sitting on the lawn below the apple tree, filled to the "
        "brim with peanuts, chestnuts and dried corn, a blank red sticky note taped to the inner wall, "
        "warm morning light spilling in from above."
    ),
}

# Ảnh tham chiếu nên gắn khi dùng "Ingredients to video" trong Google Flow.
REF = {"nutsy": "REF-NUTSY", "red": "REF-BIGRED", "sparrows": "REF-SPARROWS"}

# (mã, tiêu đề tiếng Việt, giữ lại bao nhiêu giây khi dựng, nhân vật, bối cảnh,
#  máy quay, hành động, âm thanh, ghi chú hậu kỳ)
SHOTS = [
    # ---------------- MỞ MÀN ----------------
    ("MỞ MÀN: PHI VỤ HOÀN HẢO", None),
    ("S01", "Toàn cảnh sân sau, máy ăn chim lấp lánh", "5s", ["red", "sparrows"], "yard_dawn",
     "Slow crane shot descending from the apple tree canopy to the bird feeder, which sparkles in the dawn light like a jewel in a museum.",
     "BIG RED and THE THREE SPARROWS peck sunflower seeds peacefully at the feeder; seeds tinkle as they fall.",
     "SFX: gentle birdsong, seeds tinkling. Ambient: quiet dawn breeze.",
     "Nhạc nền: chuỗi đàn dây trầm, hồi hộp kiểu phim điệp viên (thêm khi dựng)."),
    ("S02", "Con mắt sau bụi cây", "2s", ["nutsy"], "yard_dawn",
     "Extreme close-up, sudden fast snap zoom in.",
     "Between dark green bush leaves, one huge amber squirrel eye of NUTSY peers out, pupil narrowing with determination.",
     "SFX: a sharp whoosh on the zoom, leaves rustle.",
     ""),
    ("S03", "Nutsy chuẩn bị đồ nghề", "4s", ["nutsy"], "yard_dawn",
     "Series of tight close-ups, low angle, dramatic side light.",
     "NUTSY tightens the green leaf bandana on his forehead with a sharp tug, smears two stripes of mud under his eyes with his thumb like a commando, then presses a paw to his ear and chitters secretly as if talking into an earpiece.",
     "SFX: leaf snap, wet mud smear, squirrel chittering whisper.",
     ""),
    ("S04", "Zipline trên dây phơi", "5s", ["nutsy"], "yard_dawn",
     "Dynamic tracking shot following alongside, fast.",
     "NUTSY hangs from a wooden clothespin and zips down the clothesline across the backyard at high speed toward the bird feeder, fur and tail streaming in the wind, grinning with confidence.",
     "SFX: zipping whirr of the clothespin on the line, wind rush.",
     ""),
    ("S05", "Slow-motion: chạm mắt với Big Red", "4s", ["nutsy", "red"], "yard_dawn",
     "Extreme slow motion, side profile, camera tracking with NUTSY.",
     "NUTSY flies past right in front of BIG RED's face mid-air. They lock eyes. BIG RED's beak drops open in shock and a single sunflower seed slowly falls from it.",
     "SFX: slowed-down deep whoosh, a single seed drop echoing.",
     ""),
    ("S06", "Cướp sạch máy ăn", "5s", ["nutsy", "red", "sparrows"], "yard_dawn",
     "Medium shot at normal speed, handheld energy.",
     "NUTSY lands on the bird feeder and stuffs seeds into his cheeks until they bulge like two balloons, while BIG RED and THE THREE SPARROWS scatter in an explosion of feathers.",
     "SFX: rapid chomping, cheeks stretching squeak, panicked bird chirps and wing flaps.",
     ""),
    ("S07", "Tẩu thoát kiểu cao bồi", "6s", ["nutsy"], "yard_dawn",
     "Low angle on the lawn, then tilt up to the empty feeder.",
     "NUTSY drops to the grass, does a stylish roll, stands, blows on his claws like a cowboy blowing on a smoking gun, and dashes off frame. The camera tilts up to the empty feeder swaying gently as a single red cardinal feather drifts down in slow motion.",
     "SFX: roll thump, cheeky blow, zip of a fast exit, feeder creak.",
     "Chuyển cảnh: MATCH CUT từ chiếc lông đỏ đang rơi sang tờ note đỏ đang rơi (S08)."),
    ("S08", "Trong nhà: tờ note đỏ", "5s", [], "table",
     "Static close-up at table height.",
     "A single red sticky note flutters down from above and lands softly on the wooden table next to the black marker and the steaming coffee mug. The marker cap pops off by itself with a click.",
     "SFX: paper flutter, marker cap click, off-screen marker scribbling, then a long satisfied off-screen sip of hot coffee.",
     "Hậu kỳ: chèn chữ viết tay lên tờ note: 'SÓC. KẾ HOẠCH A.' Sau S08 cắt đen và chèn TIÊU ĐỀ 'NUTSY' + SFX 'BOING!' (làm trong CapCut, không cần Veo)."),

    # ---------------- PHẦN 1 ----------------
    ("PHẦN 1: CÁI CHUÔNG CẤM", None),
    ("S09", "Quả sồi trượt khỏi cành bọc nhựa", "5s", ["nutsy"], "yard_day",
     "Medium wide shot from the lawn.",
     "NUTSY fires an acorn tied to a string with a tiny twig slingshot at the feeder branch, but the branch is now wrapped in a shiny slippery plastic tube. The acorn slides straight off and the string falls in loops onto NUTSY's head.",
     "SFX: slingshot twang, plastic squeak, slide, soft plop of string.",
     ""),
    ("S10", "Nutsy nhìn thẳng vào máy quay", "3s", ["nutsy"], "yard_day",
     "Static close-up, centered, deadpan comedic framing.",
     "NUTSY, with string draped over his head, slowly looks at the string, then turns and stares directly into the camera, blinking twice in silence.",
     "SFX: silence, two tiny blink sounds, a single cricket chirp.",
     ""),
    ("S11", "Leo cột thần tốc", "3s", ["nutsy"], "yard_day",
     "Low angle looking up the green metal pole, fast.",
     "NUTSY scrambles up the green metal feeder pole at blurring cartoon speed, claws clicking on metal.",
     "SFX: rapid claw scratching on metal.",
     ""),
    ("S12", "BONG! Đâm đầu vào chuông", "4s", ["nutsy"], "yard_day",
     "Close-up at the top of the pole.",
     "NUTSY's head slams into a large clear plastic dome baffle mounted on top of the pole. BONG. His whole body vibrates rapidly like a tuning fork, eyes rattling, teeth chattering.",
     "SFX: a huge resonant church-bell BONG, trembling vibration hum.",
     ""),
    ("S13", "Trượt vòng quanh chuông rồi văng ra", "5s", ["nutsy"], "yard_day",
     "Medium shot, camera circling slightly.",
     "NUTSY clings to the rim of the clear dome baffle, the baffle tilts, and he slides around and around it like a spinning vinyl record, faster and faster, until he is flung off to the side.",
     "SFX: squeaky spinning, rising whirl, launch whoosh.",
     ""),
    ("S14", "Dính vào hàng rào hình chữ X", "4s", ["nutsy"], "yard_day",
     "Whip pan following NUTSY across the yard, landing on the fence.",
     "NUTSY flies across the backyard and splats flat against the white picket fence, spread-eagle in an X shape, then slowly slides down the boards to the grass.",
     "SFX: whip whoosh, cartoon SPLAT, slow wood squeak slide.",
     ""),
    ("S15", "Ba chim sẻ chấm điểm", "3s", ["sparrows"], "yard_day",
     "Static medium shot, the three birds perfectly centered in a row on the fence.",
     "THE THREE SPARROWS on the fence each raise a large green leaf above their heads at the exact same moment, like judges holding up scorecards.",
     "SFX: three synchronized leaf rustles, a tiny chirp in unison.",
     "Hậu kỳ: chèn số lên 3 chiếc lá: 7 – 8 – 6."),
    ("S16", "Hơi cà phê thành mặt cười", "3s", [], "window",
     "Static close-up on the coffee mug on the windowsill.",
     "The steam rising from the coffee mug curls and swirls into the shape of a smiley face, while the white curtain behind the glass sways slightly.",
     "SFX: soft off-screen chuckle behind the glass, a gentle sip.",
     "Đây là running gag, dùng lại ở S29. Nếu Veo không vẽ ra mặt cười thì gen lại 2–3 lần."),
    ("S17", "Nutsy nghi ngờ nhìn lên cửa sổ", "4s", ["nutsy"], "yard_day",
     "Medium close-up, low angle, then slow push-in on his eye.",
     "NUTSY stands up, dusts himself off, and squints suspiciously up toward the house window. The camera pushes slowly into his narrowed eye.",
     "SFX: dust pats, a low suspicious hum.",
     "Chuyển cảnh: zoom xuyên vào mắt để nối sang S18."),
    ("S18", "Kế hoạch B phản chiếu trong mắt", "3s", ["nutsy"], "yard_day",
     "Extreme macro close-up of the squirrel eye.",
     "In the glossy amber eye of NUTSY, a chalk-drawn blueprint of the bird feeder with arrows and circles appears as a reflection, glowing faintly.",
     "SFX: chalk scratching, a sly musical sting.",
     ""),

    # ---------------- PHẦN 2 ----------------
    ("PHẦN 2: MONTAGE BẪY", None),
    ("S19", "Bẫy 1: lò xo slinky thả xuống từ từ", "6s", ["nutsy"], "yard_day",
     "Medium shot of the pole, locked-off camera.",
     "A metal slinky spring toy now wraps the green feeder pole. NUTSY grabs it and starts climbing, but the slinky stretches and gently lowers him back down to the grass like a slow elevator, boing, boing. He tries again with the same result, his face getting grumpier.",
     "SFX: metallic slinky boing boing, grumpy squirrel grunt.",
     "Nhạc nền montage: kèn đồng và trống nhanh, kiểu montage tập luyện (thêm khi dựng)."),
    ("S20", "Lò xo phóng Nutsy lên trời", "4s", ["nutsy"], "yard_day",
     "Low angle looking up, camera tilting fast to follow him into the sky.",
     "On the third attempt the slinky compresses fully and launches NUTSY straight up into the blue sky like a rocket, until he becomes a tiny dot with a twinkle.",
     "SFX: a massive spring BOING, rocket whoosh, tiny twinkle ding.",
     "Chuyển cảnh: MATCH CUT theo chuyển động, bay lên ở S20 rồi rơi xuống ở S21."),
    ("S21", "Bẫy 2: rơi trúng máy ăn, cười đắc thắng", "3s", ["nutsy"], "yard_day",
     "Looking down from above the tube feeder, NUTSY falls from the sky toward camera.",
     "NUTSY drops out of the sky and lands perfectly clinging to the tube bird feeder, then flashes a huge triumphant grin.",
     "SFX: falling whistle, clunk landing, confident chuckle-chitter.",
     ""),
    ("S22", "Máy ăn quay tít, ném búa", "7s", ["nutsy", "red"], "yard_day",
     "Medium shot, camera spinning slightly with the motion.",
     "The feeder's motorized perch ring suddenly spins at high speed. NUTSY whirls around like an Olympic hammer thrower, cheeks flapping from the force, seeds shooting out of his cheeks like a machine gun at BIG RED who ducks and dodges. NUTSY loses his grip and is flung out of frame to the right.",
     "SFX: electric motor whine rising, rapid seed rat-a-tat-tat, BIG RED squawk, launch whoosh.",
     "Chuyển cảnh: bay ra mép phải, sang S23 thì lao vào từ mép trái."),
    ("S23", "Bẫy 3: máy ăn thứ hai quá dễ", "5s", ["nutsy"], "yard_day",
     "Medium shot, NUTSY tumbles in from the left edge of frame.",
     "NUTSY tumbles into frame from the left and lands on an open wooden tray feeder piled high with seeds that have a faint red coating, with no guards at all. He looks around suspiciously left and right, then shrugs and stuffs his face greedily.",
     "SFX: tumble thuds, suspicious sniffing, greedy chomping.",
     ""),
    ("S24", "Mặt đổi màu, tai phun khói", "5s", ["nutsy"], "yard_day",
     "Close-up on his face, static.",
     "NUTSY freezes mid-chew. His face slowly turns from grey to pink to red to deep purple, his eyes water, and jets of steam whistle out of both ears like a boiling kettle.",
     "SFX: rising kettle whistle, sizzle, strained squeak.",
     "Chuyện có thật: chim không cảm nhận được vị cay, còn sóc thì có."),
    ("S25", "Big Red ăn ớt tỉnh bơ", "4s", ["nutsy", "red"], "yard_day",
     "Two-shot, medium.",
     "BIG RED lands next to the steaming NUTSY, calmly crunches the same red-coated seeds with total ease, and gives him a slow pitying look.",
     "SFX: loud calm crunching, NUTSY's whistling ears continue.",
     ""),
    ("S26", "Cắm đầu xuống bồn tắm chim", "4s", ["nutsy"], "yard_day",
     "Wide shot, then the frame fills with white steam.",
     "NUTSY rockets across the lawn and dives head-first into the stone bird bath. A giant hiss of steam erupts and fills the entire frame with white.",
     "SFX: rocket whoosh, splash, massive steam HISS.",
     "Chuyển cảnh: màn hơi nước trắng tan ra thành S27."),
    ("S27", "Bẫy 4: cải trang thành chim", "6s", ["nutsy", "sparrows"], "yard_day",
     "White steam clears to reveal a medium shot on the lawn.",
     "NUTSY is now disguised as a bird, with feathers glued all over his body and an acorn cap strapped on as a fake beak, hopping bird-style toward a metal bird feeder with a weight-activated perch. THE THREE SPARROWS tilt their heads at him in perfect unison.",
     "SFX: steam fading, light bird-like hops, three puzzled chirps.",
     ""),
    ("S28", "Cửa chắn sập, rứt lông giảm cân", "7s", ["nutsy"], "yard_day",
     "Medium close-up on the feeder perch.",
     "NUTSY steps onto the perch and a metal shutter slams down over the seed ports. CLACK. He tries tiptoeing, standing on one leg, holding his breath: clack, clack. He plucks off his glued feathers one by one to lose weight until the last one is gone, and the shutter stays shut. He stands there bare, tail drooping.",
     "SFX: metal shutter CLACK repeated, feather plucks, deflated sigh.",
     ""),
    ("S29", "Chấm điểm và mặt cười nháy mắt", "4s", ["sparrows"], "yard_day",
     "Static medium shot on the fence, centered.",
     "THE THREE SPARROWS raise their leaf scorecards in unison, then the third sparrow flips his leaf around to show the other side.",
     "SFX: synchronized leaf rustles, a tiny judging chirp.",
     "Hậu kỳ: số 2 – 1 – 0, mặt sau lá con thứ ba ghi 'KHÔNG'. Chèn 1 giây S16 với mặt cười NHÁY MẮT (gen lại S16, thay 'smiley face' bằng 'winking smiley face')."),
    ("S30", "Iris-out bị kéo mở lại", "5s", ["nutsy"], "yard_day",
     "Close-up on NUTSY's dejected face with a classic cartoon black iris vignette closing in.",
     "A black circular iris closes in around NUTSY's sad face. Just before it shuts, NUTSY frowns with determination, reaches out with both paws, grabs the edge of the black circle and pulls it wide open again.",
     "SFX: cartoon iris swoosh, then a stretching rubber sound as he pulls it open.",
     "Nếu Veo làm hỏng: gen Nutsy mặt buồn chuyển sang quyết tâm, rồi làm iris trong CapCut."),

    # ---------------- PHẦN 3 ----------------
    ("PHẦN 3: PHÒNG CHIẾN LƯỢC", None),
    ("S31", "Hang sóc, bảng điều tra chỉ đỏ", "5s", ["nutsy"], "hollow",
     "Slow dolly along the evidence wall, moody noir lighting from the swinging firefly lamp.",
     "NUTSY paces back and forth in front of the wall of feeder photos and red strings, stroking his chin, the firefly lamp swinging and throwing moving shadows.",
     "SFX: creaking string of the swinging lamp, soft footsteps, firefly buzz.",
     "Nhạc: trầm, bí ẩn kiểu phim trinh thám."),
    ("S32", "Dàn trận bằng quả sồi", "4s", ["nutsy"], "hollow",
     "High angle over the dirt floor map.",
     "NUTSY moves acorns across the dirt map of the backyard with a twig like a war general, then draws a big swooping flight arrow in the dirt.",
     "SFX: acorns clicking, twig scraping dirt.",
     ""),
    ("S33", "Chế máy bắn đá bằng thìa", "3s", ["nutsy"], "hollow",
     "Quick close-up, energetic.",
     "NUTSY ties a white plastic spoon to a bent green sapling with grass string, pulls it back and tests the spring.",
     "SFX: grass knot tightening, woody creak, springy twang.",
     "Nhạc: trống nhanh kiểu montage chế tạo. Cắt S33, S34, S35 thật nhanh, mỗi đoạn 2–3 giây."),
    ("S34", "Dù lượn chiếc tất, kính nắp chai", "3s", ["nutsy"], "hollow",
     "Quick close-up, energetic.",
     "NUTSY stretches an old striped sock over a frame of crossed twigs to make a tiny hang glider, then puts on goggles made of two bottle caps.",
     "SFX: fabric stretch, twig snaps into place, goggle strap snap.",
     ""),
    ("S35", "Tấm gương bí ẩn, nhìn thẳng máy quay", "4s", ["nutsy"], "hollow",
     "Medium close-up, then he looks straight into the lens.",
     "NUTSY holds up a small round mirror, taps it knowingly and nods mysteriously. Then he pulls the bottle-cap goggles down over his eyes with a snap and stares directly into the camera.",
     "SFX: mirror tap ting, goggle SNAP.",
     "Chuyển cảnh: MATCH CUT bằng âm thanh, tiếng tách của kính thành tiếng tách công tắc đèn (S36)."),
    ("S36", "Đèn cửa sổ tắt phụt", "3s", [], "house_night",
     "Static wide shot.",
     "The single glowing window of the house clicks off, leaving the house dark under the night sky.",
     "SFX: a crisp light switch CLICK, crickets.",
     ""),

    # ---------------- PHẦN 4 ----------------
    ("PHẦN 4: PHI VỤ CUỐI CÙNG", None),
    ("S37", "Thử gió, chào nhà binh", "6s", ["nutsy", "sparrows"], "yard_sunrise",
     "Heroic low angle on NUTSY standing on the plastic spoon catapult.",
     "Wearing the bottle-cap goggles with the sock glider strapped on his back, NUTSY licks a finger and holds it up to test the wind, then gives a crisp military salute to THE THREE SPARROWS on the fence. The sparrows salute back by reflex in unison, then awkwardly lower their wings.",
     "SFX: finger lick, wind gust, crisp salute swish, embarrassed tiny chirps.",
     "Nhạc: chủ đề điệp viên quay lại, dàn nhạc đầy đủ, nhịp gấp đôi."),
    ("S38", "Cất cánh slow-motion", "6s", ["nutsy"], "yard_sunrise",
     "Extreme slow motion, camera rising with him against the sun.",
     "NUTSY bites through the grass string, the spoon catapult snaps and launches him into the air. In slow motion the striped sock glider unfurls above him and he soars heroically, backlit by the rising sun with a lens flare.",
     "SFX: string snap, catapult THWACK, slowed epic wind.",
     "Nhạc: hợp xướng hùng tráng (thêm khi dựng)."),
    ("S39", "Né chuông gió", "5s", ["nutsy"], "yard_sunrise",
     "Tracking shot flying with NUTSY, alternating slow motion and normal speed.",
     "NUTSY glides through a hanging set of metal wind chimes, twisting and dodging as each chime tube swings past just millimeters from his nose.",
     "SFX: wind chimes clinking, near-miss whooshes.",
     ""),
    ("S40", "Vòi tưới bật, né kiểu Matrix", "6s", ["nutsy"], "yard_sunrise",
     "Dynamic slow-motion orbiting camera.",
     "Lawn sprinklers suddenly burst on beneath him. NUTSY twists and rolls in mid-air to dodge each glittering jet of water like laser beams, finishing with an extreme backward bend as a jet passes over him in bullet-time slow motion.",
     "SFX: sprinkler hiss bursts, slowed water whoosh, bullet-time bass drop.",
     ""),
    ("S41", "Big Red rượt đuổi trên không", "6s", ["nutsy", "red"], "yard_sunrise",
     "Fast aerial dogfight chase shot weaving through apple tree branches.",
     "BIG RED takes off in anger and chases the gliding NUTSY between the branches like a fighter jet dogfight, both banking and weaving through leaves.",
     "SFX: flapping wings like a jet engine, angry squawks, leaves whipping.",
     ""),
    ("S42", "Tấm gương: Big Red đánh nhau với chính mình", "6s", ["nutsy", "red"], "yard_sunrise",
     "Medium shot, mid-air.",
     "NUTSY whips out the small round mirror and holds it toward BIG RED. BIG RED sees his own reflection, puffs up furiously and starts pecking and fighting the mirror, while NUTSY glides away smugly.",
     "SFX: mirror flash ting, furious flapping and pecking on glass, smug chitter.",
     ""),
    ("S43", "Hạ cánh. Im lặng. Giọt nước mắt hạnh phúc", "6s", ["nutsy"], "yard_sunrise",
     "Slow push-in on NUTSY at the main feeder.",
     "NUTSY lands perfectly on the perch of the main tube feeder. No baffle, no spring, no motor. Everything goes silent. He slowly reaches toward the glowing golden seeds, eyes sparkling, a single happy tear rolling down his cheek.",
     "SFX: complete silence except a single soft heartbeat.",
     "Nhạc: TẮT hẳn."),
    ("S44", "Tay xuyên qua tấm bìa", "6s", ["nutsy"], "yard_sunrise",
     "Medium shot from the side, revealing the feeder is flat.",
     "NUTSY's paw pokes straight through the feeder: it is only a flat cardboard cutout printed with a photo of a bird feeder. The cardboard wobbles. NUTSY looks at the hole, then slowly turns to stare into the camera, then the cutout tips over and he falls with it.",
     "SFX: cardboard poke, papery wobble, a tiny sad squeak, fall whoosh.",
     ""),
    ("S45", "Rơi slow-motion vào thùng", "4s", ["nutsy"], "yard_sunrise",
     "Slow-motion overhead shot looking down.",
     "NUTSY falls in slow motion with a flat deadpan face, down toward an open cardboard box on the lawn, and disappears into it. POOF, a puff of peanut shells bursts up.",
     "SFX: slowed falling wind, a soft POOF.",
     ""),

    # ---------------- KẾT ----------------
    ("KẾT: HIỆP ƯỚC HÒA BÌNH", None),
    ("S46", "Mở mắt giữa kho báu", "5s", ["nutsy"], "box",
     "Medium close-up inside the box, looking down at him.",
     "NUTSY slowly opens his eyes, lying in a soft pile of peanuts, chestnuts and corn. He sits up in total wonder, looks around, and notices the red sticky note taped to the box wall.",
     "SFX: soft crunchy shifting of nuts, amazed gasp-squeak.",
     "Hậu kỳ: chèn chữ lên note: 'CỦA MÀY. ĐỂ YÊN CHO CHIM ĂN.'"),
    ("S47", "Cửa sổ đáp lời", "4s", [], "window",
     "Static medium shot of the window from a low angle, as seen from the box.",
     "The white curtain behind the glass parts slightly for a moment then falls back, and the steam from the coffee mug on the sill curls into a small heart shape.",
     "SFX: soft curtain swish, a gentle off-screen chuckle.",
     ""),
    ("S48", "Nutsy chào lại đối thủ", "4s", ["nutsy"], "box",
     "Medium close-up, low angle looking up at him in the box.",
     "NUTSY looks up toward the house window, pauses, then gives a respectful two-finger salute from his forehead with a small knowing smile.",
     "SFX: soft salute swish.",
     "Nhạc: ấm áp, nhẹ nhàng."),
    ("S49", "Toàn cảnh yên bình", "6s", ["nutsy", "red", "sparrows"], "yard_golden",
     "Wide crane shot rising up and away over the backyard.",
     "NUTSY sits cross-legged in his cardboard box of nuts munching happily, while BIG RED and THE THREE SPARROWS eat peacefully at the real bird feeder nearby. A peaceful harmonious backyard.",
     "SFX: happy munching, gentle birdsong. Ambient: soft breeze.",
     ""),
    ("S50", "…nhưng mà", "7s", ["nutsy"], "yard_golden",
     "Medium close-up on NUTSY in the box.",
     "NUTSY glances at the bird feeder, then at his own pile of nuts, then back at the feeder. He wipes his mouth, slowly pulls the green leaf bandana down over his eyes like a mask, presses a paw to his ear and chitters secretly, then grins slyly at the camera.",
     "SFX: glance whooshes, sneaky chittering whisper.",
     ""),
    ("S51", "KẾ HOẠCH Z", "5s", [], "table",
     "Static close-up at table height.",
     "The black marker cap pops off by itself with a click, and a fresh red sticky note slides into frame next to the steaming coffee mug.",
     "SFX: marker cap CLICK, off-screen scribbling, a long satisfied off-screen sip of coffee.",
     "Hậu kỳ: chèn chữ 'KẾ HOẠCH Z.' lên note, rồi CẮT ĐEN. Danh đề cuối."),

    # ---------------- POST-CREDITS ----------------
    ("CẢNH SAU DANH ĐỀ", None),
    ("S52", "Chim sẻ trộm hạt của Nutsy", "5s", ["sparrows"], "box",
     "Medium shot from the rim of the box.",
     "THE THREE SPARROWS tiptoe sneakily into the cardboard box of nuts in a single-file row, each grabs one peanut in its beak, and they tiptoe away in perfect unison.",
     "SFX: sneaky tiptoe plinks, tiny muffled chirps.",
     ""),
    ("S53", "Nutsy thành 'con người'", "6s", ["nutsy"], "box",
     "Close-up, slow push-in.",
     "NUTSY returns, notices a few peanuts missing, slowly turns to stare into the camera with narrowed unimpressed eyes, then pulls out a tiny red sticky note and a stub of pencil.",
     "SFX: suspicious sniff, paper rustle, pencil click.",
     "Hậu kỳ: CẮT ĐEN. HẾT."),
]


def build_prompt(chars, setting, camera, action, audio):
    parts = [STYLE, camera]
    parts += [CHARS[c] for c in chars]
    parts += [SETTINGS[setting], f"Action: {action}", audio, NEGATIVE]
    return "\n\n".join(parts)


def main():
    lines = [
        "# NUTSY: PROMPT VEO TỪNG SHOT",
        "",
        "Mỗi shot là **một lần gen Veo, 8 giây, tỉ lệ 16:9**. Copy nguyên khối code dán vào Veo.",
        "Cột **Giữ** là số giây nên giữ lại khi dựng (Veo gen 8 giây, cắt bớt cho nhịp nhanh).",
        "**Ref** là ảnh tham chiếu cần gắn (xem `01_thiet-ke-nhan-vat.md`).",
        "",
        "> File này được sinh tự động từ `build_prompts.py`. Muốn sửa mô tả nhân vật hay bối cảnh thì sửa ở đó rồi chạy lại.",
        "",
        "## Tổng quan",
        "",
        "| Shot | Nội dung | Giữ | Ref |",
        "|---|---|---|---|",
    ]
    body = []
    total = 0
    for s in SHOTS:
        if s[1] is None:
            lines.append(f"| | **{s[0]}** | | |")
            body += ["---", "", f"## {s[0]}", ""]
            continue
        sid, title, keep, chars, setting, camera, action, audio, note = s
        total += int(keep.rstrip("s"))
        refs = ", ".join(REF[c] for c in chars) or "không"
        lines.append(f"| {sid} | {title} | {keep} | {refs} |")
        body += [f"### {sid}: {title}", "", f"**Giữ:** {keep} · **Ref:** {refs}", ""]
        body += ["```", build_prompt(chars, setting, camera, action, audio), "```", ""]
        if note:
            body += [f"📝 {note}", ""]
    n = sum(1 for s in SHOTS if s[1] is not None)
    lines += ["", f"**{n} shot**, sau khi cắt còn khoảng **{total // 60} phút {total % 60} giây** chưa tính tiêu đề và danh đề.", ""]
    OUT.write_text("\n".join(lines + body), encoding="utf-8")
    print(f"Wrote {OUT} ({n} shots, {total}s)")


if __name__ == "__main__":
    main()
