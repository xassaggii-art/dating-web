from pydantic import BaseModel


class ThemeColorsDTO(BaseModel):
    background: str
    surface: str
    primary: str
    primary_hover: str
    secondary: str
    accent: str
    text_primary: str
    text_secondary: str
    text_on_primary: str
    border: str
    success: str
    error: str
    like: str
    match: str


class ThemeDTO(BaseModel):
    id: str
    name: str
    description: str
    colors: ThemeColorsDTO


class ThemesResponseDTO(BaseModel):
    default_theme_id: str
    themes: list[ThemeDTO]
