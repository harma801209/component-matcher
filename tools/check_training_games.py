"""Verify the sole game entrance: no obsolete outer tabs or card game."""
import argparse
import json
import platform
import sys
import time
from pathlib import Path
platform._wmi=None
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from product_training import build_training_html
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true');args=parser.parse_args()
OUT=ROOT.parent/'ocr-diagnostic-20261012/training-single-entry';OUT.mkdir(parents=True,exist_ok=True)
prefix='formal' if args.public else 'local'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1000})
    if not args.public:ctx.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def frame():
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            found=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if found and found.evaluate('typeof TrainingPlayground!=="undefined"'):return found
            page.wait_for_timeout(300)
        raise AssertionError('Training not ready')
    def press(selector):
        loc=f.locator(selector);loc.focus();loc.press('Enter')
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=frame();assert f.locator('#games-card').get_attribute('open') is None
        press('#games-card>summary')
        for course in ['resistor','capacitor','inductor','diode']:
            press('button[data-course="'+course+'"]')
            assert f.locator('.game-toolbar,[data-game-mode],.game-deck,#game-restart,#game-progress,#game-feedback').count()==0
            assert '4 关挑战' in f.locator('#games-card>summary').inner_text()
            assert f.locator('[data-play-mode]').count()==2
            assert f.locator('[data-play-mode="challenge"]').get_attribute('aria-pressed')=='true'
            assert f.locator('#playground-mission').is_visible()
            press('[data-play-mode="free"]');assert f.locator('#playground-mission').is_hidden()
            press('[data-play-mode="challenge"]');assert f.locator('#playground-mission').is_visible()
            assert f.evaluate('typeof TrainingGamesMath')=='undefined'
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            f.locator('#game-summary-title').scroll_into_view_if_needed()
            dims=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth})')
            assert dims['w']<=dims['c']+1,dims
            page.screenshot(path=str(OUT/f'{prefix}-width-{width}.png'))
        page.reload(wait_until='domcontentloaded',timeout=90000);f=frame()
        assert f.locator('#games-card').get_attribute('open') is None
        assert f.evaluate('TrainingPlayground.current().snapshot().mode')=='challenge'
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'single_entrance':True,'removed_outer_tabs_and_memory':True,'challenge_free_kept':True,'courses':4,'widths':[1440,900,390],'errors':errors}),flush=True)
    finally:ctx.close();browser.close()
