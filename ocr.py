"""
✘ Commands Available -

• `{i}ocr <language code><reply to a photo>`
    text recognition service.

• `{i}ocr fas<reply to a photo/PDF>`
    local Persian OCR using Tesseract.

• reply to a PDF and run `{i}ocr` to extract Persian text locally.
"""

import asyncio
import concurrent.futures
import os
import subprocess
import tempfile
from pathlib import Path

import requests

from . import *

TE = (
    "API not found. Get one from ocr.space and set "
    f"`{HNDLR}setdb OCR_API your-api-key`, or use `.ocr fas` for local OCR."
)

_LANG_ALIASES = {
    "fa": "fas",
    "fas": "fas",
    "fa_ir": "fas",
    "fa-ir": "fas",
    "farsi": "fas",
    "persian": "fas",
}


def _local_lang(raw: str) -> str:
    key = (raw or "").strip().lower()
    if not key or key == "pdf":
        return "fas"
    return _LANG_ALIASES.get(key, key)


def _ocr_one_image(image_path, page_number, lang: str) -> dict:
    try:
        from PIL import Image, ImageEnhance
        import pytesseract

        image = Image.open(image_path)
        gray = image.convert("L")
        enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
        final_image = ImageEnhance.Sharpness(enhanced).enhance(1.3)
        text = pytesseract.image_to_string(
            final_image, lang=lang, config="--psm 3 --oem 3"
        ).strip()
        try:
            image.close()
        except Exception:
            pass
        return {
            "page_num": page_number,
            "text_content": text,
            "character_count": len(text),
            "is_successful": True,
        }
    except Exception as error:
        return {
            "page_num": page_number,
            "text_content": f"خطا در صفحه {page_number}: {error}",
            "character_count": 0,
            "is_successful": False,
        }


def _pdf_page_count(pdf_path: str) -> int:
    try:
        proc = subprocess.Popen(
            ["pdfinfo", pdf_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        output, _ = proc.communicate()
        if proc.returncode == 0:
            for line in output.splitlines():
                if "Pages:" in line:
                    return int(line.split(":", 1)[1].strip())
    except Exception:
        pass
    return 0


def _local_pdf_ocr(pdf_path: str, lang: str = "fas") -> str:
    from pdf2image import convert_from_path

    temp_dir = tempfile.mkdtemp(prefix="cipherx_ocr_")
    try:
        total_pages = _pdf_page_count(pdf_path)
        if total_pages <= 0:
            # Let pdf2image tell us by converting the first page successfully.
            probe = convert_from_path(pdf_path, first_page=1, last_page=1)
            total_pages = max(1, len(probe))
            del probe

        saved = []
        start = 1
        batch = 8
        while start <= total_pages:
            end = min(total_pages, start + batch - 1)
            images = convert_from_path(
                pdf_path,
                dpi=350,
                first_page=start,
                last_page=end,
                fmt="jpeg",
                thread_count=4,
                use_cropbox=False,
            )
            for index, image in enumerate(images):
                page_num = start + index
                path = os.path.join(temp_dir, f"page_{page_num:04d}.jpg")
                image.save(path, "JPEG", quality=95, optimize=True)
                saved.append((path, page_num))
                del image
            start = end + 1

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(_ocr_one_image, path, page_num, lang)
                for path, page_num in saved
            ]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda x: x["page_num"])
        parts = []
        for result in results:
            parts.append(f"\n--- صفحه {result['page_num']} ---\n")
            if result["is_successful"]:
                parts.append(f"({result['character_count']} کاراکتر)\n")
            parts.append(result["text_content"])
            parts.append("\n")
        return "\n".join(parts).strip()
    finally:
        try:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def _local_image_ocr(image_path: str, lang: str = "fas") -> str:
    result = _ocr_one_image(image_path, 1, lang)
    return result["text_content"]


def _message_file_name(media) -> str:
    doc = getattr(media, "document", None)
    if not doc:
        return ""
    for attr in getattr(doc, "attributes", []) or []:
        name = getattr(attr, "file_name", None)
        if name:
            return name
    return ""


def _is_pdf(media) -> bool:
    doc = getattr(media, "document", None)
    if not doc:
        return False
    mime = (getattr(doc, "mime_type", "") or "").lower()
    name = _message_file_name(media).lower()
    return mime == "application/pdf" or name.endswith(".pdf")


