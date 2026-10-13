"""Self-contained educational page; no runtime databases or external scripts."""
from pathlib import Path
import base64
import json

WEB_ROOT = Path(__file__).resolve().parent / "training_web"


def build_training_html():
    # Read on each visit so a Cloud hot update cannot retain old lesson assets.
    template = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "training.css").read_text(encoding="utf-8") + "\n" + (WEB_ROOT / "training_playground.css").read_text(encoding="utf-8")
    scripts = "\n".join((WEB_ROOT / name).read_text(encoding="utf-8") for name in (
        "vendor/training-three.min.js", "training_playground_math.js", "training_playground_levels.js",
        "training_math.js", "training_practice.js", "training_games_math.js", "training_circuit_math.js", "training_effects.js",
        "training_material_data.js", "training_material_geometry.js", "training_resistor_marking.js",
        "training_catalog.js", "training_catalog_geometry.js", "training_catalog_labs.js",
        "training.js", "training_tools.js", "training_circuit.js",
        "training_playground_scene.js", "training_playground.js", "training_games.js",
        "training_catalog_ui.js", "training_embed.js",
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
