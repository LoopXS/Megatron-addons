"""PyPI package search with safe callback state and pagination."""
from collections import OrderedDict
from html import unescape
from urllib.parse import quote
import hashlib
import re

from telethon import Button
from telethon.tl.types import InputWebDocument

try:
    from markdownify import markdownify as _markdownify
except ImportError:
    _markdownify = None

from . import InlinePlugin, LOGS, async_searcher, callback, in_pattern

_STORE = OrderedDict()
_MAX_STORE = 64
_IMAGE = "https://graph.org/file/004c65a44efa1efc85193.jpg"


def _put(key, value):
    _STORE.pop(key, None)
    _STORE[key] = value
    while len(_STORE) > _MAX_STORE:
        _STORE.popitem(last=False)


def _id(package, version):
    return hashlib.sha256(f"{package}:{version}".encode()).hexdigest()[:12]


def _clean(value, default="—"):
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _description(raw):
    raw = unescape(str(raw or "")).strip()
    if _markdownify:
        try:
            raw = _markdownify(raw)
        except Exception:
            pass
    raw = re.sub(r"^\s*(?:\.\.|\||:)\s?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"/\d+/", "", raw)
    return raw.strip()


def _document_links(text):
    return list(dict.fromkeys(re.findall(r"https?://[^\s<>\]\)]+", text or "")))[:20]


def _buttons(qid):
    return [[Button.inline("sʜᴏᴡ ᴅᴇᴛᴀɪʟs", data=f"pypi_details:{qid}"), Button.inline("ᴅᴏᴄᴜᴍᴇɴᴛ ʟɪɴᴋs", data=f"pypi_documents:{qid}")], [Button.switch_inline("sᴇᴀʀᴄʜ ᴀɢᴀɪɴ", query="pypi ", same_peer=True)]]


@in_pattern("pypi")
async def inline_pypi_handler(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        media = InputWebDocument(_IMAGE, 0, "image/jpeg", [])
        return await event.answer([await event.builder.article(type="photo", include_media=True, title="sᴇᴀʀᴄʜ ᴘʏᴘɪ", thumb=media, content=media, text="**ᴘʏᴘɪ sᴇᴀʀᴄʜ**\n\nᴇɴᴛᴇʀ ᴀ ᴘᴀᴄᴋᴀɢᴇ ɴᴀᴍᴇ.", buttons=[[Button.switch_inline("sᴇᴀʀᴄʜ ᴀɢᴀɪɴ", query="pypi ", same_peer=True)]])])

    package = parts[1].strip()
    if len(package) > 200 or not re.fullmatch(r"[A-Za-z0-9_.-]+", package):
        return await event.answer([], switch_pm="Invalid PyPI package name.", switch_pm_param="start")
    try:
        response = await async_searcher(f"https://pypi.org/pypi/{quote(package, safe='')}/json", re_json=True)
    except Exception as exc:
        LOGS.exception("PyPI lookup failed: %s", exc)
        return await event.answer([], switch_pm="PyPI is currently unavailable.", switch_pm_param="start")

    info = response.get("info") if isinstance(response, dict) else None
    if not isinstance(info, dict):
        media = InputWebDocument(_IMAGE, 0, "image/jpeg", [])
        return await event.answer([await event.builder.article(title="ᴘᴀᴄᴋᴀɢᴇ ɴᴏᴛ ғᴏᴜɴᴅ", thumb=media, text=f"**ᴘᴀᴄᴋᴀɢᴇ:** `{package}`\n\nɴᴏᴛ ғᴏᴜɴᴅ")])

    name = _clean(info.get("name"), package)
    version = _clean(info.get("version"), "unknown")
    url = _clean(info.get("package_url"), f"https://pypi.org/project/{quote(name)}/")
    summary = _clean(info.get("summary"), "No summary available.")
    description = _description(info.get("description"))
    qid = _id(name, version)
    text = f"**ᴘᴀᴄᴋᴀɢᴇ:** [{name}]({url}) (`{version}`)\n\n**ᴅᴇᴛᴀɪʟs:** {summary[:1400]}"
    _put(qid, {"info": info, "name": name, "url": url, "version": version, "summary": summary, "text": text, "description": description, "document_links": _document_links(description), "buttons": _buttons(qid)})
    media = InputWebDocument(_IMAGE, 0, "image/jpeg", [])
    return await event.answer([await event.builder.article(type="photo", include_media=True, title="ᴘᴀᴄᴋᴀɢᴇ ɪɴғᴏ", thumb=media, content=media, description=f"{name}\n{version}", text=text[:3900], buttons=_buttons(qid))])


@callback(re.compile(r"^pypi_details:([A-Za-z0-9]+)$"), owner=False)
async def show_details(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _STORE.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍", alert=True)
    info = item["info"]
    classifiers = "\n".join(info.get("classifiers") or []) or "—"
    text = f"**ᴀᴜᴛʜᴏʀ:** {_clean(info.get('author'))}\n**ᴀᴜᴛʜᴏʀ ᴇᴍᴀɪʟ:** {_clean(info.get('author_email'))}\n**ᴄʟᴀssɪғɪᴇʀs:**\n{classifiers[:1800]}"
    buttons = [[Button.inline("ᴍᴏʀᴇ", data=f"pypi_description_more:{qid}"), Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}")]] if item.get("description") else [[Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}")]]
    return await event.edit(text[:3900], buttons=buttons)


@callback(re.compile(r"^pypi_documents:([A-Za-z0-9]+)$"), owner=False)
async def show_documents(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _STORE.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍", alert=True)
    links = item.get("document_links") or []
    if not links:
        return await event.answer("ɴᴏ ᴅᴏᴄᴜᴍᴇɴᴛ ʟɪɴᴋs ғᴏᴜɴᴅ.", alert=True)
    lines = ["**ᴅᴏᴄ ʟɪɴᴋs**", ""]
    for link in links[:15]:
        lines.append(f"• [{link.split('//', 1)[-1].split('/', 1)[0]}]({link})")
    return await event.edit("\n".join(lines)[:3900], buttons=[[Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}")]])


async def _show_page(event, qid, page):
    item = _STORE.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ!", alert=True)
    description = item.get("description") or "No description available."
    page_size = 2800
    pages = [description[i:i + page_size] for i in range(0, len(description), page_size)] or ["No description available."]
    page = max(1, min(page, len(pages)))
    buttons = []
    if page > 1:
        buttons.append(Button.inline("<<", data=f"pypi_description_page:{qid}:{page-1}"))
    buttons.append(Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}"))
    if page < len(pages):
        buttons.append(Button.inline(">>", data=f"pypi_description_page:{qid}:{page+1}"))
    return await event.edit(f"**ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:**\n**Pᴀɢᴇ** `{page}`/`{len(pages)}`\n{pages[page-1]}", buttons=[buttons])


@callback(re.compile(r"^pypi_description_more:([A-Za-z0-9]+)$"), owner=False)
async def show_full_description(event):
    qid = event.data.decode().split(":", 1)[1]
    return await _show_page(event, qid, 1)


@callback(re.compile(r"^pypi_description_page:([A-Za-z0-9]+):(\d+)$"), owner=False)
async def handle_description_page(event):
    qid, page = event.data.decode().split(":")[1:]
    return await _show_page(event, qid, int(page))


@callback(re.compile(r"^pypi_back_button:([A-Za-z0-9]+)$"), owner=False)
async def back_button_clicked(event):
    qid = event.data.decode().split(":", 1)[1]
    item = _STORE.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍", alert=True)
    return await event.edit(item["text"][:3900], buttons=item["buttons"])


InlinePlugin.update({"ᴘʏᴘɪ sᴇᴀʀᴄʜ": "pypi"})
