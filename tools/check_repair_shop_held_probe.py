"""Native WebGL QA of held probes, passive hover and deliberate contact placement."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--product', choices=['lamp','fan','speaker','clock','sensor','router'])
args = parser.parse_args()
out = Path(__file__).resolve().parents[2] / 'repair-shop-qa'
out.mkdir(exist_ok=True)
tag = 'held-probe-public' if args.public else 'held-probe-local'
if args.product:
    tag += '-'+args.product
url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1080}, has_touch=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        def frame_now():
            deadline = time.monotonic()+120
            while time.monotonic()<deadline:
                for f in page.frames:
                    try:
                        if f.locator('.academy-switch').count() and f.evaluate('typeof RepairShopScene!=="undefined" && RepairShopScene.VIEW_VERSION===6'):
                            return f
                    except Exception:
                        pass
                page.wait_for_timeout(400)
            raise AssertionError('Held-probe scene did not load')

        def activate(key):
            loc = frame.locator('[data-repair-focus="'+key+'"]')
            loc.focus()
            if loc.get_attribute('data-screw-id'):
                old=frame.evaluate('JSON.stringify(RepairShop.snapshot().active.mechanics)');page.keyboard.down('Enter')
                try:
                    frame.wait_for_function('old=>JSON.stringify(RepairShop.snapshot().active.mechanics)!==old',arg=old,timeout=15000)
                finally:
                    page.keyboard.up('Enter')
            else:
                loc.press('Enter')

        def snapshot():
            return frame.evaluate('RepairShop.snapshot()')

        def scene():
            return frame.evaluate('RepairShop.sceneSnapshot()')

        def check_cable(wire):
            assert wire and wire['samples']==40,wire
            assert max(abs(x-y) for x,y in zip(wire['start'],wire['rear']))<1e-5
            step=[y-x for x,y in zip(wire['start'],wire['afterStart'])]
            dot=sum(x*y for x,y in zip(step,wire['axis']))
            assert dot>0,'Cable must leave the rear in the outward direction'
            assert all(all(abs(x)<1000 for x in p) for p in wire['points'])

        def move(x,y):
            box=canvas.bounding_box()
            page.mouse.move(box['x']+x,box['y']+y)

        page.goto(url,wait_until='domcontentloaded',timeout=120000)
        frame=frame_now()
        checked=[]
        for product in ([args.product] if args.product else ['lamp','fan','speaker','clock','sensor','router']):
            frame.evaluate('''id=>{let seed=1;while(RepairShopEngine.offer(seed).product.id!==id||!RepairShopEngine.offer(seed).fault.enabled)seed++;localStorage.setItem(RepairShopEngine.KEY,JSON.stringify(RepairShopEngine.apply(RepairShopEngine.create(),{type:'accept',seed}).state));}''',product)
            page.reload(wait_until='domcontentloaded',timeout=120000)
            frame=frame_now()
            activate('discharge')
            activate('mechanic-tool')
            for _ in range(12):
                if frame.evaluate('RepairShopMechanics.onTable(RepairShop.snapshot().active.mechanics)'):
                    break
                step=frame.evaluate('RepairShopMechanics.next(RepairShop.snapshot().active.mechanics,false)')
                activate('mechanic-'+(step.get('id') or step['op']))
            frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
            canvas=frame.locator('.rs-board-canvas')
            before=snapshot()
            activate('lead-black')
            canvas.scroll_into_view_if_needed()
            ports=scene()['contactProjections']
            size=canvas.bounding_box()
            candidates=[(size['width']*x,size['height']*y) for x in [.3,.5,.7] for y in [.3,.5,.7]]
            free=next(q for q in candidates if all((q[0]-v['x'])**2+(q[1]-v['y'])**2>65**2 for v in ports.values()))
            move(*free)
            held=scene()['heldProbe']
            assert held['visible'] and held['color']=='black' and held['target'] is None,held
            assert canvas.evaluate('n=>getComputedStyle(n).cursor')=='none'
            assert snapshot()==before
            check_cable(scene()['probeCables']['held'])
            cable_id=scene()['probeCables']['held']['geometryId']
            tip=scene()['heldProbe']['tip']
            rear=scene()['probeCables']['held']['rear']
            canvas.press('e')
            assert scene()['heldProbe']['turn']==15
            assert scene()['heldProbe']['tip']==tip
            assert scene()['probeCables']['held']['rear']!=rear
            assert scene()['probeCables']['held']['geometryId']==cable_id
            check_cable(scene()['probeCables']['held'])
            assert snapshot()==before
            canvas.press('q')
            assert scene()['heldProbe']['turn']==0 and snapshot()==before
            for _ in range(3):
                page.keyboard.press('e')
            assert scene()['heldProbe']['turn']==45,'Repeated keys must work without refocusing the canvas'
            for _ in range(3):
                page.keyboard.press('q')
            assert scene()['heldProbe']['turn']==0 and snapshot()==before
            assert canvas.evaluate('n=>document.activeElement===n')
            if product=='speaker':
                canvas.screenshot(path=str(out/(tag+'-black-direction-0.png')))
                for _ in range(6):
                    canvas.press('e')
                assert scene()['heldProbe']['turn']==90
                canvas.screenshot(path=str(out/(tag+'-black-direction-90.png')))
                for _ in range(6):
                    canvas.press('q')
            initial=scene()
            move(free[0]+18,free[1]+12)
            assert scene()['heldProbe']['tip']!=held['tip']
            assert scene()['yaw']==initial['yaw'] and snapshot()==before
            assert scene()['meshCount']==initial['meshCount'],'Hover must reuse geometry'
            move(free[0],free[1])
            page.mouse.down()
            move(free[0]+18,free[1]+12)
            page.mouse.up()
            assert scene()['yaw']==initial['yaw'],'Left probe movement must not orbit the board'
            assert snapshot()==before
            box=canvas.bounding_box()
            page.mouse.move(box['x']+10,box['y']-8)
            assert not scene()['heldProbe']['visible']
            assert canvas.evaluate('n=>getComputedStyle(n).cursor')!='none'
            ports=scene()['contactProjections']
            move(ports['GND']['x']+6,ports['GND']['y']+4)
            held=scene()['heldProbe']
            assert held['target']=='GND' and held['valid'] and snapshot()==before
            page.mouse.down()
            page.mouse.up()
            assert scene()['probeContacts']['black']=='GND'
            assert not scene()['heldProbe']['visible'] and snapshot()==before
            parked_tip=scene()['probeCables']['black']['tip']
            activate('probe-turn-black-right')
            assert scene()['probeCables']['black']['turn']==15
            assert scene()['probeCables']['black']['tip']==parked_tip
            assert scene()['probeContacts']['black']=='GND' and snapshot()==before
            check_cable(scene()['probeCables']['black'])
            activate('probe-turn-black-left')
            activate('lead-red')
            canvas.scroll_into_view_if_needed()
            point=scene()['contactProjections']['TP1']
            move(point['x']+6,point['y']+4)
            assert scene()['heldProbe']['color']=='red' and scene()['heldProbe']['target']=='TP1'
            if product=='lamp':
                canvas.screenshot(path=str(out/(tag+'-red-preview.png')))
            page.mouse.down()
            page.mouse.up()
            assert scene()['probeContacts']=={'black':'GND','red':'TP1'}
            assert snapshot()==before,'Placement must not measure or alter economy'
            activate('lead-red')
            canvas.scroll_into_view_if_needed()
            move(*free)
            yaw=scene()['yaw']
            page.mouse.down(button='right')
            assert scene()['heldProbe']['visible']
            for i in range(1,13):
                move(free[0]+i*3,free[1]+i)
                assert scene()['heldProbe']['visible'],'Right orbit must not blink the held tool'
                assert scene()['heldProbe']['target'] is None,'Orbit must not snap or attach'
                assert canvas.evaluate('n=>getComputedStyle(n).cursor')=='none'
                check_cable(scene()['probeCables']['held'])
            page.mouse.up(button='right')
            assert scene()['heldProbe']['visible']
            assert scene()['yaw']!=yaw and snapshot()==before
            canvas.press('Escape')
            assert not scene()['heldProbe']['visible']
            assert canvas.evaluate('n=>getComputedStyle(n).cursor')!='none'
            activate('lead-red')
            frame.locator('[data-repair-focus="lead-red"]').press('Escape')
            assert frame.locator('[data-repair-focus="lead-red"]').get_attribute('aria-pressed')=='false'
            assert not scene()['heldProbe']['visible'] and snapshot()==before
            activate('lead-red')
            activate('mode-component')
            assert not scene()['heldProbe']['visible']
            assert canvas.evaluate('n=>getComputedStyle(n).cursor')!='none'
            activate('mode-voltage')
            activate('probe-clear')
            activate('jack-ma')
            activate('lead-red')
            canvas.scroll_into_view_if_needed()
            point=scene()['contactProjections']['TP1']
            move(point['x'],point['y'])
            assert scene()['heldProbe']['target']=='TP1' and not scene()['heldProbe']['valid']
            page.mouse.down()
            page.mouse.up()
            assert scene()['probeContacts']['red'] is None and snapshot()==before
            canvas.press('Escape')
            activate('jack-v')
            page.set_viewport_size({'width':393,'height':960})
            activate('lead-black')
            canvas.scroll_into_view_if_needed()
            point=scene()['contactProjections']['GND']
            box=canvas.bounding_box()
            page.touchscreen.tap(box['x']+point['x'],box['y']+point['y'])
            assert scene()['probeContacts']['black']=='GND' and snapshot()==before
            assert canvas.evaluate('n=>getComputedStyle(n).cursor')!='none'
            activate('probe-turn-black-right')
            assert scene()['probeContacts']['black']=='GND'
            assert scene()['probeCables']['black']['turn']==15 and snapshot()==before
            check_cable(scene()['probeCables']['black'])
            widths=frame.evaluate('({s:document.documentElement.scrollWidth,c:document.documentElement.clientWidth})')
            assert widths['s']<=widths['c']+1
            checked.append(product)
            page.set_viewport_size({'width':1440,'height':1080})
        assert not errors,errors
        report={'status':'passed','public':args.public,'six_products':checked,'real_3d_follow':True,'smooth_rear_exit_cable':True,'held_qe_rotation_tip_fixed':True,'connected_and_phone_direction_buttons':True,'reused_tube_geometry':True,'deliberate_snap_only':True,'no_auto_measurement_or_economy':True,'left_placement_right_orbit':True,'leave_escape_cursor_restore':True,'wrong_jack_rejected':True,'phone_touch_and_containment':True,'errors':errors}
        (out/(tag+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    except Exception as exc:
        print('Held-probe QA failed: '+repr(exc),flush=True)
        raise
    finally:
        context.close()
        browser.close()
