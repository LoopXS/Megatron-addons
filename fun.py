"""
✘ Commands Available

• `{i}joke`
    To get joke.

• `{i}phlogo <first_name> <last_name>`
    Make a phub based logo.

• `{i}decide`
    Decide something.

• `{i}xo`
    Opens tic tac game only where using inline mode is allowed.

• `{i}wordi`
    Opens word game only where using inline mode is allowed.

• `{i}gps <name of place>`
    Shows the desired place in the map.
"""

import os
import random

from phlogo import generate
from pyjokes import get_joke
from telethon.errors import ChatSendMediaForbiddenError

from . import HNDLR, LOGS, async_searcher, proc_text, ultroid_cmd


@ultroid_cmd(pattern="joke$")
async def _(ult):
    await ult.eor(get_joke())


@ultroid_cmd(pattern="decide$")
async def _(event):
    hm = await event.eor("`Deciding`")
    try:
        r = await async_searcher("https://yesno.wtf/api", re_json=True)
        answer, image = r["answer"], r["image"]
    except Exception as er:
        LOGS.warning(f"yesno.wtf failed: {er}")
        return await hm.edit("`Could not decide right now, try again later.`")
    try:
        await event.reply(answer, file=image)
        await hm.delete()
    except ChatSendMediaForbiddenError:
        await hm.edit(answer)


async def _click_first(event, bot_name, query, *, pick_random=False):
    """Run an inline query on another bot and send one result to the chat."""
    results = await event.client.inline_query(bot_name, query)
    if not results:
        return False
    result = random.choice(results) if pick_random else results[0]
    await result.click(
        event.chat_id, reply_to=event.reply_to_msg_id, silent=True, hide_via=True
    )
    return True


@ultroid_cmd(pattern="xo$")
async def xo(ult):
    if not await _click_first(ult, "xobot", "play", pick_random=True):
        return await ult.eor("`No game found.`", time=5)
    await ult.delete()


@ultroid_cmd(pattern=r"phlogo(?:\s+([\s\S]*))?$")
async def make_logog(ult):
    match = (ult.pattern_match.group(1) or "").strip()
    if not match:
        reply = await ult.get_reply_message()
        match = (reply.text or "").strip() if reply else ""
    if not match:
        return await ult.eor("`Provide a name to make logo...`", time=5)
    msg = await ult.eor(proc_text())
    words = match.split()
    first, last = (words[0], words[1]) if len(words) >= 2 else ("", match)
    name = f"phlogo_{ult.id}.png"
    try:
        generate(first, last).save(name)
        await ult.client.send_message(
            ult.chat_id, file=name, reply_to=ult.reply_to_msg_id or ult.id
        )
    finally:
        if os.path.exists(name):
            os.remove(name)
    await msg.delete()


Bot = {"gps": "openmap_bot", "wordi": "wordibot"}


@ultroid_cmd(pattern=r"(gps|wordi)(?:\s+([\s\S]+))?$")
async def _map(ult):
    cmd = ult.pattern_match.group(1)
    get = (ult.pattern_match.group(2) or "").strip()
    if not get:
        return await ult.eor(f"Use this command as `{HNDLR}{cmd} <query>`", time=8)
    if not await _click_first(ult, Bot[cmd], get):
        return await ult.eor("`No results found.`", time=5)
    await ult.delete()
