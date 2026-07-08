import json
from functools import lru_cache
from pathlib import Path

from app.contracts.legal import LegalConfigDTO, LegalDocumentDTO, LegalSectionDTO

LEGAL_PATH = Path(__file__).resolve().parents[2] / "design" / "legal.json"


@lru_cache
def load_legal_config() -> LegalConfigDTO:
    data = json.loads(LEGAL_PATH.read_text(encoding="utf-8"))

    def doc(key: str) -> LegalDocumentDTO:
        d = data["documents"][key]
        return LegalDocumentDTO(
            title=d["title"],
            sections=[LegalSectionDTO(**s) for s in d["sections"]],
        )

    return LegalConfigDTO(
        pd_consent_version=data["pd_consent_version"],
        operator_name=data["operator_name"],
        operator_email=data["operator_email"],
        privacy=doc("privacy"),
        terms=doc("terms"),
    )
