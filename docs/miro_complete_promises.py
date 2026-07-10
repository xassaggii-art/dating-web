#!/usr/bin/env python3
"""Fill remaining customer-promise gaps on Miro board."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://api.miro.com/v2"
DELAY = 0.35
LEFT, RIGHT, W = 160, 560, 320
FONT32 = '<p><span style="font-size: 32">{}</span></p>'


def fmt(text: str) -> str:
    inner = "<br>".join(line.strip() for line in text.split("\n") if line.strip())
    return FONT32.format(inner)


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
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            raise RuntimeError(f"{method} {path}: {exc.code} {exc.read().decode()}") from exc
        finally:
            time.sleep(DELAY)

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


def find_frame(frames: list[dict], needle: str) -> dict:
    for f in frames:
        if needle in f.get("data", {}).get("title", ""):
            return f
    raise RuntimeError(f"Frame not found: {needle}")


def patch_sticky(client: Client, sid: str, text: str, color: str | None = None) -> None:
    body: dict = {"data": {"content": fmt(text)}, "geometry": {"width": W}}
    if color:
        body["style"] = {"fillColor": color, "textAlign": "left", "textAlignVertical": "top"}
    client.call("PATCH", f"/boards/{client.board}/sticky_notes/{sid}", body)


def add_sticky(client: Client, fid: str, text: str, x: float, y: float, color: str) -> None:
    client.call(
        "POST",
        f"/boards/{client.board}/sticky_notes",
        {
            "data": {"content": fmt(text), "shape": "square"},
            "style": {"fillColor": color, "textAlign": "left", "textAlignVertical": "top"},
            "position": {"x": x, "y": y},
            "geometry": {"width": W},
            "parent": {"id": fid},
        },
    )


def plain(c: str) -> str:
    return re.sub(r"<[^>]+>", "", c).strip()


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = Client(token, board)
    items = client.items()
    frames = [i for i in items if i["type"] == "frame"]

    # --- 1.3 Регистрация: deep questionnaire ---
    f13 = find_frame(frames, "1.3-1.4")
    for s in items:
        if s["type"] != "sticky_note" or (s.get("parent") or {}).get("id") != f13["id"]:
            continue
        if "Регистрация" in plain(s["data"]["content"]):
            patch_sticky(
                client,
                s["id"],
                "Регистрация:\n• Имя, дата, город\n• email/телефон + пароль\n• видео-визитка ≤60 сек\n• согласие 152-ФЗ",
            )
        if "Визитка" in plain(s["data"]["content"]):
            patch_sticky(
                client,
                s["id"],
                "Анкета (глубокая):\n• образование\n• цели знакомства\n• интересы (справочник)\n• видео-визитка",
                "light_green",
            )
    print("OK 1.3-1.4: образование, цели, интересы")

    # --- 1.5 БД: education field ---
    f15 = find_frame(frames, "1.5 Структура")
    has_edu = any("education" in plain(s["data"]["content"]).lower() or "образован" in plain(s["data"]["content"]).lower()
                  for s in items if s["type"] == "sticky_note" and (s.get("parent") or {}).get("id") == f15["id"])
    if not has_edu:
        add_sticky(client, f15["id"], "education\nenum/string\nbtree index", RIGHT, 540, "cyan")
    patch_sticky(client, next(
        s["id"] for s in items
        if s["type"] == "sticky_note" and (s.get("parent") or {}).get("id") == f15["id"]
        and "goals" in plain(s["data"]["content"])
    ), "goals[] · interests[]\nGIN index\nфильтр ленты", "light_green")
    print("OK 1.5: education + goals/interests")

    # --- 4. ЛК: statistics ---
    f4 = find_frame(frames, "4. ЛК")
    has_stats = any("статистик" in plain(s["data"]["content"]).lower()
                    for s in items if s["type"] == "sticky_note" and (s.get("parent") or {}).get("id") == f4["id"])
    if not has_stats:
        add_sticky(
            client,
            f4["id"],
            "Статистика ЛК:\n• просмотры анкеты\n• лайки / мэтчи\n• свидания / отзывы",
            LEFT,
            1350,
            "cyan",
        )
        add_sticky(
            client,
            f4["id"],
            "Динамика рейтинга:\n• 4 критерия\n• общий балл\n• влияние на ленту",
            RIGHT,
            1350,
            "light_blue",
        )
    print("OK 4. ЛК: статистика")

    # --- Лента: education in filters ---
    fl = find_frame(frames, "Лента рекомендаций")
    for s in items:
        if s["type"] != "sticky_note" or (s.get("parent") or {}).get("id") != fl["id"]:
            continue
        if "Поля" in plain(s["data"]["content"]):
            patch_sticky(
                client,
                s["id"],
                "Поля фильтра:\n• пол, возраст, город\n• цели, интересы\n• образование",
                "light_green",
            )
    print("OK Лента: образование в фильтре")

    # --- Wireframes: анкета deep + экран оценки ---
    fw = find_frame(frames, "Wireframes")
    wf_notes = [
        s for s in items
        if s["type"] == "sticky_note" and (s.get("parent") or {}).get("id") == fw["id"]
    ]
    for s in wf_notes:
        t = plain(s["data"]["content"])
        if "Анкеты" in t:
            patch_sticky(
                client,
                s["id"],
                "ЭКРАН: Анкеты\nобразование · цели\nинтересы · видео",
                "light_green",
            )
    has_rating = any("оценк" in plain(s["data"]["content"]).lower() for s in wf_notes)
    if not has_rating:
        try:
            client.call(
                "PATCH",
                f"/boards/{client.board}/frames/{fw['id']}",
                {"geometry": {"height": 1900}},
            )
        except RuntimeError:
            pass
        add_sticky(
            client,
            fw["id"],
            "ЭКРАН: Оценка\n4 критерия 1–5\nпосле звонка",
            LEFT,
            1740,
            "cyan",
        )
    print("OK Wireframes: глубокая анкета + оценка")

    # Expand LK frame if needed
    try:
        client.call(
            "PATCH",
            f"/boards/{client.board}/frames/{f4['id']}",
            {"geometry": {"height": 1900}},
        )
    except RuntimeError:
        pass

    print("All promise gaps filled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
