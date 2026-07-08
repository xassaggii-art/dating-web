from fastapi import APIRouter, HTTPException, status

from app.contracts.legal import LegalConfigDTO
from app.contracts.theme import ThemeDTO, ThemesResponseDTO
from app.services.legal_service import load_legal_config
from app.services.theme_service import get_theme, load_themes

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/legal", response_model=LegalConfigDTO)
async def get_legal() -> LegalConfigDTO:
    return load_legal_config()


@router.get("/themes", response_model=ThemesResponseDTO)
async def list_themes() -> ThemesResponseDTO:
    return load_themes()


@router.get("/themes/{theme_id}", response_model=ThemeDTO)
async def get_theme_by_id(theme_id: str) -> ThemeDTO:
    theme = get_theme(theme_id)
    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
    return theme
