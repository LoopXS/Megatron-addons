"""
✘ Commands Available -

• `{i}mencode <text>` (or reply)
   Encode the given text to Morse Code.

• `{i}mdecode <text>` (or reply)
   Decode the given text from Morse Code.
"""

from . import arg_or_reply, async_searcher, LOGS, proc_text, heartless_cmd, url_quote

API = "https://apis.xditya.me/morse/{}?text={}"


async def _morse(event, mode, title, label):
    text = await arg_or_reply(event)
    if not text:
        return await event.eor("Please give a text!", time=5)
    msg = await event.eor(proc_text())
    try:
        result = await async_searcher(API.format(mode, url_quote(text)))
    except Exception as er:
        LOGS.warning(f"Morse API failed: {er}")
        return await msg.edit("`Morse API is unreachable, try again later.`")
    result = (result or "").strip()
    if not result:
        return await msg.edit("`The Morse API returned an empty answer.`")
    await msg.edit(f"**{title}.**\n\n**{label}:** `{result[:3500]}`")


@heartless_cmd(pattern=r"mencode(?:\s+([\s\S]*))?$")
async def mencode(event):
    await _morse(event, "encode", "Encoded", "Morse Code")


@heartless_cmd(pattern=r"mdecode(?:\s+([\s\S]*))?$")
async def mdecode(event):
    await _morse(event, "decode", "Decoded", "Message")
