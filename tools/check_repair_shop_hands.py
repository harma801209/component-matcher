"""Actual held gestures, immersive landscape, model traces and staged repair."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi=None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
OUT=Path(__file__).resolve().parents[2]/'repair-shop-qa'
tag='hands-on-public' if args.public else 'hands-on-local'
url='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/embedded'

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':844,'height':390},has_touch=True)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))

    def ready():
        end=time.monotonic()+150
        while time.monotonic()<end:
            for f in page.frames:
                try:
                    if f.locator('.academy-switch').count() and f.evaluate('typeof RepairShop!=="undefined"&&RepairShop.HANDS_ON_VERSION===1&&RepairShopScene.VIEW_VERSION===6'):
                        return f
                except Exception:
                    pass
            page.wait_for_timeout(400)
        raise AssertionError('Hands-on version did not load')

    def state():
        return frame.evaluate('RepairShop.snapshot()')

    def control(key):
        return frame.locator('[data-repair-focus="'+key+'"]')

    def act(key):
        b=control(key);b.scroll_into_view_if_needed();b.click()

    def hold(key):
        b=control(key);old=frame.evaluate('JSON.stringify(RepairShop.snapshot().active.mechanics)');b.focus();page.keyboard.down('Enter')
        try:
            frame.wait_for_function('old=>JSON.stringify(RepairShop.snapshot().active.mechanics)!==old',arg=old,timeout=15000)
        finally:
            page.keyboard.up('Enter')
        frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')

    def fits(n):
        b=n.bounding_box();assert b and b['x']>=-1 and b['y']>=-1,b
        assert b['x']+b['width']<=page.viewport_size['width']+1 and b['y']+b['height']<=page.viewport_size['height']+1,b

    try:
        page.goto(url,wait_until='domcontentloaded',timeout=120000);frame=ready()
        # Only create a fresh isolated order; no diagnosis, screw or repair state injected.
        frame.evaluate('''()=>{let seed=1;while(RepairShopEngine.offer(seed).product.id!=='speaker'||RepairShopEngine.offer(seed).fault.reason!=='esr')seed++;localStorage.setItem(RepairShopEngine.KEY,JSON.stringify(RepairShopEngine.apply(RepairShopEngine.create(),{type:'accept',seed}).state));}''')
        page.reload(wait_until='domcontentloaded',timeout=120000);frame=ready()
        assert frame.evaluate('RepairShop.sceneSnapshot().renderer')=='WebGL'
        before=state();act('immersive');assert frame.locator('#repair-shop').get_attribute('aria-modal')=='true';assert state()==before
        fits(frame.locator('.rs-board-canvas'));fits(frame.locator('.rs-tools'))
        act('immersive-discharge');act('mechanic-tool')
        canvas=frame.locator('.rs-board-canvas');pos=frame.evaluate('RepairShop.sceneSnapshot().mechanicalProjections["@screw:S1"]');box=canvas.bounding_box()
        old=state();page.mouse.move(box['x']+pos['x'],box['y']+pos['y']);page.mouse.down();page.wait_for_timeout(350)
        partial=frame.evaluate('RepairShop.driverSnapshot()');assert partial and 0<partial['turns']<2,partial;assert state()==old
        pose=frame.evaluate('RepairShop.sceneSnapshot().assembly.driver');assert pose['active'] and pose['turns']<0,pose
        page.screenshot(path=str(OUT/(tag+'-held-driver.png')));page.mouse.up();page.wait_for_timeout(200)
        assert not frame.evaluate('RepairShop.driverSnapshot().active') and state()==old
        hold('mechanic-S1');assert state()['active']['mechanics']['loose']==['S1']
        for id in ['S2','S3','S4']:
            hold('mechanic-'+id)
        for op in ['cover-out','brace-out','unplug','board-out']:
            act('mechanic-'+op);frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
        fits(canvas);fits(frame.locator('.rs-tools'))
        act('target-C1');act('immersive-power');act('mode-scope');act('dock-scope');act('measure')
        fits(canvas)
        assert frame.locator('#repair-oscilloscope canvas').count()==1
        assert state()['active']['measurements'][-1]['trace']['mode']=='ripple'
        trace=frame.evaluate('''()=>{const a=RepairShop.snapshot().active,j=RepairShopEngine.offer(a.seed);return RepairShopWaveforms.capture(j.product,j.fault,null,{mode:'ripple',load:'specified'});}''')
        assert trace['max']-trace['min']>.08
        frame.locator('#repair-oscilloscope').scroll_into_view_if_needed();page.screenshot(path=str(OUT/(tag+'-ripple.png')))
        for mode in ['step','startup']:
            old=state();act('scope-'+mode);assert state()==old
            act('measure');assert state()['active']['measurements'][-1]['trace']['mode']==mode
            assert frame.locator('#repair-oscilloscope canvas').count()==1
        page.screenshot(path=str(OUT/(tag+'-startup.png')))
        act('immersive-power');act('immersive-discharge');act('mode-component');act('dock-component');act('measure')
        frame.locator('#repair-diagnosis').select_option('C1');frame.locator('#repair-reason').select_option('esr');act('diagnose')
        candidate=frame.evaluate('''()=>{const a=RepairShop.snapshot().active,j=RepairShopEngine.offer(a.seed),p=j.product.parts.find(p=>p.id===j.fault.component);return j.candidates.find(c=>!RepairShopEngine.compatible(p,c));}''')
        act(candidate['stockId']);frame.locator('#repair-orientation').select_option('correct');coins=state()['coins'];act('install')
        assert state()['coins']==coins and not state()['active']['installed']
        for index,op in enumerate(['remove','clean','orient','place','inspect']):
            act('repair-'+op);assert state()['coins']==coins and not state()['active']['installed']
            fits(canvas)
            if op=='remove':
                scene=frame.evaluate('RepairShop.sceneSnapshot().service');assert scene['oldOnDesk'] and not scene['replacementVisible'];page.screenshot(path=str(OUT/(tag+'-old-part.png')))
        act('install-confirm');assert state()['coins']==coins-candidate['price'];assert state()['active']['installed']
        act('immersive-power');act('test');assert state()['active']['tested']
        act('immersive-power');act('immersive-discharge')
        for op in ['board-in','plug','brace-in','cover-in']:
            act('mechanic-'+op);frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
        for id in ['S1','S2','S3','S4']:
            hold('mechanic-'+id)
        act('immersive-power');act('assembly-test');act('deliver');assert state()['completed']==1
        assert '客户反馈' in frame.locator('#repair-customer-feedback').inner_text()
        assert frame.locator('.rs-report-service').inner_text().count('✓ 已记录')==5
        act('immersive');assert frame.locator('#repair-shop').get_attribute('aria-modal') is None
        frame.locator('#repair-customer-feedback').scroll_into_view_if_needed();page.screenshot(path=str(OUT/(tag+'-customer-report.png')))
        page.set_viewport_size({'width':393,'height':780});assert frame.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1')
        assert not errors,errors
        report={'pass':True,'public':args.public,'held_cancel_and_resume':True,'real_driver_pose':True,'landscape_scene_and_tools_fit':True,'ripple_step_startup':True,'rework_stages_and_single_charge':True,'customer_report':True,'errors':errors}
        (OUT/(tag+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/(tag+'-failure.png')))
        raise
    finally:
        context.close();browser.close()
