"""
✘ Commands Available -

• `{i}sticklet <text>`
   `create random sticker with text.`
"""

import io
import random
import textwrap
from glob import glob

from PIL import Image, ImageDraw, ImageFont

from . import *

FONTS = glob("resources/fonts/*ttf")  # .ttf only; the .otf fonts are for quotes


def _render(text):
    color = tuple(random.randint(0, 255) for _ in range(3))
    wrapped = "\n".join(textwrap.wrap(text, width=10)) or text
    image = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    font_file = random.choice(FONTS)
    # shrink until the text fits the 512x512 canvas
    for size in range(230, 20, -10):
        font = ImageFont.truetype(font_file, size=size)
        width, height = text_size(font, wrapped, draw, multiline=True)
        if width <= 512 and height <= 512:
            break
    draw.multiline_text(
        ((512 - width) / 2, (512 - height) / 2), wrapped, font=font, fill=color
    )
    stream = io.BytesIO()
    stream.name = "sticklet.webp"
    image.save(stream, "WebP")
    stream.seek(0)
    return stream, wrapped


@heartless_cmd(pattern=r"sticklet(?:\s+([\s\S]*))?$")
async def sticklet(event):
    sticktext = await arg_or_reply(event)
    if not sticktext:
        return await eod(event, "`Give me some Text`")
    if not FONTS:
        return await eod(event, "`No .ttf fonts found in resources/fonts.`")
    a = await event.eor(proc_text())
    stream, wrapped = _render(sticktext[:200])
    await a.delete()
    await event.client.send_message(
        event.chat_id,
        wrapped,
        file=stream,
        reply_to=event.message.reply_to_msg_id,
    )
