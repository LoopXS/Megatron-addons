"""Koo profile search for Megatron.

Koo's public endpoints have changed repeatedly. The handler therefore treats
API changes as a normal empty/error result instead of crashing the assistant.
"""
from collections import OrderedDict
from urllib.parse import quote_plus

from telethon import Button
from telethon.tl.types import InputWebDocument

from . import InlinePlugin, LOGS, async_searcher, in_pattern

_CACHE = OrderedDict()
_MAX_CACHE = 24
_FALLBACK_IMAGE = "https://telegra.ph/file/dc28e69bd7ea2c0f25329.jpg"


def _put(key, value):
    _CACHE.pop(key, None)
    _CACHE[key] = value
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _s(v, default="—"):
    if v is None:
        return default
    v = str(v).strip()
    return v or default


@in_pattern("koo", owner=True)
async def koo_search(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2:
        return await event.answer([], switch_pm="Enter a Koo username or search term.", switch_pm_param="start")

    raw = parts[1].strip()
    key_count = None
    if " | " in raw:
        raw, count = raw.rsplit(" | ", 1)
        try:
            key_count = max(1, int(count))
        except ValueError:
            key_count = None
    query = raw.strip()
    if not query:
        return await event.answer([], switch_pm="Enter a search term.", switch_pm_param="start")

    key = query.lower()
    if key in _CACHE:
        feed = _CACHE[key]
    else:
        try:
            data = await async_searcher(
                "https://www.kooapp.com/apiV1/search?query=" + quote_plus(query) + "&searchType=EXPLORE",
                re_json=True,
            )
        except Exception as exc:
            LOGS.exception("Koo search failed: %s", exc)
            return await event.answer([], switch_pm="Koo search is currently unavailable.", switch_pm_param="start")
        feed = data.get("feed", []) if isinstance(data, dict) else []
        if not isinstance(feed, list):
            feed = []
        _put(key, feed)

    if key_count is not None:
        profiles = [feed[key_count - 1]] if len(feed) >= key_count else []
    else:
        profiles = feed[:10]

    results = []
    profile_count = 0
    for item in profiles:
        if not isinstance(item, dict) or item.get("uiItemType") != "search_profile":
            continue
        first = (item.get("items") or [None])[0]
        if not isinstance(first, dict):
            continue
        handle = _s(first.get("userHandle"), "").lstrip("@").strip()
        if not handle:
            continue
        name = _s(first.get("name"), handle)
        image_url = _s(first.get("profileImageBaseUrl"), _FALLBACK_IMAGE)
        details = {}
        try:
            details = await async_searcher(f"https://www.kooapp.com/apiV1/users/handle/{quote_plus(handle)}", re_json=True)
            if not isinstance(details, dict):
                details = {}
        except Exception as exc:
            LOGS.debug("Koo profile details failed: %s", exc)
        text = f"**Name:** `{name}`\n**Username:** `@{handle}`"
        if details.get("title"):
            text += f"\n**Title:** `{_s(details['title'])}`"
        if details.get("description"):
            text += f"\n**Description:** {_s(details['description'])[:1000]}"
        text += f"\n**Followers:** `{_s(details.get('followerCount'))}`  **Following:** `{_s(details.get('followingCount'))}`"
        website = (details.get("socialProfile") or {}).get("website") if isinstance(details.get("socialProfile"), dict) else None
        if website:
            text += f"\n**Website:** {_s(website)}"
        url = f"https://www.kooapp.com/profile/{handle}"
        try:
            image = InputWebDocument(image_url, 0, "image/jpeg", [])
            results.append(await event.builder.article(
                title=name[:120], description=f"@{handle}", type="photo", content=image,
                thumb=image, include_media=True, text=text[:3900],
                buttons=[[Button.url("View profile", url)], [Button.switch_inline("Share", query=f"koo {query}", same_peer=True)]],
            ))
            profile_count += 1
        except Exception as exc:
            LOGS.debug("Koo result failed: %s", exc)

    return await event.answer(results, cache_time=300, switch_pm=f"Koo Search · {profile_count} result(s)" if results else "No results found", switch_pm_param="start")


InlinePlugin.update({"Kᴏᴏ Sᴇᴀʀᴄʜ": "koo"})
