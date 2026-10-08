"""
✘ Commands Available -

• `{i}tts` `LanguageCode` (reply to a message)
• `{i}tts` `LanguageCode | text to speak`

• `{i}stt` `[language, default en-IN]` (reply to an audio/voice/video file)
  `Convert Speech to Text...`
  `Note - Sometimes Not 100% Accurate`
"""

import asyncio
import os

import speech_recognition as sr
from gtts import gTTS

from . import *

reco = sr.Recognizer()
MAX_STT_BYTES = 20 * 1024 * 1024
os.makedirs("downloads", exist_ok=True)


async def _ffmpeg(*args):
    """Run ffmpeg without a shell. Returns (returncode, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    return proc.returncode, err.decode(errors="replace").strip()


def _tts_save(text, lang, path):
    gTTS(text, lang=lang).save(path)  # blocking network request


@heartless_cmd(pattern=r"tts(?:\s+([\s\S]*))?$")
async def _(event):
    input_str = (event.pattern_match.group(1) or "").strip()
    if event.is_reply and "|" not in input_str:
        text = (await event.get_reply_message()).message
        lang = input_str or "en"
    elif "|" in input_str:
        lang, text = input_str.split("|", 1)
    else:
        return await eod(
            event, f"`Usage: {HNDLR}tts <lang> | <text>` or reply with `{HNDLR}tts <lang>`"
        )
    text, lang = (text or "").strip(), (lang or "en").strip()
    if not text:
        return await eod(event, "`Nothing to speak.`")
    msg = await event.eor(proc_text())
    raw = f"downloads/tts_{event.id}.mp3"
    opus = f"downloads/tts_{event.id}.opus"
    try:
        try:
            await asyncio.to_thread(_tts_save, text, lang, raw)
        except Exception as er:  # bad language code, network, empty text...
            return await msg.edit(f"`TTS failed: {er}`")
        send_path, voice = raw, False
        try:
            code, err = await _ffmpeg(
                "-i", raw, "-map", "0:a", "-codec:a", "libopus", "-b:a", "100k",
                "-vbr", "on", opus,
            )
            if code == 0 and os.path.exists(opus):
                send_path, voice = opus, True
            else:
                LOGS.warning(f"ffmpeg tts conversion failed: {err}")
        except FileNotFoundError:
            LOGS.warning("ffmpeg not installed, sending the mp3 instead")
        await event.client.send_file(
            event.chat_id,
            send_path,
            voice_note=voice,
            reply_to=event.reply_to_msg_id or event.id,
        )
        await msg.edit(f"Processed {text[:97]} ({lang})")
    finally:
        for path in (raw, opus):
            if os.path.exists(path):
                os.remove(path)


@heartless_cmd(pattern=r"stt(?:\s+(\S+))?$")
async def speec_(e):
    reply = await e.get_reply_message()
    if not (reply and reply.media):
        return await eod(e, "`Reply to Audio-File..`")
    if (reply.file.size or 0) > MAX_STT_BYTES:
        return await eod(e, "`File too big (max 20 MB).`")
    language = e.pattern_match.group(1) or "en-IN"
    msg = await e.eor(proc_text())
    src = wav = None
    try:
        # download to a path we control: the original file name is chosen by
        # the sender and must never reach a shell or a command line
        src = await reply.download_media(f"downloads/stt_{e.id}")
        wav = f"downloads/stt_{e.id}.wav"
        try:
            code, err = await _ffmpeg("-i", src, "-vn", wav)
        except FileNotFoundError:
            return await msg.edit("`ffmpeg is not installed.`")
        if code != 0:
            return await msg.edit("`Could not read this media as audio.`")

        def _recognize():
            with sr.AudioFile(wav) as source:
                audio = reco.record(source)
            return reco.recognize_google(audio, language=language)  # network

        try:
            text = await asyncio.to_thread(_recognize)
        except sr.UnknownValueError:
            return await msg.edit("`Could not understand the audio.`")
        except Exception as er:
            return await msg.edit(f"`{er}`")
        await msg.edit("**Extracted Text :**\n `" + text[:3800] + "`")
    finally:
        for path in (src, wav):
            if path and os.path.exists(path):
                os.remove(path)
