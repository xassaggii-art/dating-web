#!/usr/bin/env python3
"""
Re-layout bottom Miro frames to match the clean 3-column grid (no overlap).

Usage:
  export MIRO_ACCESS_TOKEN=...
  export MIRO_BOARD_ID=uXjVH9Gr3u0=
  python3 docs/miro_relayout_board.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

API = "https://api.miro.com/v2"
DELAY = 0.35

# Same grid as user's top blocks: centers -4200, -1800, 400; width 2000
COL_X = (-4200, -1800, 400)
FRAME_W = 2000
ROW_GAP = 450


@dataclass
class FramePlan:
    match: str
    title: str
    col: int  # 0..2 or -1 for full span
    row: int
    height: float
    fill: str
    span: int = 1  # columns spanned
    notes: list[tuple[str, float, float, str, float]] | None = None
    # note: content, x, y, color, width


def row_center_y(prev_bottom: float, height: float) -> float:
    return prev_bottom + ROW_GAP + height / 2


def frame_x(col: int, span: int = 1) -> float:
    if span == 3:
        return -1800
    if span == 2 and col == 0:
        return -3000
    return COL_X[col]


def frame_width(span: int) -> float:
    if span == 3:
        return FRAME_W * 3 + 800  # 6800 across all cols
    if span == 2:
        return FRAME_W * 2 + 400
    return FRAME_W


PLANS: list[FramePlan] = [
    FramePlan("Легенда", "Легенда статусов", 0, 0, 620, "#f5f6f8", 1, [
        ("🟢 ДОСТУПНО\nДействие доступно сейчас", 120, 120, "light_green", 1760),
        ("🟡 ОЖИДАНИЕ\nМодерация, подтверждение", 120, 300, "yellow", 1760),
        ("🔴 ЗАБЛОКИРОВАНО\nНужна регистрация или мэтч", 120, 480, "red", 1760),
    ]),
    # row 5 starts after block 4 bottom 5650
    FramePlan("Путь Анны", "Путь Анны: от скачивания до свидания", -1, 5, 1100, "#a6ccf5", 3, [
        ("1 Скачивание", 140, 200, "light_pink", 200),
        ("2 Гость", 380, 200, "light_green", 200),
        ("3 5 лайков", 620, 200, "light_green", 200),
        ("4 Регистрация", 860, 200, "yellow", 200),
        ("5 Модерация", 1100, 200, "yellow", 200),
        ("6 Лента", 1340, 200, "light_green", 200),
        ("7 Мэтч", 1580, 200, "light_blue", 200),
        ("8 Кружки", 1820, 200, "light_blue", 200),
        ("9 Свидание", 2060, 200, "violet", 200),
        ("10 Оценка", 2300, 200, "cyan", 200),
        ("Воронка: Вход -> Анкета -> Модерация -> Лента -> Общение", 140, 520, "gray", 6400),
    ]),
    FramePlan("Wireframes", "Wireframes - ключевые экраны приложения", 0, 6, 1750, "#d0e17a", 1, [
        ("ЭКРАН: Гость\n🟢", 120, 120, "light_green", 280),
        ("ЭКРАН: Анкеты\n🟢", 460, 120, "light_green", 280),
        ("ЭКРАН: Корзина\n🟢", 120, 420, "pink", 280),
        ("ЭКРАН: Регистрация\n🟡", 460, 420, "yellow", 280),
        ("ЭКРАН: Модерация\n🟡", 120, 720, "yellow", 280),
        ("ЭКРАН: Чат\n🟢", 460, 720, "light_blue", 280),
        ("ЭКРАН: Звонок\n💰", 120, 1020, "violet", 280),
        ("ЭКРАН: Оценка\n🟢", 460, 1020, "cyan", 280),
        ("ЭКРАН: Профиль\n🟢", 120, 1320, "light_yellow", 280),
        ("Анкета: образование, интересы, цели, видео-визитка", 800, 120, "orange", 1080),
    ]),
    FramePlan("Лендинг - что видит", "Лендинг - что видит заказчик (mockup)", 1, 6, 1750, "#f16c7f", 1, [
        ("HERO\nУТП + видео\nApp Store / Google Play", 120, 120, "light_pink", 1760),
        ("КАК РАБОТАЕТ\nвизитка -> лайк -> свидание", 120, 420, "light_yellow", 1760),
        ("ПРЕИМУЩЕСТВА\nмодерация, 152-ФЗ", 120, 720, "light_green", 1760),
        ("ОТЗЫВЫ · ТАРИФЫ · FAQ", 120, 1020, "cyan", 1760),
        ("FOOTER: оферта, ПДн, QR", 120, 1320, "gray", 1760),
        ("Сайт не равен приложению. Только CTA на скачивание.", 120, 1520, "yellow", 1760),
    ]),
    FramePlan("Монетизация", "Монетизация в воронке", 2, 6, 1750, "#fff9b1", 1, [
        ("Бесплатно: гость, 5 лайков", 120, 120, "light_green", 1760),
        ("Регистрация бесплатно", 120, 380, "light_yellow", 1760),
        ("1-й платёж: баланс перед свиданием", 120, 640, "violet", 1760),
        ("Звонок: поминутно М75% / Ж25%", 120, 900, "pink", 1760),
        ("Запись 30 дней (платно)", 120, 1160, "orange", 1760),
        ("ЛК: пакеты, подписка", 120, 1420, "light_blue", 1760),
    ]),
    FramePlan("Лента рекомендаций", "Лента рекомендаций (заказчик)", 0, 7, 1300, "#67c6c0", 1, [
        ("Фильтрация по совместимости и приоритетам", 120, 120, "light_blue", 1760),
        ("Поля: пол, возраст, город, цели, интересы", 120, 400, "light_green", 1760),
        ("2 канала: Анкеты и Видео-лента, без дублей", 120, 680, "cyan", 1760),
    ]),
    FramePlan("Модерация (заказчик", "Модерация (заказчик + ТЗ Brain)", 1, 7, 1300, "#f5d128", 1, [
        ("Ручная или автоматическая проверка визиток", 120, 120, "yellow", 1760),
        ("Гибрид: FFmpeg -> AI -> админ", 120, 400, "light_green", 1760),
        ("Pending: нет в ленте, но можно смотреть анкеты", 120, 680, "orange", 1760),
    ]),
]


class Client:
    def __init__(self, token: str, board: str) -> None:
        self.token = token
        self.board = board

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body else None
        req = Request(
            f"{API}{path}",
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            out = json.loads(raw) if raw else {}
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


def compute_positions() -> dict[str, tuple[float, float, float, float]]:
    """Return match -> (x, y, width, height)."""
    positions: dict[str, tuple[float, float, float, float]] = {}
    positions["Легенда"] = (-4200, -3600, FRAME_W, 620)

    row_bottom = 5650.0  # end of row 4 (Поставка и этапы)
    by_row: dict[int, list[FramePlan]] = {}
    for plan in PLANS:
        if plan.match == "Легенда":
            continue
        by_row.setdefault(plan.row, []).append(plan)

    for row in sorted(by_row):
        plans = by_row[row]
        height = max(p.height for p in plans)
        cy = row_center_y(row_bottom, height)
        for plan in plans:
            x = frame_x(plan.col, plan.span) if plan.col >= 0 else frame_x(0, plan.span)
            w = frame_width(plan.span)
            positions[plan.match] = (x, cy, w, plan.height)
        row_bottom = cy + height / 2

    return positions


def relayout(client: Client) -> None:
    positions = compute_positions()
    items = client.items()
    frames = [i for i in items if i["type"] == "frame"]
    anna_step_ids: list[str] = []

    for plan in PLANS:
        frame = find_frame(frames, plan.match)
        if not frame:
            print(f"missing: {plan.match}")
            continue

        fid = frame["id"]
        x, y, w, h = positions[plan.match]
        print(f"move {plan.title} -> ({x},{y}) {w}x{h}")

        # clear stickies
        for item in client.items():
            if item.get("type") == "sticky_note" and (item.get("parent") or {}).get("id") == fid:
                client.delete(item["id"])

        client.call(
            "PATCH",
            f"/boards/{client.board}/frames/{fid}",
            {
                "data": {"title": plan.title, "format": "custom", "type": "freeform"},
                "style": {"fillColor": plan.fill},
                "position": {"x": x, "y": y},
                "geometry": {"width": w, "height": h},
            },
        )

        for note in plan.notes or []:
            content, nx, ny, color, width = note
            sid = client.call(
                "POST",
                f"/boards/{client.board}/sticky_notes",
                {
                    "data": {"content": content, "shape": "square"},
                    "style": {
                        "fillColor": color,
                        "textAlign": "center",
                        "textAlignVertical": "middle",
                    },
                    "position": {"x": nx, "y": ny},
                    "geometry": {"width": width},
                    "parent": {"id": fid},
                },
            )["id"]
            if plan.match == "Путь Анны" and content[0].isdigit():
                anna_step_ids.append(sid)

    if len(anna_step_ids) >= 10:
        for i in range(9):
            client.call(
                "POST",
                f"/boards/{client.board}/connectors",
                {
                    "startItem": {"id": anna_step_ids[i]},
                    "endItem": {"id": anna_step_ids[i + 1]},
                    "shape": "curved",
                    "style": {"strokeColor": "#1a1a2e", "strokeWidth": "2"},
                },
            )


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1
    relayout(Client(token, board))
    print("Relayout done. Fit to screen on the NEW area below row 4.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
