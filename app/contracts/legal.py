from pydantic import BaseModel


class LegalSectionDTO(BaseModel):
    heading: str
    body: str


class LegalDocumentDTO(BaseModel):
    title: str
    sections: list[LegalSectionDTO]


class LegalConfigDTO(BaseModel):
    pd_consent_version: str
    operator_name: str
    operator_email: str
    privacy: LegalDocumentDTO
    terms: LegalDocumentDTO
