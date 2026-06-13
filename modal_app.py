import modal

modal_app = modal.App("recipe-saver")

image = modal.Image.debian_slim().pip_install(
    "torch",
    "transformers",
    "huggingface_hub",
    "yt-dlp"
)