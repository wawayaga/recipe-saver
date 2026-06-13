from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

from database import save_recipe
from modal_app import extract_recipe, transcribe


DOWNLOAD_DIR = Path("downloads")


def extract_youtube_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed_url.path.strip("/")

    if parsed_url.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query).get("v", [None])[0]

        path_parts = [part for part in parsed_url.path.split("/") if part]
        if path_parts and path_parts[0] in {"shorts", "embed", "live"}:
            return path_parts[1] if len(path_parts) > 1 else None

    return None


def download_audio(url):
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    audio_path = DOWNLOAD_DIR / f"{info['id']}.mp3"
    return str(audio_path), info


def run_pipeline(youtube_url):
    audio_path, video_info = download_audio(youtube_url)

    video_id = extract_youtube_video_id(youtube_url)
    if not video_id:
        raise ValueError(f"Could not extract YouTube video ID from URL: {youtube_url}")

    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    transcript = transcribe.remote(audio_path)
    recipe = extract_recipe.remote(transcript)
    title = video_info.get("title", "Untitled recipe")

    return save_recipe(
        title,
        recipe["ingredients"],
        recipe["steps"],
        thumbnail_url,
        youtube_url,
    )


def process_youtube_recipe(url):
    return run_pipeline(url)
