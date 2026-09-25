"""IMDb/OMDb inline search for Megatron.

OMDb is used for metadata because it provides structured data. The API key is
read from Megatron's database (OMDB). IMDb pages are only used opportunistically
for a trailer URL and never block the main movie result.
"""
import hashlib
import json
import re
from collections import OrderedDict
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from telethon import Button
from telethon.tl.types import InputWebDocument

from . import InlinePlugin, LOGS, async_searcher, callback, in_pattern, udB

_POSTER = "https://graph.org/file/3b45a9ed4868167954300.jpg"
_CACHE = OrderedDict()
_MAX_CACHE = 64


def _put(key, value):
    _CACHE.pop(key, None)
    _CACHE[key] = value
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _s(value, default="—"):
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _parse_query(raw):
    raw = raw.strip()
    match = re.match(r"^(.*?)\s+y\s*=\s*(\d{4})\s*$", raw, re.I)
    if match:
        return match.group(1).strip(), match.group(2)
    return raw, None


def _key(title, year):
    return hashlib.sha256(f"{title}|{year or ''}".encode()).hexdigest()[:12]


async def get_movie_data(search_term, full_plot=False):
    title, year = _parse_query(search_term)
    api_key = udB.get_key("OMDB")
    if not api_key:
        return None, "OMDB API key is not configured. Set the OMDB key in Megatron's database."
    params = f"apikey={quote_plus(str(api_key))}&t={quote_plus(title)}&plot={'full' if full_plot else 'short'}"
    if year:
        params += f"&y={year}"
    try:
        data = await async_searcher(f"https://www.omdbapi.com/?{params}", re_json=True)
    except Exception as exc:
        LOGS.exception("OMDb lookup failed: %s", exc)
        return None, "OMDb is currently unavailable."
    if isinstance(data, dict) and data.get("Response") == "True":
        return data, None
    return None, _s(data.get("Error") if isinstance(data, dict) else None, "Movie not found.")


