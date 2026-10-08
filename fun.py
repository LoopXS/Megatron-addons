"""
✘ Commands Available

• `{i}phlogo <first_name> <last_name>`
    Make a phub based logo. You can also reply to a text message.

• `{i}gps <name of place>`
    Shows the desired place in the map.
"""

import os

from phlogo import generate

from . import heartless_cmd, get_string, HNDLR


@heartless_cmd(pattern="phlogo( (.*)|$)")
async def make_logog(ult):
    msg = await ult.eor(get_string("com_1"))
    try:
        match = (ult.pattern_match.group(1) or "").strip()
    except Exception:
        match = ""
    reply = await ult.get_reply_message()
    if not match and reply and getattr(reply, "text", None):
        match = reply.text.strip()
    if not match:
        return await msg.edit("`Provide a name to make logo...`")

    first, last = "", ""
    parts = match.split(maxsplit=1)
    if parts:
        first = parts[0]
    if len(parts) > 1:
        last = parts[1]
    else:
        first, last = "", parts[0]

    logo = generate(first, last)
    name = f"{ult.id}.png"
    logo.save(name)
    try:
        await ult.client.send_message(
            ult.chat_id, file=name, reply_to=ult.reply_to_msg_id or ult.id
        )
    finally:
        try:
            os.remove(name)
        except OSError:
            pass
    await msg.delete()


Bot = {"gps": "openmap_bot"}


@heartless_cmd(pattern="gps ?(.*)")
async def _map(ult):
    get = ult.pattern_match.group(1)
    if not get:
        return await ult.eor(f"Use this command as `{HNDLR}gps <query>`")
    quer = await ult.client.inline_query(Bot["gps"], get)
    if not quer:
        return await ult.eor("`No results found.`")
    await quer[0].click(
        ult.chat_id, reply_to=ult.reply_to_msg_id, silent=True, hide_via=True
    )
    await ult.delete()
