#!/usr/bin/env python3
"""
Normalize Miro board:
1. Expand Legend with explanations + access matrix
2. Uniform sticky widths (320 default, 280 for pipeline steps)
3. Strip HTML so text renders at consistent size

Usage:
  export MIRO_ACCESS_TOKEN=...
  export MIRO_BOARD_ID=uXjVH9Gr3u0=
  python3 docs/miro_normalize_board.py
"""

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

LEFT, RIGHT = 160, 560
W_BODY = 320
W_STEP = 280
W_PIPE = 220
ROWS = (160, 550, 950, 1350)


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>\s*<p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&#x1f7e2;", "🟢")
        .replace("&#x1f7e1;", "🟡")
        .replace("&#x1f534;", "🔴")
        .replace("&#x1f4a1;", "💡")
        .replace("&#x1f4b0;", "💰")
        .replace("&#43;", "+")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("!&#61;", "!=")
        .replace("&amp;", "&")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def target_width(content: str, current: float, frame_title: str) -> float:
    if "User Flow" in frame_title and re.match(r"^\d+\.", content.strip()):
        return W_PIPE
    if frame_title.startswith("3. Умная модерация") and re.match(r"^\d+\.", content.strip()):
        return W_PIPE
    if len(content) > 120:
        return W_BODY
    return W_BODY


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


def rebuild_legend(client: Client, items: list[dict]) -> None:
    frame = next(i for i in items if i["type"] == "frame" and "Легенда" in i["data"]["title"])
    fid = frame["id"]
    print("Rebuild Legend", frame["data"]["title"])

    try:
        client.call(
            "PATCH",
            f"/boards/{client.board}/frames/{fid}",
            {
                "data": {"title": "Легенда статусов (для карты Miro)", "format": "custom", "type": "freeform"},
                "style": {"fillColor": "#f5f6f8"},
                "position": {"x": -4200, "y": -3750},
                "geometry": {"width": 2000, "height": 1200},
            },
        )
    except RuntimeError as exc:
        print("  frame patch skipped:", exc)

    notes = [
        ("Что это?\nМаркеры доступа функций\nна стикерах карты.\nНе элемент UI приложения.", 0, 0, "gray"),
        ("🟢 ДОСТУПНО\nМожно сейчас.\nПример: свайп, лайк.", 1, 0, "light_green"),
        ("🟡 ОЖИДАНИЕ\nВ процессе.\nПример: визитка на проверке.", 0, 1, "yellow"),
        ("🔴 ЗАБЛОКИРОВАНО\nНужно условие.\nПример: чаты без мэтча.", 1, 1, "red"),
        ("Гость:\nСвайп🟢 Лайки🟢\nКорзина🔴 Чаты🔴", 0, 2, "light_yellow"),
        ("На модерации:\nСвайп🟢 Лайки🟢\nСвоя лента🔴 Чаты🔴", 1, 2, "yellow"),
        ("Одобрен + мэтч:\nЛента🟢 Чаты🟢\nСвидание🟢", 0, 3, "light_green"),
        ("Где смотреть:\n• Wireframes (🟢🟡🔴)\n• ТЗ §1.2 таблица", 1, 3, "cyan"),
    ]

    existing = [
        i
        for i in items
        if i.get("type") == "sticky_note" and (i.get("parent") or {}).get("id") == fid
    ]
    existing.sort(key=lambda x: (x["position"]["y"], x["position"]["x"]))

    for idx, (text, col, row, color) in enumerate(notes):
        body = {
            "data": {"content": text},
            "style": {"fillColor": color, "textAlign": "left", "textAlignVertical": "top"},
            "position": {"x": LEFT if col == 0 else RIGHT, "y": ROWS[row]},
            "geometry": {"width": W_BODY},
        }
        if idx < len(existing):
            try:
                client.call("PATCH", f"/boards/{client.board}/sticky_notes/{existing[idx]['id']}", body)
            except RuntimeError:
                client.call(
                    "POST",
                    f"/boards/{client.board}/sticky_notes",
                    {**body, "data": {**body["data"], "shape": "square"}, "parent": {"id": fid}},
                )
        else:
            client.call(
                "POST",
                f"/boards/{client.board}/sticky_notes",
                {
                    "data": {"content": text, "shape": "square"},
                    "style": {"fillColor": color, "textAlign": "left", "textAlignVertical": "top"},
                    "position": {"x": LEFT if col == 0 else RIGHT, "y": ROWS[row]},
                    "geometry": {"width": W_BODY},
                    "parent": {"id": fid},
                },
            )


def normalize_stickies(client: Client, items: list[dict]) -> int:
    frames = {i["id"]: i["data"]["title"] for i in items if i["type"] == "frame"}
    changed = 0
    for item in items:
        if item["type"] != "sticky_note":
            continue
        if "Легенда" in frames.get((item.get("parent") or {}).get("id", ""), ""):
            continue

        raw = item.get("data", {}).get("content", "")
        clean = strip_html(raw)
        if not clean:
            continue

        par = (item.get("parent") or {}).get("id")
        frame_title = frames.get(par, "")
        cur_w = float((item.get("geometry") or {}).get("width") or W_BODY)
        new_w = target_width(clean, cur_w, frame_title)

        need_patch = clean != raw or abs(cur_w - new_w) > 1
        if not need_patch:
            continue

        body: dict = {"geometry": {"width": new_w}}
        if clean != raw:
            body["data"] = {"content": clean}

        client.call("PATCH", f"/boards/{client.board}/sticky_notes/{item['id']}", body)
        changed += 1
        print(f"  {frame_title[:28]:28} w {cur_w:.0f}->{new_w:.0f}")

    return changed


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = Client(token, board)
    items = client.items()
    rebuild_legend(client, items)
    items = client.items()
    n = normalize_stickies(client, items)
    print(f"Normalized {n} stickies. Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
