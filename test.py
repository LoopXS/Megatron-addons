"""
✘ Commands Available -

• `{i}test`
    Test CɪᴘʜᴇʀX Server Speed.
• `{i}test image` / `{i}test file`
    Same, but send the speedtest result image (as photo / as file).
"""

import asyncio
from datetime import datetime

import speedtest

from . import *


def _run_speedtest(share):
    """Blocking speedtest-cli run (takes ~30s) - must run in a thread."""
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download()
    s.upload()
    image = None
    if share:
        try:
            image = s.results.share()
        except Exception as exc:  # share() is optional, keep the numbers
            LOGS.warning(f"speedtest share failed: {exc}")
    return s.results.dict(), image


def _mbit(bits):
    return f"{(bits or 0) / 1_000_000:.2f} Mbit/s"


@ultroid_cmd(pattern=r"test(?:\s+(image|file))?$")
async def _(event):
    input_str = event.pattern_match.group(1)
    as_document = {"image": False, "file": True}.get(input_str)
    xx = await event.eor("`Ⲥⲁⳑⲥυⳑⲁⲧⲓⲛⳋ CɪᴘʜᴇʀX Ⲋⲉʀⳳⲉʀ Ⲋⲣⲉⲉⲇ...`")
    start = datetime.now()
    try:
        response, speedtest_image = await asyncio.to_thread(
            _run_speedtest, as_document is not None
        )
    except Exception as exc:  # speedtest.SpeedtestException and network errors
        LOGS.warning(f"speedtest failed: {exc}")
        return await xx.edit(f"**Speed Test failed:** `{exc}`")
    ms = (datetime.now() - start).seconds
    client_infos = response.get("client") or {}
    if as_document is not None and speedtest_image:
        await event.client.send_file(
            event.chat_id,
            speedtest_image,
            caption=f"**Ⲋⲣⲉⲉⲇ Ⲧⲉⲋⲧ** Ⲥⲟⲙⲣⳑⲉⲧⲉⲇ ⲓⲛ {ms} Ⲋⲉⲥⲟⲛⲇⲋ",
            force_document=as_document,
            reply_to=event.reply_to_msg_id or event.id,
            allow_cache=False,
        )
        return await event.delete()
    await xx.edit(
        f"`CɪᴘʜᴇʀX Ⲋⲉʀⳳⲉʀ Ⲥⲁⳑⲥυⳑⲁⲧⲉⲇ Ⲋⲣⲉⲉⲇ Ⲓⲛ {ms} Ⲋⲉⲥ`\n\n"
        f"`Dᴏwnlᴏᴀd: {_mbit(response.get('download'))}`\n"
        f"`Uᴩlᴏᴀd: {_mbit(response.get('upload'))}`\n"
        f"`𝙿𝙸𝙽𝙶: {response.get('ping')} ms`\n"
        f"`Inᴛᴇrnᴇᴛ Sᴇrviᴄᴇ Prᴏvidᴇr: {client_infos.get('isp')}`\n"
        f"`ISP Rᴀᴛing: {client_infos.get('isprating')}`"
    )
