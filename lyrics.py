"""
✘ Commands Available -
• `{i}lyrics <search query>`
    get lyrics of song.
"""

import re
import urllib.parse

from . import *


def _clean_lyrics(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    # If a synced LRCLIB response is returned, strip timestamp tags.
    if re.search(r"\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]", text):
        lines = []
        for line in text.splitlines():
            cleaned = re.sub(r"^\[[^\]]+\]\s*", "", line).strip()
            if cleaned:
                lines.append(cleaned)
        return "\n".join(lines)
    return text


@cipherx_cmd(pattern=r"lyrics ?(.*)")
async def lyrics(event):
    query = (event.pattern_match.group(1) or "").strip()
    if not query:
        return await event.eor("`Give a song name to search lyrics for.`")

    status = await event.eor("`Getting lyrics..`")
    url = "https://lrclib.net/api/search?q=" + urllib.parse.quote(query)
    try:
        data = await async_searcher(url, re_json=True)
    except Exception as exc:
        return await status.edit(f"`Lyrics search failed:` `{exc}`")

    if not data or not isinstance(data, list):
        return await status.edit("`No Results Found`")

    item = next(
        (
            entry
            for entry in data
            if entry.get("plainLyrics") or entry.get("syncedLyrics")
        ),
        data[0] if data else {},
    )
    text = (
        item.get("plainLyrics")
        or item.get("syncedLyrics")
        or item.get("lyrics")
        or ""
    )
    text = _clean_lyrics(text)
    if not text:
        return await status.edit("`No Results Found`")

    title = item.get("trackName") or item.get("name") or query
    artist = item.get("artistName") or item.get("artist") or ""
    header = f"**{title}**" + (f" — **{artist}**" if artist else "") + "\n\n"
    await event.client.send_message(
        event.chat_id, header + text[:3900], reply_to=event.reply_to_msg_id
    )
    await status.delete()
