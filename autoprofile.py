"""
✘ Commands Available -

• `{i}autoname`
   `Starts AUTONAME`.

• `{i}stopname`
   `Stops AUTONAME.`

• `{i}autobio`
   `Starts AUTOBIO.`

• `{i}stopbio`
   `Stops AUTOBIO.`
"""

import random

from telethon.tl.functions.account import UpdateProfileRequest

from . import *


@ultroid_cmd(pattern="(auto|stop)name$")
async def autoname_(event):
    match = event.pattern_match.group(1)
    if match == "stop":
        udB.delete("AUTONAME")
        await eor(event, "`AUTONAME has been Stopped !`")
        return
    udB.set("AUTONAME", "True")
    await eod(event, "`Started AUTONAME`")
    while True:
        getn = udB.get("AUTONAME")
        if not getn:
            return
        DM = time.strftime("%d-%m-%y")
        HM = time.strftime("%H:%M")
        name = f"𝒉𝒆𝒂𝒓𝒕𝒍𝒆𝒔𝒔 "
        await event.client(UpdateProfileRequest(first_name=name))
        await asyncio.sleep(1111)


@ultroid_cmd(pattern="(auto|stop)bio$")
async def autoname_(event):
    match = event.pattern_match.group(1)
    if match == "stop":
        udB.delete("AUTOBIO")
        await eor(event, "`AUTOBIO has been Stopped !`")
        return
    udB.set("AUTOBIO", "True")
    await eod(event, "`Started AUTOBIO`")
    BIOS = [
        "Busy Today !",
        "ULTROID USER",
        "Enjoying Life!",
        "Unique as Always!" "Sprinkling a bit of magic",
        "Intelligent !",
    ]
    while True:
        getn = udB.get("AUTOBIO")
        if not getn:
            return
        BIOMSG = "• 𝒖𝒏 𝒂𝒎𝒂𝒏𝒕 𝒔𝒂𝒏𝒔 𝒄𝒐𝒆𝒖𝒓 | 𝒆𝒏𝒔 𝒑𝒂𝒓𝒊𝒔 🎭"
        DM = time.strftime("%d-%m-%y")
        HM = time.strftime("%H:%M")
        name = f"{HM} {BIOMSG}"
        await event.client(
            UpdateProfileRequest(
                about=name,
            )
        )
        await asyncio.sleep(1111)
