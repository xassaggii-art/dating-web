#!/usr/bin/env python3
"""
Populate a Miro board with VideoDating product specification.

Usage:
  export MIRO_ACCESS_TOKEN="your_token"
  export MIRO_BOARD_ID="uXjV..."
  python3 docs/miro_populate_board.py

Optional:
  export MIRO_DRY_RUN=1   # print actions without API calls
"""

from __future__ import annotations

import json
import os
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
    width: float = 320


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
    def __init__(self, token: str, board_id: str, *, dry_run: bool = False) -> None:
        self.token = token
        self.board_id = board_id
        self.dry_run = dry_run
        self._counter = 0

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{API_BASE}{path}"
        body = json.dumps(payload).encode() if payload is not None else None
        if self.dry_run:
            self._counter += 1
            fake_id = f"dry_{self._counter}"
            print(f"[DRY] {method} {path}")
            return {"id": fake_id}
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
                data = resp.read().decode()
                return json.loads(data) if data else {}
        except HTTPError as exc:
            err = exc.read().decode()
            raise RuntimeError(f"Miro API {exc.code} {path}: {err}") from exc
        finally:
            time.sleep(REQUEST_DELAY_SEC)

    def create_frame(self, spec: FrameSpec) -> str:
        payload = {
            "data": {"title": spec.title, "format": "custom", "type": "freeform"},
            "style": {"fillColor": spec.fill},
            "position": {"x": spec.x, "y": spec.y},
            "geometry": {"width": spec.width, "height": spec.height},
        }
        result = self._request("POST", f"/boards/{self.board_id}/frames", payload)
        return result["id"]

    def create_sticky(
        self,
        *,
        content: str,
        x: float,
        y: float,
        parent_id: str | None,
        color: str = "light_yellow",
        width: float = 320,
    ) -> str:
        payload: dict[str, Any] = {
            "data": {"content": content, "shape": "square"},
            "style": {
                "fillColor": color,
                "textAlign": "left",
                "textAlignVertical": "top",
            },
            "position": {"x": x, "y": y},
            "geometry": {"width": width},
        }
        if parent_id:
            payload["parent"] = {"id": parent_id}
        result = self._request("POST", f"/boards/{self.board_id}/sticky_notes", payload)
        return result["id"]

    def create_connector(self, start_id: str, end_id: str) -> str:
        payload = {
            "startItem": {"id": start_id},
            "endItem": {"id": end_id},
            "shape": "curved",
            "style": {"strokeColor": "#1a1a2e", "strokeWidth": "2"},
        }
        result = self._request("POST", f"/boards/{self.board_id}/connectors", payload)
        return result["id"]


