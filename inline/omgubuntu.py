"""OMG! Ubuntu article search."""
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


@in_pattern("omgu", owner=True)
async def omgubuntu(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return await event.answer([], switch_pm="Enter a query to search OMG! Ubuntu.", switch_pm_param="start")
    query = parts[1].strip()
    key = query.lower()
    if key in _CACHE:
        items = _CACHE[key]
    else:
        try:
            raw = await async_searcher(f"https://www.omgubuntu.co.uk/?s={quote_plus(query)}", re_content=True)
            soup = BeautifulSoup(raw, "html.parser")
        except Exception as exc:
            LOGS.exception("OMG Ubuntu search failed: %s", exc)
            return await event.answer([], switch_pm="OMG! Ubuntu is currently unavailable.", switch_pm_param="start")
        items = []
        seen = set()
        for node in soup.select("article, .sbs-layout__item, [class*='post']"):
            anchor = node.select_one("a[href]")
            if not anchor:
                continue
            url = urljoin("https://www.omgubuntu.co.uk", anchor.get("href", ""))
            title_node = node.select_one("h2, h3, h4, .layout__title-link, a")
            title = _s(title_node.get_text(" ", strip=True) if title_node else anchor.get_text(" ", strip=True))
            if not title or not url or url in seen:
                continue
            seen.add(url)
            desc_node = node.select_one("p, .layout__description, [class*='description']")
            image_node = node.select_one("img[data-src], img[src]")
            image = _s(image_node.get("data-src") or image_node.get("src")) if image_node else ""
            items.append({"title": title, "url": url, "description": _s(desc_node.get_text(" ", strip=True) if desc_node else ""), "image": urljoin(url, image) if image else ""})
            if len(items) >= 12:
                break
        _put(key, items)

    results = []
    for item in items[:10]:
        title, url = item["title"], item["url"]
        kwargs = dict(title=title[:120], description=item.get("description") or "OMG! Ubuntu", url=url, text=f"**[{title}]({url})**\n\n{item.get('description') or ''}"[:3900], buttons=[[Button.url("Read article", url)], [Button.switch_inline("Search again", query="omgu ", same_peer=True)]])
        image = item.get("image", "")
        if image.startswith(("http://", "https://")):
            try:
                media = InputWebDocument(image, 0, "image/jpeg", [])
                kwargs.update(type="photo", content=media, thumb=media, include_media=True)
            except Exception:
                pass
        try:
            results.append(await event.builder.article(**kwargs))
        except Exception as exc:
            LOGS.debug("Skipping OMG result: %s", exc)
    return await event.answer(results, cache_time=300, switch_pm=f"OMG! Ubuntu · {len(results)} result(s)" if results else "No results found", switch_pm_param="start")


InlinePlugin.update({"OᴍɢUʙᴜɴᴛᴜ": "omgu"})
