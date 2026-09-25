"""Windows Package Manager (winget.run) search."""
from collections import OrderedDict
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from telethon import Button

from . import InlinePlugin, LOGS, async_searcher, in_pattern

_CACHE = OrderedDict()
_MAX_CACHE = 32


def _put(key, value):
    _CACHE.pop(key, None)
    _CACHE[key] = value
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _s(v, default=""):
    if v is None:
        return default
    v = str(v).strip()
    return v or default


async def _api_search(query):
    url = "https://api.winget.run/v2/packages?ensureContains=true&partialMatch=true&take=20&query=" + quote_plus(query)
    data = await async_searcher(url, re_json=True)
    if not isinstance(data, dict):
        return []
    packages = data.get("Packages") or data.get("packages") or []
    return packages if isinstance(packages, list) else []


async def _web_search(query):
    html = await async_searcher(f"https://winget.run/search?query={quote_plus(query)}", re_content=True)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for anchor in soup.select('a[href^="/pkg/"]'):
        href = anchor.get("href")
        name = anchor.get_text(" ", strip=True)
        if href and name:
            results.append({"name": name, "id": href.split("/pkg/", 1)[-1], "url": "https://winget.run" + href})
    return results[:20]


@in_pattern("winget", owner=True)
async def search_winget(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return await event.answer([], switch_pm="Enter a package name to search.", switch_pm_param="start")
    query = parts[1].strip()
    key = query.lower()
    if key in _CACHE:
        packages = _CACHE[key]
    else:
        try:
            packages = await _api_search(query)
        except Exception as exc:
            LOGS.debug("winget API failed: %s", exc)
            try:
                packages = await _web_search(query)
            except Exception as exc2:
                LOGS.exception("winget search failed: %s", exc2)
                return await event.answer([], switch_pm="Winget search is currently unavailable.", switch_pm_param="start")
        _put(key, packages)

    results = []
    for item in packages[:20]:
        latest = item.get("Latest") or item.get("latest") or item if isinstance(item, dict) else {}
        if not isinstance(latest, dict):
            latest = {}
        package_id = _s(item.get("Id") if isinstance(item, dict) else None) or _s(latest.get("Id"))
        name = _s(latest.get("Name"), package_id or "Winget package")
        description = _s(latest.get("Description"), "No description available.")
        homepage = _s(latest.get("Homepage"))
        versions = latest.get("Versions") or item.get("Versions") if isinstance(item, dict) else []
        version = _s(versions[0] if isinstance(versions, list) and versions else latest.get("Version"), "unknown")
        tags = latest.get("Tags") or []
        if not isinstance(tags, list):
            tags = []
        url = homepage if homepage.startswith(("http://", "https://")) else (f"https://winget.run/pkg/{package_id}" if package_id else "https://winget.run/")
        text = f"**{name}**\n\n{description[:1400]}\n\n**Install:** `{('winget install ' + package_id).strip()}`\n**Version:** `{version}`"
        if tags:
            text += "\n**Tags:** " + " ".join(f"#{str(tag).replace(' ', '_')}" for tag in tags[:20])
        try:
            results.append(await event.builder.article(
                title=name[:120], description=description[:220], url=url, text=text[:3900],
                buttons=[[Button.url("Open", url)], [Button.switch_inline("Search again", query="winget ", same_peer=True)]],
            ))
        except Exception as exc:
            LOGS.debug("Skipping winget result: %s", exc)

    return await event.answer(results, cache_time=3000, switch_pm=f"Winget · {len(results)} result(s)" if results else "No results found", switch_pm_param="start")


InlinePlugin.update({"Search Winget": "winget"})
