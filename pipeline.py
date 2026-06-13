import json
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

import modal
from youtube_transcript_api import YouTubeTranscriptApi

from database import recipe_exists, save_recipe


MODAL_APP_NAME = "recipe-saver"


def get_modal_functions():
    extract_recipe = modal.Function.from_name(MODAL_APP_NAME, "extract_recipe")
    return extract_recipe


def get_youtube_video_id(youtube_url):
    parsed_url = urlparse(youtube_url)
    host = parsed_url.netloc.removeprefix("www.")

    if host == "youtu.be":
        video_id = parsed_url.path.strip("/").split("/")[0]
    elif parsed_url.path == "/watch":
        video_id = parse_qs(parsed_url.query).get("v", [""])[0]
    elif parsed_url.path.startswith(("/shorts/", "/embed/")):
        video_id = parsed_url.path.strip("/").split("/")[1]
    else:
        video_id = ""

    if not video_id:
        raise ValueError("Could not determine the YouTube video id from the URL.")

    return video_id


def get_video_title(youtube_url):
    query = urlencode({"url": youtube_url, "format": "json"})
    oembed_url = f"https://www.youtube.com/oembed?{query}"

    try:
        with urlopen(oembed_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return "Untitled recipe"

    return data.get("title") or "Untitled recipe"


def fetch_transcript(video_id):
    transcript_api = YouTubeTranscriptApi()

    if hasattr(transcript_api, "fetch"):
        transcript = transcript_api.fetch(video_id)
        snippets = transcript.to_raw_data()
    else:
        snippets = YouTubeTranscriptApi.get_transcript(video_id)

    return " ".join(snippet["text"] for snippet in snippets)


def run_pipeline(youtube_url):
    if recipe_exists(youtube_url):
        raise ValueError("This recipe is already saved.")

    video_id = get_youtube_video_id(youtube_url)
    title = get_video_title(youtube_url)
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    transcript = fetch_transcript(video_id)
    extract_recipe = get_modal_functions()
    recipe = extract_recipe.remote(transcript)
    ingredients = recipe["ingredients"]
    steps = recipe["steps"]

    save_recipe(title, ingredients, steps, youtube_url, thumbnail_url)

    return {
        "ingredients": ingredients,
        "steps": steps,
        "title": title,
        "thumbnail_url": thumbnail_url,
    }
