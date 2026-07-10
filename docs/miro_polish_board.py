#!/usr/bin/env python3
"""
Polish Miro board: human dashes, grid layout, text alignment for added frames.

Usage:
  export MIRO_ACCESS_TOKEN="..."
  export MIRO_BOARD_ID="uXjVH9Gr3u0="
  python3 docs/miro_polish_board.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.miro.com/v2"
DELAY = 0.35

FRAMES_TO_POLISH = [
    "Легенда статусов",
    "Путь Анны: от скачивания до свидания",
    "Wireframes",
    "Лендинг - что видит заказчик",
    "Монетизация в воронке",
    "Модерация (заказчик",
    "Лента рекомендаций",
]


def humanize(text: str) -> str:
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("→", "->")
    text = re.sub(r"\s+-\s+", " - ", text)
    return text.strip()


@dataclass
class Note:
    content: str
    x: float
    y: float
    color: str = "light_yellow"
    width: float = 280
    align: str = "center"
    valign: str = "middle"


@dataclass
class FrameLayout:
    title_match: str
    new_title: str
    x: float
    y: float
    width: float
    height: float
    fill: str
    notes: list[Note]


LAYOUTS: list[FrameLayout] = [
    FrameLayout(
        "Легенда статусов",
        "Легенда статусов",
        -4200,
        -3600,
        980,
        700,
        "#f5f6f8",
        [
            Note("🟢 ДОСТУПНО\nДействие доступно сейчас", 490, 130, "light_green", 760, "center", "middle"),
            Note("🟡 ОЖИДАНИЕ\nМодерация, подтверждение, ожидание", 490, 330, "yellow", 760, "center", "middle"),
            Note("🔴 ЗАБЛОКИРОВАНО\nНужна регистрация, мэтч или одобрение", 490, 530, "red", 760, "center", "middle"),
        ],
    ),
    FrameLayout(
        "Путь Анны",
        "Путь Анны: от скачивания до свидания",
        -900,
        6600,
        5400,
        1300,
        "#a6ccf5",
        [
            Note("1. Скачивание\nс лендинга", 130, 220, "light_pink", 210, "center", "middle"),
            Note("2. Гость\nпол + возраст", 390, 220, "light_green", 210, "center", "middle"),
            Note("3. Листает\n5 лайков", 650, 220, "light_green", 210, "center", "middle"),
            Note("4. Регистрация\n+ визитка", 910, 220, "yellow", 210, "center", "middle"),
            Note("5. Модерация\nожидание", 1170, 220, "yellow", 210, "center", "middle"),
            Note("6. Лента\n30 лайков/сутки", 1430, 220, "light_green", 210, "center", "middle"),
            Note("7. Мэтч\nоткрыт чат", 1690, 220, "light_blue", 210, "center", "middle"),
            Note("8. Видео-кружки\nперед свиданием", 1950, 220, "light_blue", 210, "center", "middle"),
            Note("9. Видео-свидание\nпоминутная оплата", 2210, 220, "violet", 210, "center", "middle"),
            Note("10. Оценка\n4 критерия", 2470, 220, "cyan", 210, "center", "middle"),
            Note(
                "Воронка заказчика: Вход -> Анкета -> Модерация -> Лента -> Общение",
                2700,
                220,
                "gray",
                420,
                "center",
                "middle",
            ),
        ],
    ),
    FrameLayout(
        "Wireframes",
        "Wireframes - ключевые экраны приложения",
        -4200,
        6600,
        3300,
        2000,
        "#d0e17a",
        [
            Note("ЭКРАН: Гость\n[пол] [возраст]\n[Начать]\n🟢", 200, 180, "light_green", 300, "center", "middle"),
            Note("ЭКРАН: Анкеты\n[видео]\n✕  ♥\n🟢", 560, 180, "light_green", 300, "center", "middle"),
            Note("ЭКРАН: Корзина\nлайки / мэтчи\n🟢", 920, 180, "pink", 300, "center", "middle"),
            Note("ЭКРАН: Регистрация\nимя, дата, город\nвизитка\n🟡", 200, 520, "yellow", 300, "center", "middle"),
            Note("ЭКРАН: Модерация\n«На проверке»\nможно листать\n🟡", 560, 520, "yellow", 300, "center", "middle"),
            Note("ЭКРАН: Чат\nвидео-кружки\n[свидание]\n🟢", 920, 520, "light_blue", 300, "center", "middle"),
            Note("ЭКРАН: Звонок\nтаймер, камеры\nбаланс\n💰", 200, 860, "violet", 300, "center", "middle"),
            Note("ЭКРАН: Оценка\n4 критерия\n🟢", 560, 860, "cyan", 300, "center", "middle"),
            Note("ЭКРАН: Профиль\nрейтинг, баланс\n🟢", 920, 860, "light_yellow", 300, "center", "middle"),
            Note(
                "Анкета (заказчик): образование, интересы, цели отношений, видео-визитка. Задел под фильтрацию совместимости.",
                1650,
                520,
                "orange",
                360,
                "left",
                "middle",
            ),
        ],
    ),
    FrameLayout(
        "Лендинг",
        "Лендинг - что видит заказчик (mockup)",
        -900,
        8100,
        3200,
        1650,
        "#f16c7f",
        [
            Note("HERO\nАгентство + app\nвидео-превью\n[App Store] [Google Play]", 420, 200, "light_pink", 520, "center", "middle"),
            Note("КАК РАБОТАЕТ\n1 визитка\n2 лайк\n3 свидание", 1080, 200, "light_yellow", 520, "center", "middle"),
            Note("ПРЕИМУЩЕСТВА\nмодерация\n152-ФЗ\nживое видео", 420, 620, "light_green", 520, "center", "middle"),
            Note("ОТЗЫВЫ · ТАРИФЫ · FAQ", 1080, 620, "cyan", 520, "center", "middle"),
            Note("FOOTER: оферта, ПДн, контакты, QR-код", 750, 1020, "gray", 1100, "center", "middle"),
            Note("Сайт не равен приложению. На сайте только CTA на скачивание.", 750, 1320, "yellow", 1100, "center", "middle"),
        ],
    ),
    FrameLayout(
        "Монетизация",
        "Монетизация в воронке",
        2450,
        6600,
        2400,
        1650,
        "#fff9b1",
        [
            Note("Бесплатно:\nгость, 5 лайков\nпросмотр ленты", 400, 200, "light_green", 480, "center", "middle"),
            Note("Регистрация:\nбесплатно\nнужна для мэтчей", 1200, 200, "light_yellow", 480, "center", "middle"),
            Note("1-й платёж:\nпополнение баланса\nперед свиданием\n2FA", 400, 620, "violet", 480, "center", "middle"),
            Note("Звонок:\nпоминутно\nМ 75% / Ж 25%", 1200, 620, "pink", 480, "center", "middle"),
            Note("Дополнительно:\nзапись 30 дней\nпо согласию", 400, 1040, "orange", 480, "center", "middle"),
            Note("ЛК:\nпакеты минут\nподписка / тарифы", 1200, 1040, "light_blue", 480, "center", "middle"),
        ],
    ),
    FrameLayout(
        "Модерация (заказчик",
        "Модерация (заказчик + ТЗ Brain)",
        2450,
        8450,
        2400,
        1250,
        "#f5d128",
        [
            Note("Заказчик: ручная или автоматическая проверка видео-визиток", 1200, 180, "yellow", 2100, "center", "middle"),
            Note("Гибрид: FFmpeg -> AI пре-мод -> админ. 70-80% автофильтр", 1200, 480, "light_green", 2100, "center", "middle"),
            Note("Пока pending: нет в ленте, но можно смотреть чужие анкеты", 1200, 780, "orange", 2100, "center", "middle"),
        ],
    ),
    FrameLayout(
        "Лента рекомендаций",
        "Лента рекомендаций (заказчик)",
        -4200,
        8750,
        3300,
        1150,
        "#67c6c0",
        [
            Note("Фильтрация по совместимости и приоритетам пользователя", 1650, 180, "light_blue", 2900, "center", "middle"),
            Note("База: пол, возраст, город, цели, интересы. Индексы GIN/btree", 1650, 430, "light_green", 2900, "center", "middle"),
            Note("2 канала: Анкеты (свайп) и Видео-лента (рилсы), без дублей", 1650, 680, "cyan", 2900, "center", "middle"),
        ],
    ),
]


class MiroClient:
    def __init__(self, token: str, board_id: str) -> None:
        self.token = token
        self.board_id = board_id

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{API_BASE}{path}"
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(
            url,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            raise RuntimeError(f"Miro {exc.code} {path}: {exc.read().decode()[:400]}") from exc
        finally:
            time.sleep(DELAY)

    def list_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor = None
        while True:
            q = "limit=50" + (f"&cursor={cursor}" if cursor else "")
            data = self._request("GET", f"/boards/{self.board_id}/items?{q}")
            items.extend(data.get("data", []))
            cursor = data.get("cursor")
            if not cursor:
                break
        return items

    def delete_item(self, item_id: str) -> None:
        try:
            self._request("DELETE", f"/boards/{self.board_id}/items/{item_id}")
        except RuntimeError as exc:
            if "404" not in str(exc):
                raise

    def update_frame(self, item_id: str, layout: FrameLayout) -> None:
        payload = {
            "data": {"title": layout.new_title, "format": "custom", "type": "freeform"},
            "style": {"fillColor": layout.fill},
            "position": {"x": layout.x, "y": layout.y},
            "geometry": {"width": layout.width, "height": layout.height},
        }
        self._request("PATCH", f"/boards/{self.board_id}/frames/{item_id}", payload)

    def create_sticky(self, parent_id: str, note: Note) -> str:
        payload = {
            "data": {"content": humanize(note.content), "shape": "square"},
            "style": {
                "fillColor": note.color,
                "textAlign": note.align,
                "textAlignVertical": note.valign,
            },
            "position": {"x": note.x, "y": note.y},
            "geometry": {"width": note.width},
            "parent": {"id": parent_id},
        }
        return self._request("POST", f"/boards/{self.board_id}/sticky_notes", payload)["id"]

    def update_sticky_text(self, item_id: str, content: str, align: str = "left") -> None:
        payload = {
            "data": {"content": humanize(content)},
            "style": {"textAlign": align, "textAlignVertical": "top"},
        }
        self._request("PATCH", f"/boards/{self.board_id}/sticky_notes/{item_id}", payload)

    def create_connector(self, a: str, b: str) -> None:
        payload = {
            "startItem": {"id": a},
            "endItem": {"id": b},
            "shape": "curved",
            "style": {"strokeColor": "#1a1a2e", "strokeWidth": "2"},
        }
        self._request("POST", f"/boards/{self.board_id}/connectors", payload)


def clean_html(text: str) -> str:
    t = re.sub("<[^<]+?>", "\n", text or "")
    t = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r"\s+", " ", t).strip()
    return humanize(t)


def find_frame(frames: list[dict[str, Any]], match: str) -> dict[str, Any] | None:
    for frame in frames:
        title = frame.get("data", {}).get("title", "")
        if title == match or (match not in ("Лендинг", "Wireframes", "Монетизация", "Путь Анны", "Модерация (заказчик") and match in title):
            return frame
    for frame in frames:
        title = frame.get("data", {}).get("title", "")
        if match in title:
            return frame
    return None


def polish_frames(client: MiroClient) -> list[str]:
    items = client.list_items()
    frames = [i for i in items if i.get("type") == "frame"]
    anna_ids: list[str] = []

    for layout in LAYOUTS:
        frame = find_frame(frames, layout.title_match)
        if not frame:
            print(f"Skip missing frame: {layout.title_match}")
            continue

        fid = frame["id"]
        print(f"Polish frame: {layout.new_title}")

        # remove old stickies
        items = client.list_items()
        for item in items:
            if item.get("type") == "sticky_note" and (item.get("parent") or {}).get("id") == fid:
                client.delete_item(item["id"])

        client.update_frame(fid, layout)

        for note in layout.notes:
            sid = client.create_sticky(fid, note)
            if layout.title_match == "Путь Анны" and note.content[0].isdigit():
                anna_ids.append(sid)

    return anna_ids


def humanize_all_stickies(client: MiroClient) -> None:
    items = client.list_items()
    count = 0
    for item in items:
        if item.get("type") != "sticky_note":
            continue
        raw = item.get("data", {}).get("content", "")
        text = clean_html(raw)
        if "—" in raw or "–" in raw or "→" in text or text != clean_html(raw):
            client.update_sticky_text(item["id"], text)
            count += 1
    print(f"Humanized {count} stickies board-wide")


def connect_anna(client: MiroClient, ids: list[str]) -> None:
    if len(ids) < 10:
        return
    print("Reconnect Anna journey (9 arrows)")
    for i in range(9):
        client.create_connector(ids[i], ids[i + 1])


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board_id = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = MiroClient(token, board_id)
    anna_ids = polish_frames(client)
    humanize_all_stickies(client)
    connect_anna(client, anna_ids)
    print("Polish complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
