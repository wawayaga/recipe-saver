from pathlib import Path

import imageio_ffmpeg
import modal
import yt_dlp

from database import recipe_exists, save_recipe


TEMP_AUDIO_PATH = Path("temp_audio.mp3")
MODAL_APP_NAME = "recipe-saver"


def get_modal_functions():
    transcribe = modal.Function.from_name(MODAL_APP_NAME, "transcribe")
    extract_recipe = modal.Function.from_name(MODAL_APP_NAME, "extract_recipe")
    return transcribe, extract_recipe


def run_pipeline(youtube_url):
    if recipe_exists(youtube_url):
        raise ValueError("This recipe is already saved.")

    ydl_opts = {
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(youtube_url, download=True)

        title = video_info.get("title", "Untitled recipe")
        video_id = video_info["id"]
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        transcribe, extract_recipe = get_modal_functions()
        transcript = transcribe.remote(TEMP_AUDIO_PATH.read_bytes())
        recipe = extract_recipe.remote(transcript)
        ingredients = recipe["ingredients"]
        steps = recipe["steps"]

        save_recipe(title, ingredients, steps, youtube_url, thumbnail_url)
    finally:
        if TEMP_AUDIO_PATH.exists():
            TEMP_AUDIO_PATH.unlink()

    return {
        "ingredients": ingredients,
        "steps": steps,
        "title": title,
        "thumbnail_url": thumbnail_url,
    }
