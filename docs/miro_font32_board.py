#!/usr/bin/env python3
"""
Force uniform font size 32 on every Miro sticky.

Miro auto-scales short text unless font-size uses Miro's native format
`font-size: 32` (not 32px). Also normalizes width/height so rendering matches.

Usage:
  export MIRO_ACCESS_TOKEN=...
  export MIRO_BOARD_ID=uXjVH9Gr3u0=
  python3 docs/miro_font32_board.py
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
W = 320.0
H = 366.63316582914575
W_PIPE = 220.0
H_PIPE = 220.0
FONT32 = '<p><span style="font-size: 32">{}</span></p>'
MIN_CHARS = 28  # pad short labels so Miro stops auto-enlarging text


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>\s*<p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&#x1f7e2;", "")
        .replace("&#x1f7e1;", "")
        .replace("&#x1f534;", "")
        .replace("&#x1f4b0;", "")
        .replace("&#x1f4a1;", "💡")
        .replace("&#x1f4f1;", "📱")
        .replace("&#43;", "+")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("!&#61;", "!=")
        .replace("&amp;", "&")
        .replace("🟢", "")
        .replace("🟡", "")
        .replace("🔴", "")
        .replace("💰", "")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def pad_short(text: str) -> str:
    """Pad short single-line labels so Miro auto-fit matches size 32."""
    if "\n" in text:
        return text
    if len(text) >= MIN_CHARS:
        return text
    # thin spaces - nearly invisible, increase char count for auto-fit
    return text + "\u2009" * (MIN_CHARS - len(text))


def to_font32(text: str) -> str:
    clean = pad_short(strip_html(text))
    if not clean:
        return FONT32.format("")
    inner = "<br>".join(line.strip() for line in clean.split("\n") if line.strip())
    return FONT32.format(inner)


def is_font32(text: str) -> bool:
    return bool(re.search(r"font-size:\s*32\b", text))


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


def target_geometry(clean: str, frame_title: str, cur_w: float) -> tuple[float, float]:
    if re.match(r"^\d+\.\s", clean) and len(clean) < 40:
        return W_PIPE, H_PIPE
    if "User Flow" in frame_title and cur_w <= 280:
        return W_PIPE, H_PIPE
    return W, H


def apply_all(client: Client, items: list[dict]) -> tuple[int, int]:
    frames = {i["id"]: i["data"]["title"] for i in items if i["type"] == "frame"}
    ok = fail = 0
    for item in items:
        if item["type"] != "sticky_note":
            continue
        raw = item.get("data", {}).get("content", "")
        clean = strip_html(raw)
        new = to_font32(raw)
        geo = item.get("geometry") or {}
        cur_w = float(geo.get("width") or 0)
        cur_h = float(geo.get("height") or 0)
        frame_title = frames.get((item.get("parent") or {}).get("id", ""), "")
        tw, th = target_geometry(clean, frame_title, cur_w)
        need = (
            new != raw
            or not is_font32(raw)
            or "32px" in raw
            or abs(cur_w - tw) > 1
        )
        if not need:
            continue
        body = {
            "data": {"content": new},
            "geometry": {"width": tw},
            "style": {
                "textAlign": (item.get("style") or {}).get("textAlign", "left"),
                "textAlignVertical": "top",
            },
        }
        try:
            client.call("PATCH", f"/boards/{client.board}/sticky_notes/{item['id']}", body)
            ok += 1
            title = frames.get((item.get("parent") or {}).get("id", ""), "canvas")[:28]
            print(f"  fixed: {title}")
        except RuntimeError as exc:
            fail += 1
            print(f"  FAIL {item['id']}: {exc}")
    return ok, fail


def main() -> int:
    token = os.environ.get("MIRO_ACCESS_TOKEN", "").strip()
    board = os.environ.get("MIRO_BOARD_ID", "uXjVH9Gr3u0=").strip()
    if not token:
        print("Set MIRO_ACCESS_TOKEN", file=sys.stderr)
        return 1

    client = Client(token, board)
    items = client.items()
    ok, fail = apply_all(client, items)
    print(f"Updated {ok} stickies, {fail} failed.")

    # verify
    items = client.items()
    bad = []
    for s in items:
        if s["type"] != "sticky_note":
            continue
        c = s["data"]["content"]
        if not is_font32(c) or "32px" in c:
            bad.append(f"font: {c[:60]}")
        w = (s.get("geometry") or {}).get("width") or 0
        if w > 400:
            bad.append(f"width={w}")
    print(f"Verification: {len(bad)} issues remain")
    for b in bad[:10]:
        print(" ", b)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
