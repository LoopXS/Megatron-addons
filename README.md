# MegatronAddons
Plugins repository for Megatron.

## Layout
- `*.py` – command addons (`@ultroid_cmd`), loaded by Megatron's `load_addons`.
- `inline/*.py` – inline-mode addons (`@in_pattern`), shown in the assistant's inline menu via `InlinePlugin`.
- `__init__.py` – shared namespace + helpers: `arg_or_reply`, `proc_text`, `url_quote`, `deEmojify`, `text_size`, `TTLCache`.

## Config keys (`{i}setdb KEY value`)
| Key | Used by |
|---|---|
| `OMDB` | `imdb` (command + inline) – free key from omdbapi.com |
| `OCR_API` | `ocr` – ocr.space |
| `LYRICS_API_KEY`, `LYRICS_ENGINE_ID` | `lyrics` – Google Custom Search |

System tools: `ffmpeg` (tts/stt), optional `lottie_convert.py` and `opencv-python-headless` (memify on stickers/videos).

# Contributing
Kindly do not steal others works without credits.
