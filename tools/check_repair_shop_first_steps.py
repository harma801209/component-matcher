"""Real Chrome clicks through the novice flow; no practice-state injection."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--mobile', action='store_true')
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--width', type=int)
parser.add_argument('--height', type=int)
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[2] / 'repair-shop-qa'
OUT.mkdir(exist_ok=True)
tag = 'first-steps-' + ('public' if args.public else 'local') + ('-phone' if args.mobile else '-desktop')
if args.width:
    tag += '-'+str(args.width)+'x'+str(args.height or 780)
url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/'
if args.embedded and not args.public:
    url += 'embedded'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':args.width or (393 if args.mobile else 1440),'height':args.height or (780 if args.mobile else 1000)}, has_touch=args.mobile)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def ready():
        deadline = time.monotonic()+150
        while time.monotonic()<deadline:
            for f in page.frames:
                try:
                    if f.locator('.academy-switch').count() and f.evaluate('typeof RepairShopFirstStepsUI!=="undefined" && RepairShopFirstStepsUI.VERSION===1 && RepairShop.FIRST_STEPS_VERSION===2'):
                        return f
                except Exception:
                    pass
            page.wait_for_timeout(500)
        raise AssertionError('New first-steps UI did not load')

    def s():
        return frame.evaluate('RepairShop.firstStepsSnapshot()')

    def in_view(locator):
        b = locator.bounding_box()
        assert b and b['y']>=-2 and b['y']+b['height']<=page.viewport_size['height']+2, b
        assert b['x']>=-1 and b['x']+b['width']<=page.viewport_size['width']+1, b

    def click(key):
        control = frame.locator('[data-first-action="'+key+'"]')
        control.click()
        if args.mobile:
            in_view(frame.locator('.rs-first-canvas'))
            box = frame.locator('.rs-first-work').bounding_box()
            assert box and box['height']<=page.viewport_size['height']+2, box
        assert frame.evaluate('RepairShop.snapshot()')==paid_before, 'Practice changed the paid job or economy'

    try:
        page.goto(url,wait_until='domcontentloaded',timeout=120000)
        frame=ready()
        frame.get_by_role('button',name='电子维修店',exact=True).click()
        # Accept an ordinary job by its existing UI; it must survive all practice.
        frame.get_by_role('button',name='接下这单',exact=True).first.click()
        for _ in range(14):
            if frame.evaluate('RepairShopMechanics.onTable(RepairShop.snapshot().active.mechanics)'):
                break
            target=frame.locator('#repair-coach').get_attribute('data-target')
            frame.locator('[data-repair-focus="'+target+'"]').click()
            page.wait_for_timeout(80)
            frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
        assert frame.evaluate('RepairShopMechanics.onTable(RepairShop.snapshot().active.mechanics)')
        frame.locator('[data-repair-focus="lead-black"]').click()
        paid_before=frame.evaluate('RepairShop.snapshot()')
        frame.locator('[data-repair-focus="first-steps"]').click()
        assert s()['episode']==0 and not s()['fixture']
        assert frame.evaluate('RepairShop.firstStepsSceneSnapshot().renderer')=='WebGL'
        pristine=s()
        frame.locator('[data-first-action="fixture"]').focus()
        for key in ('q','e','Escape'):
            page.keyboard.press(key)
        assert s()==pristine
        frame.locator('[data-first-action="exit"]').click()
        assert frame.locator('[data-repair-focus="lead-black"]').get_attribute('aria-pressed')=='true', 'Practice Escape dropped the paused workbench probe'
        frame.locator('[data-repair-focus="first-steps"]').click()
        click('fixture');click('power');click('observe')
        assert s()['observed']['current']==0
        click('power');click('discharge');click('part-F1');click('inspect')
        assert not s()['inspected']['F1']['proof']
        click('part-R1');click('inspect')
        assert s()['inspected']['R1']['proof']
        # Real refresh and explicit re-entry must replay, not silently reset/skip.
        prior=s()
        page.reload(wait_until='domcontentloaded',timeout=120000)
        frame=ready();frame.locator('[data-repair-focus="first-steps"]').click()
        assert s()==prior
        frame.locator('#first-reason').select_option('drift');click('diagnose')
        assert not s()['diagnosed']
        frame.locator('#first-reason').select_option('open');click('diagnose')
        click('stock-higher');assert not s()['installed']
        click('stock-original');assert s()['installed']=='original'
        click('power');click('test')
        assert s()['tested']
        page.screenshot(path=str(OUT/(tag+'-first-success.png')))
        click('next');assert s()['episode']==1
        click('predict-same');assert s()['prediction']=='same'
        click('fixture');click('power');click('observe')
        click('power');click('discharge');click('resistor-440');click('power');click('observe')
        x=s()['comparisons']['220']['current'];y=s()['comparisons']['440']['current']
        assert x>y>0 and abs(y/x-.5)>.001
        page.screenshot(path=str(OUT/(tag+'-experiment.png')))
        click('principle-power');assert not s()['tested']
        click('principle-series');click('next');assert s()['episode']==2
        assert s()['records'][1]['firstPrediction']=='same'
        assert not s()['records'][1]['firstPredictionCorrect']
        click('fixture');click('power');click('observe')
        assert 0<s()['observed']['current']<.01
        click('power');click('discharge');click('part-R1');click('inspect')
        frame.locator('#first-reason').select_option('drift');click('diagnose')
        click('stock-original');click('power');click('test')
        page.screenshot(path=str(OUT/(tag+'-transfer.png')))
        # Next ends the scene; the report deliberately has no canvas.
        frame.locator('[data-first-action="next"]').click()
        final=s();assert final['done'] and final['records'][2]['independent']
        assert not final['records'][2]['helpUsed']
        page.screenshot(path=str(OUT/(tag+'-report.png')))
        assert frame.locator('.rs-first-report').is_visible()
        frame.locator('[data-first-action="exit-report"]').click()
        assert frame.evaluate('RepairShop.snapshot()')==paid_before
        assert frame.locator('.rs-board-canvas').is_visible()
        frame.locator('[data-repair-focus="first-steps"]').click()
        assert s()==final and frame.locator('.rs-first-report').is_visible()
        widths=frame.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
        assert widths['scroll']<=widths['client']+1,widths
        assert not errors,errors
        report={'url':url,'mobile':args.mobile,'embedded':args.embedded,'physicsCurrents':[x,y],'practice':final,'paidJobUnchanged':True,'errors':errors}
        (OUT/(tag+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'pass':True,'tag':tag,'currents':[x,y],'paidJobUnchanged':True}))
    except Exception:
        page.screenshot(path=str(OUT/(tag+'-failure.png')))
        raise
    finally:
        context.close();browser.close()
