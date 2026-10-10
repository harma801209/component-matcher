"""Self-contained educational page; no runtime databases or external scripts."""
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parent / "training_web"


def build_training_html():
    # Read on each visit so a Cloud hot update cannot retain old lesson assets.
    template = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "training.css").read_text(encoding="utf-8")
    scripts = "\n".join((WEB_ROOT / name).read_text(encoding="utf-8") for name in (
        "training_math.js", "training_practice.js", "training_circuit_math.js",
        "training.js", "training_tools.js", "training_circuit.js", "training_materials.js",
    ))
    return template.replace("__TRAINING_CSS__", css).replace("__TRAINING_JS__", scripts.replace("</script", "<\\/script"))


def render_training_page(components):
    components.html(build_training_html(), height=1050, scrolling=True)
