#!/usr/bin/env python3
"""
Apply recommended fixes and extensions to the VideoDating Miro board.

Usage:
  export MIRO_ACCESS_TOKEN="..."
  export MIRO_BOARD_ID="uXjVH9Gr3u0="
  python3 docs/miro_update_board.py
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
REQUEST_DELAY_SEC = 0.35


@dataclass
class StickySpec:
    content: str
    x: float
    y: float
    color: str = "light_yellow"
    width: float = 300


@dataclass
class FrameSpec:
    title: str
    x: float
    y: float
    width: float
    height: float
    fill: str = "#ffcee0"
    stickies: list[StickySpec] | None = None


class MiroClient:
    def __init__(self, token: str, board_id: str) -> None:
        self.token = token
        self.board_id = board_id

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{API_BASE}{path}"
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            err = exc.read().decode()
            raise RuntimeError(f"Miro API {exc.code} {path}: {err}") from exc
        finally:
            time.sleep(REQUEST_DELAY_SEC)

    def list_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            query = "limit=50"
            if cursor:
                query += f"&cursor={cursor}"
            data = self._request("GET", f"/boards/{self.board_id}/items?{query}")
            items.extend(data.get("data", []))
            cursor = data.get("cursor")
            if not cursor:
                break
        return items

    def delete_item(self, item_id: str) -> bool:
        try:
            self._request("DELETE", f"/boards/{self.board_id}/items/{item_id}")
            return True
        except RuntimeError as exc:
            if "404" in str(exc):
                return False
            raise

    def create_frame(self, spec: FrameSpec) -> str:
        payload = {
            "data": {"title": spec.title, "format": "custom", "type": "freeform"},
            "style": {"fillColor": spec.fill},
            "position": {"x": spec.x, "y": spec.y},
            "geometry": {"width": spec.width, "height": spec.height},
        }
        return self._request("POST", f"/boards/{self.board_id}/frames", payload)["id"]

    def create_sticky(
        self,
        *,
        content: str,
        x: float,
        y: float,
        parent_id: str,
        color: str = "light_yellow",
        width: float = 300,
    ) -> str:
        payload = {
            "data": {"content": content, "shape": "square"},
            "style": {
                "fillColor": color,
                "textAlign": "left",
                "textAlignVertical": "top",
            },
            "position": {"x": x, "y": y},
            "geometry": {"width": width},
            "parent": {"id": parent_id},
        }
        return self._request("POST", f"/boards/{self.board_id}/sticky_notes", payload)["id"]

    def create_connector(self, start_id: str, end_id: str) -> str:
        payload = {
            "startItem": {"id": start_id},
            "endItem": {"id": end_id},
            "shape": "curved",
            "style": {"strokeColor": "#1a1a2e", "strokeWidth": "2"},
        }
        return self._request("POST", f"/boards/{self.board_id}/connectors", payload)["id"]


def clean_html(text: str) -> str:
    t = re.sub("<[^<]+?>", "\n", text or "")
    t = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def count_stickies_in_frame(items: list[dict[str, Any]], frame_id: str) -> int:
    return sum(
        1
        for item in items
        if item.get("type") == "sticky_note" and (item.get("parent") or {}).get("id") == frame_id
    )


def cleanup_board(client: MiroClient, items: list[dict[str, Any]]) -> None:
    frames = [i for i in items if i.get("type") == "frame"]
    stickies = [i for i in items if i.get("type") == "sticky_note"]

    # Delete orphan canvas stickies
    for sticky in stickies:
        parent = (sticky.get("parent") or {}).get("id")
        content = clean_html(sticky.get("data", {}).get("content", ""))
        if not parent or content in {"t1", "test sticky"} or content.startswith("inside "):
            print(f"Delete sticky: {content[:40]}")
            client.delete_item(sticky["id"])

    # Delete TEST frame and its children
    for frame in frames:
        title = frame.get("data", {}).get("title", "")
        if title == "TEST delete me":
            fid = frame["id"]
            current = client.list_items()
            for sticky in current:
                if sticky.get("type") == "sticky_note" and (sticky.get("parent") or {}).get("id") == fid:
                    print("Delete test sticky")
                    client.delete_item(sticky["id"])
            print("Delete frame: TEST delete me")
            client.delete_item(fid)

    # Refresh after deletions
    items = client.list_items()
    frames = [i for i in items if i.get("type") == "frame"]

    # Delete empty duplicate «0. Сайт ≠ Приложение»
    site_frames = [f for f in frames if f.get("data", {}).get("title") == "0. Сайт ≠ Приложение"]
    if len(site_frames) > 1:
        for frame in sorted(site_frames, key=lambda f: count_stickies_in_frame(items, f["id"])):
            if count_stickies_in_frame(items, frame["id"]) == 0:
                print("Delete empty duplicate frame: 0. Сайт ≠ Приложение")
                client.delete_item(frame["id"])
                break


def find_frame_id(items: list[dict[str, Any]], title: str) -> str | None:
    for item in items:
        if item.get("type") == "frame" and item.get("data", {}).get("title") == title:
            return item["id"]
    return None


def connect_user_flow(client: MiroClient, items: list[dict[str, Any]]) -> None:
    frame_id = find_frame_id(items, "1. User Flow — воронка")
    if not frame_id:
        print("User Flow frame not found, skip connectors")
        return

    stickies = [
        s
        for s in items
        if s.get("type") == "sticky_note" and (s.get("parent") or {}).get("id") == frame_id
    ]

    def step_num(content: str) -> int | None:
        text = clean_html(content)
        match = re.match(r"^(\d+)\.", text)
        return int(match.group(1)) if match else None

    ordered = sorted(
        [s for s in stickies if step_num(s.get("data", {}).get("content", ""))],
        key=lambda s: step_num(s.get("data", {}).get("content", "")) or 0,
    )

    if len(ordered) < 10:
        print(f"Expected 10 funnel stickies, found {len(ordered)}")
        return

    print("Create 9 User Flow connectors")
    for i in range(9):
        client.create_connector(ordered[i]["id"], ordered[i + 1]["id"])


def build_new_frames() -> list[FrameSpec]:
    return [
        FrameSpec(
            title="Легенда статусов",
            x=-4200,
            y=-3600,
            width=900,
            height=520,
            fill="#f5f6f8",
            stickies=[
                StickySpec("🟢 ДОСТУПНО\nПользователь может выполнить действие сейчас", 80, 100, "light_green", 340),
                StickySpec("🟡 ОЖИДАНИЕ\nДействие в процессе (модерация, подтверждение)", 80, 250, "yellow", 340),
                StickySpec("🔴 ЗАБЛОКИРОВАНО\nНужна регистрация, мэтч или одобрение", 80, 400, "red", 340),
            ],
        ),
        FrameSpec(
            title="Путь Анны: от скачивания до свидания",
            x=-800,
            y=6600,
            width=5200,
            height=1100,
            fill="#a6ccf5",
            stickies=[
                StickySpec("1. Скачивает app\nиз лендинга", 120, 180, "light_pink", 200),
                StickySpec("2. Гость:\nпол + возраст", 360, 180, "light_green", 200),
                StickySpec("3. Листает анкеты\n5 лайков", 600, 180, "light_green", 200),
                StickySpec("4. Регистрация\n+ визитка 60с", 840, 180, "yellow", 200),
                StickySpec("5. Модерация\n(ждёт push)", 1080, 180, "yellow", 200),
                StickySpec("6. Лента + лайки\n30/сутки", 1320, 180, "light_green", 200),
                StickySpec("7. Мэтч\n→ чат", 1560, 180, "light_blue", 200),
                StickySpec("8. Видео-кружки\nпредсвидание", 1800, 180, "light_blue", 200),
                StickySpec("9. Видео-свидание\n💰 поминутно", 2040, 180, "violet", 200),
                StickySpec("10. Оценка\n4 критерия", 2280, 180, "cyan", 200),
                StickySpec(
                    "Заказчик: воронка Вход → Анкета → Модерация → Лента → Общение",
                    120,
                    520,
                    "gray",
                    900,
                ),
            ],
        ),
        FrameSpec(
            title="Wireframes — ключевые экраны приложения",
            x=-4200,
            y=6600,
            width=3000,
            height=1800,
            fill="#d0e17a",
            stickies=[
                StickySpec("ЭКРАН: Гость\n[пол] [возраст]\n[Начать просмотр]\n🟢", 120, 140, "light_green", 260),
                StickySpec("ЭКРАН: Анкеты\n[видео без звука]\n✕  ♥\n🟢", 420, 140, "light_green", 260),
                StickySpec("ЭКРАН: Регистрация\nимя · дата · город\nзапись визитки\n🟡", 120, 460, "yellow", 260),
                StickySpec("ЭКРАН: Ожидание модерации\n«Визитка на проверке»\nможно листать дальше\n🟡", 420, 460, "yellow", 260),
                StickySpec("ЭКРАН: Корзина\nЯ лайкнул | Лайкнули меня🔒\n🟢/🔴", 720, 140, "pink", 260),
                StickySpec("ЭКРАН: Чат\nтолько видео-кружки\n[свидание] [профиль]\n🟢", 720, 460, "light_blue", 260),
                StickySpec("ЭКРАН: Видео-звонок\nтаймер · камеры · баланс\n💰", 1020, 140, "violet", 260),
                StickySpec("ЭКРАН: Оценка\n4 критерия + отзыв\n🟢", 1020, 460, "cyan", 260),
                StickySpec("ЭКРАН: Профиль / ЛК\nрейтинг · баланс · подписка\n🟢", 1320, 300, "light_yellow", 280),
                StickySpec(
                    "Анкета (глубокие критерии — заказчик):\nобразование · интересы · цели отношений · видео-визитка\n(задел под фильтрацию совместимости)",
                    120,
                    780,
                    "orange",
                    1480,
                ),
            ],
        ),
        FrameSpec(
            title="Лендинг — что видит заказчик (mockup)",
            x=-800,
            y=8000,
            width=3000,
            height=1500,
            fill="#f16c7f",
            stickies=[
                StickySpec("HERO\nБрачное агентство + app\nвидео-превью\n[App Store] [Google Play]", 120, 140, "light_pink", 400),
                StickySpec("КАК РАБОТАЕТ\n1 визитка → 2 лайк → 3 свидание", 560, 140, "light_yellow", 400),
                StickySpec("ПРЕИМУЩЕСТВА\nмодерация · 152-ФЗ · живое видео", 120, 460, "light_green", 400),
                StickySpec("ОТЗЫВЫ · ТАРИФЫ · FAQ", 560, 460, "cyan", 400),
                StickySpec("FOOTER\nоферта · ПДн · контакты · QR", 120, 780, "gray", 840),
                StickySpec("⚠️ Сайт ≠ приложение. CTA только на скачивание.", 120, 1020, "yellow", 840),
            ],
        ),
        FrameSpec(
            title="Монетизация в воронке",
            x=2400,
            y=6600,
            width=2200,
            height=1500,
            fill="#fff9b1",
            stickies=[
                StickySpec("Бесплатно:\nгостевой просмотр\n5 лайков", 120, 140, "light_green", 320),
                StickySpec("Регистрация:\nбесплатно\nнужна для мэтчей", 120, 400, "light_yellow", 320),
                StickySpec("1-й платёж:\nпополнение баланса\nперед видео-свиданием\n💰 + 2FA", 120, 660, "violet", 320),
                StickySpec(
                    "Во время звонка:\nпоминутное списание\nМ75% / Ж25%\n«Оплачу полностью»",
                    500,
                    140,
                    "pink",
                    360,
                ),
                StickySpec("Дополнительно:\nзапись свидания 30 дней\n(платно, обоюдное согласие)", 500, 460, "orange", 360),
                StickySpec("ЛК: пакеты минут\nподписка / тарифы\npricing_plans", 500, 760, "light_blue", 360),
            ],
        ),
        FrameSpec(
            title="Модерация (заказчик + ТЗ Brain)",
            x=2400,
            y=8300,
            width=2200,
            height=1200,
            fill="#f5d128",
            stickies=[
                StickySpec(
                    "Заказчик: ручная ИЛИ автоматическая\nпроверка видео-визиток",
                    120,
                    140,
                    "yellow",
                    880,
                ),
                StickySpec(
                    "Гибрид (рекомендация):\nFFmpeg → AI пре-мод → админ\n70-80% автофильтр",
                    120,
                    380,
                    "light_green",
                    880,
                ),
                StickySpec(
                    "Пока pending:\n❌ нет в ленте\n✅ можно смотреть чужие анкеты",
                    120,
                    680,
                    "orange",
                    880,
                ),
            ],
        ),
        FrameSpec(
            title="Лента рекомендаций (заказчик)",
            x=-4200,
            y=8600,
            width=3000,
            height=1000,
            fill="#67c6c0",
            stickies=[
                StickySpec(
                    "Фильтрация по совместимости и приоритетам пользователя\n(заказчик)",
                    120,
                    140,
                    "light_blue",
                    1280,
                ),
                StickySpec(
                    "База: пол · возраст · город · цели · интересы\nиндексы GIN/btree для скорости",
                    120,
                    360,
                    "light_green",
                    1280,
                ),
                StickySpec(
                    "2 канала: Анкеты (свайп) + Видео-лента (рилсы)\nбез дублей между каналами",
                    120,
                    580,
                    "cyan",
                    1280,
                ),
            ],
        ),
    ]


def add_frames(client: MiroClient) -> None:
    items = client.list_items()
    existing_titles = {
        i.get("data", {}).get("title", "")
        for i in items
        if i.get("type") == "frame"
    }

    funnel_ids: list[str] = []
    for frame in build_new_frames():
        if frame.title in existing_titles:
            print(f"Skip existing frame: {frame.title}")
            continue
        print(f"Add frame: {frame.title}")
        frame_id = client.create_frame(frame)
        for sticky in frame.stickies or []:
            sid = client.create_sticky(
                content=sticky.content,
                x=sticky.x,
                y=sticky.y,
                parent_id=frame_id,
                color=sticky.color,
                width=sticky.width,
            )
            if frame.title == "Путь Анны: от скачивания до свидания" and sticky.x < 2500:
                if re.match(r"^\d+\.", sticky.content):
                    funnel_ids.append(sid)

    if len(funnel_ids) >= 10:
        print("Create 9 Anna journey connectors")
        for i in range(9):
            client.create_connector(funnel_ids[i], funnel_ids[i + 1])


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board_id = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()

    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = MiroClient(token, board_id)
    print("=== Cleanup ===")
    items = client.list_items()
    cleanup_board(client, items)

    print("=== User Flow connectors ===")
    items = client.list_items()
    connect_user_flow(client, items)

    print("=== New frames ===")
    add_frames(client)

    print("Done. Open board and press Fit to screen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
