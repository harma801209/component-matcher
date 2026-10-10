"""Verify PCB topology/flows, teaching stages, controls and original-tool coexistence."""
import argparse
import platform
import sys
import time
import json
from pathlib import Path
platform._wmi=None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from product_training import build_training_html
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
out=Path(__file__).resolve().parents[2]/'dark-ui-test/test-runtime/visual-qa/training-circuit'
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce')
    if not args.public:context.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=None;deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#circuit-card').count()),None)
            if f:break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingCircuit!=="undefined"')
        def press(loc):loc.focus();loc.press('Enter')
        for course in ['resistor','capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            assert f.evaluate('TrainingCircuit.current().course')==course
            assert f.evaluate('TrainingCircuit.current().step')==0
            assert f.locator('[data-circuit-step]').count()==3
            for s in [1,2,0]:
                press(f.locator('[data-circuit-step="'+str(s)+'"]'))
                assert f.evaluate('TrainingCircuit.current().step')==s
                assert f.locator('#circuit-headline').inner_text()
            press(f.locator('#circuit-next'));assert f.evaluate('TrainingCircuit.current().step')==1
            press(f.locator('#circuit-schematic'));assert f.locator('#circuit-svg').get_attribute('class')=='schematic'
            press(f.locator('#circuit-pcb'));assert f.locator('#circuit-svg').get_attribute('class')=='pcb'
            if course=='resistor':
                assert f.evaluate('TrainingCircuit.current().result.i')>0
                f.locator('#circuit-resistance').select_option('1000')
                assert abs(f.evaluate('TrainingCircuit.current().result.i')-.003)<1e-12
            elif course=='capacitor':
                r=f.evaluate('TrainingCircuit.current().result');assert r['icap']<0
                assert float(f.locator('#flow-cap-up').get_attribute('data-current'))<0
                # No animated path is drawn through the capacitor dielectric gap.
                assert f.locator('#flow-cap-up').get_attribute('d')=='M310 95V150'
                assert f.locator('#flow-cap-down').get_attribute('d')=='M310 170V220'
                press(f.locator('#circuit-remove-cap'))
                assert f.evaluate('TrainingCircuit.current().result.v')<r['v']
                assert f.locator('#flow-cap-up').evaluate('e=>e.style.opacity')=='0'
                press(f.locator('#circuit-remove-cap'))
            elif course=='inductor':
                press(f.locator('[data-circuit-step="2"]'))
                assert f.locator('#flow-supply').evaluate('e=>e.style.opacity')=='0'
                assert f.locator('#flow-freewheel').evaluate('e=>e.style.opacity')=='1'
                assert '续流' in f.locator('#circuit-story').inner_text()
            else:
                press(f.locator('[data-circuit-step="2"]'))
                assert f.evaluate('TrainingCircuit.current().result.reverse')
                assert f.locator('#flow-main').evaluate('e=>e.style.opacity')=='0'
                assert f.locator('#circuit-output-value').text_content()=='负载 0.0 V'
            f.locator('#circuit-card').scroll_into_view_if_needed()
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}.png'),full_page=True)
            # Clicking original tabs must not hide the PCB lesson or practice panel.
            press(f.locator('#tab-principle'))
            assert f.locator('#circuit-card').is_visible()
            assert f.locator('#tool-panel-decode').is_visible()
        press(f.locator('button[data-course="capacitor"]'))
        press(f.locator('#circuit-play'))
        f.locator('#circuit-card').scroll_into_view_if_needed()
        f.wait_for_function('TrainingCircuit.current().step===1',timeout=7000)
        press(f.locator('#circuit-play'))
        state=f.evaluate('TrainingCircuit.current()');assert not state['playing']
        page.wait_for_timeout(300)
        assert f.evaluate('TrainingCircuit.current().u')==state['u']
        press(f.locator('#circuit-play'))
        f.locator('#circuit-card').scroll_into_view_if_needed()
        f.wait_for_function('TrainingCircuit.current().step===2&&!TrainingCircuit.current().playing',timeout=14000)
        assert f.evaluate('TrainingCircuit.current().u')==1
        press(f.locator('#circuit-reset'));assert f.evaluate('TrainingCircuit.current().step')==0
        for width in [900,390]:
            page.set_viewport_size({'width':width,'height':1100})
            f.locator('#circuit-card').scroll_into_view_if_needed()
            size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert size['scroll']<=size['client']+1,size
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{width}.png'),full_page=True)
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'courses':4,'views':2,'stages':3,'play_pause_finish':True,'flow_topology':True,'mobile':True,'errors':errors}),flush=True)
    finally:context.close();browser.close()
