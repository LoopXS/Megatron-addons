import re
from html import escape

from telethon.tl.custom import Button
from telethon.tl.types import InputWebDocument

from . import InlinePlugin, LOGS, async_searcher, in_pattern

_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


@in_pattern("gh", owner=True)
async def gh_feeds(ult):
    parts = ult.text.split(maxsplit=1)
    if len(parts) < 2:
        return await ult.answer(
            [],
            switch_pm="Enter Github Username to see feeds...",
            switch_pm_param="start",
        )
    username = parts[1].strip()
    if not username.endswith("."):
        return await ult.answer(
            [], switch_pm="End your query with . to search...", switch_pm_param="start"
        )
    username = username[:-1]
    if not _USER_RE.match(username):
        return await ult.answer(
            [], switch_pm="Invalid GitHub username", switch_pm_param="start"
        )
    try:
        data = await async_searcher(
            f"https://api.github.com/users/{username}/events", re_json=True
        )
    except Exception as er:
        LOGS.warning(f"GitHub feeds request failed: {er}")
        return await ult.answer(
            [], switch_pm="GitHub is unreachable, try later", switch_pm_param="start"
        )
    if not isinstance(data, list):
        # GitHub error object, e.g. {"message": "Not Found", ...} or rate limit
        data = data if isinstance(data, dict) else {}
        msg = "".join(f"{k}: `{v}`\n" for k, v in data.items())
        return await ult.answer(
            [
                await ult.builder.article(
                    title=str(data.get("message", "Error"))[:60],
                    text=msg or "Unexpected response from GitHub",
                    link_preview=False,
                )
            ],
            cache_time=300,
            switch_pm="Error!!!",
            switch_pm_param="start",
        )
    res = []
    res_ids = set()
    uname = escape(username)
    for cont in data[:50]:
        etype = cont.get("type")
        payload = cont.get("payload") or {}
        text = f"<b><a href='https://github.com/{uname}'>@{uname}</a></b>"
        title = f"@{username}"
        extra = None
        if etype == "PushEvent":
            text += " pushed in"
            title += " pushed in"
            commits = payload.get("commits") or []
            repo_name = cont["repo"]["name"]
            url = f"https://github.com/{repo_name}"
            if commits:
                url = "https://github.com/" + commits[-1]["url"].split("/repos/")[-1]
                extra = f"\n-> <b>message:</b> <code>{escape(commits[-1]['message'])}</code>"
        elif etype == "IssueCommentEvent":
            title += " commented at"
            text += " commented at"
            url = payload["comment"]["html_url"]
        elif etype == "CreateEvent":
            title += " created"
            text += " created"
            url = "https://github.com/" + cont["repo"]["name"]
        elif etype == "PullRequestEvent":
            pr = payload.get("pull_request") or {}
            if (pr.get("user") or {}).get("login", "").lower() != username.lower():
                continue
            url = pr["html_url"]
            text += " created a pull request in"
            title += " created a pull request in"
        elif etype == "ForkEvent":
            text += " forked"
            title += " forked"
            url = payload["forkee"]["html_url"]
        else:
            continue
        repo = cont["repo"]["name"]
        repo_url = f"https://github.com/{repo}"
        title += f" {repo}"
        text += f" <b><a href='{escape(repo_url)}'>{escape(repo)}</a></b>"
        if extra:
            text += extra
        thumb = InputWebDocument(cont["actor"]["avatar_url"], 0, "image/jpeg", [])
        article = await ult.builder.article(
            title=title,
            text=text,
            url=repo_url,
            parse_mode="html",
            link_preview=False,
            thumb=thumb,
            buttons=[
                Button.url("View", url),
                Button.switch_inline("Search again", query=ult.text, same_peer=True),
            ],
        )
        if article.id not in res_ids:
            res_ids.add(article.id)
            res.append(article)
    msg = f"Showing {len(res)} feeds!" if res else "Nothing Found"
    await ult.answer(res, cache_time=300, switch_pm=msg, switch_pm_param="start")


InlinePlugin.update({"GɪᴛHᴜʙ ғᴇᴇᴅs": "gh"})
