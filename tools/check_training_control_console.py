"""Capture the actual game flow and verify one grouped learner control console."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--before', action='store_true')
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'ocr-diagnostic-20261012/training-control-console'
OUT.mkdir(parents=True, exist_ok=True)
prefix = 'before' if args.before else 'formal' if args.public else 'local'
URL = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    ctx = browser.new_context(viewport={'width':1440,'height':1024}, reduced_motion='reduce')
    page = ctx.new_page(); errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto(URL, wait_until='domcontentloaded', timeout=90000)
        f = None; deadline = time.monotonic()+150
        while time.monotonic()<deadline:
            f = next((x for x in page.frames if x.locator('#training-app').count()), None)
            if f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'): break
            page.wait_for_timeout(250)
        assert f
        def press(selector):
            loc=f.locator(selector)
            # Fresh DOM evidence identifies exactly one live control before acting.
            assert loc.count()==1 and loc.is_visible(), selector
            loc.focus(); loc.press('Enter')
        def select(family,id):
            press('button[data-course="'+family+'"]')
            press('button[data-subtype="'+id+'"]')
        def capture(name):
            f.locator('.play-stage').screenshot(path=str(OUT/f'{prefix}-{name}.png'))
        press('#games-card>summary')
        select('crystal','xtal-active')
        f.locator('#subgame-canvas').scroll_into_view_if_needed()
        f.wait_for_function('Number(document.getElementById("subgame-canvas").dataset.frames)>1')
        if args.before:
            f.locator('.play-workbench').screenshot(path=str(OUT/'before-01-start.png'))
            assert f.locator('#subgame-power').is_visible() and f.locator('#subgame-action').is_visible()
            assert f.locator('#subgame-power').inner_text()==f.locator('#subgame-action').inner_text()
            print(json.dumps({'status':'captured','duplicate_start':True,'spread_fields_actions_controls':True,'errors':errors}),flush=True)
        else:
            chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:d.baseline}))')
            for chapter in chapters:
                select(chapter['family'],chapter['id'])
                console=f.locator('.play-console')
                assert console.count()==1 and console.is_visible(), chapter
                assert f.locator('.play-viewport button').count()==0, chapter
                for selector in ['.play-action-row','.play-controls','.play-tray' if chapter['baseline'] else '.subgame-fields']:
                    assert console.locator(selector).count()==1, (chapter,selector)
                # No duplicate visible controls with the same action label.
                labels=console.locator('button:visible').evaluate_all('ns=>ns.map(n=>n.textContent.trim()).filter(Boolean)')
                assert len(labels)==len(set(labels)), (chapter,labels)
                assert all(button.evaluate('e=>e.getBoundingClientRect().height>=44') for button in console.locator('button:visible').all()), chapter
            select('crystal','xtal-active');capture('01-start')
            assert f.locator('#subgame-action').inner_text()=='开始观察'
            assert f.locator('#subgame-power').is_hidden()
            press('#subgame-help');assert f.locator('.play-mission-hint').is_visible()
            press('#subgame-help');assert f.locator('.play-mission-hint').is_hidden()
            fields=f.evaluate('TrainingSubtypeGameMath.profile("xtal-active").fields')
            # First XO task: normal VDD while OE stays off, as the goal asks.
            press('[data-subgame-field="'+fields[0]['key']+'"][data-subgame-option="1"]')
            capture('02-selected')
            press('#subgame-action')
            assert f.evaluate('TrainingSubtypeGame.current().snapshot().progress.started')
            assert f.locator('#subgame-power').inner_text()=='停止观察'
            capture('03-observing')
            press('#subgame-power');assert not f.evaluate('TrainingSubtypeGame.current().snapshot().progress.started')
            for _ in range(3):press('#subgame-action')
            assert f.evaluate('TrainingSubtypeGame.current().snapshot().progress.cleared')==[0]
            assert f.locator('#subgame-next').is_visible()
            capture('04-completed')
            press('#subgame-power')
            assert f.locator('#subgame-power').is_visible()
            assert f.locator('#subgame-power').inner_text()=='重新观察'
            assert not f.evaluate('TrainingSubtypeGame.current().snapshot().progress.started')
            assert f.evaluate('TrainingSubtypeGame.current().snapshot().progress.cleared')==[0]
            assert f.locator('#subgame-next').is_visible()
            press('#subgame-power')
            assert f.evaluate('TrainingSubtypeGame.current().snapshot().progress.started')
            assert f.evaluate('TrainingSubtypeGame.current().snapshot().progress.cleared')==[0]
            press('#subgame-reset')
            press('[data-subgame-mode="free"]');assert f.locator('#subgame-help').is_hidden()
            for width in [1440,900,390]:
                page.set_viewport_size({'width':width,'height':1024})
                for family,id in [('crystal','xtal-active'),('resistor','res-thick'),('capacitor','cap-tantalum')]:
                    select(family,id)
                    f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
                    assert f.frame_element().get_attribute('scrolling')=='no'
                    bounds=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
                    assert bounds['w']<=bounds['c']+1 and bounds['h']<=bounds['v']+1,bounds
                    assert f.locator('.play-console').evaluate('e=>e.scrollHeight<=e.clientHeight+1&&getComputedStyle(e).overflowY!=="auto"')
                    # All buttons stay within the panel; choices can wrap without
                    # causing horizontal scroll or tiny targets.
                    assert f.locator('.play-console').evaluate('''e=>{const r=e.getBoundingClientRect();return [...e.querySelectorAll('button')].filter(n=>n.getClientRects().length).every(n=>{const b=n.getBoundingClientRect();return b.x>=r.x-1&&b.right<=r.right+1&&b.height>=44;});}''')
                    capture(f'{id}-{width}')
                    f.locator('.play-console').screenshot(path=str(OUT/f'{prefix}-{id}-console-{width}.png'))
            assert not errors, errors
            print(json.dumps({'status':'passed','public':args.public,'chapters':30,'one_console':True,'one_start':True,'hint_start_stop_reset_free':True,'target_size':44,'host_only_scroll':[1440,900,390],'errors':errors}),flush=True)
    finally:
        ctx.close();browser.close()
