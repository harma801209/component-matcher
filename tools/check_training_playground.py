"""Exercise actual WebGL, parameter-to-light coupling and one outer scroll."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi=None
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
parser.add_argument('--url',default='http://127.0.0.1:8534/')
args=parser.parse_args()
OUT=ROOT.parent/'ocr-diagnostic-20261012/training-playground'
OUT.mkdir(parents=True,exist_ok=True)
prefix='formal' if args.public else 'local'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1024})
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('https://fruition-component.pages.dev/?training=1' if args.public else args.url,wait_until='domcontentloaded',timeout=90000)
    deadline=time.monotonic()+150;f=None
    while time.monotonic()<deadline:
        f=next((x for x in page.frames if x.locator('#training-app').count()),None)
        if f and f.evaluate('typeof TrainingPlayground!=="undefined"'):break
        page.wait_for_timeout(300)
    assert f and f.evaluate('typeof TrainingPlayground!=="undefined"'),'Playground not available'
    def press(loc):loc.focus();loc.press('Enter')
    def current():return f.evaluate('TrainingPlayground.current().snapshot()')
    def ready():
        f.locator('#playground-canvas').scroll_into_view_if_needed()
        f.wait_for_function('document.getElementById("playground-canvas").dataset.frames>1')
        assert current()['scene']['renderer']=='WebGL'
    try:
        press(f.locator('#games-card>summary'));ready()
        press(f.locator('[data-play-mode="free"]'))
        canvas=f.locator('#playground-canvas')
        assert canvas.get_attribute('data-marking')=='331'
        assert '9.1 mA' in f.locator('.play-hud').inner_text()
        base=float(canvas.get_attribute('data-brightness'))
        frame1=int(canvas.get_attribute('data-frames'))
        page.wait_for_timeout(200)
        assert int(canvas.get_attribute('data-frames'))>frame1
        press(f.locator('[data-play-choice="100"]'))
        assert current()['result']['current']==.03
        assert float(canvas.get_attribute('data-brightness'))>base
        assert canvas.get_attribute('data-marking')=='101'
        canvas.screenshot(path=str(OUT/f'{prefix}-lamp-high.png'))
        press(f.locator('[data-play-choice="1000"]'))
        assert float(canvas.get_attribute('data-brightness'))<base
        canvas.screenshot(path=str(OUT/f'{prefix}-lamp-low.png'))
        press(f.locator('#playground-pause'))
        assert not current()['playing']
        page.wait_for_timeout(150)
        phase=float(canvas.get_attribute('data-flow-phase'))
        page.wait_for_timeout(180)
        assert float(canvas.get_attribute('data-flow-phase'))==phase
        press(f.locator('[data-play-choice="330"]'))
        assert abs(current()['result']['current']-3/330)<1e-12
        assert float(canvas.get_attribute('data-flow-phase'))==phase
        press(f.locator('#playground-pause'))
        press(f.locator('#playground-speed'))
        assert current()['speed']==.35
        press(f.locator('#playground-power'))
        assert current()['result']['current']==0
        assert canvas.get_attribute('data-flow-count')=='0'
        canvas.screenshot(path=str(OUT/f'{prefix}-lamp-off.png'))
        press(f.locator('#playground-reset'))
        assert current()['params']['power'] and current()['params']['value']==330
        # A real HTML drag uses the same validated input path as click/keyboard.
        f.locator('[data-play-choice="100"]').drag_to(f.locator('.play-viewport'))
        assert current()['params']['value']==100
        press(f.locator('[data-play-choice="330"]'))
        yaw=float(canvas.get_attribute('data-yaw'));canvas.focus();canvas.press('ArrowRight')
        assert float(canvas.get_attribute('data-yaw'))!=yaw
        canvas.press('0')
        f.evaluate('document.activeElement?.blur()')
        f.locator('#playground').screenshot(path=str(OUT/f'{prefix}-resistor.png'))
        for course in ['capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'));ready()
            press(f.locator('[data-play-mode="free"]'))
            assert current()['scene']['course']==course
            if course=='capacitor':
                press(f.locator('#playground-trigger'));page.wait_for_timeout(550)
                r=current()['result'];assert r['storage']<0
                assert abs(r['source']-r['load']-r['storage'])<1e-12
                assert f.locator('#playground-canvas').get_attribute('data-energy-through-load')=='true'
                press(f.locator('#playground-pause'))
                near=current()['params']['near'];v=current()['result']['voltage']
                press(f.locator('#playground-near'))
                assert current()['params']['near']!=near
                assert current()['result']['voltage']==v
                press(f.locator('#playground-pause'));page.wait_for_timeout(6500)
                assert current()['result']['storage']==0
                assert current()['result']['voltage']==3.3
                press(f.locator('#playground-trigger'));page.wait_for_timeout(450)
                press(f.locator('#playground-pause'))
            elif course=='inductor':
                press(f.locator('[data-play-choice="22"]'));page.wait_for_timeout(2500)
                assert current()['result']['unknown']
                assert current()['result']['value']=='不再预测'
                press(f.locator('[data-play-choice="220"]'))
                assert not current()['result']['unknown']
            else:
                assert current()['result']['current']>0
                press(f.locator('[data-play-choice="false"]'))
                assert current()['result']['current']==0
                press(f.locator('#playground-reverse'))
                assert current()['result']['current']<0
                press(f.locator('[data-play-choice="true"]'))
                assert current()['result']['current']==0
                press(f.locator('#playground-reset'))
                assert f.locator('#playground-reverse').get_attribute('aria-pressed')=='false'
                assert f.locator('#playground-reverse').inner_text()=='试着接反电源'
                assert current()['result']['current']>0
            f.evaluate('document.activeElement?.blur()')
            f.locator('#playground').screenshot(path=str(OUT/f'{prefix}-{course}.png'))
        # Mobile/tablet layout and keyboard choices stay reachable without inner scrolling.
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1024})
            press(f.locator('button[data-course="resistor"]'));ready()
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            dims=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
            assert dims['w']<=dims['c']+1 and dims['h']<=dims['v']+1,dims
            assert f.frame_element().get_attribute('scrolling')=='no'
            assert f.evaluate('document.scrollingElement.scrollTop')==0
            f.locator('#playground').screenshot(path=str(OUT/f'{prefix}-width-{width}.png'))
        assert not errors,errors
        # A browser without WebGL must still offer honest, usable numeric feedback.
        fallback=browser.new_context(viewport={'width':900,'height':1000})
        fallback.add_init_script('''const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...rest){return /webgl/i.test(kind)?null:original.call(this,kind,...rest)};''')
        fallback_page=fallback.new_page();fallback_errors=[]
        fallback_page.on('pageerror',lambda e:fallback_errors.append(str(e)))
        try:
            fallback_page.goto('https://fruition-component.pages.dev/?training=1' if args.public else args.url,wait_until='domcontentloaded',timeout=90000)
            until=time.monotonic()+150;ff=None
            while time.monotonic()<until:
                ff=next((x for x in fallback_page.frames if x.locator('#training-app').count()),None)
                if ff and ff.evaluate('typeof TrainingPlayground!=="undefined"'):break
                fallback_page.wait_for_timeout(300)
            assert ff
            ff.locator('#games-card>summary').focus();ff.locator('#games-card>summary').press('Enter')
            ff.locator('[data-play-mode="free"]').focus();ff.locator('[data-play-mode="free"]').press('Enter')
            assert ff.locator('.play-fallback').is_visible()
            ff.locator('[data-play-choice="1000"]').focus();ff.locator('[data-play-choice="1000"]').press('Enter')
            assert '3.0 mA' in ff.locator('.play-hud').inner_text()
            assert '无法显示3D' in ff.locator('#playground-status').inner_text()
            assert not fallback_errors,fallback_errors
        finally:fallback.close()
        print(json.dumps({'status':'passed','public':args.public,'webgl_courses':4,'live_brightness_current':True,'pause_slow_reset':True,'keyboard_drag':True,'capacitor_load_loop':True,'saturation_bound':True,'single_scroll':[1440,900,390],'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'))
        print(json.dumps({'errors':errors}),flush=True)
        raise
    finally:ctx.close();browser.close()
