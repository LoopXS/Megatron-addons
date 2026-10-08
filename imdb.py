"""
Search movie details from IMDB

✘ Commands Available
• `{i}imdb <title>`
    Movie/series details. Add a year with `y=`: `{i}imdb Inception y= 2010`.
    Works inline too: `@<assistant> imdb <title>`.
    Uses the OMDB key (`{i}setdb OMDB <key>`); without a key it falls back to @imdb.
"""

from . import *


@heartless_cmd(pattern=r"imdb(?:\s+([\s\S]*))?$")
async def imdb(e):
    movie_name = await arg_or_reply(e)
    if not movie_name:
        return await eod(e, "`Provide a movie name too`")
    m = await e.eor(get_string("com_2").replace("{p}", "").strip())
    # Prefer our own inline plugin (inline/imdb.py); fall back to @imdb when
    # no OMDB key has been configured.
    bot_name = asst.me.username if udB.get_key("OMDB") else "imdb"
    try:
        results = await e.client.inline_query(bot_name, f"imdb {movie_name}" if bot_name != "imdb" else movie_name)
        if not results:
            return await m.edit("`No Results Found...`")
        await results[0].click(e.chat_id, reply_to=e.reply_to_msg_id)
        await m.delete()
    except Exception as er:
        LOGS.exception(er)
        await m.edit(f"`{er}`")
