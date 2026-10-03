"""
✘ Commands Available -

• `{i}spcheck <text>` (or reply to a message)
    Check spelling of the text/sentence (English).
"""

import asyncio

from textblob import TextBlob

from . import *


@ultroid_cmd(pattern=r"spcheck(?:\s+([\s\S]*))?$")
async def spellchk(event):
    to_check = await arg_or_reply(event)
    if not to_check:
        return await eod(event, "`Give me some text/sentence to check its spelling!.`")
    # TextBlob.correct() is CPU heavy (pure Python) -> keep it off the event loop
    correct = await asyncio.to_thread(lambda: str(TextBlob(to_check).correct()))
    await event.eor(
        f"**Given Phrase:** `{to_check[:1800]}`\n**Corrected Phrase:** `{correct[:1800]}`"
    )
