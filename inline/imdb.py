import hashlib
import json
import re

import requests
from bs4 import BeautifulSoup
from telethon import Button

try:
    from PIL import Image
except ImportError:
    Image = None

from telethon.tl.types import InputWebDocument as wb

from . import LOGS, callback, in_pattern, udB, async_searcher, InlinePlugin

# Define your OMDB API key
OMDB_API_KEY = udB.get_key("OMDB")  #OpenMovies Database get free key from http://www.omdbapi.com/ with 1000 dailiy uses
imdbp = "https://graph.org/file/3b45a9ed4868167954300.jpg"

LIST = {}
hash_to_url = {}


def generate_unique_id(url):
    hashed_id = hashlib.sha256(url.encode()).hexdigest()[:8]
    hash_to_url[hashed_id] = url
    return hashed_id


def get_original_url(hashed_id):
    return hash_to_url.get(hashed_id)


async def get_movie_data(search_term, full_plot=False):
    omdb_api_key = udB.get_key("OMDB")
    if not omdb_api_key:
        LOGS.info("OMDB API key is not set. Use `setdb OMDB <key>`")
        return None
    if "y=" in search_term:
        parts = search_term.split("y=")
        if parts:
            LOGS.info(f"YEAR_prts: {parts}")
            movie_name = parts[0].strip()
            if movie_name:
                year = parts[1].strip() if len(parts) > 1 else None
                if year:
                    SBY = True
                else:
                    SBY = False
            else:
                SBY = False
                movie_name = search_term
        else:
            SBY = False
            movie_name = search_term
    else:
        SBY = False
        movie_name = search_term

    url = f"http://www.omdbapi.com/?apikey={omdb_api_key}&t={movie_name}"

    if SBY is True:
        url += f"&y={year}"
    if full_plot is True:
        url += "&plot=full"

    data = await async_searcher(url, re_json=True)
    if data.get("Response") == "True":
        return data
    else:
        LOGS.info("Error: Unable to fetch movie data")
        return None


def get_trailer(imdbID):
    url = f"https://www.imdb.com/title/{imdbID}/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        script = soup.find("script", type="application/ld+json")
        data = json.loads(script.string)
        trailer_url = data.get("trailer", {}).get("embedUrl")
        if trailer_url:
            LOGS.info(f"Trailer URL: {trailer_url}")
            return f"{trailer_url}"
        else:
            LOGS.info("Could not find trailer link")
            return None

    else:
        LOGS.info("Error: Unable to fetch IMDb page")
        return None


