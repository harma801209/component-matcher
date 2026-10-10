"""Cross-section interaction, source scopes and existing-lesson coexistence."""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from product_training import build_training_html
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
out = ROOT.parent / 'dark-ui-test/test-runtime/visual-qa/training-materials'
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
    if not args.public:
        context.route('http://training.local/**', lambda r:r.fulfill(body=build_training_html(), content_type='text/html'))
    page = context.new_page()
    errors=[]
    page.on('pageerror', lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/', wait_until='domcontentloaded', timeout=90000)
        f=None
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#cross-section-card').count()),None)
            if f:
                break
            page.wait_for_timeout(400)
        assert f is not None, 'Material section did not render'
        f.wait_for_function('typeof TrainingMaterials!=="undefined"')
        def press(n):n.focus();n.press('Enter')
        for course in ['resistor','capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            assert f.evaluate('TrainingMaterials.current().course')==course
            assert f.locator('#cross-section-card').get_attribute('data-course')==course
            data=f.evaluate('TrainingMaterials.lesson(TrainingMaterials.current().course)')
            assert f.locator('#cross-section-layers button').count()==len(data['layers'])
            assert f.locator('#cross-section-drawing svg').get_attribute('role')=='group'
            for part in data['layers']:
                press(f.locator('#cross-section-layers button[data-material="'+part['id']+'"]'))
                assert f.evaluate('TrainingMaterials.current().selected')==part['id']
                assert f.locator('#cross-section-detail h3').inner_text()==part['name']
                assert f.locator('#cross-section-detail details').get_attribute('open') is None
                press(f.locator('#cross-section-detail summary'))
                text=f.locator('#cross-section-detail').inner_text()
                assert part['composition'] in text and part['role'] in text and part['scope'] in text
                assert f.locator('#cross-section-drawing .selected').count()==1
                assert f.locator('#cross-section-layers button[aria-pressed=true]').count()==1
                assert f.locator('#cross-section-detail a').count()==len(part['refs'])
            first=data['layers'][0]['id']
            target=f.locator('#cross-section-drawing [data-material="'+first+'"]')
            target.focus();target.press('Space')
            assert f.evaluate('TrainingMaterials.current().selected')==first
            target=f.locator('#cross-section-drawing [data-material="'+data['layers'][-1]['id']+'"]')
            target.locator('.number').click()
            assert f.evaluate('TrainingMaterials.current().selected')==data['layers'][-1]['id']
            assert not f.evaluate('TrainingMaterials.select("<bad>")')
            press(f.locator('#show-cross-section'))
            assert f.locator('#cross-section-title').evaluate('e=>e===document.activeElement')
            assert f.locator('#cross-section-card').is_visible()
            press(f.locator('#tab-performance'))
            assert f.locator('#metrics').is_visible()
            assert f.locator('#cross-section-card').is_visible()
            press(f.locator('#tab-principle'))
            assert f.locator('#circuit-card').is_visible()
            assert f.locator('#tool-panel-decode').is_visible()
            f.locator('#cross-section-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}.png'))
            disclosure=f.locator('#cross-section-sources').locator('xpath=..')
            if disclosure.get_attribute('open') is None:
                press(disclosure.locator('summary'))
            assert data['scope'] in f.locator('#cross-section-limits').inner_text()
            assert f.locator('#cross-section-sources a').count()==len(data['sources'])
            for link in f.locator('#cross-section-sources a').all():
                assert link.get_attribute('href').startswith('https://')
                assert link.get_attribute('rel')=='noopener noreferrer'
        for width in [900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            for course in ['resistor','capacitor','inductor','diode']:
                press(f.locator('button[data-course="'+course+'"]'))
                f.locator('#cross-section-card').scroll_into_view_if_needed()
                size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
                assert size['scroll']<=size['client']+1,size
                for button in f.locator('#cross-section-layers button').all():
                    assert button.evaluate('e=>e.offsetHeight>=44')
                f.locator('#cross-section-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}-{width}.png'))
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'courses':4,'layers':20,
                          'diagram_keyboard_and_click':True,'sources_and_scopes':True,
                          'widths':[1440,900,390],'browser_errors':errors}),flush=True)
    finally:
        context.close()
        browser.close()
