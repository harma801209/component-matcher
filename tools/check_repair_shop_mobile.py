"""Real phone-sized clicks: operate beside the scene and actually see its motion."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--embedded', action='store_true')
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[2] / 'repair-shop-qa'
OUT.mkdir(exist_ok=True)
tag = 'mobile-workbench-public' if args.public else 'mobile-workbench-local'
if args.embedded:
    tag += '-embedded'
url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/'
if args.embedded and not args.public:
    url += 'embedded'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':393,'height':780}, has_touch=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        def frame_now():
            deadline = time.monotonic()+120
            while time.monotonic()<deadline:
                for f in page.frames:
                    try:
                        if f.locator('.academy-switch').count() and f.evaluate('typeof RepairShopScene!=="undefined" && RepairShopScene.VIEW_VERSION===6 && (!window.frameElement || !!window.TrainingEmbedLayout)'):
                            return f
                    except Exception:
                        pass
                page.wait_for_timeout(400)
            raise AssertionError('New workbench did not load')

        def snapshot():
            return frame.evaluate('RepairShop.snapshot()')

        def scene():
            return frame.evaluate('RepairShop.sceneSnapshot()')

        def in_view(locator):
            box = locator.bounding_box()
            assert box, 'Missing visible control'
            assert box['y']>=-2 and box['y']+box['height']<=page.viewport_size['height']+2,box
            assert box['x']>=-1 and box['x']+box['width']<=page.viewport_size['width']+1,box

        def watch_motion():
            frame.evaluate('''()=>{const samples=[];window.__mobileMotion=samples;const start=performance.now();function sample(){const s=RepairShop.sceneSnapshot();samples.push({moving:s.assembly.moving,points:s.mechanicalProjections});if(performance.now()-start<3500)requestAnimationFrame(sample);}requestAnimationFrame(sample);}''')

        page.goto(url, wait_until='domcontentloaded', timeout=120000)
        frame=frame_now()
        checked=[]
        for i,product in enumerate(['router','speaker','lamp','fan','clock','sensor']):
            page.set_viewport_size({'width':360 if i%2 else 393,'height':780})
            # Only create a fresh isolated order; all subsequent steps are real buttons.
            frame.evaluate('''id=>{let seed=1;while(RepairShopEngine.offer(seed).product.id!==id||!RepairShopEngine.offer(seed).fault.enabled)seed++;localStorage.setItem(RepairShopEngine.KEY,JSON.stringify(RepairShopEngine.apply(RepairShopEngine.create(),{type:'accept',seed}).state));}''',product)
            page.reload(wait_until='domcontentloaded',timeout=120000)
            frame=frame_now()
            canvas=frame.locator('.rs-board-canvas')
            primary=frame.locator('.rs-mobile-execute')
            primary.scroll_into_view_if_needed()
            primary.click()  # discharge, also aligns the whole compact work area
            assert snapshot()['active']['discharged']
            in_view(canvas)
            in_view(frame.locator('.rs-mobile-execute'))
            primary.click()  # deliberate pickup of screwdriver
            assert not snapshot()['active']['mechanics']['loose']
            opening=[]
            for _ in range(10):
                if frame.evaluate('RepairShopMechanics.onTable(RepairShop.snapshot().active.mechanics)'):
                    break
                next_step=frame.evaluate('RepairShopMechanics.next(RepairShop.snapshot().active.mechanics,false)')
                control=frame.locator('.rs-mobile-execute')
                in_view(canvas)
                in_view(control)
                before=snapshot()
                watch_motion()
                if control.get_attribute('data-screw-id'):
                    old=frame.evaluate('JSON.stringify(RepairShop.snapshot().active.mechanics)');control.focus();page.keyboard.down('Enter')
                    try:
                        frame.wait_for_function('old=>JSON.stringify(RepairShop.snapshot().active.mechanics)!==old',arg=old,timeout=15000)
                    finally:
                        page.keyboard.up('Enter')
                else:
                    control.click()
                in_view(canvas)
                assert snapshot()['coins']==before['coins'] and snapshot()['points']==before['points']
                assert not snapshot()['active']['diagnosed'] and not snapshot()['active']['measurements']
                frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
                samples=frame.evaluate('__mobileMotion')
                assert any(s['moving'] for s in samples),next_step
                assert len({json.dumps(s['points'],sort_keys=True) for s in samples})>1,next_step
                opening.append(next_step['op'])
                if product=='router' and next_step['op']=='cover-out':
                    page.screenshot(path=str(OUT/(tag+'-router-cover.png')))
            assert len(opening)==8,opening
            assert scene()['assembly']['boardOnTable']
            assert len(snapshot()['active']['mechanics']['loose'])==4
            before=snapshot()
            for color,contact in [('black','GND'),('red','TP1')]:
                button=frame.locator('[data-repair-focus="mobile-lead-'+color+'"]')
                in_view(button)
                button.click()
                in_view(canvas)
                point=scene()['contactProjections'][contact]
                box=canvas.bounding_box()
                page.touchscreen.tap(box['x']+point['x'],box['y']+point['y'])
                assert scene()['probeContacts'][color]==contact
            assert snapshot()==before,'Quick connections must not auto-measure'
            frame.locator('[data-repair-focus="mobile-power"]').click()
            in_view(canvas)
            frame.locator('[data-repair-focus="mobile-measure"]').click()
            in_view(canvas)
            in_view(frame.locator('[data-repair-focus="mobile-measure"]'))
            assert snapshot()['active']['measurements']
            assert not snapshot()['active']['diagnosed'] and snapshot()['points']==before['points']
            assert frame.locator('.rs-mobile-reading').inner_text()!='接线不等于测量，需亲自点击记录'
            widths=frame.evaluate('({s:document.documentElement.scrollWidth,c:document.documentElement.clientWidth})')
            assert widths['s']<=widths['c']+1,widths
            if product in ['router','speaker']:
                page.screenshot(path=str(OUT/(tag+'-'+product+'-probes.png')))
            # Full tools remain accessible; acting there also returns to visible animation.
            frame.locator('[data-repair-focus="mobile-more"]').click()
            frame.locator('[data-repair-focus="power"]').click()
            in_view(canvas)
            checked.append({'product':product,'width':page.viewport_size['width'],'animated_steps':opening})
        assert not errors,errors
        report={'status':'passed','public':args.public,'products':checked,'scene_and_controls_same_view':True,'observed_real_motion':True,'mobile_probes_and_readout':True,'no_auto_diagnosis_or_economy':True,'full_tools_return_to_scene':True,'errors':errors}
        (OUT/(tag+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    finally:
        context.close()
        browser.close()
