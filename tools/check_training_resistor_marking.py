"""Actual cover print, scoped precision examples and existing 3D controls."""
import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
platform._wmi=None
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from product_training import build_training_html
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
out=ROOT.parent/'dark-ui-test/test-runtime/visual-qa/training-resistor-marking'
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1100})
    if not args.public:
        context.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=None;deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#marking-profile').count()),None)
            if f:break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingResistorMarking!=="undefined"')
        canvas=f.locator('#model-canvas')
        def press(n):n.focus();n.press('Enter')
        def painted(code,under=False):
            canvas.scroll_into_view_if_needed();canvas.focus()
            f.wait_for_function('v=>{const c=document.querySelector("#model-canvas");return c.dataset.resistorMarking===v[0]&&c.dataset.resistorUnderline===String(v[1]);}',arg=[code,under])
            assert canvas.get_attribute('data-marking-faces')==('1' if code else '0')
        for mode in ['exterior','materials']:
            for profile,code in [('three','102'),('four','1001'),('underline','221')]:
                press(f.locator('button[data-course="resistor"]'))
                press(f.locator('#model-exterior' if mode=='exterior' else '#show-cross-section'))
                f.locator('#marking-profile').select_option(profile)
                painted(code,profile=='underline')
                assert (f.evaluate('TrainingLesson.current().params.r')==220)==(profile=='underline')
                assert code in f.locator('#resistor-marking-value').inner_text()
                if profile=='underline':
                    assert '220 Ω' in f.locator('#panel-spec tbody tr:first-child td strong').inner_text()
                    before=canvas.evaluate('c=>c.toDataURL()')
                    f.locator('#marking-profile').select_option('three');painted('221')
                    assert canvas.evaluate('c=>c.toDataURL()')!=before
                    f.locator('#marking-profile').select_option('underline');painted('221',True)
                for width in [1440,900,390]:
                    page.set_viewport_size({'width':width,'height':1100})
                    painted(code,profile=='underline')
                    assert f.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1')
                    f.locator('.model-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{mode}-{profile}-{width}.png'))
                page.set_viewport_size({'width':1440,'height':1100})
                painted(code,profile=='underline')
                before=canvas.evaluate('c=>c.toDataURL()')
                canvas.press('ArrowRight')
                f.wait_for_function('v=>document.querySelector("#model-canvas").toDataURL()!==v',arg=before)
                f.locator('#explode').focus();f.locator('#explode').press('End');painted(code,profile=='underline')
                f.wait_for_function('document.querySelector("#explode-value").value==="100%"')
                f.locator('.model-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{mode}-{profile}-exploded.png'))
        press(f.locator('#resistor-marking .lesson-more>summary'))
        text=f.locator('#resistor-marking').inner_text()
        assert all(word in text for word in ['101＝','R10＝','不是所有1%','2025-04-01','部分0402'])
        for value,code in [('1000','102'),('100','101'),('4.7','4R7'),('0.1','R10')]:
            press(f.locator('[data-marking-example="'+value+'"]'));painted(code)
            assert f.evaluate('TrainingLesson.current().params.r')==float(value)
            assert f.locator('#marking-profile').input_value()=='three'
            f.locator('.model-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-value-{code}.png'))
        f.locator('#marking-profile').select_option('four');painted('R100')
        assert f.evaluate('TrainingLesson.current().params.r')==.1
        f.locator('#marking-profile').select_option('three');painted('R10')
        press(f.locator('#tab-performance'))
        slider=f.locator('input[data-param="r"]')
        slider.evaluate('e=>{e.value="1.1";e.dispatchEvent(new Event("input",{bubbles:true}));}')
        painted('')
        assert '不适用所选印字规则' in f.locator('#resistor-marking-value').inner_text()
        assert f.evaluate('TrainingResistorMarking.encode(TrainingLesson.current().params.r)') is None
        for course in ['capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'));painted('')
            assert not f.locator('#resistor-marking').is_visible()
        press(f.locator('button[data-course="resistor"]'));painted('102')
        assert f.locator('#marking-profile').input_value()=='three'
        assert f.locator('#cross-section-card,#material-leaders').count()==0
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'modes':2,'profiles':3,'exact_r_examples':4,'rotation_and_explosion':True,'widths':[1440,900,390],'browser_errors':errors}),flush=True)
    except Exception:
        print(json.dumps({'errors':errors,'state':f.evaluate('({lesson:TrainingLesson.current(),canvas:{...document.querySelector("#model-canvas").dataset},profile:document.querySelector("#marking-profile").value,readout:document.querySelector("#resistor-marking-value").textContent,rect:document.querySelector("#model-canvas").getBoundingClientRect().toJSON()})') if f else None}),flush=True)
        raise
    finally:context.close();browser.close()
