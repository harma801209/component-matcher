"""Same-canvas material mode, labels, camera controls and course coexistence."""
import argparse
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
out=ROOT.parent/'dark-ui-test/test-runtime/visual-qa/training-material-3d'
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000})
    if not args.public:
        context.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=None;deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#model-labels').count()),None)
            if f:break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingMaterials!=="undefined"')
        def press(n):n.focus();n.press('Enter')
        canvas=f.locator('#model-canvas')
        canvas.scroll_into_view_if_needed()
        f.wait_for_function('document.querySelector("canvas").dataset.meshFaces>20')
        assert f.locator('#cross-section-card').get_attribute('open') is None
        for course in ['resistor','capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            press(f.locator('#model-exterior'))
            press(f.locator('#tab-performance'))
            before=f.evaluate('TrainingLesson.current()')
            canvas.scroll_into_view_if_needed();canvas.focus();canvas.press('ArrowRight')
            page.wait_for_timeout(80);yaw=canvas.get_attribute('data-yaw')
            press(f.locator('#show-cross-section'))
            canvas.scroll_into_view_if_needed()
            f.wait_for_function('c=>document.querySelector("canvas").dataset.mode==="materials"&&document.querySelector("canvas").dataset.course===c',arg=course)
            state=f.evaluate('TrainingLesson.current()')
            assert state['params']==before['params'] and state['tab']=='performance'
            assert canvas.get_attribute('data-yaw')==yaw
            assert f.locator('#animate').is_disabled()
            data=f.evaluate('TrainingMaterialData.lesson(TrainingLesson.current().course)')
            assert f.locator('#model-labels button').count()==len(data['layers'])
            for part in data['layers']:
                button=f.locator('[data-model-material="'+part['id']+'"]')
                press(button)
                assert f.evaluate('TrainingLesson.current().part')==part['id']
                assert f.evaluate('TrainingMaterials.current().selected')==part['id']
                assert part['composition'] in f.locator('#part-detail').inner_text()
                assert part['role'] in f.locator('#part-detail').inner_text()
                assert button.get_attribute('aria-pressed')=='true'
            canvas.scroll_into_view_if_needed()
            path=f.locator('#material-leaders path').first.get_attribute('d')
            canvas.focus();canvas.press('ArrowRight');canvas.press('+')
            page.wait_for_timeout(120)
            assert f.locator('#material-leaders path').first.get_attribute('d')!=path
            assert float(canvas.get_attribute('data-zoom'))>1
            f.locator('#explode').focus();f.locator('#explode').press('End')
            assert f.evaluate('TrainingLesson.current().explosion')==1
            canvas.scroll_into_view_if_needed()
            press(f.locator('#rotate'));page.wait_for_timeout(160)
            auto_yaw=canvas.get_attribute('data-yaw');page.wait_for_timeout(160)
            assert canvas.get_attribute('data-yaw')!=auto_yaw
            press(f.locator('#rotate'));press(f.locator('#reset-view'))
            canvas.scroll_into_view_if_needed();page.wait_for_timeout(120)
            if not args.public:
                canvas.scroll_into_view_if_needed();rect=canvas.bounding_box()
                old_yaw=float(canvas.get_attribute('data-yaw'))
                page.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']/2)
                page.mouse.down();page.mouse.move(rect['x']+rect['width']/2+35,rect['y']+rect['height']/2+12,steps=8);page.mouse.up()
                page.wait_for_timeout(100)
                assert abs(float(canvas.get_attribute('data-yaw'))-old_yaw)>.2
                page.mouse.wheel(0,-100);page.wait_for_timeout(100)
                assert float(canvas.get_attribute('data-zoom'))>1
                press(f.locator('#reset-view'))
                # Real pointer activation of a face, not just API/button selection.
                press(f.locator('#parts [data-part]').nth(1))
                canvas.scroll_into_view_if_needed();selected=f.evaluate('TrainingLesson.current().part')
                size=canvas.bounding_box();hit=False
                for dx,dy in [(0,0),(-30,0),(30,0),(0,-40),(0,40)]:
                    canvas.click(position={'x':size['width']/2+dx,'y':size['height']/2+dy})
                    if f.evaluate('TrainingLesson.current().part')!=selected:
                        hit=True;break
                assert hit,'No material face selected by pointer: '+course
            press(f.locator('#show-cross-section'))
            canvas.scroll_into_view_if_needed();page.wait_for_timeout(100)
            for width in [1440,900,390]:
                page.set_viewport_size({'width':width,'height':1100})
                canvas.scroll_into_view_if_needed();page.wait_for_timeout(100)
                size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
                assert size['scroll']<=size['client']+1,size
                for button in f.locator('#model-labels button').all():
                    assert button.is_visible()
                    assert button.evaluate('e=>e.offsetHeight>=44')
                    assert button.evaluate('e=>{const p=e.parentElement.getBoundingClientRect(),r=e.getBoundingClientRect();return r.left>=p.left&&r.right<=p.right+1&&r.top>=p.top&&r.bottom<=p.bottom+1;}')
                f.locator('.model-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}-{width}.png'))
            page.set_viewport_size({'width':1440,'height':1000})
            press(f.locator('#model-exterior'));canvas.scroll_into_view_if_needed()
            f.wait_for_function('document.querySelector("canvas").dataset.mode==="exterior"')
            assert not f.locator('#model-labels').is_visible()
            assert not f.locator('#animate').is_disabled()
            assert f.evaluate('TrainingLesson.current().params')==before['params']
        press(f.locator('#show-cross-section'))
        press(f.locator('button[data-course="capacitor"]'))
        assert f.evaluate('TrainingLesson.current().modelMode')=='materials'
        assert f.locator('#model-labels button').count()==5
        assert f.evaluate('TrainingMaterials.current().course')=='capacitor'
        state=f.evaluate('TrainingLesson.current()')
        assert not f.evaluate('TrainingLesson.setModelMode("unknown")')
        assert not f.evaluate('TrainingLesson.selectMaterial("unknown")')
        assert f.evaluate('TrainingLesson.current()')==state
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'courses':4,'material_parts':20,'same_canvas':True,'labels_camera_and_selection':True,'pointer_mesh_selection':not args.public,'widths':[1440,900,390],'browser_errors':errors}),flush=True)
    except Exception:
        print(json.dumps({'browser_errors':errors,'state':f.evaluate('TrainingLesson.current()') if f else None}),flush=True)
        raise
    finally:context.close();browser.close()
