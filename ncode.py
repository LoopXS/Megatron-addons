# Credits @buddhhu
# Ported to Ultroid by @Hackintush

"""
✘ Commands Available
• `{i}ncode <reply to file>`
   Paste the contents of file and send as pic.
"""

import os

import pygments
from pygments.formatters import ImageFormatter
from pygments.lexers import Python3Lexer

from . import *


@ultroid_cmd(pattern="ncode")
async def coder_print(event):
    a = await event.client.download_media(
        await event.get_reply_message(),
    )
    s = open(a, "r")
    c = s.read()
    s.close()
    pygments.highlight(
        f"{c}",
        Python3Lexer(),
        ImageFormatter(font_name="DejaVu Sans Mono", line_numbers=True),
        "cipherx.png",
    )
    res = await event.client.send_message(
        event.chat_id,
        "Pasting this code on my page...",
        reply_to=event.reply_to_msg_id,
    )
    await event.client.send_file(
        event.chat_id,
        "cipherx.png",
        force_document=True,
        reply_to=event.reply_to_msg_id,
    )
    await res.delete()
    await event.delete()
    os.remove(a)
    os.remove("cipherx.png")


