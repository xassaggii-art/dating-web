from pydantic import BaseModel, Field


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFactorCodeDTO(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TwoFactorStatusDTO(BaseModel):
    enabled: bool
