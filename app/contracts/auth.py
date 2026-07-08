from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class GuestSessionDTO(BaseModel):
    gender: str = Field(pattern=r"^(male|female)$")
    age: int = Field(ge=18, le=99)


class GuestSessionResponse(BaseModel):
    guest_session_id: UUID
    gender: str
    age: int


class UserRegisterDTO(BaseModel):
    guest_session_id: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    birth_date: date
    city: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    accepted_terms: bool

    @model_validator(mode="after")
    def require_contact(self) -> "UserRegisterDTO":
        if self.email is None and self.phone is None:
            raise ValueError("email or phone is required")
        if not self.accepted_terms:
            raise ValueError("accepted_terms must be true")
        return self


class UserLoginDTO(BaseModel):
    login: str = Field(min_length=3, max_length=255)
    password: str


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
    requires_2fa: bool = False


class UserResponseDTO(BaseModel):
    id: UUID
    name: str | None
    email: str | None
    phone: str | None
    city: str | None
    is_registered: bool
    gender: str | None
