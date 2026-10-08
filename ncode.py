"""
✘ Commands Available -

• `{i}ncode` (reply to a file or message)
   Paste the contents of the file/message as a syntax highlighted picture.
"""

import os

from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import Python3Lexer, guess_lexer, guess_lexer_for_filename
from pygments.util import ClassNotFound

from . import check_filename, heartless_cmd

MAX_BYTES = 1024 * 1024  # do not render files larger than 1 MB


def _lexer(code, filename=None):
    try:
        if filename:
            return guess_lexer_for_filename(filename, code)
        return guess_lexer(code)
    except ClassNotFound:
        return Python3Lexer()


@heartless_cmd(pattern="ncode$")
async def coder_print(event):
    if not event.reply_to_msg_id:
        return await event.eor("`Reply to a file or message!`", time=5)
    msg = await event.get_reply_message()
    downloaded = None
    out_path = check_filename("ncode_result.png")
    try:
        if msg.document:
            if (msg.document.size or 0) > MAX_BYTES:
                return await event.eor("`File too big (max 1 MB).`", time=5)
            downloaded = await msg.download_media(check_filename("ncode_input"))
            with open(downloaded, "r", encoding="utf-8", errors="replace") as s:
                code = s.read()
            filename = getattr(msg.file, "name", None)
        else:
            code, filename = msg.text, None
        if not code:
            return await event.eor("`Nothing to render.`", time=5)
        image = highlight(
            code, _lexer(code, filename), ImageFormatter(line_numbers=True)
        )
        with open(out_path, "wb") as f:
            f.write(image)
        await event.client.send_file(
            event.chat_id, out_path, force_document=True, reply_to=event.reply_to_msg_id
        )
        await event.delete()
    finally:
        for path in (downloaded, out_path):
            if path and os.path.exists(path):
                os.remove(path)