def build_frames() -> list[FrameSpec]:
    return [
        FrameSpec(
            title="0. Сайт ≠ Приложение",
            x=-4200,
            y=-2200,
            width=2000,
            height=1400,
            fill="#ea94bb",
            stickies=[
                StickySpec(
                    "📱 ПРИЛОЖЕНИЕ (iOS/Android)\nОсновной продукт:\n• анкеты и свайпы\n• лайки и корзина\n• чаты (видео-кружки)\n• видео-свидания\n• личный кабинет",
                    180,
                    180,
                    "light_blue",
                    360,
                ),
                StickySpec(
                    "🌐 САЙТ = ЛЕНДИНГ\nРеклама агентства + приложения:\n• УТП и позиционирование\n• как работает (3–5 шагов)\n• отзывы, доверие, 152-ФЗ\n• CTA: App Store / Google Play\n• оферта, политика ПДн",
                    560,
                    180,
                    "light_pink",
                    360,
                ),
                StickySpec(
                    "⚠️ Web-прототип — только демо логики для разработчиков, не публичный сайт.",
                    180,
                    720,
                    "yellow",
                    740,
                ),
            ],
        ),
        FrameSpec(
            title="1. User Flow — воронка",
            x=-1800,
            y=-2200,
            width=3600,
            height=1400,
            fill="#a6ccf5",
            stickies=[
                StickySpec("1. Первый визит", 200, 200, "light_green", 220),
                StickySpec("2. Гость\n(пол + возраст)", 500, 200, "light_green", 220),
                StickySpec("3. Регистрация\n+ визитка", 800, 200, "light_yellow", 220),
                StickySpec("4. Модерация\nвизитки", 1100, 200, "orange", 220),
                StickySpec("5. Полный доступ\nв ленте", 1400, 200, "light_green", 220),
                StickySpec("6. Лайки", 1700, 200, "pink", 220),
                StickySpec("7. Мэтч", 2000, 200, "pink", 220),
                StickySpec("8. Чат", 2300, 200, "light_blue", 220),
                StickySpec("9. Видео-свидание", 2600, 200, "violet", 220),
                StickySpec("10. Оценка", 2900, 200, "cyan", 220),
                StickySpec(
                    "Навигация (5 вкладок):\n1 Анкеты · 2 Видео-лента · 3 Сообщения · 4 Корзина · 5 Профиль",
                    200,
                    520,
                    "gray",
                    700,
                ),
            ],
        ),
        FrameSpec(
            title="1.2 Гостевой режим",
            x=-4200,
            y=-500,
            width=2000,
            height=1600,
            fill="#d5f692",
            stickies=[
                StickySpec("Первый запуск → пол + возраст → лента", 160, 160, "light_yellow"),
                StickySpec("Свайп: вправо лайк, влево пропуск\nВидео без звука", 160, 360),
                StickySpec("Видео-лента: не дублировать «Анкеты»", 160, 560),
                StickySpec("Лайки: копятся, получатель НЕ видит\nЛимит 5", 160, 760, "pink"),
                StickySpec("«Лайкнули меня» — ЗАБЛОКИРОВАНО", 160, 960, "red"),
                StickySpec("Чаты — недоступны", 160, 1160, "gray"),
                StickySpec(
                    "⚡ Edge case: 5 лайков исчерпаны\n→ экран «Зарегистрируйтесь»\n+ показ накопленных симпатий",
                    560,
                    760,
                    "orange",
                    360,
                ),
            ],
        ),
        FrameSpec(
            title="1.3–1.4 Регистрация и модерация",
            x=-1800,
            y=-500,
            width=2000,
            height=1600,
            fill="#fff9b1",
            stickies=[
                StickySpec(
                    "Регистрация:\n• Имя, дата рождения, город\n• email/телефон + пароль\n• видео-визитка ≤60 сек\n• согласие 152-ФЗ",
                    160,
                    160,
                    "light_yellow",
                    360,
                ),
                StickySpec(
                    "Визитка:\n• вопросы каждые 15–20 сек\n• авто стоп-кадр\n• статус «На проверке»",
                    560,
                    160,
                    "light_blue",
                    360,
                ),
                StickySpec("Пока на модерации — МОЖНО:\n✅ смотреть анкеты\n✅ лайкать (30/сутки)", 160, 520, "light_green"),
                StickySpec("НЕЛЬЗЯ:\n❌ своя карточка в ленте\n❌ чаты", 560, 520, "red"),
                StickySpec(
                    "Профиль: черновик + статус ожидания\nPush: «Проверяем визитку…»",
                    160,
                    760,
                    "cyan",
                ),
                StickySpec(
                    "Отклонено → причина + «Перезаписать»",
                    560,
                    760,
                    "orange",
                ),
            ],
        ),
        FrameSpec(
            title="1.5 Структура анкеты (БД)",
            x=400,
            y=-500,
            width=1400,
            height=1600,
            fill="#d0e17a",
            stickies=[
                StickySpec("gender · birth_date · city", 140, 140, "light_yellow"),
                StickySpec("goals[] · interests[] — GIN index", 140, 340, "light_green"),
                StickySpec("has_children · moderation_status", 140, 540),
                StickySpec("profile_frozen — partial index", 140, 740),
                StickySpec(
                    "💡 Справочники с фиксированными ID,\nне свободный текст → быстрые фильтры PostgreSQL",
                    140,
                    960,
                    "yellow",
                    500,
                ),
            ],
        ),
        FrameSpec(
            title="2. Лайки, корзина, мэтчи",
            x=-4200,
            y=1300,
            width=2000,
            height=1500,
            fill="#ffcee0",
            stickies=[
                StickySpec("Лайк A→B: «Я лайкнул» у A", 160, 160, "pink"),
                StickySpec("«Лайкнули меня» у B", 560, 160, "pink"),
                StickySpec("Взаимность → автооткрытие чата", 160, 400, "light_green", 360),
                StickySpec("Гость: 5 лайков/сессия", 160, 640),
                StickySpec("Юзер: 30 лайков/сутки", 560, 640),
                StickySpec("Бейдж на корзине при мэтче", 160, 840, "yellow"),
                StickySpec("Контакты только через чат\n(не телефон/email напрямую)", 560, 840, "gray", 360),
            ],
        ),
        FrameSpec(
            title="2.2 Чаты",
            x=-1800,
            y=1300,
            width=2000,
            height=1500,
            fill="#a6ccf5",
            stickies=[
                StickySpec(
                    "Доступ: регистрация + мэтч + одобренная визитка",
                    160,
                    160,
                    "light_blue",
                    360,
                ),
                StickySpec("Макс. 5 активных чатов", 560, 160, "orange"),
                StickySpec("Только видео-кружки ≤60 сек\nБез текста", 160, 400, "violet", 360),
                StickySpec("Лимит: 10 кружков от одного", 560, 400),
                StickySpec("Архив: лимит ИЛИ 7 дней тишины", 160, 640, "gray"),
                StickySpec(
                    "Действия:\n• записать кружок\n• предложить свидание\n• профиль собеседника",
                    560,
                    640,
                    "light_green",
                    360,
                ),
            ],
        ),
        FrameSpec(
            title="2.3 Видео-свидания (WebRTC)",
            x=400,
            y=1300,
            width=2000,
            height=1500,
            fill="#7b92ff",
            stickies=[
                StickySpec("«Прямо сейчас» — окно 5 мин", 160, 160, "light_yellow"),
                StickySpec("«По расписанию» — слоты", 560, 160, "light_yellow"),
                StickySpec("Звонок: камеры, таймер, поминутная оплата", 160, 400, "cyan", 360),
                StickySpec("Стандарт: М 75% / Ж 25%", 160, 640, "pink"),
                StickySpec("«Оплачу полностью» — 100% один", 560, 640, "pink"),
                StickySpec("Оба делят → у кого больше баланс", 160, 840),
                StickySpec("Запись: согласие обоих, 30 дней", 560, 840, "gray"),
                StickySpec("WebSocket + WebRTC + TURN\n2FA для платежей", 160, 1080, "violet", 360),
            ],
        ),
        FrameSpec(
            title="3. Умная модерация",
            x=-4200,
            y=3100,
            width=3600,
            height=1500,
            fill="#f5d128",
            stickies=[
                StickySpec("1. Загрузка", 160, 160, "light_yellow", 180),
                StickySpec("2. FFmpeg\nвалидация", 400, 160, "light_blue", 180),
                StickySpec("3. AI пре-мод\nscore 0–100", 640, 160, "violet", 180),
                StickySpec("4. Решение\nпо score", 880, 160, "orange", 180),
                StickySpec("5. Админ", 1120, 160, "pink", 180),
                StickySpec("6. В ленте", 1360, 160, "light_green", 180),
                StickySpec("≥85 → админ «вероятно ОК»", 160, 400, "light_green"),
                StickySpec("50–84 → ручной просмотр", 560, 400, "yellow"),
                StickySpec("<50 → автоотклонение", 960, 400, "red"),
                StickySpec(
                    "Очередь: user_id, video_url, ai_score,\nai_flags, status, reviewer_id,\nrejection_reason",
                    160,
                    640,
                    "gray",
                    500,
                ),
                StickySpec("~70–80% авто · SLA до 24ч", 760, 640, "cyan", 300),
            ],
        ),
        FrameSpec(
            title="4. ЛК и рейтинги",
            x=-4200,
            y=4900,
            width=2000,
            height=1500,
            fill="#67c6c0",
            stickies=[
                StickySpec("Профиль: фото, рейтинг, совместимость %", 160, 160, "light_blue"),
                StickySpec("Баланс и подписка", 560, 160, "light_green"),
                StickySpec("Настройки, Support, 152-ФЗ", 160, 400, "gray"),
                StickySpec(
                    "4 критерия (1–5):\nАдекватность · Юмор\nДоброта · Эмпатия",
                    560,
                    400,
                    "pink",
                    360,
                ),
                StickySpec("1 отзыв на свидание (unique)", 160, 720),
                StickySpec("Только после реального звонка", 560, 720),
                StickySpec("Анти-накрутка → флаг админу", 160, 920, "orange"),
                StickySpec("Платежи через шлюз + 2FA", 560, 920, "violet"),
            ],
        ),
        FrameSpec(
            title="5. Лендинг (рекламный сайт)",
            x=-1800,
            y=4900,
            width=2000,
            height=1500,
            fill="#f16c7f",
            stickies=[
                StickySpec("Hero: УТП + видео + Скачать", 160, 160, "light_pink"),
                StickySpec("Как работает: 3 шага", 560, 160, "light_yellow"),
                StickySpec("Преимущества · О агентстве", 160, 400),
                StickySpec("Отзывы · Тарифы · FAQ", 560, 400),
                StickySpec("Footer: сторы, ПДн, оферта", 160, 640, "gray"),
                StickySpec("CTA: App Store / Google Play\nQR на мобиле · предзапись", 560, 640, "light_green", 360),
            ],
        ),
        FrameSpec(
            title="6–7. Поставка и этапы",
            x=400,
            y=4900,
            width=2000,
            height=1500,
            fill="#b384bb",
            stickies=[
                StickySpec("🗺️ Miro карта экранов", 160, 160, "light_yellow"),
                StickySpec("📄 Текстовое ТЗ", 560, 160, "light_blue"),
                StickySpec("🗄️ Схема БД", 160, 400, "light_green"),
                StickySpec("🔌 API-контуры", 560, 400, "violet"),
                StickySpec("Этапы 1–8: спроектировано ✅", 160, 640, "light_green", 360),
                StickySpec("Этап 9: лендинг 🔲", 560, 640, "orange"),
                StickySpec("Этап 10: релиз в сторы 🔲", 160, 880, "pink"),
            ],
        ),
    ]


