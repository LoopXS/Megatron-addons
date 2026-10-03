"""
✘ Commands Available -

• `{i}mmf <upper text> ; <lower text>` (reply to media)
    To create memes as sticker,
    for trying different fonts use (.mmf <text>_1)(u can use 1 to 10).

• `{i}mms <upper text> ; <lower text>` (reply to media)
    To create memes as pic,
    for trying different fonts use (.mms <text>_1)(u can use 1 to 10).

"""

import asyncio
import os
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont

from . import *

FONT_DIR = "resources/fonts"
DEFAULT_FONT = "1"
os.makedirs("downloads", exist_ok=True)


def _parse(msg):
    """'upper ; lower _3' -> ('upper', 'lower', '3')"""
    font = DEFAULT_FONT
    if m := re.search(r"_(\d{1,2})\s*$", msg):
        if 1 <= int(m.group(1)) <= 10:
            font, msg = m.group(1), msg[: m.start()]
    upper, _, lower = msg.partition(";")
    return upper.strip(), lower.strip(), font


def _outlined(draw, xy, text, font):
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))


def _font_path(name):
    """Fonts 1-10 are a mix of .ttf and .otf files (e.g. 3 and 4 are .otf)."""
    for ext in ("ttf", "otf"):
        path = f"{FONT_DIR}/{name}.{ext}"
        if os.path.exists(path):
            return path
    return f"{FONT_DIR}/{DEFAULT_FONT}.ttf"


def draw_meme(image_path, msg, lower_margin):
    """Render the meme text on the image and return a PIL image (blocking)."""
    upper_text, lower_text, font_name = _parse(msg)
    img = Image.open(image_path).convert("RGBA")
    i_width, i_height = img.size
    draw = ImageDraw.Draw(img)
    m_font = ImageFont.truetype(
        _font_path(font_name), max(10, int((70 / 640) * i_width))
    )
    pad, current_h = 5, 10
    for u_text in textwrap.wrap(upper_text, width=15):
        u_width, u_height = text_size(m_font, u_text, draw)
        _outlined(
            draw, ((i_width - u_width) / 2, int((current_h / 640) * i_width)), u_text, m_font
        )
        current_h += u_height + pad
    for l_text in textwrap.wrap(lower_text, width=15):
        u_width, u_height = text_size(m_font, l_text, draw)
        _outlined(
            draw,
            (
                (i_width - u_width) / 2,
                i_height - u_height - int((lower_margin / 640) * i_width),
            ),
            l_text,
            m_font,
        )
        current_h += u_height + pad
    return img


async def _first_frame(media_path, out_png):
    """Convert a downloaded media file to a PNG (image, tgs or video)."""
    if media_path.endswith(".tgs"):
        proc = await asyncio.create_subprocess_exec(
            "lottie_convert.py",
            media_path,
            out_png,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()
        return os.path.exists(out_png)
    if media_path.endswith((".webp", ".png", ".jpg", ".jpeg")):
        Image.open(media_path).convert("RGBA").save(out_png, format="PNG")
        return True
    try:
        import cv2  # optional dependency (opencv-python-headless)
    except ImportError:
        return False
    cap = cv2.VideoCapture(media_path)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return False
    cv2.imwrite(out_png, frame)
    return True


async def _memify(event, as_sticker):
    ureply = await event.get_reply_message()
    msg = (event.pattern_match.group(1) or "").strip()
    if not (ureply and ureply.media):
        return await eod(event, "`Reply to any media`")
    if not msg:
        return await eod(event, "`Give me something text to write...`")
    xx = await event.eor("`Ooo Animated Sticker 👀...`" if ureply.file and ureply.file.ext == ".tgs" else proc_text())
    base = f"downloads/meme_{event.id}"
    downloaded, png, out = None, f"{base}.png", f"{base}_out.{'webp' if as_sticker else 'png'}"
    try:
        downloaded = await ureply.download_media(base)
        if not await _first_frame(downloaded, png):
            return await xx.edit("`Could not read this media (is opencv/lottie installed for videos/stickers?).`")
        img = await asyncio.to_thread(draw_meme, png, msg, 80 if as_sticker else 20)
        img.save(out, "WebP" if as_sticker else "PNG")
        await event.client.send_file(
            event.chat_id, out, force_document=False, reply_to=event.reply_to_msg_id
        )
        await xx.delete()
    except OSError as er:  # unreadable image / missing font
        LOGS.warning(f"memify failed: {er}")
        await xx.edit(f"`Failed to create the meme: {er}`")
    finally:
        for path in (downloaded, png, out):
            if path and os.path.exists(path):
                os.remove(path)


@ultroid_cmd(pattern=r"mmf(?:\s+([\s\S]*))?$")
async def ultd(event):
    await _memify(event, as_sticker=True)


@ultroid_cmd(pattern=r"mms(?:\s+([\s\S]*))?$")
async def mms(event):
    await _memify(event, as_sticker=False)
