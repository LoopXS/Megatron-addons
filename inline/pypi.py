import hashlib
import re

from telethon import Button
from telethon.tl.types import InputWebDocument as wb

try:
    from markdownify import markdownify as md
except ImportError:  # optional: falls back to the raw description
    md = None

from . import InlinePlugin, LOGS, TTLCache, async_searcher, callback, in_pattern, url_quote

PYPI_LIST = TTLCache(maxsize=200, ttl=3 * 3600)
PAGE_SIZE = 1000  # characters of description per page (message limit is 4096)
pypimg = "https://graph.org/file/004c65a44efa1efc85193.jpg"
pypimg2 = "https://graph.org/file/f09380ada91534b2f6687.jpg"


def generate_unique_id(name):
    return hashlib.sha256(name.encode()).hexdigest()[:8]


def clean_desc(description):
    description = re.sub(r"^\.\.", "", description, flags=re.MULTILINE)
    description = re.sub(r"^\|", "", description, flags=re.MULTILINE)
    description = re.sub(r"^:", "", description, flags=re.MULTILINE)
    description = re.sub(r"^ {2}:", "", description, flags=re.MULTILINE)
    description = re.sub(r"/\d+/", "", description)
    description = re.sub(
        r"^\s*code-block::.*$", "", description, flags=re.IGNORECASE | re.MULTILINE
    )
    return description.strip()


def _qid(event):
    return event.data.decode().split(":")[1]


@in_pattern("pypi", owner=False)
async def inline_pypi_handler(event):
    parts = event.text.split(" ", maxsplit=1)
    package = parts[1].strip() if len(parts) > 1 else ""
    if not package:
        return await event.answer(
            [
                await event.builder.article(
                    type="photo",
                    include_media=True,
                    title="sᴇᴀʀᴄʜ ᴘʏᴘɪ",
                    thumb=wb(pypimg, 0, "image/jpeg", []),
                    content=wb(pypimg, 0, "image/jpeg", []),
                    text="**ᴘʏᴘɪ sᴇᴀʀᴄʜ**\n\nUsage: `pypi <package>`",
                    buttons=[
                        Button.switch_inline("sᴇᴀʀᴄʜ ᴀɢᴀɪɴ", query="pypi ", same_peer=True)
                    ],
                )
            ]
        )

    try:
        response = await async_searcher(
            f"https://pypi.org/pypi/{url_quote(package)}/json", re_json=True
        )
    except Exception as er:
        LOGS.warning(f"PyPI request failed: {er}")
        response = None

    if not isinstance(response, dict) or "info" not in response:
        return await event.answer(
            [
                await event.builder.article(
                    title="ᴘᴀᴄᴋᴀɢᴇ ɴᴏᴛ ғᴏᴜɴᴅ",
                    thumb=wb(pypimg, 0, "image/jpeg", []),
                    text=f"**ᴘᴀᴄᴋᴀɢᴇ:** `{package}`\n\n**ᴅᴇᴛᴀɪʟs:** `ɴᴏᴛ ғᴏᴜɴᴅ`",
                )
            ]
        )

    info = response["info"]
    name = info.get("name") or package
    url = info.get("package_url") or f"https://pypi.org/project/{name}/"
    version = info.get("version") or "?"
    summary = info.get("summary") or "No summary"
    qid = generate_unique_id(name)
    txt = f"**ᴘᴀᴄᴋᴀɢᴇ:** [{name}]({url}) (`{version}`)\n\n**ᴅᴇᴛᴀɪʟs:** `{summary}`"
    document_links = re.findall(r"(https?://[^\s)\]>\"']+)", info.get("description") or "")
    buttons = [
        Button.inline("sʜᴏᴡ ᴅᴇᴛᴀɪʟs", data=f"pypi_details:{qid}"),
        Button.inline("ᴅᴏᴄᴜᴍᴇɴᴛ ʟɪɴᴋs", data=f"pypi_documents:{qid}"),
    ]
    PYPI_LIST.set(
        qid,
        {"info": info, "text": txt, "document_links": document_links, "buttons": buttons},
    )
    await event.answer(
        [
            await event.builder.article(
                type="photo",
                include_media=True,
                title="ᴘᴀᴄᴋᴀɢᴇ ɪɴғᴏ",
                thumb=wb(pypimg2, 0, "image/jpeg", []),
                content=wb(pypimg2, 0, "image/jpeg", []),
                description=f"{name}\n{version}",
                text=txt,
                buttons=buttons,
            )
        ]
    )


