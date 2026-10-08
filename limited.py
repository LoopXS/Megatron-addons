"""
✘ Commands Available -

• `{i}limited`
   Check you are limited or not !
"""

from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError

from . import heartless_cmd

SPAMBOT_ID = 178220800  # @SpamBot


@heartless_cmd(pattern="limited$")
async def demn(ult):
    chat = "@SpamBot"
    msg = await ult.eor("Checking If You Are Limited...")
    try:
        async with ult.client.conversation(chat, timeout=30) as conv:
            response = conv.wait_event(
                events.NewMessage(incoming=True, from_users=SPAMBOT_ID)
            )
            await conv.send_message("/start")
            response = await response
            await ult.client.send_read_acknowledge(chat)
    except YouBlockedUserError:
        return await msg.edit("Boss! Please Unblock @SpamBot ")
    except TimeoutError:
        return await msg.edit("`@SpamBot did not answer in time, try again later.`")
    await msg.edit(f"~ {response.message.message}")
