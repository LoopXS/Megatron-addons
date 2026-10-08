"""
✘ Commands Available -

• `{i}wiki <search query>`
    Wikipedia search from telegram.
"""

import json
from urllib.parse import urlencode

import requests

from . import *

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_HEADERS = {"User-Agent": "CipherXBot/1.2 (+https://t.me/CipherXBot)"}


def _get_json(params: dict):
    url = _WIKI_API + "?" + urlencode(params)
    try:
        response = requests.get(url, headers=_HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except (json.JSONDecodeError, ValueError, requests.RequestException) as exc:
        raise RuntimeError(f"Wikipedia API failed: {exc}")


def _wiki_summary(query: str) -> str:
    search = _get_json(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
            "format": "json",
            "origin": "*",
        }
    )
    pages = search.get("query", {}).get("search", [])
    if not pages:
        raise RuntimeError("No Wikipedia page found.")

    for page in pages:
        title = page.get("title")
        if not title:
            continue
        data = _get_json(
            {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "exintro": 1,
                "exsentences": 3,
                "titles": title,
                "format": "json",
                "origin": "*",
            }
        )
        pages_obj = data.get("query", {}).get("pages", {})
        for item in pages_obj.values():
            text = (item.get("extract") or "").strip()
            if text and "may refer to" not in text.lower():
                return text
    return "No readable summary was found for that query."


@heartless_cmd(pattern="wiki ?(.*)")
async def wiki(e):
    srch = (e.pattern_match.group(1) or "").strip()
    if not srch:
        return await e.eor("`Give some text to search on wikipedia !`")
    msg = await e.eor(f"`Searching {srch} on wikipedia..`")
    try:
        result = _wiki_summary(srch)
        await msg.edit(f"**Search Query :** {srch}\n\n**Results :** {result[:3900]}")
    except RuntimeError as err:
        await msg.edit(f"`{err}`")
    except Exception as err:
        await msg.edit(f"**ERROR** : `{err}`")