def _is_photo(repm) -> bool:
    media = getattr(repm, "media", None)
    return bool(getattr(repm, "photo", None) or getattr(media, "photo", None))


def _ocr_space_file(file_path: str, api_key: str, language: str = "") -> str:
    with open(file_path, "rb") as f:
        data = {"apikey": api_key, "isOverlayRequired": "false"}
        if language:
            data["language"] = language
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data=data,
            files={"file": f},
            timeout=180,
        )
    response.raise_for_status()
    result = response.json()
    if isinstance(result, str):
        raise RuntimeError(result)
    if result.get("IsErroredOnProcessing"):
        details = result.get("ErrorMessage") or result.get("ErrorDetails") or result
        raise RuntimeError(str(details))
    parsed = result.get("ParsedResults") or []
    if not parsed:
        return ""
    return parsed[0].get("ParsedText", "")


@heartless_cmd(pattern="ocr ?(.*)")
async def ocrify(ult):
    if not ult.is_reply:
        return await ult.eor("`Reply to a Photo or PDF...`")
    msg = await ult.eor("`Processing..`")
    pat = (ult.pattern_match.group(1) or "").strip()
    repm = await ult.get_reply_message()

    pdf = _is_pdf(getattr(repm, "media", None))
    photo = _is_photo(repm)
    lang = _local_lang(pat)
    wants_local = (
        pdf
        or pat.lower() in _LANG_ALIASES
        or pat.lower() in {"pdf", "local", "tesseract"}
        or not udB.get_key("OCR_API")
    )

    if wants_local and (pdf or photo):
        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401
            if pdf:
                from pdf2image import convert_from_path  # noqa: F401
        except Exception as exc:
            return await msg.edit(
                "`Local OCR needs pytesseract, pillow, pdf2image, tesseract and poppler.`"
                f"\n`{exc}`"
            )
        try:
            dl = await repm.download_media()
        except Exception as exc:
            return await msg.edit(f"`Download failed:` `{exc}`")
        try:
            if pdf:
                trt = await asyncio.to_thread(_local_pdf_ocr, dl, lang)
            else:
                trt = await asyncio.to_thread(_local_image_ocr, dl, lang)
        except Exception as exc:
            api = udB.get_key("OCR_API")
            if api and (pdf or photo):
                dl2 = dl
                try:
                    trt = await asyncio.to_thread(
                        _ocr_space_file, dl2, api, "" if lang == "fas" else lang
                    )
                    if trt:
                        return await msg.edit(
                            f"**🎉 ⲞⲤR Ⲣⲟʀⲧⲁⳑ\n\nRⲉⲋυⳑⲧⲋ ~ ** `{trt[:3900]}`"
                        )
                except Exception:
                    pass
            try:
                os.remove(dl)
            except Exception:
                pass
            return await msg.edit(
                "`Local OCR failed.`"
                "\nMake sure tesseract, the `fas` language pack, Pillow, pdf2image and Poppler are installed."
                f"\n`{exc}`"
            )
        finally:
            try:
                os.remove(dl)
            except Exception:
                pass
        if not trt:
            return await msg.edit("`No text extracted.`")
        return await msg.edit(f"**🎉 ⲞⲤR Ⲣⲟʀⲧⲁⳑ\n\n`{trt[:3900]}`")

    if not photo:
        return await msg.edit("`Reply to a photo or PDF...`")

    OAPI = udB.get_key("OCR_API")
    if not OAPI:
        return await msg.edit(TE)
    try:
        dl = await repm.download_media()
    except Exception as exc:
        return await msg.edit(f"`Download failed:` `{exc}`")
    try:
        language = pat
        if not language or language.lower() in {"local", "tesseract", "pdf"}:
            language = ""
        trt = await asyncio.to_thread(_ocr_space_file, dl, OAPI, language)
        if not trt:
            return await msg.edit("`No text extracted.`")
        await msg.edit(f"**🎉 ⲞⲤR Ⲣⲟʀⲧⲁⳑ\n\nRⲉⲋυⳑⲧⲋ ~ ** `{trt[:3900]}`")
    except Exception as exc:
        await msg.edit(f"`OCR failed:` `{exc}`")
    finally:
        try:
            os.remove(dl)
        except Exception:
            pass
