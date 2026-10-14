"""Native UI acceptance for the product chapter; only browser-local progress."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[2] / 'ocr-diagnostic-20261014/training-nightlight'
OUT.mkdir(parents=True, exist_ok=True)
prefix = 'formal' if args.public else 'local'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    def run(device, label):
        ctx = browser.new_context(**device, reduced_motion='reduce')
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
        def load():
            page.goto(url, wait_until='domcontentloaded', timeout=90000)
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                f = next((f for f in page.frames if f.locator('#training-app').count()), None)
                if f and f.evaluate('typeof TrainingNightlight !== "undefined"'):
                    return f
                page.wait_for_timeout(250)
            raise AssertionError('Product chapter not available')
        f = load()
        def press(selector):
            n = f.locator(selector)
            assert n.count() == 1 and n.is_visible(), selector
            n.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            if device.get('has_touch'):
                last = None
                for _ in range(12):
                    b = n.bounding_box()
                    if b == last: break
                    last = b
                    page.wait_for_timeout(80)
                n.tap()
            else:
                n.focus()
                n.press('Enter')
            page.wait_for_timeout(140)
        def choice(field, value):
            press(f'[data-nightlight-field="{field}"][data-nightlight-value="{value}"]')
        def state():
            return f.evaluate('TrainingNightlight.current().snapshot()')
        def passed(n):
            assert state()['state']['cleared'] == n, state()
        def capture(n):
            f.locator('.nightlight-stage').screenshot(path=str(OUT / f'{prefix}-{label}-{n}.png'))
            f.locator('.nightlight-head').evaluate('e=>e.scrollIntoView({block:"start"})')
            page.screenshot(path=str(OUT / f'{prefix}-{label}-{n}-viewport.png'))
        press('#nightlight-card>summary')
        f.wait_for_function('document.getElementById("nightlight-canvas").dataset.textureLoaded === "true"')
        assert state()['state']['cleared'] == 0 and not state()['playing']
        assert f.locator('#nightlight-action').is_disabled()
        assert f.locator('[data-nightlight-level="4"]').is_disabled()
        capture('01-start')
        choice('resistance', '330')
        passed(0)
        press('#nightlight-action')
        passed(1)
        phase = state()['scene']['phase']
        page.wait_for_timeout(300)
        assert state()['scene']['phase'] > phase
        if state()['playing'] and f.locator('#nightlight-pause').is_enabled():
            press('#nightlight-pause')
        phase = state()['scene']['phase']
        page.wait_for_timeout(200)
        assert state()['scene']['phase'] == phase
        press('#nightlight-action')
        assert state()['state']['index'] == 1
        choice('resistance', '1000')
        passed(1)
        choice('resistance', '330')
        passed(2)
        capture('02-soft-light')
        press('#nightlight-action')
        choice('diode', 'backward')
        press('#nightlight-action')
        assert state()['result']['unknown']
        passed(2)
        choice('diode', 'forward')
        press('#nightlight-action')
        assert state()['result']['current'] == 0
        passed(2)
        press('#nightlight-action')
        passed(3)
        capture('03-protection')
        # Progress survives a full reload; no API or account storage writes.
        f = load()
        assert '继续制作' in f.locator('#nightlight-count').inner_text()
        press('#nightlight-card>summary')
        passed(3)
        assert state()['state']['index'] == 3
        choice('capacitance', '0.00047')
        press('#nightlight-action')
        if state()['playing'] and f.locator('#nightlight-pause').is_enabled():
            press('#nightlight-pause')
        for _ in range(4):
            if not state()['state']['running']: break
            press('#nightlight-step')
        assert state()['state']['elapsed'] == 2
        passed(3)
        choice('capacitance', '0.01')
        assert state()['state']['power'] and state()['state']['elapsed'] == 0
        press('#nightlight-action')
        assert state()['scene']['flowKind'] == 'capacitor'
        if state()['playing'] and f.locator('#nightlight-pause').is_enabled():
            press('#nightlight-pause')
        for _ in range(4):
            if not state()['state']['running']: break
            press('#nightlight-step')
        passed(4)
        assert not state()['playing'] and state()['result']['current'] >= .004, state()
        contacts = state()['scene']['contacts']
        cap = next(c for c in contacts if c['id'] == 'cap-aluminum')
        positive = next(p for p in cap['pins'] if p['role'] == '+')
        negative = next(p for p in cap['pins'] if p['role'] == '−')
        assert positive['point'][2] < negative['point'][2]
        capture('04-backup')
        press('#nightlight-action')
        assert state()['state']['index'] == 4
        assert f.locator('#nightlight-action').is_disabled()
        choice('mos', 'true')
        press('#nightlight-action')
        assert state()['result']['current'] > 0
        passed(4)
        press('#nightlight-action')
        assert state()['result']['current'] == 0
        passed(4)
        press('#nightlight-action')
        passed(5)
        capture('05-product')
        assert f.locator('.nightlight-trophy').is_visible()
        assert not f.locator('#games-card').evaluate('e=>e.open')
        for c in state()['scene']['contacts']:
            assert all(p['gap'] < 1e-5 for p in c['seating']), c
        page.once('dialog', lambda d: d.dismiss())
        press('#nightlight-restart')
        passed(5)
        f = load()
        press('#nightlight-card>summary')
        passed(5)
        assert state()['state']['mos'] and state()['state']['gate']
        press('#nightlight-action')
        assert state()['result']['current'] == 0
        press('#nightlight-action')
        assert state()['result']['current'] > 0
        dimensions = f.evaluate('({width:innerWidth,content:document.getElementById("training-app").scrollWidth,frame:frameElement.getAttribute("scrolling")})')
        assert dimensions['content'] <= dimensions['width'] + 1, dimensions
        assert dimensions['frame'] == 'no'
        press('#nightlight-practice')
        assert f.locator('#games-card').evaluate('e=>e.open')
        assert not f.locator('#nightlight-card').evaluate('e=>e.open')
        assert f.locator('#playground-action').is_visible()
        assert not errors, errors
        print(json.dumps({'device':label,'status':'passed','chapter':5,'errors':errors,'dimensions':dimensions}, ensure_ascii=False), flush=True)
        ctx.close()
    run({'viewport': {'width':1440,'height':1024}}, 'desktop')
    iphone = {k:v for k,v in p.devices['iPhone 15 Pro'].items() if k != 'default_browser_type'}
    run(iphone, 'iphone-15-pro')
    # Capability fallback, not injected game answers or progression.
    ctx=browser.new_context(viewport={'width':393,'height':659},reduced_motion='reduce')
    ctx.add_init_script('''Object.defineProperty(window,'localStorage',{get(){throw new Error('storage disabled for QA');}});
const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){if(type==='webgl'||type==='webgl2'||type==='experimental-webgl')return null;return get.call(this,type,...args);};''')
    page=ctx.new_page()
    page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/',wait_until='domcontentloaded',timeout=90000)
    deadline=time.monotonic()+150
    while time.monotonic()<deadline:
        f=next((f for f in page.frames if f.locator('#training-app').count()),None)
        if f and f.evaluate('typeof TrainingNightlight!=="undefined"'):break
        page.wait_for_timeout(250)
    assert f
    for selector in ['#nightlight-card>summary','[data-nightlight-field="resistance"][data-nightlight-value="330"]','#nightlight-action']:
        n=f.locator(selector);n.focus();n.press('Enter');page.wait_for_timeout(150)
    fallback=f.evaluate('TrainingNightlight.current().snapshot()')
    assert fallback['state']['cleared']==1 and not fallback['storageOK']
    assert f.locator('.nightlight-fallback').is_visible()
    assert '无法保存' in f.locator('.nightlight-footer').inner_text()
    print(json.dumps({'capability':'no-webgl-and-no-storage','status':'passed'}),flush=True)
    ctx.close()
    browser.close()
