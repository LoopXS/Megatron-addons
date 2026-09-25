"""npm package search for Megatron inline mode."""
from collections import OrderedDict
from urllib.parse import quote_plus

from telethon import Button

from . import InlinePlugin, LOGS, async_searcher, in_pattern

_CACHE = OrderedDict()
_MAX_CACHE = 40


def _cache_put(key, value):
    _CACHE.pop(key, None)
    _CACHE[key] = value
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _clean(value, default=""):
    value = "" if value is None else str(value).strip()
    return value or default


@in_pattern("npm")
async def search_npm(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return await event.answer([], switch_pm="Enter an npm package or search term.", switch_pm_param="start")

    query = parts[1].strip()
    key = query.lower()
    if key in _CACHE:
        data = _CACHE[key]
    else:
        try:
            data = await async_searcher(
                f"https://registry.npmjs.com/-/v1/search?text={quote_plus(query)}&size=10",
                re_json=True,
                headers={"Accept": "application/json", "User-Agent": "Megatron-Userbot"},
            )
        except Exception as exc:
            LOGS.exception("npm search failed: %s", exc)
            return await event.answer([], switch_pm="npm search failed. Try again later.", switch_pm_param="start")
        data = data if isinstance(data, dict) else {}
        _cache_put(key, data)

    objects = data.get("objects") or []
    results = []
    for obj in objects[:10]:
        package = obj.get("package") if isinstance(obj, dict) else None
        if not isinstance(package, dict):
            continue
        name = _clean(package.get("name"), "Unnamed package")
        version = _clean(package.get("version"), "unknown")
        description = _clean(package.get("description"), "No description available.")
        links = package.get("links") or {}
        npm_url = links.get("npm") or f"https://www.npmjs.com/package/{quote_plus(name)}"
        homepage = links.get("homepage") or npm_url
        keywords = package.get("keywords") or []
        if not isinstance(keywords, list):
            keywords = []
        text = (
            f"**[{name}]({npm_url})**\n\n{description[:1500]}\n\n"
            f"**Version:** `{version}`\n"
            f"**Keywords:** `{', '.join(map(str, keywords[:20])) or '—'}`"
        )
        try:
            results.append(await event.builder.article(
                title=name[:120], description=description[:220], url=npm_url,
                text=text[:3900], link_preview=False,
                buttons=[[Button.url("View package", npm_url)], [Button.switch_inline("Search again", query="npm ", same_peer=True)]],
            ))
        except Exception as exc:
            LOGS.debug("Skipping npm result: %s", exc)

    return await event.answer(results, cache_time=300, switch_pm=f"NPM Search · {len(results)} result(s)", switch_pm_param="start")


InlinePlugin.update({"Npm Search": "npm"})
