from pydantic import BaseModel, Field


class FaqItemDTO(BaseModel):
    question: str
    answer: str


class SupportFaqResponse(BaseModel):
    items: list[FaqItemDTO]


class SupportMessageDTO(BaseModel):
    message: str = Field(min_length=10, max_length=2000)
    email: str | None = Field(default=None, max_length=255)


class ReportProfileDTO(BaseModel):
    reported_user_id: str
    reason: str = Field(min_length=3, max_length=500)
