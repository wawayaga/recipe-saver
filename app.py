import html

import gradio as gr

from database import get_all_recipes
from pipeline import run_pipeline


def format_numbered_list(items):
    if not items:
        return ""

    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def add_recipe(youtube_url):
    recipe = run_pipeline(youtube_url)
    ingredients = format_numbered_list(recipe["ingredients"])
    steps = format_numbered_list(recipe["steps"])

    return recipe["title"], recipe["thumbnail_url"], ingredients, steps


def render_recipe_cards():
    recipes = get_all_recipes()
    if not recipes:
        return "<p>No recipes saved yet.</p>"

    cards = []
    for recipe in recipes:
        title = html.escape(recipe.get("title") or "Untitled recipe")
        url = html.escape(recipe.get("url") or "#", quote=True)
        thumbnail_url = html.escape(recipe.get("thumbnail_url") or "", quote=True)
        ingredients = recipe.get("ingredients") or []
        steps = recipe.get("steps") or []

        ingredient_items = "".join(
            f"<li>{html.escape(str(ingredient))}</li>" for ingredient in ingredients
        )
        step_items = "".join(f"<li>{html.escape(str(step))}</li>" for step in steps)

        cards.append(
            f"""
            <article class="recipe-card">
                <img src="{thumbnail_url}" alt="{title}" class="recipe-thumbnail">
                <div class="recipe-content">
                    <h3>{title}</h3>
                    <a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>
                    <div class="recipe-columns">
                        <section>
                            <h4>Ingredients</h4>
                            <ol>{ingredient_items}</ol>
                        </section>
                        <section>
                            <h4>Steps</h4>
                            <ol>{step_items}</ol>
                        </section>
                    </div>
                </div>
            </article>
            """
        )

    return f'<div class="recipe-grid">{"".join(cards)}</div>'


css = """
.recipe-grid {
    display: grid;
    gap: 16px;
}

.recipe-card {
    display: grid;
    grid-template-columns: minmax(180px, 260px) 1fr;
    gap: 16px;
    padding: 14px;
    border: 1px solid #d8dde6;
    border-radius: 8px;
    background: #ffffff;
}

.recipe-thumbnail {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    border-radius: 6px;
    background: #eef1f5;
}

.recipe-content h3 {
    margin: 0 0 6px;
    font-size: 18px;
}

.recipe-content a {
    display: inline-block;
    margin-bottom: 12px;
    overflow-wrap: anywhere;
}

.recipe-columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.recipe-columns h4 {
    margin: 0 0 6px;
    font-size: 14px;
}

.recipe-columns ol {
    margin: 0;
    padding-left: 20px;
}

@media (max-width: 720px) {
    .recipe-card,
    .recipe-columns {
        grid-template-columns: 1fr;
    }
}
"""


with gr.Blocks() as app:
    gr.Markdown("# Recipe Saver")

    with gr.Tab("Add Recipe"):
        youtube_url_input = gr.Textbox(label="YouTube URL")
        submit_button = gr.Button("Submit", variant="primary")

        title_output = gr.Textbox(label="Recipe title")
        thumbnail_output = gr.Image(label="Thumbnail")
        ingredients_output = gr.Textbox(label="Ingredients", lines=8)
        steps_output = gr.Textbox(label="Steps", lines=8)

        submit_button.click(
            fn=add_recipe,
            inputs=youtube_url_input,
            outputs=[
                title_output,
                thumbnail_output,
                ingredients_output,
                steps_output,
            ],
        )

    with gr.Tab("My Recipes"):
        load_recipes_button = gr.Button("Load recipes")
        recipes_output = gr.HTML()

        load_recipes_button.click(
            fn=render_recipe_cards,
            inputs=None,
            outputs=recipes_output,
        )


app.launch(server_port=8100, css=css)
