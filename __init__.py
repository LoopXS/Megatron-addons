"""Shared namespace for Megatron addons.

Every addon does ``from . import *`` and therefore receives everything that
``plugins`` exports, plus the small helpers defined below. Keep this file
free of side effects: it is imported by every addon (and by ``addons.inline``).
"""

import re as _re
from urllib.parse import quote_plus as _quote_plus

from plugins import *

bot = ultroid_bot

# --------------------------------------------------------------------------- #
# Shared helpers (used by several addons)
# --------------------------------------------------------------------------- #

_EMOJI_RE = _re.compile(
    "["
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001faff"
    "\U00002600-\U000027bf"  # misc symbols, dingbats
    "\U00002b00-\U00002bff"
    "\U0000fe00-\U0000fe0f"  # variation selectors
    "\U0000200d"  # zero width joiner
    "]+",
    flags=_re.UNICODE,
)


def deEmojify(text: str) -> str:
    """Strip emoji from ``text`` (used for bots that choke on them)."""
    return _EMOJI_RE.sub("", text or "")


def proc_text() -> str:
    """Localised "Processing..." text.

    ``com_1`` contains a ``{p}`` placeholder (premium-emoji slot) that must be
    removed when the string is used directly with ``get_string``.
    """
    return get_string("com_1").replace("{p}", "").strip()


def url_quote(text: str) -> str:
    """Percent-encode user input before placing it in a URL query/path."""
    return _quote_plus(str(text).strip())


async def arg_or_reply(event, group: int = 1) -> str:
    """Return the command argument, or the text of the replied message.

    ``group`` is the index of the capture group in the command pattern.
    Returns an empty string when neither is available.
    """
    arg = ""
    try:
        arg = (event.pattern_match.group(group) or "").strip()
    except (IndexError, AttributeError):
        pass
    if arg:
        return arg
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.text:
            return reply.text.strip()
    return ""


def text_size(font, text: str, draw=None, multiline: bool = False):
    """``(width, height)`` of ``text`` for any Pillow version.

    Pillow >= 10 removed ``ImageDraw.textsize``, ``multiline_textsize`` and
    ``FreeTypeFont.getsize``; ``textbbox`` is available from Pillow 8.0.
    """
    if draw is None:
        from PIL import Image, ImageDraw

        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    if multiline:
        box = draw.multiline_textbbox((0, 0), text, font=font)
    else:
        box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


class TTLCache:
    """Tiny bounded cache (LRU eviction + optional TTL in seconds).

    Used by inline addons to remember results for callback buttons without
    letting module-level dicts grow forever.
    """

    def __init__(self, maxsize: int = 128, ttl: float = None):
        from collections import OrderedDict

        self._data = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl

    def get(self, key, default=None):
        import time as _time

        item = self._data.get(key)
        if item is None:
            return default
        stamp, value = item
        if self.ttl and _time.monotonic() - stamp > self.ttl:
            self._data.pop(key, None)
            return default
        self._data.move_to_end(key)
        return value

    def set(self, key, value):
        import time as _time

        self._data[key] = (_time.monotonic(), value)
        self._data.move_to_end(key)
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)
        return value

    def __contains__(self, key):
        return self.get(key) is not None
