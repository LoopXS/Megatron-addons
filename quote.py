"""
✘ Commands Available -

• `{i}qbot <reply>`
    Make sticker quote without QuotlyBot
"""


import io
import os
import random
import textwrap

import emoji
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageOps
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl import functions, types
from telethon.utils import get_display_name

from . import *

# Oringinal Source from Nicegrill: https://github.com/erenmetesar/NiceGrill/
# Ported to Ultroid


def is_emoji(char):
    """`emoji.UNICODE_EMOJI` was removed in emoji 2.0 (`EMOJI_DATA` replaced it)."""
    data = getattr(emoji, "EMOJI_DATA", None)
    if data is None:
        data = getattr(emoji, "UNICODE_EMOJI", {})
    return char in data


COLORS = [
    "#F07975",
    "#F49F69",
    "#F9C84A",
    "#8CC56E",
    "#6CC7DC",
    "#80C1FA",
    "#BCB3F9",
    "#E181AC",
]


async def process(msg, user, client, reply, replied=None):
    # Importıng fonts and gettings the size of text
    font = ImageFont.truetype(
        "resources/fonts/1.ttf", 43, encoding="utf-16"
    )
    font2 = ImageFont.truetype(
        "resources/fonts/10.ttf", 33, encoding="utf-16"
    )
    mono = ImageFont.truetype(
        "resources/fonts/12.ttf", 30, encoding="utf-16"
    )
    italic = ImageFont.truetype(
        "resources/fonts/18.ttf", 33, encoding="utf-16"
    )
    fallback = ImageFont.truetype("resources/fonts/0.otf", 43, encoding="utf-16")

    # Splitting text
    maxlength = 0
    width = 0
    text = []
    for line in msg.split("\n"):
        length = len(line)
        if length > 43:
            text += textwrap.wrap(line, 43)
            maxlength = 43
            if width < int(fallback.getlength(line[:43])):
                if "MessageEntityCode" in str(reply.entities):
                    width = int(mono.getlength(line[:43])) + 30
                else:
                    width = int(fallback.getlength(line[:43]))
        else:
            text.append(line + "\n")
            if width < int(fallback.getlength(line)):
                if "MessageEntityCode" in str(reply.entities):
                    width = int(mono.getlength(line)) + 30
                else:
                    width = int(fallback.getlength(line))
            if maxlength < length:
                maxlength = length

    title = ""
    try:
        details = await client(
            functions.channels.GetParticipantRequest(reply.chat_id, user.id)
        )
        if isinstance(details.participant, types.ChannelParticipantCreator):
            title = details.participant.rank if details.participant.rank else "Creator"
        elif isinstance(details.participant, types.ChannelParticipantAdmin):
            title = details.participant.rank if details.participant.rank else "Admin"
    except (TypeError, UserNotParticipantError):
        pass
    except Exception as er:
        LOGS.exception(er)
    titlewidth = int(font2.getlength(title))

    # Get user name
    tot = get_display_name(user) or "Deleted Account"

    namewidth = int(fallback.getlength(tot)) + 10

    if namewidth > width:
        width = namewidth
    width += titlewidth + 30 if titlewidth > width - namewidth else -(titlewidth - 30)
    height = len(text) * 40

    # Profile Photo BG
    pfpbg = Image.new("RGBA", (125, 600), (0, 0, 0, 0))

    # Draw Template
    top, middle, bottom = await drawer(width, height)
    # Profile Photo Check and Fetch
    yes = False
    color = random.choice(COLORS)
    async for photo in client.iter_profile_photos(user, limit=1):
        yes = True
    if yes:
        pfp = await client.download_profile_photo(user)
        paste = Image.open(pfp)
        os.remove(pfp)
        paste.thumbnail((105, 105))

        # Mask
        mask_im = Image.new("L", paste.size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, 105, 105), fill=255)

        # Apply Mask
        pfpbg.paste(paste, (0, 0), mask_im)
    else:
        paste, color = await no_photo(user, tot)
        pfpbg.paste(paste, (0, 0))

    # Creating a big canvas to gather all the elements
    canvassize = (
        middle.width + pfpbg.width,
        top.height + middle.height + bottom.height,
    )
    canvas = Image.new("RGBA", canvassize)
    draw = ImageDraw.Draw(canvas)

    y = 80
    if replied:
        # Creating a big canvas to gather all the elements
        reptot = get_display_name(await replied.get_sender()) or "Deleted Account"
        if reply.sticker:
            sticker = await reply.download_media()
            stimg = Image.open(sticker)
            canvas = canvas.resize((stimg.width + pfpbg.width, stimg.height + 160))
            top = Image.new("RGBA", (200 + stimg.width, 300), (29, 29, 29, 255))
            draw = ImageDraw.Draw(top)
            await replied_user(
                draw, reptot, replied.message.replace("\n", " "), 20, len(title)
            )
            top = top.crop((135, 70, top.width, 300))
            canvas.paste(pfpbg, (0, 0))
            canvas.paste(top, (pfpbg.width + 10, 0))
            canvas.paste(stimg, (pfpbg.width + 10, 140))
            os.remove(sticker)
            return True, canvas
        canvas = canvas.resize((canvas.width + 60, canvas.height + 120))
        top, middle, bottom = await drawer(middle.width + 60, height + 105)
        canvas.paste(pfpbg, (0, 0))
        canvas.paste(top, (pfpbg.width, 0))
        canvas.paste(middle, (pfpbg.width, top.height))
        canvas.paste(bottom, (pfpbg.width, top.height + middle.height))
        draw = ImageDraw.Draw(canvas)
        if replied.sticker:
            replied.text = "Sticker"
        elif replied.photo:
            replied.text = "Photo"
        elif replied.audio:
            replied.text = "Audio"
        elif replied.voice:
            replied.text = "Voice Message"
        elif replied.document:
            replied.text = "Document"
        await replied_user(
            draw,
            reptot,
            replied.message.replace("\n", " "),
            maxlength + len(title),
            len(title),
        )
        y = 200
    elif reply.sticker:
        sticker = await reply.download_media()
        stimg = Image.open(sticker)
        canvas = canvas.resize((stimg.width + pfpbg.width + 30, stimg.height + 10))
        canvas.paste(pfpbg, (0, 0))
        canvas.paste(stimg, (pfpbg.width + 10, 10))
        os.remove(sticker)
        return True, canvas
    elif reply.document and not reply.audio and not reply.voice:
        fname_ = reply.file.name or "file"
        docname = ".".join(fname_.split(".")[:-1]) or fname_
        doctype = fname_.split(".")[-1].upper() if "." in fname_ else ""
        if reply.document.size < 1024:
            docsize = str(reply.document.size) + " Bytes"
        elif reply.document.size < 1048576:
            docsize = str(round(reply.document.size / 1024, 2)) + " KB "
        elif reply.document.size < 1073741824:
            docsize = str(round(reply.document.size / 1024**2, 2)) + " MB "
        else:
            docsize = str(round(reply.document.size / 1024**3, 2)) + " GB "
        docbglen = (
            int(font.getlength(docsize))
            if int(font.getlength(docsize)) > int(font.getlength(docname))
            else int(font.getlength(docname))
        )
        canvas = canvas.resize((pfpbg.width + width + docbglen, 160 + height))
        top, middle, bottom = await drawer(width + docbglen, height + 30)
        canvas.paste(pfpbg, (0, 0))
        canvas.paste(top, (pfpbg.width, 0))
        canvas.paste(middle, (pfpbg.width, top.height))
        canvas.paste(bottom, (pfpbg.width, top.height + middle.height))
        canvas = await doctype(docname, docsize, doctype, canvas)
        y = 80 if text else 0
    else:
        canvas.paste(pfpbg, (0, 0))
        canvas.paste(top, (pfpbg.width, 0))
        canvas.paste(middle, (pfpbg.width, top.height))
        canvas.paste(bottom, (pfpbg.width, top.height + middle.height))
        y = 85

    # Writing User's Name
    space = pfpbg.width + 30
    namefallback = ImageFont.truetype(
        "resources/fonts/0.otf", 43, encoding="utf-16"
    )
    for letter in tot:
        if is_emoji(letter):
            newemoji, mask = await emoji_fetch_safe(letter)
            canvas.paste(newemoji, (space, 24), mask)
            space += 40
        else:
            if not await fontTest(letter):
                draw.text((space, 20), letter, font=namefallback, fill=color)
                space += int(namefallback.getlength(letter))
            else:
                draw.text((space, 20), letter, font=font, fill=color)
                space += int(font.getlength(letter))

    if title:
        draw.text(
            (canvas.width - titlewidth - 20, 25), title, font=font2, fill="#898989"
        )

    # Writing all separating emojis and regular texts
    x = pfpbg.width + 30
    bold, mono, italic, link = await get_entity(reply)
    index = 0
    emojicount = 0
    textfallback = ImageFont.truetype(
        "resources/fonts/0.otf", 33, encoding="utf-16"
    )
    textcolor = "white"
    for line in text:
        for letter in line:
            index = (
                msg.find(letter) if emojicount == 0 else msg.find(letter) + emojicount
            )
            for offset, length in bold.items():
                if index in range(offset, length):
                    font2 = ImageFont.truetype(
                        "resources/fonts/1.ttf", 33, encoding="utf-16"
                    )
                    textcolor = "white"
            for offset, length in italic.items():
                if index in range(offset, length):
                    font2 = ImageFont.truetype(
                        "resources/fonts/10.ttf", 33, encoding="utf-16"
                    )
                    textcolor = "white"
            for offset, length in mono.items():
                if index in range(offset, length):
                    font2 = ImageFont.truetype(
                        "resources/fonts/12.ttf", 30, encoding="utf-16"
                    )
                    textcolor = "white"
            for offset, length in link.items():
                if index in range(offset, length):
                    font2 = ImageFont.truetype(
                        "resources/fonts/18.ttf", 30, encoding="utf-16"
                    )
                    textcolor = "#898989"
            if is_emoji(letter):
                newemoji, mask = await emoji_fetch_safe(letter)
                canvas.paste(newemoji, (x, y - 2), mask)
                x += 45
                emojicount += 1
            else:
                if not await fontTest(letter):
                    draw.text((x, y), letter, font=textfallback, fill=textcolor)
                    x += int(textfallback.getlength(letter))
                else:
                    draw.text((x, y), letter, font=font2, fill=textcolor)
                    x += int(font2.getlength(letter))
            msg = msg.replace(letter, "¶", 1)
        y += 40
        x = pfpbg.width + 30
    return True, canvas


