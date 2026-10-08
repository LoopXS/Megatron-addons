"""
✘ Commands Available -
• `{i}lyrics <search query>`
    get lyrics of song.

• `{i}song <search query>`
    send a song from the music archive group.

`{i}lyrics` needs a Google Custom Search key + engine id:
  `{i}setdb LYRICS_API_KEY <key>`
  `{i}setdb LYRICS_ENGINE_ID <engine id>`
"""

from io import BytesIO

from lyrics_extractor import SongLyrics as sl
from lyrics_extractor.lyrics import LyricScraperException as LyError
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputMessagesFilterMusic as filtermus

from . import *

SONG_INVITE = "DdR2SUvJPBouSW4QlbJU4g"
SONG_CHAT = -1001271479322
_joined = False


@heartless_cmd(pattern=r"lyrics(?:\s+([\s\S]*))?$")
async def original(event):
    query = await arg_or_reply(event)
    if not query:
        return await eod(event, "give query to search.")
    key = udB.get_key("LYRICS_API_KEY")
    engine = udB.get_key("LYRICS_ENGINE_ID")
    if not (key and engine):
        return await eod(
            event,
            f"`Set LYRICS_API_KEY and LYRICS_ENGINE_ID first:`\n"
            f"`{HNDLR}setdb LYRICS_API_KEY <key>`\n`{HNDLR}setdb LYRICS_ENGINE_ID <id>`",
            time=15,
        )
    ab = await event.eor("Getting lyrics..")
    try:
        data = await sl(key, engine).get_lyrics(query)
    except LyError:
        return await ab.edit("No Results Found")
    except Exception as er:
        LOGS.warning(f"lyrics lookup failed: {er}")
        return await ab.edit(f"`Lyrics lookup failed: {er}`")
    lyrics = data.get("lyrics") or ""
    if not lyrics:
        return await ab.edit("No Results Found")
    reply_to = event.reply_to_msg_id
    if len(lyrics) > 4000:
        file = BytesIO(lyrics.encode())
        file.name = "lyrics.txt"
        await event.client.send_file(
            event.chat_id, file, caption=data.get("title"), reply_to=reply_to
        )
    else:
        await event.client.send_message(event.chat_id, lyrics, reply_to=reply_to)
    await ab.delete()


@heartless_cmd(pattern=r"song(?:\s+([\s\S]*))?$")
async def _(event):
    global _joined
    args = await arg_or_reply(event)
    if not args:
        return await eod(event, "`Enter song name`")
    client = event.client
    if not _joined:
        try:
            await client(ImportChatInviteRequest(SONG_INVITE))
        except UserAlreadyParticipantError:
            pass
        except Exception:
            return await event.eor(
                f"You need to join [this](https://t.me/joinchat/{SONG_INVITE}) "
                "group for this module to work."
            )
        _joined = True
    okla = await event.eor("processing...")
    try:
        async for song in client.iter_messages(
            SONG_CHAT, search=args, limit=1, filter=filtermus
        ):
            await client.send_file(event.chat_id, song, caption=song.message)
            return await okla.delete()
    except Exception as er:
        LOGS.warning(f"song search failed: {er}")
    await okla.edit("`Song not found.`")
