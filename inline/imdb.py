import hashlib
import json
import re

from telethon import Button
from telethon.tl.types import InputWebDocument as wb

from . import (
    HNDLR,
    LOGS,
    InlinePlugin,
    TTLCache,
    async_searcher,
    callback,
    in_pattern,
    udB,
    url_quote,
)

imdbp = "https://graph.org/file/3b45a9ed4868167954300.jpg"

# plot_id -> dict(text, buttons, imdbID, movie_name, plot, details)
LIST = TTLCache(maxsize=200, ttl=3 * 3600)


def _api_key():
    # Read lazily so `setdb OMDB <key>` works without a restart.
    # Free key: http://www.omdbapi.com/ (1000 requests per day)
    return udB.get_key("OMDB")


def generate_unique_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:8]


_YEAR_RE = re.compile(r"^(.*?)\s+y=\s*(\d{4})\s*$", re.S)


def _parse_query(search_term):
    """'Title y= 2020' / 'Title y=2020' -> ('Title', '2020').

    Only a trailing ``y=<4 digits>`` token is a year filter; ``y=`` inside a
    word (e.g. ``apikey=``) is left alone.
    """
    search_term = search_term.strip()
    if m := _YEAR_RE.match(search_term):
        return m.group(1).strip(), m.group(2)
    return search_term, None


async def get_movie_data(search_term, full_plot=False):
    key = _api_key()
    if not key:
        return None
    name, year = _parse_query(search_term)
    url = f"https://www.omdbapi.com/?apikey={url_quote(key)}&t={url_quote(name)}"
    if year:
        url += f"&y={year}"
    if full_plot:
        url += "&plot=full"
    try:
        data = await async_searcher(url, re_json=True)
    except Exception as er:
        LOGS.warning(f"OMDB request failed: {er}")
        return None
    if isinstance(data, dict) and data.get("Response") == "True":
        return data
    return None


async def get_trailer(imdbID):
    """Best-effort trailer lookup (scrapes the title page's JSON-LD)."""
    if not re.fullmatch(r"tt\d+", imdbID or ""):
        return None
    try:
        html = await async_searcher(
            f"https://www.imdb.com/title/{imdbID}/",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
        if not match:
            return None
        data = json.loads(match.group(1))
        if isinstance(data, list):
            data = data[0] if data else {}
        trailer = data.get("trailer") or {}
        if isinstance(trailer, list):
            trailer = trailer[0] if trailer else {}
        return trailer.get("embedUrl")
    except Exception as er:
        LOGS.info(f"Trailer lookup failed for {imdbID}: {er}")
        return None


def _na(value):
    return "" if value in (None, "N/A") else str(value)


def _poster(movie_data):
    url = _na(movie_data.get("Poster"))
    return url if url.startswith(("http://", "https://")) else imdbp


def _notice(event, title, text):
    return event.builder.article(
        title=title,
        text=text,
        thumb=wb(imdbp, 0, "image/jpeg", []),
        buttons=[
            Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True),
            Button.switch_inline(
                "Sᴇᴀʀᴄʜ Bʏ Yᴇᴀʀ", query="imdb Inception y= 2010", same_peer=True
            ),
        ],
    )


