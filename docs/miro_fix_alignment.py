#!/usr/bin/env python3
"""
Fix Miro board using the user's alignment method:
- Frames: 2000x1500 (or 3600 for wide flows), cols at x=-4200,-1800,400
- Stickies: LEFT=160, RIGHT=560, WIDTH=320, rows Y=160,550,950,1350
- Never full-width stickies inside frames

Usage:
  export MIRO_ACCESS_TOKEN=...
  export MIRO_BOARD_ID=uXjVH9Gr3u0=
  python3 docs/miro_fix_alignment.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

API = "https://api.miro.com/v2"
DELAY = 0.35

# User's measured layout from frames 1.2, 1.3-1.4, 2, 2.2
LEFT = 160
RIGHT = 560
W = 320
W_WIDE = 360
ROWS = (160, 550, 950, 1350, 1740)

COL_CX = (-4200, -1800, 400)
FRAME_W = 2000
FRAME_H = 1500
FRAME_H_TALL = 1750  # some AI frames can't shrink below 1750 via API
WIDE_W = 3600
WIDE_CX = -3400
ROW_GAP = 400


@dataclass
class S:
    text: str
    col: int  # 0=left 1=right
    row: int
    color: str = "light_yellow"
    wide: bool = False


@dataclass
class F:
    match: str
    title: str
    cx: float
    cy: float
    width: float
    height: float
    fill: str
    notes: list[S]


def y(row: int) -> float:
    return ROWS[row] if row < len(ROWS) else ROWS[-1] + (row - len(ROWS) + 1) * 390


def x(col: int, wide: bool = False) -> float:
    return LEFT if col == 0 else RIGHT


def note_geom(s: S) -> tuple[float, float, float]:
    return x(s.col, s.wide), y(s.row), W_WIDE if s.wide else W


def all_frames() -> list[F]:
    row5_cy = 6800.0
    anna_h = 1900.0  # row 4 (y=1740) needs taller frame than 1500
    row6_cy = row5_cy + anna_h / 2 + ROW_GAP + FRAME_H / 2
    row7_cy = row6_cy + FRAME_H / 2 + ROW_GAP + FRAME_H / 2

    anna_notes = [
        S("1. Скачивание", 0, 0, "light_pink"),
        S("2. Гость", 1, 0, "light_green"),
        S("3. 5 лайков", 0, 1, "light_green"),
        S("4. Регистрация", 1, 1, "yellow"),
        S("5. Модерация", 0, 2, "yellow"),
        S("6. Лента", 1, 2, "light_green"),
        S("7. Мэтч", 0, 3, "light_blue"),
        S("8. Кружки", 1, 3, "light_blue"),
        S("9. Свидание", 0, 4, "violet"),
        S("10. Оценка", 1, 4, "cyan"),
    ]

    return [
        F("Путь Анны", "Путь Анны: от скачивания до свидания", WIDE_CX, row5_cy, WIDE_W, anna_h, "#a6ccf5", anna_notes),
        F("Wireframes", "Wireframes - ключевые экраны приложения", COL_CX[0], row6_cy, FRAME_W, anna_h, "#d0e17a", [
            S("ЭКРАН: Гость", 0, 0, "light_green"),
            S("ЭКРАН: Анкеты", 1, 0, "light_green"),
            S("ЭКРАН: Корзина", 0, 1, "pink"),
            S("ЭКРАН: Регистрация", 1, 1, "yellow"),
            S("ЭКРАН: Модерация", 0, 2, "yellow"),
            S("ЭКРАН: Чат", 1, 2, "light_blue"),
            S("ЭКРАН: Звонок", 0, 3, "violet"),
            S("ЭКРАН: Профиль", 1, 3, "light_yellow"),
            S("ЭКРАН: Оценка", 0, 4, "cyan"),
        ]),
        F("Лендинг - что видит", "Лендинг - что видит заказчик (mockup)", COL_CX[1], row6_cy, FRAME_W, FRAME_H_TALL, "#f16c7f", [
            S("HERO\nУТП + видео", 0, 0, "light_pink"),
            S("CTA: App Store\nGoogle Play", 1, 0, "light_pink"),
            S("КАК РАБОТАЕТ\n3 шага", 0, 1, "light_yellow"),
            S("ПРЕИМУЩЕСТВА\n152-ФЗ", 1, 1, "light_green"),
            S("ОТЗЫВЫ · FAQ", 0, 2, "cyan"),
            S("FOOTER\nоферта, ПДн", 1, 2, "gray"),
            S("Сайт != app\nтолько CTA", 0, 3, "yellow", True),
        ]),
        F("Монетизация", "Монетизация в воронке", COL_CX[2], row6_cy, FRAME_W, FRAME_H_TALL, "#fff9b1", [
            S("Бесплатно:\nгость, 5 лайков", 0, 0, "light_green"),
            S("Регистрация\nбесплатно", 1, 0, "light_yellow"),
            S("1-й платёж:\nбаланс", 0, 1, "violet"),
            S("Звонок:\nпоминутно", 1, 1, "pink"),
            S("Запись 30 дней", 0, 2, "orange"),
            S("ЛК: подписка", 1, 2, "light_blue"),
        ]),
        F("Лента рекомендаций", "Лента рекомендаций (заказчик)", COL_CX[0], row7_cy, FRAME_W, FRAME_H, "#67c6c0", [
            S("Фильтрация\nсовместимость", 0, 0, "light_blue"),
            S("Поля: пол,\nгород, цели", 1, 0, "light_green"),
            S("2 канала:\nАнкеты + Рилсы", 0, 1, "cyan", True),
            S("Без дублей\nмежду каналами", 1, 1, "cyan"),
        ]),
        F("Модерация (заказчик", "Модерация (заказчик + ТЗ Brain)", COL_CX[1], row7_cy, FRAME_W, FRAME_H, "#f5d128", [
            S("Ручная или\nавто проверка", 0, 0, "yellow"),
            S("FFmpeg -> AI\n-> админ", 1, 0, "light_green"),
            S("Pending:\nнет в ленте", 0, 1, "orange"),
            S("Можно смотреть\nчужие анкеты", 1, 1, "orange"),
        ]),
    ]


class Client:
    def __init__(self, token: str, board: str) -> None:
        self.token = token
        self.board = board

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        from urllib.error import HTTPError

        data = json.dumps(body).encode() if body else None
        req = Request(
            f"{API}{path}",
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                out = json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode()
            raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc
        time.sleep(DELAY)
        return out

    def items(self) -> list[dict]:
        out: list[dict] = []
        cursor = None
        while True:
            q = "limit=50" + (f"&cursor={cursor}" if cursor else "")
            chunk = self.call("GET", f"/boards/{self.board}/items?{q}")
            out.extend(chunk.get("data", []))
            cursor = chunk.get("cursor")
            if not cursor:
                break
        return out

    def delete(self, iid: str) -> None:
        try:
            self.call("DELETE", f"/boards/{self.board}/items/{iid}")
        except Exception:
            pass


def find_frame(frames: list[dict], needle: str) -> dict | None:
    for f in frames:
        if needle in f.get("data", {}).get("title", ""):
            return f
    return None


def apply_frame(client: Client, plan: F) -> None:
    items = client.items()
    frames = [i for i in items if i["type"] == "frame"]
    frame = find_frame(frames, plan.match)
    if not frame:
        print(f"SKIP missing {plan.match}")
        return

    fid = frame["id"]
    print(f"FIX {plan.title}")

    for item in items:
        if item.get("type") == "sticky_note" and (item.get("parent") or {}).get("id") == fid:
            client.delete(item["id"])

    client.call(
        "PATCH",
        f"/boards/{client.board}/frames/{fid}",
        {
            "data": {"title": plan.title, "format": "custom", "type": "freeform"},
            "style": {"fillColor": plan.fill},
            "position": {"x": plan.cx, "y": plan.cy},
            "geometry": {"width": plan.width, "height": plan.height},
        },
    )

    for note in plan.notes:
        nx, ny, nw = note_geom(note)
        client.call(
            "POST",
            f"/boards/{client.board}/sticky_notes",
            {
                "data": {"content": note.text, "shape": "square"},
                "style": {
                    "fillColor": note.color,
                    "textAlign": "left",
                    "textAlignVertical": "top",
                },
                "position": {"x": nx, "y": ny},
                "geometry": {"width": nw},
                "parent": {"id": fid},
            },
        )

def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = Client(token, board)
    for plan in all_frames():
        apply_frame(client, plan)

    print("Alignment fix complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
