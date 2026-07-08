import json
from pathlib import Path

from app.contracts.theme import ThemeColorsDTO, ThemeDTO, ThemesResponseDTO

_THEMES_PATH = Path(__file__).resolve().parents[2] / "design" / "themes.json"


def load_themes() -> ThemesResponseDTO:
    data = json.loads(_THEMES_PATH.read_text(encoding="utf-8"))
    themes = [
        ThemeDTO(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            colors=ThemeColorsDTO(**t["colors"]),
        )
        for t in data["themes"].values()
    ]
    return ThemesResponseDTO(default_theme_id=data["default_theme_id"], themes=themes)


def get_theme(theme_id: str) -> ThemeDTO | None:
    response = load_themes()
    for theme in response.themes:
        if theme.id == theme_id:
            return theme
    return None
