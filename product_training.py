"""Self-contained educational page; no runtime databases or external scripts."""
from pathlib import Path
import base64
import json

WEB_ROOT = Path(__file__).resolve().parent / "training_web"


def build_training_html():
    # Read on each visit so a Cloud hot update cannot retain old lesson assets.
    template = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = "\n".join((WEB_ROOT / name).read_text(encoding="utf-8") for name in (
        "training.css", "training_playground.css", "training_nightlight.css", "repair_shop.css",
    ))
    scripts = "\n".join((WEB_ROOT / name).read_text(encoding="utf-8") for name in (
        "vendor/training-three.min.js", "training_playground_math.js", "training_playground_levels.js", "training_beginner.js",
        "training_math.js", "training_practice.js", "training_circuit_math.js", "training_effects.js",
        "training_material_data.js", "training_material_geometry.js", "training_resistor_marking.js",
        "training_catalog.js", "training_catalog_geometry.js", "training_catalog_labs.js", "training_subtype_game_math.js", "training_game_packages.js", "training_game_progress.js",
        "training_game_feedback.js", "training_game_choices.js", "training_model_labels.js", "training_playground_layout.js", "training.js", "training_tools.js", "training_circuit.js",
        "training_playground_scene.js", "training_playground.js", "training_subtype_game_scene.js", "training_subtype_game.js", "training_playground_entry.js",
        "training_catalog_ui.js", "training_journey.js", "training_nightlight_math.js", "training_nightlight_scene.js", "training_nightlight.js",
        "repair_shop_physics.js", "repair_shop_data.js", "repair_shop_board.js", "repair_shop_mechanics.js", "repair_shop_meter.js", "repair_shop_learning.js", "repair_shop_engine.js", "repair_shop_evidence.js", "repair_shop_coach.js", "repair_shop_enclosure.js", "repair_shop_copper.js", "repair_shop_probes.js", "repair_shop_scene.js", "repair_shop_ui.js", "training_embed.js",
    ))
    assets = {
        "pcb": "data:image/webp;base64," + base64.b64encode((WEB_ROOT / "assets/playground-pcb.webp").read_bytes()).decode("ascii"),
        "icons": {key: (WEB_ROOT / f"assets/playground-{key}.svg").read_text(encoding="utf-8") for key in ("pause", "play", "arrow-path")},
    }
    scripts = "window.TrainingPlaygroundAssets=" + json.dumps(assets, ensure_ascii=False) + ";\n" + scripts
    return template.replace("__TRAINING_CSS__", css).replace("__TRAINING_JS__", scripts.replace("</script", "<\\/script"))


def render_training_page(components):
    # 1050 is an initial paint size only; the trusted lesson expands its own frame.
    components.html(build_training_html(), height=1050, scrolling=False)
