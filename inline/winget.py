from telethon.tl.custom import Button

from . import InlinePlugin, LOGS, async_searcher, get_string, in_pattern, url_quote


@in_pattern("winget", owner=True)
async def search_winget(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        return await event.answer(
            [], switch_pm=get_string("instu_3"), switch_pm_param="start"
        )
    query = parts[1]
    url = (
        "https://api.winget.run/v2/packages?ensureContains=true&partialMatch=true"
        f"&take=20&query={url_quote(query)}"
    )
    try:
        ct = await async_searcher(url, re_json=True)
    except Exception as er:
        LOGS.warning(f"winget.run request failed: {er}")
        ct = None
    packages = ct.get("Packages") if isinstance(ct, dict) else None
    out = []
    for on in packages or []:
        data = on.get("Latest") or {}
        name = data.get("Name")
        if not name:
            continue
        homep = data.get("Homepage")
        desc = data.get("Description") or ""
        versions = on.get("Versions") or ["?"]
        text = f"> **{name}**\n - {desc}\n\n`winget install {on.get('Id')}`\n\n**Version:** `{versions[0]}`\n"
        text += "**Tags:** " + " ".join(f"#{t}" for t in data.get("Tags") or [])
        if homep:
            text += f"\n\n{homep}"
        out.append(
            await event.builder.article(
                title=name,
                description=desc[:100] or None,
                url=homep,
                text=text[:4000],
                buttons=Button.switch_inline("Search Again", "winget ", same_peer=True),
            )
        )
    await event.answer(
        out,
        switch_pm="|> Winget Results" if out else "No Results Found :(",
        switch_pm_param="start",
        cache_time=300,
    )


InlinePlugin.update({"Search Winget": "winget telegram"})
