"""
✘ Commands Available -

• `{i}type <msg>`
    Edits the Message and shows like someone is typing (max 150 characters).
"""

import asyncio

from telethon.errors import FloodWaitError, MessageNotModifiedError

from . import *

MAX_CHARS = 150


@ultroid_cmd(pattern=r"type(?:\s+([\s\S]*))?$", fullsudo=True)
async def _(event):
    input_str = await arg_or_reply(event)
    if not input_str:
        return await eod(event, "Give me something to type !")
    input_str = input_str[:MAX_CHARS]
    typing_symbol = "|"
    previous_text = ""
    okla = await event.eor("\u2060" * 602)
    for character in input_str:
        previous_text += character
        try:
            await okla.edit(previous_text + typing_symbol)
            await asyncio.sleep(0.1)
            await okla.edit(previous_text)
            await asyncio.sleep(0.1)
        except MessageNotModifiedError:
            pass
        except FloodWaitError as fw:
            await asyncio.sleep(min(fw.seconds, 120) + 1)
