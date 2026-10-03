"""
✘ Commands Available
• `{i}spam <no of msgs> <your msg>`
  `{i}spam <no of msgs>` (reply to a message)
    Spams chat, count 1 to 99.

• `{i}bigspam <no of msgs> <your msg>`
  `{i}bigspam <no of msgs>` (reply to a message)
    Spams chat, count above 99 (max 2000). Full sudo only.

• `{i}tspam <text>`
    Spam chat with the text one character at a time.

For delayed spam use the official `{i}delayspam` command.
"""

import asyncio

from telethon.errors import FloodWaitError

from . import *

MAX_SPAM = 99
MAX_BIGSPAM = 2000


async def _send_many(event, message, count, delay=0.3):
    """Send ``message`` ``count`` times sequentially, obeying FloodWait.

    Messages are sent one after another (not as a burst of concurrent
    requests) and a FloodWait pauses the loop instead of aborting it or
    disconnecting the client.
    """
    for _ in range(count):
        while True:
            try:
                await event.respond(message)
                break
            except FloodWaitError as fw:
                await asyncio.sleep(min(fw.seconds, 300) + 1)
        await asyncio.sleep(delay)


async def _parse_spam(event, cmd):
    """Return ``(count, message)`` or ``None`` after replying with usage."""
    count_s, text = event.pattern_match.group(1), event.pattern_match.group(2)
    if not count_s:
        await eod(event, f"`Usage: {HNDLR}{cmd} <count> <text | reply>`")
        return None
    if event.is_reply and not text:
        message = await event.get_reply_message()
    elif text:
        message = text
    else:
        await eod(event, "`Reply to a Message or Give some Text..`")
        return None
    return int(count_s), message


@ultroid_cmd(pattern=r"tspam(?:\s+([\s\S]*))?$")
async def tmeme(e):
    message = (e.pattern_match.group(1) or "").replace(" ", "")
    if not message:
        return await eod(e, "`Give some text..`")
    await e.delete()
    await _send_many_chars(e, message)


async def _send_many_chars(event, chars):
    for letter in chars:
        while True:
            try:
                await event.respond(letter)
                break
            except FloodWaitError as fw:
                await asyncio.sleep(min(fw.seconds, 300) + 1)
        await asyncio.sleep(0.3)


@ultroid_cmd(pattern=r"spam(?:\s+(\d+))?(?:\s+([\s\S]+))?$")
async def spammer(e):
    parsed = await _parse_spam(e, "spam")
    if not parsed:
        return
    counter, message = parsed
    if counter < 1:
        return await eod(e, "`Count must be at least 1`")
    if counter > MAX_SPAM:
        return await eod(e, "`Use bigspam cmd`")
    await e.delete()
    await _send_many(e, message, counter)


@ultroid_cmd(pattern=r"bigspam(?:\s+(\d+))?(?:\s+([\s\S]+))?$", fullsudo=True)
async def bigspam(e):
    parsed = await _parse_spam(e, "bigspam")
    if not parsed:
        return
    counter, message = parsed
    if not 1 <= counter <= MAX_BIGSPAM:
        return await eod(e, f"`Count must be between 1 and {MAX_BIGSPAM}`")
    await e.delete()
    await _send_many(e, message, counter)
