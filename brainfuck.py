# Made by : @DarkPentester
# Made For : https://github.com/LoopXS/Megatron-addons

"""
✘ Commands Available

• `{i}bf <text>` (or reply)
    Text to Brainfuck string generator (characters 0-255 only).

• `{i}rbf <code>` (or reply)
    Brainfuck interpreter. Execution is limited in steps and output size.
"""

import asyncio

from . import *

MAX_STEPS = 2_000_000
MAX_OUTPUT = 4000


class BrainfuckError(Exception):
    pass


def _match_brackets(code):
    """Return {open_index: close_index, close_index: open_index}."""
    pairs, stack = {}, []
    for i, ch in enumerate(code):
        if ch == "[":
            stack.append(i)
        elif ch == "]":
            if not stack:
                raise BrainfuckError(f"Unmatched `]` at position {i}")
            j = stack.pop()
            pairs[i], pairs[j] = j, i
    if stack:
        raise BrainfuckError(f"Unmatched `[` at position {stack[-1]}")
    return pairs


def evaluate(code, max_steps=MAX_STEPS, max_output=MAX_OUTPUT):
    """Run brainfuck ``code`` and return its output.

    Raises ``BrainfuckError`` on malformed code, a pointer moving left of the
    tape, or when the step/output limits are exceeded (e.g. ``+[]``).
    """
    code = "".join(c for c in code if c in "><+-.,[]")
    pairs = _match_brackets(code)
    tape, ptr, ip, steps, out = [0], 0, 0, 0, []
    while ip < len(code):
        steps += 1
        if steps > max_steps:
            raise BrainfuckError(f"Step limit exceeded ({max_steps})")
        ch = code[ip]
        if ch == ">":
            ptr += 1
            if ptr == len(tape):
                tape.append(0)
        elif ch == "<":
            ptr -= 1
            if ptr < 0:
                raise BrainfuckError("Pointer moved left of the tape")
        elif ch == "+":
            tape[ptr] = (tape[ptr] + 1) % 256
        elif ch == "-":
            tape[ptr] = (tape[ptr] - 1) % 256
        elif ch == ".":
            out.append(chr(tape[ptr]))
            if len(out) > max_output:
                raise BrainfuckError(f"Output limit exceeded ({max_output})")
        elif ch == ",":
            tape[ptr] = 0  # no input stream is available
        elif ch == "[":
            if tape[ptr] == 0:
                ip = pairs[ip]
        elif ch == "]":
            if tape[ptr] != 0:
                ip = pairs[ip]
        ip += 1
    return "".join(out)


def bf(text):
    items = []
    for c in text:
        items.append(
            "[-]>[-]<"
            + ("+" * (ord(c) // 10))
            + "[>++++++++++<-]>"
            + ("+" * (ord(c) % 10))
            + ".<"
        )
    return "".join(items)


@heartless_cmd(pattern=r"bf(?:\s+([\s\S]*))?$")
async def _(event):
    text = await arg_or_reply(event)
    if not text:
        return await eod(event, "`Give me some text (or reply to one).`", time=5)
    if any(ord(c) > 255 for c in text):
        return await eod(event, "`Only characters with code 0-255 are supported.`")
    await event.eor(bf(text)[:4096], parse_mode=None)


@heartless_cmd(pattern=r"rbf(?:\s+([\s\S]*))?$")
async def _(event):
    code = await arg_or_reply(event)
    if not code:
        return await eod(event, "`Give me brainfuck code (or reply to it).`", time=5)
    try:
        # CPU-bound pure-Python loop (bounded by MAX_STEPS): keep it off the
        # event loop so the userbot stays responsive.
        result = await asyncio.to_thread(evaluate, code)
    except BrainfuckError as er:
        return await event.eor(f"**Error:** {er}")
    await event.eor(result or "`(no output)`", parse_mode=None if result else "md")