async def drawer(width, height):
    # Top part
    top = Image.new("RGBA", (width, 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(top)
    draw.line((10, 0, top.width - 20, 0), fill=(29, 29, 29, 255), width=50)
    draw.pieslice((0, 0, 30, 50), 180, 270, fill=(29, 29, 29, 255))
    draw.pieslice((top.width - 75, 0, top.width, 50), 270, 360, fill=(29, 29, 29, 255))

    # Middle part
    middle = Image.new("RGBA", (top.width, height + 75), (29, 29, 29, 255))

    # Bottom part
    bottom = ImageOps.flip(top)

    return top, middle, bottom


_CMAP = None


async def fontTest(letter):
    global _CMAP
    if _CMAP is None:
        _CMAP = set()
        for table in TTFont("resources/fonts/18.ttf")["cmap"].tables:
            _CMAP.update(table.cmap.keys())
    return ord(letter) in _CMAP


async def get_entity(msg):
    bold = {0: 0}
    italic = {0: 0}
    mono = {0: 0}
    link = {0: 0}
    if not msg.entities:
        return bold, mono, italic, link
    for entity in msg.entities:
        if isinstance(entity, types.MessageEntityBold):
            bold[entity.offset] = entity.offset + entity.length
        elif isinstance(entity, types.MessageEntityItalic):
            italic[entity.offset] = entity.offset + entity.length
        elif isinstance(entity, types.MessageEntityCode):
            mono[entity.offset] = entity.offset + entity.length
        elif isinstance(entity, types.MessageEntityUrl):
            link[entity.offset] = entity.offset + entity.length
        elif isinstance(entity, types.MessageEntityTextUrl):
            link[entity.offset] = entity.offset + entity.length
        elif isinstance(entity, types.MessageEntityMention):
            link[entity.offset] = entity.offset + entity.length
    return bold, mono, italic, link


async def doctype(name, size, _type, canvas):
    font = ImageFont.truetype("resources/fonts/12.ttf", 38)
    doc = Image.new("RGBA", (130, 130), (29, 29, 29, 255))
    draw = ImageDraw.Draw(doc)
    draw.ellipse((0, 0, 130, 130), fill="#434343")
    draw.line((66, 28, 66, 53), width=14, fill="white")
    draw.polygon([(67, 77), (90, 53), (42, 53)], fill="white")
    draw.line((40, 87, 90, 87), width=8, fill="white")
    canvas.paste(doc, (160, 23))
    draw2 = ImageDraw.Draw(canvas)
    draw2.text((320, 40), name, font=font, fill="white")
    draw2.text((320, 97), size + _type, font=font, fill="#AAAAAA")
    return canvas


async def no_photo(reply, tot):
    pfp = Image.new("RGBA", (105, 105), (0, 0, 0, 0))
    pen = ImageDraw.Draw(pfp)
    color = random.choice(COLORS)
    pen.ellipse((0, 0, 105, 105), fill=color)
    letter = "" if not tot else tot[0]
    font = ImageFont.truetype("resources/fonts/10.ttf", 60)
    pen.text((32, 17), letter, font=font, fill="white")
    return pfp, color


_EMOJIS = None
_EMOJI_IMG = {}


async def emoji_fetch(char):
    """Fetch (and cache) the emoji image; falls back to the "no entry" emoji."""
    global _EMOJIS
    if _EMOJIS is None:
        _EMOJIS = await async_searcher(
            "https://github.com/erenmetesar/modules-repo/raw/master/emojis.txt",
            re_json=True,
        )
    key = char if char in _EMOJIS else "⛔"
    if key not in _EMOJIS:
        raise LookupError("emoji index unavailable")
    if key not in _EMOJI_IMG:
        _EMOJI_IMG[key] = await async_searcher(_EMOJIS[key], re_content=True)
    return await transparent(io.BytesIO(_EMOJI_IMG[key]))


async def emoji_fetch_safe(char):
    """Like emoji_fetch but never fails: network trouble -> blank placeholder."""
    global _EMOJIS
    try:
        return await emoji_fetch(char)
    except Exception as er:
        LOGS.warning(f"emoji image unavailable ({er}); drawing a blank placeholder")
        if _EMOJIS is None:
            _EMOJIS = {}  # do not retry the index on every single emoji
        blank = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
        return blank, Image.new("L", (40, 40), 0)


async def transparent(source):
    emoji = Image.open(source).convert("RGBA")
    emoji.thumbnail((40, 40))

    # Mask
    mask = Image.new("L", (40, 40), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 40, 40), fill=255)
    return emoji, mask


async def replied_user(draw, tot, text, maxlength, title):
    namefont = ImageFont.truetype("resources/fonts/1.ttf", 38)
    namefallback = ImageFont.truetype("resources/fonts/0.otf", 38)
    textfont = ImageFont.truetype("resources/fonts/10.ttf", 32)
    textfallback = ImageFont.truetype("resources/fonts/12.ttf", 38)
    maxlength = maxlength + 7 if maxlength < 10 else maxlength
    text = text[: maxlength - 2] + ".." if len(text) > maxlength else text
    draw.line((165, 90, 165, 170), width=5, fill="white")
    space = 0
    for letter in tot:
        if not await fontTest(letter):
            draw.text((180 + space, 86), letter, font=namefallback, fill="#888888")
            space += int(namefallback.getlength(letter))
        else:
            draw.text((180 + space, 86), letter, font=namefont, fill="#888888")
            space += int(namefont.getlength(letter))
    space = 0
    for letter in text:
        if not await fontTest(letter):
            draw.text((180 + space, 132), letter, font=textfallback, fill="#888888")
            space += int(textfallback.getlength(letter))
        else:
            draw.text((180 + space, 132), letter, font=textfont, fill="white")
            space += int(textfont.getlength(letter))


@ultroid_cmd(pattern="qbot$")
async def _(event):
    reply = await event.get_reply_message()
    if not reply:
        return await eod(event, "`Reply to a message to quote it.`")
    if not (reply.message or reply.sticker or reply.document):
        return await eod(event, "`Reply to a text message, sticker or file.`")
    msg = reply.message or ""
    repliedreply = await reply.get_reply_message()
    user = await reply.get_sender()
    out = f"downloads/qbot_{event.id}.webp"
    os.makedirs("downloads", exist_ok=True)
    try:
        res, canvas = await process(msg, user, event.client, reply, repliedreply)
        if not res:
            return
        canvas.save(out)
        await event.client.send_file(
            event.chat_id, out, reply_to=event.reply_to_msg_id
        )
        await event.delete()
    except OSError as er:  # missing font / unreadable image
        LOGS.warning(f"qbot failed: {er}")
        await eod(event, f"`Could not build the quote: {er}`")
    finally:
        if os.path.exists(out):
            os.remove(out)