def funnel_connector_ids(frame: FrameSpec, sticky_ids: list[str]) -> list[tuple[str, str]]:
    """Connect first 10 funnel stickies in order within User Flow frame."""
    if frame.title != "1. User Flow — воронка" or len(sticky_ids) < 10:
        return []
    pairs: list[tuple[str, str]] = []
    for i in range(9):
        pairs.append((sticky_ids[i], sticky_ids[i + 1]))
    return pairs


def moderation_connector_ids(sticky_ids: list[str]) -> list[tuple[str, str]]:
    if len(sticky_ids) < 6:
        return []
    return [(sticky_ids[i], sticky_ids[i + 1]) for i in range(5)]


def populate_board(client: MiroClient) -> None:
    frames = build_frames()
    all_connectors: list[tuple[str, str]] = []

    for frame in frames:
        print(f"Frame: {frame.title}")
        frame_id = client.create_frame(frame)
        sticky_ids: list[str] = []
        for sticky in frame.stickies or []:
            sid = client.create_sticky(
                content=sticky.content,
                x=sticky.x,
                y=sticky.y,
                parent_id=frame_id,
                color=sticky.color,
                width=sticky.width,
            )
            sticky_ids.append(sid)

        if frame.title == "1. User Flow — воронка":
            all_connectors.extend(funnel_connector_ids(frame, sticky_ids))
        if frame.title == "3. Умная модерация":
            all_connectors.extend(moderation_connector_ids(sticky_ids[:6]))

    print(f"Connectors: {len(all_connectors)}")
    for start_id, end_id in all_connectors:
        client.create_connector(start_id, end_id)

    print("Done.")


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board_id = os.environ.get("MIRO_BOARD_ID", "").strip()
    dry_run = os.environ.get("MIRO_DRY_RUN", "").strip() in {"1", "true", "yes"}

    if not token or not board_id:
        print(
            "Missing credentials.\n\n"
            "Set environment variables:\n"
            "  export MIRO_ACCESS_TOKEN='...'\n"
            "  export MIRO_BOARD_ID='uXjV...'\n\n"
            "Then run:\n"
            "  python3 docs/miro_populate_board.py\n",
            file=sys.stderr,
        )
        return 1

    client = MiroClient(token, board_id, dry_run=dry_run)
    populate_board(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
