"""

✘ Commands Available -

• `{i}wiki <search query>`
    Wikipedia search from telegram.

"""

import asyncio

import wikipedia

from . import *


@heartless_cmd(pattern=r"wiki(?:\s+([\s\S]*))?$")
async def wiki(e):
    srch = await arg_or_reply(e)
    if not srch:
        return await eod(e, "`Give some text to search on wikipedia !`")
    msg = await e.eor(f"`Searching {srch[:100]} on wikipedia..`")
    try:
        # the `wikipedia` package is synchronous (requests) -> run in a thread
        mk = await asyncio.to_thread(wikipedia.summary, srch)
    except wikipedia.DisambiguationError as err:
        options = ", ".join(err.options[:10])
        return await msg.edit(f"**Too many results for** `{srch[:100]}`**:** {options}")
    except wikipedia.PageError:
        return await msg.edit(f"**No page found for** `{srch[:100]}`")
    except Exception as err:
        LOGS.warning(f"wikipedia lookup failed: {err}")
        return await msg.edit(f"**ERROR** : {err}")
    await msg.edit(f"**Search Query :** {srch[:100]}\n\n**Results :** {mk[:3500]}")
