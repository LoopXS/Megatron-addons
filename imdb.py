"""
Search movie details from IMDB

✘ Commands Available
• `{i}imdb <keyword>`
"""

from . import *


@heartless_cmd(pattern="imdb ?(.*)")
async def imdb(e):
    m = await e.eor("`...`")
    movie_name = e.pattern_match.group(1)
    if not movie_name:
        return await eor(m, "`Provide a movie name too`")
    try:
        results = await e.client.inline_query(asst.me.username, f"imdb {movie_name}")
        await results[0].click(e.chat_id)
        await m.delete()
    except IndexError:
        return await eor(m, "No Results Found...")
    except Exception as er:
        return await eor(m, str(er))
