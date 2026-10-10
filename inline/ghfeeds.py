from telethon.tl.custom import Button
from telethon.tl.types import InputWebDocument
import html

from . import in_pattern, InlinePlugin, async_searcher


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _escape(value):
    """Escape HTML special characters."""
    return html.escape(str(value))


@in_pattern("gh", owner=True)
async def gh_feeds(ult):
    try:
        username = (ult.text or "").split(maxsplit=1)[1].strip()
    except IndexError:
        await ult.answer(
            [],
            switch_pm="Enter Github Username to see profile...",
            switch_pm_param="start",
        )
        return

    username = username.rstrip(".")
    if not username or "/" in username:
        await ult.answer(
            [],
            switch_pm="Enter a valid Github Username",
            switch_pm_param="start",
        )
        return

    data = await async_searcher(
        f"https://api.github.com/users/{username}",
        re_json=True,
    )
    if not isinstance(data, dict) or data.get("message"):
        message = _clean(data.get("message") if isinstance(data, dict) else data)
        return await ult.answer(
            [
                await ult.builder.article(
                    title="GitHub Error",
                    description=message or "User not found",
                    text=f"<b>GitHub Error</b>\n<code>{_escape(message or 'User not found')}</code>",
                    link_preview=False,
                    buttons=[
                        Button.switch_inline(
                            "Search again",
                            query="gh ",
                            same_peer=True,
                        )
                    ],
                )
            ],
            cache_time=300,
            switch_pm="GitHub Error",
            switch_pm_param="start",
        )

    login = _clean(data.get("login")) or username
    name = _clean(data.get("name")) or login
    bio = _clean(data.get("bio"))
    company = _clean(data.get("company"))
    location = _clean(data.get("location"))
    blog = _clean(data.get("blog"))
    twitter = _clean(data.get("twitter_username"))
    profile_url = _clean(data.get("html_url")) or f"https://github.com/{login}"
    avatar_url = _clean(data.get("avatar_url")) or (
        "https://github.com/images/error/octocat_happy.gif"
    )
    public_repos = data.get("public_repos", 0)
    followers = data.get("followers", 0)
    following = data.get("following", 0)
    created_at = _clean(data.get("created_at"))[:10]

    text = (
        f"<b><a href=\"{_escape(profile_url)}\">{_escape(name)}</a></b>\n"
        f"<b>Username:</b> <code>@{_escape(login)}</code>\n"
    )
    if bio:
        text += f"<b>Bio:</b> {_escape(bio)}\n"
    if company:
        text += f"<b>Company:</b> <code>{_escape(company)}</code>\n"
    if location:
        text += f"<b>Location:</b> <code>{_escape(location)}</code>\n"
    if blog:
        blog_url = blog if blog.startswith("http") else f"https://{blog}"
        text += f"<b>Blog:</b> <a href=\"{_escape(blog_url)}\">{_escape(blog)}</a>\n"
    if twitter:
        text += f"<b>Twitter:</b> <code>@{_escape(twitter)}</code>\n"
    text += (
        f"<b>Public repos:</b> <code>{public_repos}</code>\n"
        f"<b>Followers:</b> <code>{followers}</code>\n"
        f"<b>Following:</b> <code>{following}</code>\n"
        f"<b>Joined:</b> <code>{_escape(created_at)}</code>"
    )

    buttons = [
        [Button.url("Vɪᴇᴡ Pʀᴏғɪʟᴇ", url=profile_url)],
        [Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="gh ", same_peer=True)],
    ]
    if blog:
        blog_url = blog if blog.startswith("http") else f"https://{blog}"
        buttons.insert(1, [Button.url("Bʟᴏɢ", url=blog_url)])

    await ult.answer(
        [
            await ult.builder.article(
                title=name,
                description=f"@{login} • {followers} followers",
                text=text,
                url=profile_url,
                parse_mode="html",
                link_preview=True,
                thumb=InputWebDocument(avatar_url, 0, "image/jpeg", []),
                buttons=buttons,
            )
        ],
        cache_time=300,
        switch_pm=f"GitHub: {login}",
        switch_pm_param="start",
    )


InlinePlugin.update({"GɪᴛHᴜʙ": "gh "})
