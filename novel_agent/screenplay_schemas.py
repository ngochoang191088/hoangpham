"""Cấu trúc dữ liệu cho chế độ viết kịch bản phim."""
from typing import Literal

from pydantic import BaseModel, Field


class Beat(BaseModel):
    name: str = Field(description="Tên nhịp: hình ảnh mở đầu, sự kiện kích động, điểm giữa phim...")
    minute: float = Field(description="Phút thứ mấy trong phim")
    content: str


class ScriptCharacter(BaseModel):
    name: str
    age: str
    role: str = Field(description="Nhân vật chính / đối thủ / phụ ... và chức năng trong truyện")
    physical: str = Field(description="Chiều sinh lý: ngoại hình, sức khoẻ, một hành động đặc trưng khi xuất hiện")
    social: str = Field(description="Chiều xã hội: nghề, giai tầng, gia đình, hoàn cảnh")
    psychological: str = Field(description="Chiều tâm lý: khát vọng, nỗi sợ, niềm tin sai lầm, mâu thuẫn trong ngoài")
    want: str = Field(description="Muốn gì trong phim (cụ thể, nhìn thấy được)")
    attitude_to_theme: str = Field(description="Thái độ với chủ đề lúc đầu -> lúc cuối")
    voice: str = Field(description="Cách nói riêng: từ ngữ, nhịp câu, xưng hô, điều không bao giờ nói ra")


class Development(BaseModel):
    title: str
    genre: str
    logline: str = Field(description="Nhân vật chính + sự kiện kích động + thử thách + cái giá + chủ đề, 1-2 câu")
    premise: str = Field(description="Tiền đề: đặc điểm tính cách nhân vật + dẫn tới + kết cục")
    controlling_idea: str = Field(description="Tư tưởng chủ đạo: giá trị + nguyên nhân (lý tưởng / bi quan / trớ trêu)")
    core: str = Field(description="Lõi kịch: tình huống mà rút đi thì cả phim sụp")
    desire_vs_false_belief: str = Field(description="Khát vọng của nhân vật chính và niềm tin sai lầm của họ")
    why_now: str = Field(description="Vì sao câu chuyện phải xảy ra lúc này")
    world_rules: str = Field(description="Luật của thế giới phim phải lộ ra sớm")
    characters: list[ScriptCharacter]
    binding: str = Field(description="Thứ trói chặt nhân vật chính và đối thủ khiến không ai rút lui được")
    opponent_weapon: str = Field(description="Con dao của đối thủ: thứ đối thủ nắm có thể làm nhân vật chính mất tất cả")
    protagonist_shackles: str = Field(description="Xiềng xích của nhân vật chính: điều trói tay họ")
    ending: str = Field(description="Kết phim (quyết định TRƯỚC mọi thứ khác)")
    ending_type: str = Field(description="Kiểu kết: sấm nổ / bỏ ngỏ / kéo dài / bật ngược / điểm nhãn / hô ứng / luân hồi / kết luận")
    key_image: str = Field(description="Hình ảnh chủ đạo của cao trào")
    beats: list[Beat] = Field(description="Bảng nhịp theo phút")
    subplot: str = Field(description="Tuyến phụ và quan hệ với tư tưởng chủ đạo (mâu thuẫn / vọng lại / gài báo / đan xen)")


class SceneCard(BaseModel):
    number: int
    heading: str = Field(description="NỘI/NGOẠI. ĐỊA ĐIỂM - NGÀY/ĐÊM (viết hoa)")
    summary: str = Field(description="Một câu: ai làm gì, kết quả khác với dự tính thế nào")
    value_open: str = Field(description="Giá trị bị đặt cược lúc mở cảnh, kèm dấu (+) hoặc (-), vd 'tin tưởng (+)'")
    value_close: str = Field(description="Giá trị đó lúc đóng cảnh, kèm dấu; phải khác lúc mở")
    conflict: str = Field(description="Ai muốn gì, ai cản, ai thắng")
    position: str = Field(description="Vị trí cấu trúc: nhịp nào / khởi-thừa-chuyển-hợp")
    seconds: int = Field(description="Thời lượng ước tính trên màn ảnh, tính bằng giây")


class Outline(BaseModel):
    scenes: list[SceneCard]


class ScriptIssue(BaseModel):
    severity: Literal["critical", "major", "minor"]
    scenes: list[int] = Field(description="Số các cảnh liên quan (rỗng nếu là vấn đề toàn kịch bản)")
    checklist_item: str = Field(description="Câu hỏi chẩn đoán nào không đạt")
    problem: str
    suggestion: str


class ScriptReview(BaseModel):
    score: float = Field(description="Điểm 0-10")
    strengths: list[str]
    issues: list[ScriptIssue]
    summary: str


class RevisedScene(BaseModel):
    number: int
    text: str = Field(description="Toàn văn cảnh đã sửa, bắt đầu bằng dòng tiêu đề 'CẢNH <số>. ...'")


class Revision(BaseModel):
    scenes: list[RevisedScene]
    notes: str = Field(description="Đã sửa gì, vì sao, 2-5 dòng")