@in_pattern("imdb", owner=False)
async def inline_imdb_command(event):
    parts = event.text.split(" ", maxsplit=1)
    movie_name = parts[1].strip() if len(parts) > 1 else ""
    if not movie_name:
        return await event.answer(
            [
                await _notice(
                    event,
                    "Sᴇᴀʀᴄʜ Sᴏᴍᴇᴛʜɪɴɢ",
                    "**Iᴍᴅʙ Sᴇᴀʀᴄʜ**\n\nUsage: `imdb <title>` or `imdb <title> y= 2010`",
                )
            ]
        )
    if not _api_key():
        return await event.answer(
            [
                await _notice(
                    event,
                    "OMDB API key missing",
                    f"Set a free key from omdbapi.com with `{HNDLR}setdb OMDB <key>`",
                )
            ]
        )

    movie_data = await get_movie_data(movie_name)
    if not movie_data:
        return await event.answer(
            [
                await _notice(
                    event,
                    "Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ",
                    "**IMDʙ**\nTry another title, or add a year: `imdb <title> y= 2010`",
                )
            ],
            switch_pm=movie_name[:60],
            switch_pm_param="start",
        )

    g = lambda k: _na(movie_data.get(k))  # noqa: E731
    ratings_str = ", ".join(
        f"{r.get('Source')}: `{r.get('Value')}`"
        for r in movie_data.get("Ratings") or []
    )
    details = (
        f"**Tɪᴛʟᴇ:** {g('Title')}\n"
        f"**Yᴇᴀʀ:** `{g('Year')}`\n"
        f"**Rᴀᴛᴇᴅ:** `{g('Rated')}`\n"
        f"**Rᴇʟᴇᴀsᴇᴅ:** {g('Released')}\n"
        f"**Rᴜɴᴛɪᴍᴇ:** `{g('Runtime')}`\n"
        f"**Gᴇɴʀᴇ:** {g('Genre')}\n"
        f"**Dɪʀᴇᴄᴛᴏʀ:** {g('Director')}\n"
        f"**Aᴄᴛᴏʀs:** {g('Actors')}\n"
        f"**Pʟᴏᴛ:** {g('Plot')}\n"
        f"**Lᴀɴɢᴜᴀɢᴇ:** `{g('Language')}`\n"
        f"**Cᴏᴜɴᴛʀʏ:** {g('Country')}\n"
        f"**Aᴡᴀʀᴅs:** {g('Awards')}\n"
        f"**Rᴀᴛɪɴɢs:** {ratings_str}\n"
        f"**IMDʙ Rᴀᴛɪɴɢ:** `{g('imdbRating')}`\n"
        f"**IMDʙ Lɪɴᴋ:** https://www.imdb.com/title/{g('imdbID')}\n"
        f"**IMDʙ Vᴏᴛᴇs:** `{g('imdbVotes')}`\n"
        f"**Bᴏx Oғғɪᴄᴇ:** `{g('BoxOffice')}`"
    )[:4000]
    plot_id = generate_unique_id(details)
    txt = f"**Tɪᴛʟᴇ:** {g('Title')}\n**Rᴇʟᴇᴀsᴇᴅ:** {g('Released')}\n**Cᴏᴜɴᴛʀʏ:** {g('Country')}"
    button = [
        [Button.inline("Fᴜʟʟ Dᴇᴛᴀɪʟs", data=f"plot_button:{plot_id}")],
        [Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True)],
    ]
    poster = wb(_poster(movie_data), 0, "image/jpeg", [])
    article = await event.builder.article(
        type="photo",
        text=txt,
        title=g("Title") or movie_name,
        include_media=True,
        description=f"{g('Released')}\nɪᴍᴅʙ: {g('imdbRating')}\nLᴀɴɢᴜᴀɢᴇ: {g('Language')}",
        link_preview=False,
        thumb=poster,
        content=poster,
        buttons=button,
    )
    LIST.set(
        plot_id,
        {
            "text": txt,
            "buttons": button,
            "details": details,
            "imdbID": g("imdbID"),
            "movie_name": movie_name,
            "plot": g("Plot"),
        },
    )
    await event.answer([article])


def _plot_id(event):
    return event.data.decode().split(":", 1)[1]


@callback(re.compile("plot_button:(.*)"), owner=False)
async def plot_button_clicked(event):
    plot_id = _plot_id(event)
    item = LIST.get(plot_id)
    if not item:
        return await event.answer("Query Expired! Search again 🔍")
    btns = [[Button.inline("Back", data=f"imdb_back_button:{plot_id}")]]
    trailer_url = await get_trailer(item["imdbID"])
    if trailer_url:
        btns.insert(0, [Button.url("Trailer", url=trailer_url)])
    if item["plot"].endswith("..."):
        btns.insert(
            0, [Button.inline("Extended Plot", data=f"extended_plot:{plot_id}")]
        )
    await event.edit(item["details"], buttons=btns)


@callback(re.compile("imdb_back_button:(.*)"), owner=False)
async def back_button_clicked(event):
    item = LIST.get(_plot_id(event))
    if not item:
        return await event.answer("Query Expired! Search again 🔍")
    await event.edit(item["text"], buttons=item["buttons"])


@callback(re.compile("extended_plot:(.*)"), owner=False)
async def extended_plot_button_clicked(event):
    plot_id = _plot_id(event)
    item = LIST.get(plot_id)
    if not item:
        return await event.answer("Query Expired! Search again 🔍")
    ext_plot = await get_movie_data(item["movie_name"], full_plot=True)
    fullplot = _na((ext_plot or {}).get("Plot"))
    if not fullplot:
        return await event.answer("Extended plot unavailable.", alert=True)
    await event.edit(
        f"**Exᴛᴇɴᴅᴇᴅ Pʟᴏᴛ:** {fullplot}"[:4000],
        buttons=[[Button.inline("Back", data=f"imdb_back_button:{plot_id}")]],
    )


InlinePlugin.update({"Iᴍᴅʙ Sᴇᴀʀᴄʜ": "imdb "})
