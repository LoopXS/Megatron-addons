from bs4 import BeautifulSoup as bs
from telethon.tl.custom import Button
from telethon.tl.types import InputWebDocument as wb

from .. import InlinePlugin, LOGS, TTLCache, async_searcher, in_pattern, url_quote

_OMG = TTLCache(maxsize=50, ttl=1800)


@in_pattern("omgu", owner=True)
async def omgubuntu(ult):
    parts = ult.text.split(maxsplit=1)
    if len(parts) < 2:
        return await ult.answer(
            [], switch_pm="Enter Query to search...", switch_pm_param="start"
        )
    match = parts[1].lower()
    if cached := _OMG.get(match):
        return await ult.answer(
            cached, switch_pm="OMG Ubuntu Search :]", switch_pm_param="start"
        )
    try:
        get_ = await async_searcher(
            "https://www.omgubuntu.co.uk/?s=" + url_quote(match), re_content=True
        )
    except Exception as er:
        LOGS.warning(f"OMG Ubuntu request failed: {er}")
        get_ = None
    res = []
    if get_:
        soup = bs(get_, "html.parser", from_encoding="utf-8")
        for cont in soup.find_all("div", "sbs-layout__item"):
            try:
                img = cont.find("div", "sbs-layout__image")
                url = img.find("a")["href"]
                src = img.find("img")["src"]
                con = cont.find("div", "sbs-layout__content")
                title = con.find("a", "layout__title-link").text.strip()
                desc = con.find("p", "layout__description").text.strip()
            except (AttributeError, KeyError, TypeError):
                continue  # markup changed / partial item: skip it
            thumb = wb(src, 0, "image/jpeg", [])
            res.append(
                await ult.builder.article(
                    title=title,
                    type="photo",
                    description=desc,
                    url=url,
                    text=f"[{title}]({url})\n\n{desc}",
                    buttons=Button.switch_inline(
                        "Search Again", query=ult.text, same_peer=True
                    ),
                    include_media=True,
                    content=thumb,
                    thumb=thumb,
                )
            )
    if res:
        _OMG.set(match, res)
    await ult.answer(
        res,
        switch_pm=f"Showing {len(res)} results!" if res else "No Results Found :[",
        switch_pm_param="start",
    )


InlinePlugin.update({"OᴍɢUʙᴜɴᴛᴜ": "omgu cutefish"})
