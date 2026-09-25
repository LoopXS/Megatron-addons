"""XDA Developers search with defensive HTML parsing."""
from collections import OrderedDict
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from telethon import Button
from telethon.tl.types import InputWebDocument

from .. import InlinePlugin, LOGS, async_searcher, in_pattern

_CACHE = OrderedDict()
_MAX_CACHE = 24


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


@in_pattern("xda", owner=True)
async def xda_dev(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return await event.answer([], switch_pm="Enter something to search on XDA.", switch_pm_param="start")
    query = parts[1].strip()
    key = query.lower()
    if key in _CACHE:
        items = _CACHE[key]
    else:
        try:
            raw = await async_searcher(f"https://www.xda-developers.com/search/{quote_plus(query)}/", re_content=True)
            soup = BeautifulSoup(raw, "html.parser")
        except Exception as exc:
            LOGS.exception("XDA search failed: %s", exc)
            return await event.answer([], switch_pm="XDA search is currently unavailable.", switch_pm_param="start")

        items = []
        candidates = soup.select("article, div[class*='layout_post_'], div[id^='post-']")
        seen = set()
        for node in candidates:
            link = node.select_one("a[href]")
            title_node = node.select_one("h2 a, h3 a, h4 a, .item_content h4 a, a[href]")
            if not link and not title_node:
                continue
            link = title_node or link
            href = urljoin("https://www.xda-developers.com", link.get("href", ""))
            title = _s(link.get_text(" ", strip=True))
            if not href or not title or href in seen:
                continue
            seen.add(href)
            img = node.select_one("img[src], img[data-src]")
            image = _s(img.get("data-src") or img.get("src")) if img else ""
            desc_node = node.select_one("p, .item_meta, [class*='description']")
            items.append({"title": title, "url": href, "description": _s(desc_node.get_text(" ", strip=True) if desc_node else ""), "image": urljoin(href, image) if image else ""})
            if len(items) >= 12:
                break
        _put(key, items)

    results = []
    for item in items[:10]:
        title, url = item["title"], item["url"]
        image = item.get("image")
        kwargs = dict(title=title[:120], description=item.get("description") or "XDA Developers", url=url, text=f"**[{title}]({url})**\n\n{item.get('description') or 'Open the article on XDA Developers.'}"[:3900], link_preview=False, buttons=[[Button.url("Open article", url)], [Button.switch_inline("Search again", query="xda ", same_peer=True)]])
        if image.startswith(("http://", "https://")):
            try:
                media = InputWebDocument(image, 0, "image/jpeg", [])
                kwargs.update(type="photo", content=media, thumb=media, include_media=True)
            except Exception:
                pass
        try:
            results.append(await event.builder.article(**kwargs))
        except Exception as exc:
            LOGS.debug("Skipping XDA result: %s", exc)

    return await event.answer(results, cache_time=300, switch_pm=f"XDA Search · {len(results)} result(s)" if results else "No results found", switch_pm_param="start")


InlinePlugin.update({"Search on XDA": "xda"})
