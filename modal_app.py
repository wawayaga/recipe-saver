import modal

modal_app = modal.App("recipe-saver")

image = modal.Image.debian_slim().pip_install(
    "torch",
    "transformers",
    "huggingface_hub",
    "yt-dlp"
)


@modal_app.function(image=image, gpu="A10G")
def transcribe(audio_path):
    import torch
    from transformers import pipeline

    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3",
        torch_dtype=torch.float16,
        device=0,
    )
    result = pipe(audio_path, return_timestamps=False)
    return result["text"]


@modal_app.function(image=image, gpu="A10G", secrets=[modal.Secret.from_name("huggingface-secret")])
def extract_recipe(transcript):
    import json
    import os
    import re

    import torch
    from transformers import pipeline

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN environment variable is required")

    generator = pipeline(
        "text-generation",
        model="mistralai/Mistral-7B-Instruct-v0.3",
        token=hf_token,
        torch_dtype=torch.float16,
        device=0,
    )

    prompt = (
        "<s>[INST] Extract a recipe from the transcript below. "
        "Return only valid JSON with exactly these keys: "
        '"ingredients" (a list of strings) and "steps" (a list of strings). '
        "Do not include markdown, comments, or any extra text.\n\n"
        f"Transcript:\n{transcript} [/INST]"
    )
    output = generator(
        prompt,
        max_new_tokens=1024,
        do_sample=False,
        temperature=0,
        return_full_text=False,
    )[0]["generated_text"].strip()

    json_match = re.search(r"\{.*\}", output, flags=re.DOTALL)
    if not json_match:
        raise ValueError(f"Model did not return a JSON object: {output}")

    recipe = json.loads(json_match.group(0))
    return {
        "ingredients": [str(item) for item in recipe.get("ingredients", [])],
        "steps": [str(item) for item in recipe.get("steps", [])],
    }