@in_pattern("imdb", owner=False)
async def inline_imdb_command(event):
    try:
        movie_name = (event.text or "").split(" ", maxsplit=1)[1].strip()
        if not movie_name:
            raise IndexError("empty")
        LOGS.info(f"QUERY\n{movie_name}")
    except IndexError:
        indexarticle = event.builder.article(
            title="Sᴇᴀʀᴄʜ Sᴏᴍᴇᴛʜɪɴɢ",
            thumb=wb(imdbp, 0, "image/jpeg", []),
            text="**Iᴍᴅʙ Sᴇᴀʀᴄʜ**\n\nʏᴏᴜ ᴅɪᴅɴ'ᴛ sᴇᴀʀᴄʜ ᴀɴʏᴛʜɪɴɢ",
            buttons=[
                Button.switch_inline(
                    "Sᴇᴀʀᴄʜ Aɢᴀɪɴ",
                    query="imdb ",
                    same_peer=True,
                ),
                Button.switch_inline(
                    "Sᴇᴀʀᴄʜ Bʏ Yᴇᴀʀ",
                    query="imdb IF y= 2024 ",
                    same_peer=True,
                ),
            ],
        )
        await event.answer([indexarticle])
        return

    try:
        movie_data = await get_movie_data(movie_name)
        if movie_data:
            title = movie_data.get("Title", "")
            year = movie_data.get("Year", "")
            rated = movie_data.get("Rated", "")
            released = movie_data.get("Released", "")
            runtime = movie_data.get("Runtime", "")
            ratings = movie_data.get("Ratings", "")
            ratings_str = ", ".join(
                [f"{rating['Source']}: `{rating['Value']}`" for rating in ratings]
            )
            genre = movie_data.get("Genre", "")
            director = movie_data.get("Director", "")
            actors = movie_data.get("Actors", "")
            plot = movie_data.get("Plot", "")
            language = movie_data.get("Language", "")
            country = movie_data.get("Country", "")
            awards = movie_data.get("Awards", "")
            poster_url = movie_data.get("Poster", "")
            imdbRating = movie_data.get("imdbRating", "")
            imdbVotes = movie_data.get("imdbVotes", "")
            BoxOffice = movie_data.get("BoxOffice", "")
            imdbID = movie_data.get("imdbID", "")
            movie_details = (
                f"**Tɪᴛʟᴇ:** {title}\n"
                f"**Yᴇᴀʀ:** `{year}`\n"
                f"**Rᴀᴛᴇᴅ:** `{rated}`\n"
                f"**Rᴇʟᴇᴀsᴇᴅ:** {released}\n"
                f"**Rᴜɴᴛɪᴍᴇ:** `{runtime}`\n"
                f"**Gᴇɴʀᴇ:** {genre}\n"
                f"**Dɪʀᴇᴄᴛᴏʀ:** {director}\n"
                f"**Aᴄᴛᴏʀs:** {actors}\n"
                f"**Pʟᴏᴛ:** {plot}\n"
                f"**Lᴀɴɢᴜᴀɢᴇ:** `{language}`\n"
                f"**Cᴏᴜɴᴛʀʏ:** {country}\n"
                f"**Aᴡᴀʀᴅs:** {awards}\n"
                f"**Rᴀᴛɪɴɢs:** {ratings_str}\n"
                f"**IMDʙ Rᴀᴛɪɴɢ:** `{imdbRating}`\n"
                f"**IMDʙ Lɪɴᴋ:** https://www.imdb.com/title/{imdbID}\n"
                f"**ɪᴍᴅʙVᴏᴛᴇs:** `{imdbVotes}`\n"
                f"**BᴏxOғғɪᴄᴇ:** `{BoxOffice}`"
            )
    except Exception as er:
        LOGS.info(f"Exception: {er}")

    try:
        plot_id = generate_unique_id(movie_details)
    except UnboundLocalError:
        if " y= " in movie_name:
            noresult = movie_name.replace(" y= ", " ")
        elif "y= " in movie_name:
            noresult = movie_name.replace("y= ", "")
        elif "y=" in movie_name:
            noresult = movie_name.replace("y=", "")
        else:
            noresult = movie_name
        
        return await event.answer(
            [
                await event.builder.article(
                    title="Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ",
                    text=f"**IMDʙ**\nTʀʏ ᴀɴᴏᴛʜᴇʀ sᴇᴀʀᴄʜ",
                    thumb=wb(imdbp, 0, "image/jpeg", []),
                    buttons=[
                        Button.switch_inline(
                            "Sᴇᴀʀᴄʜ Aɢᴀɪɴ",
                            query="imdb ",
                            same_peer=True,
                        ),
                            Button.switch_inline(
                            "Sᴇᴀʀᴄʜ Bʏ Yᴇᴀʀ",
                            query=f"imdb {movie_name} y= ",
                            same_peer=True,
                        ),
                    ],
                )
            ],
            switch_pm="No results",
            switch_pm_param="start",
        )
    except Exception as er:
        LOGS.info(f"Exception: {er}")
        return

    if not poster_url or not poster_url.lower().startswith(("http://", "https://")):
        poster_url = imdbp

    txt = f"**Tɪᴛʟᴇ:** {title}\n**Rᴇʟᴇᴀsᴇᴅ:** {released}\n**Cᴏᴜɴᴛʀʏ:** {country}"
    button = [
        [Button.inline("Fᴜʟʟ Dᴇᴛᴀɪʟs", data=f"plot_button:{plot_id}")],
        [Button.switch_inline("Sᴇᴀʀᴄʜ Aɢᴀɪɴ", query="imdb ", same_peer=True)],
    ]

    article = await event.builder.article(
        text=txt,
        title=f"{title}",
        description=f"{released}\nɪᴍᴅʙ: {imdbRating}\nLᴀɴɢᴜᴀɢᴇ: {language}",
        link_preview=False,
        thumb=wb(poster_url, 0, "image/jpeg", []),
        content=wb(poster_url, 0, "image/jpeg", []),
        buttons=button,
    )
    LIST.update(
        {
            plot_id: {
                "text": txt,
                "buttons": button,
                "imdbID": imdbID,
                "movie_name": movie_name,
                "plot": plot,
            }
        }
    )
    await event.answer([article])


@callback(re.compile("plot_button:(.*)"), owner=False)
async def plot_button_clicked(event):
    plot_id = event.data.decode().split(":", 1)[1]
    details = get_original_url(plot_id)
    plot = LIST[plot_id]["plot"]
    imdbID = LIST[plot_id]["imdbID"]
    trailer_url = get_trailer(imdbID)
    btns = [
        [Button.inline("Back", data=f"imdb_back_button:{plot_id}")],
    ]
    if trailer_url:
        btns.insert(0, [Button.url("Trailer", url=trailer_url)])
    if plot.endswith("..."):
        btns.insert(
            0, [Button.inline("Extended Plot", data=f"extended_plot:{plot_id}")]
        )
    await event.edit(details, buttons=btns)


@callback(re.compile("imdb_back_button:(.*)"), owner=False)
async def back_button_clicked(event):
    plot_id = event.data.decode().split(":", 1)[1]
    if not LIST.get(plot_id):
        return await event.answer("Query Expired! Search again 🔍")
    text = LIST[plot_id]["text"]
    buttons = LIST[plot_id]["buttons"]
    await event.edit(text, buttons=buttons)


@callback(re.compile("extended_plot:(.*)"), owner=False)
async def extended_plot_button_clicked(event):
    plot_id = event.data.decode().split(":", 1)[1]
    if not LIST.get(plot_id):
        return await event.answer("Query Expired! Search again 🔍")
    movie_name = LIST[plot_id]["movie_name"]

    ext_plot = await get_movie_data(movie_name, full_plot=True)
    fullplot = ext_plot.get("Plot", "")

    if fullplot:
        extended_plot = f"**Exᴛᴇɴᴅᴇᴅ Pʟᴏᴛ:** {fullplot}"
        btns = [
            [Button.inline("Back", data=f"imdb_back_button:{plot_id}")],
        ]
    await event.edit(extended_plot, buttons=btns)
    
InlinePlugin.update({"Iᴍᴅʙ Sᴇᴀʀᴄʜ": "imdb "})
