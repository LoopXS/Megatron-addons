"""
✘ Commands Available -

• `{i}ncode <file>`
   Use - Paste the contents of file and send as pic.
"""

import pygments
from pygments.formatters import ImageFormatter
from pygments.lexers import Python3Lexer
from . import heartless_cmd, check_filename


@heartless_cmd(pattern="ncode$")
async def coder_print(event):
    if not event.reply_to_msg_id:
        return await event.eor("`Reply to a file or message!`", time=5)
    msg = await event.get_reply_message()
    if msg.document:
        a = await event.client.download_media(
            await event.get_reply_message(), check_filename("ncode.png")
        )
        with open(a, "r") as s:
            c = s.read()
    else:
        a = None
        c = msg.text
    pygments.highlight(
        c,
        Python3Lexer(),
        ImageFormatter(line_numbers=True),
        check_filename("result.png"),
    )
    res = await event.client.send_message(
        event.chat_id,
        "**Pasting this code on my page...**",
        reply_to=event.reply_to_msg_id,
    )
    await event.client.send_file(
        event.chat_id, "result.png", force_document=True, reply_to=event.reply_to_msg_id
    )
    await res.delete()
    await event.delete()
    if a:
        os.remove(a)
    os.remove("result.png")
