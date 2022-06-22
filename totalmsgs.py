"""
✘ Commands Available -
• `{i}totals`
    Returns your total messages count in current chat
    
• `{i}totals [username]/<reply>`
    Returns total messages count of user in current chat
"""

from telethon.utils import get_display_name

from . import *


@ultroid_cmd(pattern="totals ?(.*)")
async def _(e):
    match = e.pattern_match.group(1)
    if match:
        user = match
    elif e.is_reply:
        user = (await e.get_reply_message()).sender_id
    else:
        user = "me"
    a = await e.client.get_messages(e.chat_id, 0, from_user=user)
    user = await e.client.get_entity(user)
    await eor(e, f"Total Msgs `{get_display_name(user)}` Here ~ {a.total}")


