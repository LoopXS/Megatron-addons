import re

from bs4 import BeautifulSoup as bs
from telethon.tl.types import InputWebDocument as wb

from .. import InlinePlugin, LOGS, async_searcher, get_string, in_pattern, url_quote

# Inspired by @FindXDaBot


@in_pattern("xda", owner=True)
async def xda_dev(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        return await event.answer(
            [], switch_pm=get_string("instu_3"), switch_pm_param="start"
        )
    try:
        ct = await async_searcher(
            "https://www.xda-developers.com/search/" + url_quote(parts[1]),
            re_content=True,
        )
    except Exception as er:
        LOGS.warning(f"XDA request failed: {er}")
        ct = None
    out = []
    if ct:
        soup = bs(ct, "html.parser", from_encoding="utf-8")
        posts = soup.find_all("div", re.compile("layout_post_"), id=re.compile("post-"))
        for on in posts:
            try:
                data = on.find_all("img", "xda_image")[0]
                title = data["alt"]
                hre = on.find_all("div", "item_content")[0].find("h4").find("a")["href"]
                desc = on.find_all("div", "item_meta clearfix")[0].text
                thumb = wb(data["src"], 0, "image/jpeg", [])
            except (IndexError, KeyError, AttributeError, TypeError):
                continue  # markup changed / partial post: skip it
            out.append(
                await event.builder.article(
                    title=title,
                    description=desc,
                    url=hre,
                    thumb=thumb,
                    text=f"[{title}]({hre})",
                )
            )
    await event.answer(
        out,
        switch_pm="|| XDA Search Results ||" if out else "No Results Found :(",
        switch_pm_param="start",
        cache_time=300,
    )


InlinePlugin.update({"Search on XDA": "xda telegram"})
