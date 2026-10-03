"""
✘ Commands Available -

• `{i}ocr <language code>` (reply to a photo)
    Text recognition service (ocr.space). Language code is optional,
    3 letters, e.g. `eng`, `fre`, `ara`.

Needs an API key: `{i}setdb OCR_API <your-api-key>` (free at ocr.space).
"""

import os
import re

import aiohttp

from . import *

TE = f"API not found, Please get it from ocr.space and set\n\ncommand `{HNDLR}setdb OCR_API your-api-key`"
_LANG_RE = re.compile(r"^[a-zA-Z]{3}(-[a-zA-Z]{2,4})?$")


@ultroid_cmd(pattern=r"ocr(?:\s+(\S+))?$")
async def ocrify(ult):
    if not ult.is_reply:
        return await eod(ult, "`Reply to Photo...`")
    api_key = udB.get_key("OCR_API")
    if not api_key:
        return await eod(ult, TE, time=15)
    lang = ult.pattern_match.group(1)
    if lang and not _LANG_RE.match(lang):
        return await eod(ult, "`Invalid language code, use e.g. eng, fre, ara`")
    repm = await ult.get_reply_message()
    is_image = repm.photo or (
        repm.document and (repm.document.mime_type or "").startswith("image/")
    )
    if not is_image:
        return await eod(ult, "`Not a Photo..`")
    msg = await ult.eor(proc_text())
    dl = None
    try:
        dl = await repm.download_media(f"downloads/ocr_{ult.id}")
        form = aiohttp.FormData()
        form.add_field("apikey", api_key)
        if lang:
            form.add_field("language", lang)
        with open(dl, "rb") as fh:
            form.add_field("file", fh.read(), filename=os.path.basename(dl))
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                async with session.post(
                    "https://api.ocr.space/parse/image", data=form
                ) as resp:
                    data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as er:
            LOGS.warning(f"ocr.space request failed: {er}")
            return await msg.edit("`OCR service is unreachable, try again later.`")
        if not isinstance(data, dict) or data.get("IsErroredOnProcessing"):
            err = data.get("ErrorMessage") if isinstance(data, dict) else None
            if isinstance(err, list):
                err = ", ".join(err)
            return await msg.edit(f"`OCR failed: {err or 'unknown error'}`")
        results = data.get("ParsedResults") or []
        text = (results[0].get("ParsedText") or "").strip() if results else ""
        if not text:
            return await msg.edit("`No text found in the image.`")
        await msg.edit(f"**🎉 ⲞⲤR Ⲣⲟʀⲧⲁⳑ\n\nRⲉⲋυⳑⲧⲋ ~ ** `{text[:3800]}`")
    finally:
        if dl and os.path.exists(dl):
            os.remove(dl)
