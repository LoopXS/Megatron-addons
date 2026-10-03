"""
✘ Commands Available -

• `{i}uta <search query>`
    Inline song search and downloader.

• `{i}gglax <query>`
    Create google search sticker with text.

• `{i}stic <emoji>`
    Get random stickers from emoji.

• `{i}frog <text>`
    make text stickers.

• `{i}tweet <text>`
    make twitter posts.

• `{i}quot <text>`
    write quote on animated sticker.
"""

from random import choice

from . import *


async def _send_sticker(event, bot_name, query, caption, *, pick="first", wait=None):
    """Run an inline query on a third-party bot and reply with a result's file.

    ``pick`` is "first", "random" or an int index (clamped to what exists).
    Returns True when something was sent.
    """
    results = await event.client.inline_query(bot_name, query)
    if not results:
        return False
    if pick == "random":
        result = choice(results)
    elif isinstance(pick, int):
        result = results[min(pick, len(results) - 1)]
    else:
        result = results[0]
    await event.reply(caption, file=result.document)
    return True


async def _run(event, bot_name, text_arg, caption, **kw):
    """Shared flow: processing message -> inline query -> cleanup / error."""
    wai = await event.eor(proc_text())
    try:
        sent = await _send_sticker(event, bot_name, text_arg, caption, **kw)
    except Exception as er:
        LOGS.warning(f"{bot_name} inline query failed: {er}")
        return await wai.edit(f"`{er}`")
    if not sent:
        return await wai.edit("`No results found.`")
    await wai.delete()


@ultroid_cmd(pattern=r"tweet(?:\s+([\s\S]*))?$")
async def tweet(e):
    text = await arg_or_reply(e)
    if not text:
        return await eod(e, "`Give me Some Text !`")
    await _run(e, "twitterstatusbot", text, "New Tweet")


@ultroid_cmd(pattern=r"stic(?:\s+([\s\S]*))?$")
async def stic(e):
    # anchored with `$`/`\s+` so that `.sticklet` is NOT swallowed by `.stic`
    text = await arg_or_reply(e)
    if not text:
        return await eod(e, "`Give me Some Emoji !`")
    await _run(e, "sticker", text, "@sticker", pick="random")


@ultroid_cmd(pattern=r"gglax(?:\s+([\s\S]*))?$")
async def gglax_sticker(e):
    text = await arg_or_reply(e)
    if not text:
        return await eod(e, "`Give me Some Text !`")
    await _run(e, "googlaxbot", text, "Googlax")


@ultroid_cmd(pattern=r"frog(?:\s+([\s\S]*))?$")
async def honkasays(e):
    text = deEmojify(await arg_or_reply(e)).strip()
    if not text:
        return await eod(e, "`Give Me Some Text !`")
    if not text.endswith("."):
        text += "."
    # the bot returns variants sized for short/medium/long text
    q = 2 if len(text) <= 9 else 0 if len(text) >= 14 else 1
    await _run(e, "honka_says_bot", text, "Honka", pick=q)


@ultroid_cmd(pattern=r"uta(?:\s+([\s\S]*))?$")
async def nope(doit):
    query = deEmojify(await arg_or_reply(doit)).strip()
    if not query:
        return await eod(
            doit, "`Sir please give some query to search and download it for you..!`"
        )
    wai = await doit.eor(proc_text())
    try:
        results = await doit.client.inline_query("Lybot", query)
        if not results:
            return await wai.edit("`No results found.`")
        await doit.reply(file=results[0].document)
    except Exception as er:
        LOGS.warning(f"Lybot inline query failed: {er}")
        return await wai.edit(f"`{er}`")
    await wai.delete()


@ultroid_cmd(pattern=r"quot(?:\s+([\s\S]*))?$")
async def quote_(event):
    text = await arg_or_reply(event)
    if not text:
        return await eod(event, "`Give some text to make Quote..`")
    wai = await event.eor(proc_text())
    try:
        results = await event.client.inline_query("@QuotAfBot", text)
        if not results:
            return await wai.edit("`No results found.`")
        await event.reply(file=choice(results).document)
    except Exception as er:
        LOGS.warning(f"QuotAfBot inline query failed: {er}")
        return await wai.edit(f"`{er}`")
    await wai.delete()
