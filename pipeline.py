import modal

from database import recipe_exists, save_recipe


MODAL_APP_NAME = "recipe-saver"


def get_modal_functions():
    download_audio = modal.Function.from_name(MODAL_APP_NAME, "download_audio")
    transcribe = modal.Function.from_name(MODAL_APP_NAME, "transcribe")
    extract_recipe = modal.Function.from_name(MODAL_APP_NAME, "extract_recipe")
    return download_audio, transcribe, extract_recipe


def run_pipeline(youtube_url):
    if recipe_exists(youtube_url):
        raise ValueError("This recipe is already saved.")

    download_audio, transcribe, extract_recipe = get_modal_functions()
    audio_bytes, title, video_id = download_audio.remote(youtube_url)
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    transcript = transcribe.remote(audio_bytes)
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
