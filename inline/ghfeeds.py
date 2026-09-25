"""GitHub activity search for Megatron inline mode."""
from collections import OrderedDict
from urllib.parse import quote

from telethon import Button
from telethon.tl.types import InputWebDocument

from . import InlinePlugin, LOGS, async_searcher, in_pattern

_CACHE = OrderedDict()
_MAX_CACHE = 32
_AVATAR = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"


def _cache_put(key, value):
    _CACHE.pop(key, None)
    _CACHE[key] = value
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _text(value, default=""):
    if value is None:
        return default
    return str(value).strip() or default


async def _error(event, title, message):
    return await event.answer(
        [await event.builder.article(title=title, text=f"**{title}**\n\n{message}")],
        cache_time=30,
    )


@in_pattern("gh", owner=True)
async def gh_feeds(event):
    """Show recent public GitHub activity for a user.

    A trailing ``.`` is intentionally required so Telegram does not issue a
    request for every partially typed username.
    """
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2:
        return await event.answer([], switch_pm="Enter a GitHub username ending with .", switch_pm_param="start")

    raw = parts[1].strip()
    if not raw.endswith("."):
        return await event.answer([], switch_pm="End the username with . to search.", switch_pm_param="start")

    username = raw[:-1].strip().lstrip("@").lower()
    if not username or len(username) > 39 or not all(c.isalnum() or c in "-" for c in username):
        return await _error(event, "Invalid GitHub Username", "Use a valid GitHub username.")

    if username in _CACHE:
        data = _CACHE[username]
    else:
        try:
            data = await async_searcher(
                f"https://api.github.com/users/{quote(username)}/events/public",
                re_json=True,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "Megatron-Userbot"},
            )
        except Exception as exc:
            LOGS.exception("GitHub feed lookup failed: %s", exc)
            return await _error(event, "GitHub Request Failed", "GitHub could not be reached right now.")
        if not isinstance(data, list):
            message = data.get("message", "GitHub returned an unexpected response.") if isinstance(data, dict) else "Unexpected GitHub response."
            return await _error(event, "GitHub Error", _text(message))
        _cache_put(username, data)

    results = []
    seen = set()
    for item in data[:30]:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        payload = item.get("payload") or {}
        repo = (item.get("repo") or {}).get("name")
        if not repo:
            continue
        repo_url = f"https://github.com/{repo}"
        url = repo_url
        title = f"@{username}"
        text = f"**@{username}** · [{repo}]({repo_url})"
        extra = ""

        if kind == "PushEvent":
            commits = payload.get("commits") or []
            commit = commits[-1] if commits else {}
            commit_url = commit.get("url") or ""
            if commit_url:
                url = "https://github.com/" + commit_url.split("/repos/", 1)[-1]
            title += " pushed"
            text += "\n**Action:** pushed"
            if commit.get("message"):
                extra = f"\n**Commit:** `{_text(commit['message'])[:500]}`"
        elif kind == "IssueCommentEvent":
            comment = payload.get("comment") or {}
            url = comment.get("html_url") or repo_url
            title += " commented"
            text += "\n**Action:** commented on an issue"
        elif kind == "CreateEvent":
            ref_type = _text(payload.get("ref_type"), "repository object")
            title += f" created {ref_type}"
            text += f"\n**Action:** created {ref_type}"
        elif kind == "PullRequestEvent":
            pr = payload.get("pull_request") or {}
            if (pr.get("user") or {}).get("login", "").lower() != username:
                continue
            url = pr.get("html_url") or repo_url
            title += " opened a pull request"
            text += "\n**Action:** opened a pull request"
        elif kind == "ForkEvent":
            fork = payload.get("forkee") or {}
            url = fork.get("html_url") or repo_url
            title += " forked"
            text += "\n**Action:** forked a repository"
        else:
            continue

        text += extra
        key = (url, kind)
        if key in seen:
            continue
        seen.add(key)
        try:
            article = await event.builder.article(
                title=title[:120],
                description=repo,
                text=text[:3900],
                url=url,
                parse_mode="md",
                link_preview=False,
                thumb=InputWebDocument(_text((item.get("actor") or {}).get("avatar_url"), _AVATAR), 0, "image/png", []),
                buttons=[[Button.url("View", url)], [Button.switch_inline("Search again", query=f"gh {username}.", same_peer=True)]],
            )
            results.append(article)
        except Exception as exc:
            LOGS.debug("Skipping GitHub result: %s", exc)

    return await event.answer(
        results,
        cache_time=300,
        switch_pm=f"Showing {len(results)} feed(s)" if results else "Nothing found",
        switch_pm_param="start",
    )


InlinePlugin.update({"GɪᴛHᴜʙ ғᴇᴇᴅs": "gh"})
