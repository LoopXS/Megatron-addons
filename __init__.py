from plugins import *

bot = heartless_bot

# Inline menu entries for addon-provided patterns (merged at runtime with Megatron).
InlinePlugin.update(
    {
        "GɪᴛHᴜʙ": "gh ToxygenX",
        "ᴘʏᴘɪ sᴇᴀʀᴄʜ": "pypi requests",
        "Iᴍᴅʙ Sᴇᴀʀᴄʜ": "imdb inception",
        "Sᴇᴀʀᴄʜ Wɪɴɢᴇᴛ": "winget telegram",
    }
)
