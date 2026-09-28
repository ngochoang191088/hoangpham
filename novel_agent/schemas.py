"""Cấu trúc dữ liệu trao đổi giữa các agent (AI trả về JSON đúng các mẫu này)."""
from typing import Literal

from pydantic import BaseModel, Field


class Character(BaseModel):
    name: str
    role: str = Field(description="Vai trò: chính, phản diện, phụ...")
    description: str = Field(description="Ngoại hình, tính cách, quá khứ, giọng nói")
    goal: str = Field(description="Điều nhân vật muốn và nỗi sợ")
    arc: str = Field(description="Nhân vật thay đổi thế nào từ đầu tới cuối truyện")
    current_state: str = Field(description="Trạng thái hiện tại (ban đầu: trước chương 1)")


class PartOutline(BaseModel):
    number: int
    title: str
    arc: str = Field(description="Mạch chính của phần: mở đầu, xung đột, cao trào, kết phần")
    ending_hook: str = Field(description="Kết phần để lại gì, nối sang phần sau thế nào")


class StoryBible(BaseModel):
    title: str
    genre: str
    premise: str = Field(description="Tóm tắt ý tưởng cốt lõi, 3-5 câu")
    themes: list[str]
    style_guide: str = Field(description="Giọng kể, ngôi kể, thì, nhịp văn, mức độ miêu tả, cách viết thoại")
    world: str = Field(description="Bối cảnh, thời đại, địa danh, luật lệ / hệ thống sức mạnh nếu có")
    characters: list[Character]
    parts: list[PartOutline]
    ending: str = Field(description="Kết cục dự kiến của toàn truyện")


class ChapterPlan(BaseModel):
    number: int = Field(description="Số thứ tự chương trong TOÀN truyện")
    title: str
    pov: str = Field(description="Góc nhìn nhân vật nào")
    goal: str = Field(description="Chương này phải đạt được gì cho cốt truyện")
    beats: list[str] = Field(description="Các diễn biến chính theo thứ tự")
    threads: list[str] = Field(description="Tuyến truyện / chi tiết cài cắm được mở hoặc khép trong chương")
    ending_hook: str = Field(description="Chương kết thúc ở đâu để kéo người đọc sang chương sau")


class PartPlan(BaseModel):
    chapters: list[ChapterPlan]


class Issue(BaseModel):
    severity: Literal["critical", "major", "minor"]
    location: str = Field(description="Đoạn / câu trích dẫn ngắn hoặc vị trí trong chương")
    problem: str
    suggestion: str


class Review(BaseModel):
    score: float = Field(description="Điểm 0-10")
    strengths: list[str]
    issues: list[Issue]
    summary: str = Field(description="Nhận xét chung 1-3 câu")


class CharacterUpdate(BaseModel):
    name: str
    current_state: str = Field(description="Trạng thái MỚI sau chương: vị trí, thể chất, cảm xúc, quan hệ, điều đã biết")


class ChapterRecord(BaseModel):
    summary: str = Field(description="Tóm tắt chương 150-250 chữ, đủ để viết tiếp mà không cần đọc lại")
    key_events: list[str]
    character_updates: list[CharacterUpdate]
    new_characters: list[Character] = Field(description="Nhân vật mới xuất hiện có vai trò đáng kể")
    new_facts: list[str] = Field(description="Sự thật mới về thế giới / nhân vật phải giữ nhất quán về sau")
    threads_opened: list[str] = Field(description="Bí ẩn, lời hứa, chi tiết cài cắm mới cần giải quyết sau")
    threads_resolved: list[str] = Field(description="Nguyên văn các tuyến truyện đang mở đã được khép trong chương này")
    ending_state: str = Field(description="Chương dừng ở đâu: thời gian, địa điểm, ai đang làm gì")
