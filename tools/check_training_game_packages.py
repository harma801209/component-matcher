"""Check all 30 actual WebGL game packages, contact vertices and native polarity UI.

No business writes, injected answers or hidden-control clicks. Evidence stays
outside the release tree. --public checks the formal page after deployment.
"""
import argparse
import base64
import html
import json
import platform
import sys
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "ocr-diagnostic-20261014/training-game-model-repair"
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument("--public", action="store_true")
parser.add_argument("--gallery-only", action="store_true")
args = parser.parse_args()
prefix = "formal" if args.public else "local"

def galleries(browser):
    notes = json.loads((OUT / f"{prefix}-observations.json").read_text(encoding="utf-8"))["chapters"]
    sheet = browser.new_page(viewport={"width": 1480, "height": 1000})
    for family in ["resistor", "capacitor", "inductor", "crystal", "mos", "diode", "transistor"]:
        cards = []
        for row in notes:
            if row["family"] == family:
                data = base64.b64encode((OUT / row["file"]).read_bytes()).decode("ascii")
                cards.append('<article><h2>' + html.escape(row["title"] + " · " + row["id"]) + '</h2><img src="data:image/png;base64,' + data + '"></article>')
        sheet.set_content('<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;padding:12px;background:#fff;font:16px Microsoft YaHei,sans-serif}main{display:grid;grid-template-columns:1fr 1fr;gap:12px}article{border:1px solid #cad6e3;border-radius:8px;overflow:hidden}h2{font-size:17px;margin:0;padding:10px;background:#edf3fd}img{display:block;width:100%;height:auto}</style><main>' + ''.join(cards) + '</main>')
        sheet.evaluate('Promise.all([...document.images].map(i=>i.decode()))')
        sheet.screenshot(path=str(OUT / f"{prefix}-gallery-{family}.png"), full_page=True)
    sheet.close()

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    if args.gallery_only:
        galleries(browser)
        browser.close()
        print(json.dumps({"status": "arranged", "unmodified_source_screenshots": 30}), flush=True)
        sys.exit(0)
    page = browser.new_page(viewport={"width": 1440, "height": 1100}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    try:
        page.goto("https://fruition-component.pages.dev/?training=1" if args.public else "http://127.0.0.1:8534/", wait_until="domcontentloaded", timeout=90000)
        deadline = time.monotonic() + 150
        f = None
        while time.monotonic() < deadline:
            f = next((x for x in page.frames if x.locator("#training-app").count()), None)
            if f and f.evaluate("typeof TrainingGamePackages!== 'undefined'"):
                break
            page.wait_for_timeout(300)
        assert f and f.evaluate("typeof TrainingGamePackages!== 'undefined'"), "package revision not loaded"

        def press(selector):
            button = f.locator(selector)
            assert button.count() == 1 and button.is_visible(), selector
            button.focus()
            button.press("Enter")

        def screenshot(target, file):
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            target.scroll_into_view_if_needed()
            previous, stable = None, 0
            for _ in range(35):
                page.wait_for_timeout(100)
                box = target.bounding_box()
                assert box
                if box["y"] < 0 or box["y"] + box["height"] > 1098:
                    target.hover()
                    page.mouse.wheel(0, -100 if box["y"] < 0 else 100)
                    stable = 0
                    continue
                current = tuple(round(box[k], 1) for k in ("x", "y", "width", "height"))
                stable = stable + 1 if current == previous else 0
                previous = current
                if stable >= 3:
                    page.screenshot(path=str(OUT / file), clip=box)
                    return
            raise AssertionError(("unstable/clipped screenshot", box))

        def scene(chapter):
            api = "TrainingPlayground" if chapter["baseline"] else "TrainingSubtypeGame"
            return f.evaluate(api + ".current().snapshot().scene")

        def check_contacts(chapter, canvas):
            value = scene(chapter)
            assert value and value["renderer"] == "WebGL", value
            count = f.evaluate("id=>TrainingGamePackages.profile(id).pins.length", chapter["id"])
            assert len(value["contacts"]) == count and len(value["seating"]) == count, value
            assert max(q["gap"] for q in value["seating"]) < 1e-6, value
            points = {q["number"]: q["point"] for q in value["contacts"]}
            for foot in value["seating"]:
                pin = points[foot["number"]]
                assert abs(pin[0] - foot["center"][0]) < 1e-6 and abs(pin[2] - foot["center"][2]) < 1e-6, (chapter, foot, pin)
            assert value["connections"], value
            for connection in value["connections"]:
                assert all(abs(a - b) < 1e-9 for a, b in zip(connection["pin"], connection["traceStart"])), connection
            assert float(canvas.get_attribute("data-seating-gap")) < 1e-6
            return value

        chapters = f.evaluate("TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,title:d.title,baseline:!!d.baseline}))")
        notes = []
        low_ids = {"mos-n", "mos-dual", "xtal-active", "cap-aluminum", "cap-safety", "ind-common", "dio-rectifier", "dio-led", "res-thick", "cap-mlcc", "ind-wound", "dio-switch"}
        flip_ids = {"dio-rectifier", "dio-led", "cap-tantalum", "dio-switch"}
        for index, chapter in enumerate(chapters, 1):
            id = chapter["id"]
            press('button[data-course="' + chapter["family"] + '"]')
            press('button[data-subtype="' + id + '"]')
            press('[data-learning-target="game"]')
            sel = "#playground-canvas" if chapter["baseline"] else "#subgame-canvas"
            canvas = f.locator(sel)
            assert canvas.is_visible()
            f.evaluate("()=>{const i=new Image();i.src=TrainingPlaygroundAssets.pcb;return i.decode();}")
            frames = int(canvas.get_attribute("data-frames") or 0)
            f.wait_for_function("({sel,frames})=>Number(document.querySelector(sel).dataset.frames)>frames+3", arg={"sel": sel, "frames": frames})
            value = check_contacts(chapter, canvas)
            file = f"{prefix}-{index:02d}-{id}-board.png"
            screenshot(f.locator(".play-viewport"), file)
            note = {**chapter, "file": file, "scene": value}
            if id in low_ids:
                canvas.focus()
                for _ in range(4):
                    canvas.press("ArrowDown")
                screenshot(f.locator(".play-viewport"), f"{prefix}-{id}-low.png")
            if id in flip_ids:
                press('[data-play-mode="free"]' if chapter["baseline"] else '[data-subgame-mode="free"]')
                choose = '[data-play-choice="{}"]' if chapter["baseline"] else '[data-subgame-field="forward"][data-subgame-option="{}"]'
                states = []
                for direction in (["true", "false"] if chapter["baseline"] else ["0", "1"]):
                    press(choose.format(direction))
                    states.append(canvas.get_attribute("data-cathode-side") if id != "cap-tantalum" else canvas.get_attribute("data-positive-side"))
                    check_contacts(chapter, canvas)
                    screenshot(f.locator(".play-viewport"), f"{prefix}-{id}-direction-{direction}.png")
                assert set(states) == {"left", "right"}, (id, states)
                note["polarity_sides"] = states
            notes.append(note)
            print(json.dumps({"checked": index, "id": id, "pins": len(value["contacts"]), "max_vertex_gap": max(q["gap"] for q in value["seating"])}, ensure_ascii=False), flush=True)
        assert len(notes) == 30 and not errors, errors
        (OUT / f"{prefix}-observations.json").write_text(json.dumps({"chapters": notes, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "passed", "public": args.public, "packages": 30, "actual_contact_meshes": sum(len(q["scene"]["seating"]) for q in notes), "low_views": len(low_ids), "polarity_pairs": len(flip_ids), "errors": errors}), flush=True)
    finally:
        browser.close()
