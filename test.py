"""
✘ Commands Available -

• `{i}test`
    Test Server Speed.

"""

from datetime import datetime

import speedtest

from . import *


@heartless_cmd(pattern="test ?(.*)")
async def _(event):
    input_str = event.pattern_match.group(1)
    as_document = None
    if input_str == "image":
        as_document = False
    elif input_str == "file":
        as_document = True
    xx = await event.eor("`Ⲥⲁⳑⲥυⳑⲁⲧⲓⲛⳋ Ⲋⲉʀⳳⲉʀ Ⲋⲣⲉⲉⲇ...`")
    start = datetime.now()
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download()
    s.upload()
    end = datetime.now()
    ms = (end - start).seconds
    response = s.results.dict()
    download_speed = response.get("download")
    upload_speed = response.get("upload")
    ping_time = response.get("ping")
    client_infos = response.get("client")
    i_s_p = client_infos.get("isp")
    i_s_p_rating = client_infos.get("isprating")
    reply_msg_id = event.message.id
    if event.reply_to_msg_id:
        reply_msg_id = event.reply_to_msg_id
    try:
        response = s.results.share()
        speedtest_image = response
        if as_document is None:
            await xx.edit(
                """`Ⲥⲁⳑⲥυⳑⲁⲧⲉⲇ Ⲋⲣⲉⲉⲇ Ⲓⲛ {} Ⲋⲉⲥ`

`Dᴏwnlᴏᴀd: {}`
`Uᴩlᴏᴀd: {}`
`𝙿𝙸𝙽𝙶: {}`
`Inᴛᴇrnᴇᴛ Sᴇrviᴄᴇ Prᴏvidᴇr: {}`
`ISP Rᴀᴛing: {}`""".format(
                    ms,
                    humanbytes(download_speed),
                    humanbytes(upload_speed),
                    ping_time,
                    i_s_p,
                    i_s_p_rating,
                )
            )
        else:
            await event.client.send_file(
                event.chat_id,
                speedtest_image,
                caption="**Ⲋⲣⲉⲉⲇ Ⲧⲉⲋⲧ** Ⲥⲟⲙⲣⳑⲉⲧⲉⲇ ⲓⲛ {} Ⲋⲉⲥⲟⲛⲇⲋ".format(ms),
                force_document=as_document,
                reply_to=reply_msg_id,
                allow_cache=False,
            )
            await event.delete()
    except Exception as exc:  # dc
        await xx.edit(
            """**Ⲋⲣⲉⲉⲇ Ⲧⲉⲋⲧ** Ⲥⲟⲙⲣⳑⲉⲧⲉⲇ ⲓⲛ {} Ⲋⲉⲥⲟⲛⲇⲋ
Dᴏwnlᴏᴀd: {}
Uᴩlᴏᴀd: {}
𝙿𝙸𝙽𝙶: {}


__With the Following ERRORs__
{}""".format(
                ms,
                humanbytes(download_speed),
                humanbytes(upload_speed),
                ping_time,
                str(exc),
            )
        )
