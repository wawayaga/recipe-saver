from pathlib import Path

import yt_dlp

from database import save_recipe
from modal_app import extract_recipe, transcribe


TEMP_AUDIO_PATH = Path("temp_audio.mp3")


def run_pipeline(youtube_url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "temp_audio.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(youtube_url, download=True)

        title = video_info.get("title", "Untitled recipe")
        video_id = video_info["id"]
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        transcript = transcribe.remote(str(TEMP_AUDIO_PATH))
        recipe = extract_recipe.remote(transcript)
        ingredients = recipe["ingredients"]
        steps = recipe["steps"]

        save_recipe(title, ingredients, steps, youtube_url, thumbnail_url)

        if TEMP_AUDIO_PATH.exists():
        TEMP_AUDIO_PATH.unlink()
        
    return {
        "ingredients": ingredients,
        "steps": steps,
        "title": title,
        "thumbnail_url": thumbnail_url,
    }