async def _trailer(imdb_id):
    if not imdb_id:
        return None
    try:
        raw = await async_searcher(f"https://www.imdb.com/title/{quote_plus(imdb_id)}/", re_content=True, headers={"User-Agent": "Mozilla/5.0 (Megatron)"})
        soup = BeautifulSoup(raw, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (TypeError, ValueError):
                continue
            trailer = data.get("trailer") if isinstance(data, dict) else None
            if isinstance(trailer, dict):
                url = trailer.get("embedUrl") or trailer.get("url")
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    return url
    except Exception as exc:
        LOGS.debug("IMDb trailer lookup failed: %s", exc)
    return None


def _movie_text(data, full=False):
    ratings = data.get("Ratings") or []
    rating_text = ", ".join(f"{_s(x.get('Source'))}: `{_s(x.get('Value'))}`" for x in ratings if isinstance(x, dict)) or "—"
    if full:
        return (
            f"**Tɪᴛʟᴇ:** {_s(data.get('Title'))}\n**Yᴇᴀʀ:** `{_s(data.get('Year'))}`\n"
            f"**Rᴀᴛᴇᴅ:** `{_s(data.get('Rated'))}`\n**Rᴇʟᴇᴀsᴇᴅ:** {_s(data.get('Released'))}\n"
            f"**Rᴜɴᴛɪᴍᴇ:** `{_s(data.get('Runtime'))}`\n**Gᴇɴʀᴇ:** {_s(data.get('Genre'))}\n"
            f"**Dɪʀᴇᴄᴛᴏʀ:** {_s(data.get('Director'))}\n**Aᴄᴛᴏʀs:** {_s(data.get('Actors'))}\n"
            f"**Pʟᴏᴛ:** {_s(data.get('Plot'))}\n**Lᴀɴɢᴜᴀɢᴇ:** `{_s(data.get('Language'))}`\n"
            f"**Cᴏᴜɴᴛʀʏ:** {_s(data.get('Country'))}\n**Aᴡᴀʀᴅs:** {_s(data.get('Awards'))}\n"
            f"**Rᴀᴛɪɴɢs:** {rating_text}\n**IMDʙ Rᴀᴛɪɴɢ:** `{_s(data.get('imdbRating'))}`\n"
            f"**IMDʙ Vᴏᴛᴇs:** `{_s(data.get('imdbVotes'))}`\n**Bᴏx Oғғɪᴄᴇ:** `{_s(data.get('BoxOffice'))}`"
        )
    return f"**Tɪᴛʟᴇ:** {_s(data.get('Title'))}\n**Rᴇʟᴇᴀsᴇᴅ:** {_s(data.get('Released'))}\n**Cᴏᴜɴᴛʀʏ:** {_s(data.get('Country'))}"


@in_pattern("imdb")
async def inline_imdb_command(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        media = InputWebDocument(_POSTER, 0, "image/jpeg", [])
        return await event.answer([await event.builder.article(title="Sᴇᴀʀᴄʜ Sᴏᴍᴇᴛʜɪɴɢ", thumb=media, text="**Iᴍᴅʙ Sᴇᴀʀᴄʜ**\n\nᴇɴᴛᴇʀ ᴀ ᴍᴏᴠɪᴇ ᴏʀ sᴇʀɪᴇs.", buttons=[[Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True)], [Button.switch_inline("Sᴇᴀʀᴄʜ Bʏ Yᴇᴀʀ", query="imdb Dune y= 2024", same_peer=True)]])])

    query = parts[1].strip()
    data, error = await get_movie_data(query)
    if not data:
        return await event.answer([await event.builder.article(title="Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ", thumb=InputWebDocument(_POSTER, 0, "image/jpeg", []), text=f"**IMDʙ**\n\n{error}", buttons=[[Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True)]])], switch_pm="No result", switch_pm_param="start")

    imdb_id = _s(data.get("imdbID"), "")
    title = _s(data.get("Title"), query)
    year = _s(data.get("Year"), "")
    qid = _key(title, year)
    poster = data.get("Poster")
    if not isinstance(poster, str) or not poster.startswith(("http://", "https://")) or poster == "N/A":
        poster = _POSTER
    text = _movie_text(data)
    buttons = [[Button.inline("Fᴜʟʟ Dᴇᴛᴀɪʟs", data=f"plot_button:{qid}")], [Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True)]]
    _put(qid, {"data": data, "text": text, "buttons": buttons})
    media = InputWebDocument(poster, 0, "image/jpeg", [])
    article = await event.builder.article(type="photo", text=text, title=title[:120], include_media=True, description=f"{_s(data.get('Released'))}\nIMDb: {_s(data.get('imdbRating'))}\nLanguage: {_s(data.get('Language'))}", link_preview=False, thumb=media, content=media, buttons=buttons)
    return await event.answer([article])


@callback(re.compile(r"^plot_button:([A-Za-z0-9]+)$"), owner=False)
async def plot_button_clicked(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _CACHE.get(qid)
    if not item:
        return await event.answer("Query expired. Search again.", alert=True)
    data = item["data"]
    buttons = [[Button.inline("Back", data=f"imdb_back_button:{qid}")]]
    trailer = await _trailer(data.get("imdbID"))
    if trailer:
        buttons.insert(0, [Button.url("Trailer", trailer)])
    if _s(data.get("Plot"), "").endswith("..."):
        buttons.insert(0, [Button.inline("Extended Plot", data=f"extended_plot:{qid}")])
    return await event.edit(_movie_text(data, full=True)[:3900], buttons=buttons)


@callback(re.compile(r"^imdb_back_button:([A-Za-z0-9]+)$"), owner=False)
async def back_button_clicked(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _CACHE.get(qid)
    if not item:
        return await event.answer("Query expired. Search again.", alert=True)
    return await event.edit(item["text"], buttons=item["buttons"])


@callback(re.compile(r"^extended_plot:([A-Za-z0-9]+)$"), owner=False)
async def extended_plot_button_clicked(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _CACHE.get(qid)
    if not item:
        return await event.answer("Query expired. Search again.", alert=True)
    title = _s(item["data"].get("Title"), "")
    data, error = await get_movie_data(title, full_plot=True)
    if not data:
        return await event.answer(error, alert=True)
    item["data"] = data
    return await event.edit(f"**Exᴛᴇɴᴅᴇᴅ Pʟᴏᴛ:** {_s(data.get('Plot'))}", buttons=[[Button.inline("Back", data=f"imdb_back_button:{qid}")]])


InlinePlugin.update({"Iᴍᴅʙ Sᴇᴀʀᴄʜ": "imdb"})
