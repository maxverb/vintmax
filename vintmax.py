#!/usr/bin/env python3
"""Zoek Vinted-listings waar 'max' of 'maximaal' in de titel/beschrijving staat.

Gebruik:
    python3 vintmax.py                 # standaard: 3 paginas, NL
    python3 vintmax.py --pages 5       # meer resultaten
    python3 vintmax.py --query maxi    # andere zoekterm
    python3 vintmax.py --html out.html # schrijf klikbare HTML met plaatjes
"""

from __future__ import annotations

import argparse
import gzip
import http.cookiejar
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass

DOMAIN = "www.vinted.nl"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
WORD_RE = re.compile(r"\bmax(?:imaal|imum|imize|imal)?\b", re.IGNORECASE)


@dataclass
class Item:
    id: int
    title: str
    brand: str
    size: str
    price: str
    url: str
    photo: str

    def matches(self) -> bool:
        hay = f"{self.title} {self.brand}"
        return bool(WORD_RE.search(hay))


def build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [
        ("User-Agent", UA),
        ("Accept-Language", "nl-NL,nl;q=0.9,en;q=0.8"),
        ("Accept-Encoding", "gzip"),
    ]
    return opener


def fetch(opener: urllib.request.OpenerDirector, url: str, *, json_accept: bool = False) -> bytes:
    headers = {"Accept": "application/json" if json_accept else "text/html"}
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=20) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


def warm_up(opener: urllib.request.OpenerDirector) -> None:
    """Haal homepage op om session-cookies (incl. anti-bot) binnen te halen."""
    fetch(opener, f"https://{DOMAIN}/")


def search_page(opener: urllib.request.OpenerDirector, query: str, page: int) -> list[Item]:
    params = {
        "search_text": query,
        "page": str(page),
        "per_page": "96",
        "order": "newest_first",
    }
    url = f"https://{DOMAIN}/api/v2/catalog/items?" + urllib.parse.urlencode(params)
    raw = fetch(opener, url, json_accept=True)
    data = json.loads(raw.decode("utf-8"))
    out: list[Item] = []
    for it in data.get("items", []):
        price = it.get("price") or {}
        if isinstance(price, dict):
            price_str = f"{price.get('amount', '?')} {price.get('currency_code', '')}".strip()
        else:
            price_str = str(price)
        out.append(
            Item(
                id=it.get("id", 0),
                title=(it.get("title") or "").strip(),
                brand=(it.get("brand_title") or "").strip(),
                size=(it.get("size_title") or "").strip(),
                price=price_str,
                url=it.get("url") or f"https://{DOMAIN}/items/{it.get('id')}",
                photo=(it.get("photo") or {}).get("url", "") if isinstance(it.get("photo"), dict) else "",
            )
        )
    return out


def render_terminal(items: list[Item]) -> None:
    if not items:
        print("Geen hits gevonden.")
        return
    for i, it in enumerate(items, 1):
        print(f"{i:3}. {it.title}")
        meta = " | ".join(x for x in [it.brand, it.size, it.price] if x)
        if meta:
            print(f"     {meta}")
        print(f"     {it.url}")
        print()


def render_html(items: list[Item], path: str, query: str) -> None:
    cards = []
    for it in items:
        img = f'<img src="{it.photo}" loading="lazy">' if it.photo else ""
        cards.append(
            f'<a class="card" href="{it.url}" target="_blank" rel="noopener">'
            f'{img}'
            f'<div class="title">{_esc(it.title)}</div>'
            f'<div class="meta">{_esc(it.brand)} · {_esc(it.size)} · {_esc(it.price)}</div>'
            f"</a>"
        )
    html = f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<title>Vintmax: {_esc(query)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 20px; background:#fafafa; }}
  h1 {{ font-size: 18px; }}
  .grid {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:12px; }}
  .card {{ background:#fff; border:1px solid #eee; border-radius:8px; padding:8px; text-decoration:none; color:#111; }}
  .card:hover {{ border-color:#999; }}
  .card img {{ width:100%; aspect-ratio:3/4; object-fit:cover; border-radius:4px; }}
  .title {{ font-size:13px; margin-top:6px; }}
  .meta {{ font-size:11px; color:#666; margin-top:4px; }}
</style></head>
<body>
<h1>Vintmax — {len(items)} hits voor "{_esc(query)}"</h1>
<div class="grid">{''.join(cards)}</div>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="max", help="zoekterm (default: max)")
    ap.add_argument("--pages", type=int, default=3, help="aantal paginas (default: 3, max ~96/pagina)")
    ap.add_argument("--html", help="schrijf resultaat naar HTML-bestand")
    ap.add_argument("--no-filter", action="store_true", help="toon alle resultaten, niet alleen whole-word matches")
    args = ap.parse_args()

    opener = build_opener()
    try:
        warm_up(opener)
    except Exception as e:
        print(f"Kon Vinted niet bereiken: {e}", file=sys.stderr)
        return 1

    seen: set[int] = set()
    collected: list[Item] = []
    for page in range(1, args.pages + 1):
        try:
            batch = search_page(opener, args.query, page)
        except Exception as e:
            print(f"Pagina {page} faalde: {e}", file=sys.stderr)
            break
        if not batch:
            break
        for it in batch:
            if it.id in seen:
                continue
            seen.add(it.id)
            if args.no_filter or it.matches():
                collected.append(it)
        print(f"Pagina {page}: {len(batch)} items, totaal matches: {len(collected)}", file=sys.stderr)

    render_terminal(collected)
    if args.html:
        render_html(collected, args.html, args.query)
        print(f"\nHTML geschreven naar {args.html}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