@callback(re.compile("pypi_details:(.*)"), owner=False)
async def show_details(event):
    qid = _qid(event)
    item = PYPI_LIST.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍")
    details = item["info"]
    description = details.get("description") or ""
    if description:
        formatted = md(description) if md else description
        item["description"] = clean_desc(re.sub(r"\*\*|`|\\|_", "", formatted))

    classifiers = "\n".join(details.get("classifiers") or [])[:2000]
    text = (
        f"**ᴀᴜᴛʜᴏʀ:** {details.get('author') or 'Uɴᴋɴᴏᴡɴ'}\n"
        f"**ᴀᴜᴛʜᴏʀ ᴇᴍᴀɪʟ:** {details.get('author_email') or 'Uɴᴋɴᴏᴡɴ'}\n"
        f"**ᴄʟᴀssɪғɪᴇʀs:**\n{classifiers}\n"
    )
    buttons = [Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}")]
    if item.get("description"):
        buttons.insert(0, Button.inline("ᴍᴏʀᴇ", data=f"pypi_description_more:{qid}"))
    await event.edit(text, buttons=buttons)


@callback(re.compile("pypi_documents:(.*)"), owner=False)
async def show_documents(event):
    qid = _qid(event)
    item = PYPI_LIST.get(qid)
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍")
    links = list(dict.fromkeys(item["document_links"]))[:25]
    if not links:
        return await event.answer("ɴᴏ ᴅᴏᴄᴜᴍᴇɴᴛ ʟɪɴᴋs ғᴏᴜɴᴅ.")
    text = "**ᴅᴏᴄ ʟɪɴᴋs**\n╭────────────────•\n"
    text += "\n".join(f"╰➢ [{link.split('//')[1].split('/')[0]}]({link})" for link in links)
    text += "\n╰────────────────•"
    await event.edit(
        text[:4000], buttons=[Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}")]
    )


async def show_description_page(event, qid, page):
    item = PYPI_LIST.get(qid)
    description = item.get("description") if item else None
    if not description:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍")
    chunks = [description[i : i + PAGE_SIZE] for i in range(0, len(description), PAGE_SIZE)]
    page = max(1, min(page, len(chunks)))  # clamp: never wrap around / IndexError
    text = f"**ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:**\n**Pᴀɢᴇ** `{page}`/`{len(chunks)}`\n{chunks[page - 1]}"
    nav = []
    if page > 1:
        nav.append(Button.inline("<<", data=f"pypi_description_page:{qid}:{page - 1}"))
    nav.append(Button.inline("ʙᴀᴄᴋ", data=f"pypi_back_button:{qid}"))
    if page < len(chunks):
        nav.append(Button.inline(">>", data=f"pypi_description_page:{qid}:{page + 1}"))
    await event.edit(text, buttons=nav)


@callback(re.compile("pypi_description_more:(.*)"), owner=False)
async def show_full_description(event):
    await show_description_page(event, _qid(event), 1)


@callback(re.compile(r"pypi_description_page:(.*):(\d+)"), owner=False)
async def handle_description_page(event):
    _, qid, page = event.data.decode().split(":")
    await show_description_page(event, qid, int(page))


@callback(re.compile("pypi_back_button:(.*)"), owner=False)
async def back_button_clicked(event):
    item = PYPI_LIST.get(_qid(event))
    if not item:
        return await event.answer("Qᴜᴇʀʏ ᴇxᴘɪʀᴇᴅ! Sᴇᴀʀᴄʜ ᴀɢᴀɪɴ 🔍")
    await event.edit(item["text"], buttons=item["buttons"])


InlinePlugin.update({"ᴘʏᴘɪ sᴇᴀʀᴄʜ": "pypi"})
