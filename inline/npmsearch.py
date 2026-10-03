from telethon.tl.custom import Button

from . import InlinePlugin, LOGS, async_searcher, in_pattern, url_quote


@in_pattern("npm")
async def search_npm(event):
    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        return await event.answer(
            [], switch_pm="Enter query to search", switch_pm_param="start"
        )
    try:
        data = await async_searcher(
            f"https://registry.npmjs.com/-/v1/search?text={url_quote(parts[1])}&size=7",
            re_json=True,
        )
    except Exception as er:
        LOGS.warning(f"npm search failed: {er}")
        data = None
    objects = data.get("objects") if isinstance(data, dict) else None
    res = []
    for obj in objects or []:
        package = obj.get("package") or {}
        title = package.get("name")
        if not title:
            continue
        links = package.get("links") or {}
        url = links.get("npm") or f"https://www.npmjs.com/package/{title}"
        home = links.get("homepage") or url
        keys = package.get("keywords") or []
        text = f"**[{title}]({home})**\n{package.get('description') or ''}\n"
        text += f"**Version:** `{package.get('version', '?')}`\n"
        text += f"**Keywords:** `{','.join(keys)}`"
        res.append(
            await event.builder.article(
                title=title,
                description=package.get("description") or None,
                text=text,
                url=url,
                link_preview=False,
                buttons=[
                    Button.url("View", url),
                    Button.switch_inline("Search again", query=event.text, same_peer=True),
                ],
            )
        )
    await event.answer(
        res,
        switch_pm="NPM Search" if res else "No Results Found :(",
        switch_pm_param="start",
        cache_time=300,
    )


InlinePlugin.update({"Npm Search": "npm"})
