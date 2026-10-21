"""Native Chrome QA: a real repair, save/resume, rewards, keyboard and mobile fit."""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--gallery', action='store_true', help='Inspect all six teaching diagrams in an isolated browser context')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'repair-shop-qa'
OUT.mkdir(exist_ok=True)
URL = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1080}, device_scale_factor=1)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    report = {'public': args.public}
    try:
        def find_frame():
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                for frame in page.frames:
                    try:
                        if frame.locator('.academy-switch').count():
                            return frame
                    except Exception:
                        pass
                page.wait_for_timeout(400)
            raise AssertionError('Repair-shop entrance did not load')

        def activate(locator):
            locator.focus()
            locator.press('Enter')

        page.goto(URL, wait_until='domcontentloaded', timeout=120000)
        frame = find_frame()
        activate(frame.get_by_role('button', name='电子维修店', exact=True))
        shop = frame.locator('#repair-shop')
        assert shop.is_visible()
        assert frame.locator('#academy-lessons').is_hidden()
        assert shop.locator('.rs-order').count() == 3
        page.screenshot(path=str(OUT / ('public-lobby.png' if args.public else 'local-lobby.png')), full_page=True)
        activate(shop.get_by_role('button', name='接下这单').first)
        job = frame.evaluate('RepairShopEngine.offer(RepairShop.snapshot().active.seed)')
        culprit = job['fault']['component']
        assert frame.locator('#repair-reason').input_value() == ''
        assert frame.locator('#repair-diagnosis').input_value() == ''
        assert not frame.evaluate('RepairShop.snapshot().active.power')
        activate(shop.get_by_role('button', name=culprit+' '+next(part['name'] for part in job['product']['parts'] if part['id']==culprit), exact=True))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        assert '电压测量需要' in frame.locator('#repair-status').inner_text()
        activate(shop.get_by_role('button', name='开启模拟电源', exact=True))
        activate(shop.get_by_role('button', name='诊断测试波形', exact=True))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        activate(shop.get_by_role('button', name='关闭模拟电源', exact=True))
        activate(shop.get_by_role('button', name='断电后放电', exact=True))
        activate(shop.get_by_role('button', name='隔离元件检测', exact=True))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        assert job['fault']['bad'] in frame.locator('#repair-meter').inner_text()
        frame.locator('#repair-reason').select_option(job['fault']['reason'])
        activate(shop.get_by_role('button', name='提交诊断', exact=True))
        assert frame.evaluate('RepairShop.snapshot().active.diagnosed')
        page.screenshot(path=str(OUT / ('public-workbench.png' if args.public else 'local-workbench.png')), full_page=True)
        before = frame.evaluate('RepairShop.snapshot()')
        page.reload(wait_until='domcontentloaded', timeout=120000)
        frame = find_frame()
        # A resumed unfinished job opens directly, without revealing/preselecting a part.
        shop = frame.locator('#repair-shop')
        assert shop.is_visible()
        after = frame.evaluate('RepairShop.snapshot()')
        assert after['active']['diagnosed'] and after['active']['seed'] == before['active']['seed']
        assert after['coins'] == before['coins']
        assert not shop.locator('.rs-stock [aria-pressed=true]').count()
        stock_id = frame.evaluate('''() => {const j=RepairShopEngine.offer(RepairShop.snapshot().active.seed),p=j.product.parts.find(p=>p.id===j.fault.component);return j.candidates.find(c=>!RepairShopEngine.compatible(p,c)).stockId;}''')
        activate(shop.locator('[data-repair-focus="'+stock_id+'"]'))
        if frame.locator('#repair-orientation').count():
            frame.locator('#repair-orientation').select_option('correct')
        activate(shop.get_by_role('button', name='采购并更换', exact=True))
        assert frame.evaluate('!!RepairShop.snapshot().active.installed')
        activate(shop.get_by_role('button', name='运行功能与负载测试', exact=True))
        assert '先通电' in frame.locator('#repair-status').inner_text()
        activate(shop.get_by_role('button', name='开启模拟电源', exact=True))
        activate(shop.get_by_role('button', name='运行功能与负载测试', exact=True))
        activate(shop.get_by_role('button', name='交付并领取报酬', exact=True))
        done = frame.evaluate('RepairShop.snapshot()')
        assert done['completed'] == 1 and done['points'] == 100 and done['active']['delivered']
        assert job['fault']['symptom'] in shop.locator('.rs-ticket').inner_text()
        assert shop.locator('.rs-settlement').is_visible()
        report['case'] = {'product':job['product']['name'],'fault':culprit,'loop':'passed','resume':'passed'}
        activate(shop.get_by_role('button', name='奖励小铺', exact=True))
        activate(shop.get_by_role('button', name='兑换奖励').first)
        assert 'mint' in frame.evaluate('RepairShop.snapshot().owned')
        assert shop.get_attribute('data-theme') == 'mint'
        activate(shop.get_by_role('button', name='返回维修台', exact=True))
        for width in [1024,760,393,360]:
            page.set_viewport_size({'width':width,'height':960})
            page.wait_for_timeout(250)
            sizes=frame.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert sizes['scroll'] <= sizes['client']+1, (width,sizes)
            assert shop.locator('.rs-board').bounding_box()['width'] > 200
            if width==393:
                page.screenshot(path=str(OUT / ('public-phone.png' if args.public else 'local-phone.png')), full_page=True)
        activate(shop.get_by_role('button', name='接待下一位客人 →', exact=True))
        assert shop.locator('.rs-order').count()==3
        activate(frame.get_by_role('button', name='器件课堂', exact=True))
        assert frame.locator('#academy-lessons').is_visible()
        assert frame.locator('#model-canvas').count()==1
        assert shop.is_hidden()
        page.set_viewport_size({'width':1280,'height':960})
        activate(frame.locator('button[data-course="resistor"]'))
        canvas=frame.locator('#model-canvas')
        canvas.scroll_into_view_if_needed()
        frame.wait_for_function('Number(document.querySelector("#model-canvas").dataset.meshFaces)>20', timeout=30000)
        activate(frame.get_by_role('tab', name='电气性能', exact=True))
        assert frame.evaluate('TrainingLesson.current().course')=='resistor'
        assert frame.evaluate('TrainingLesson.current().result.current')>0
        report['original_3d_and_calculation']='passed'
        if args.public:
            height=frame.evaluate('({content:Math.ceil(document.querySelector("#training-app").getBoundingClientRect().height),frame:window.frameElement?Number.parseFloat(window.frameElement.style.height):null})')
            if height['frame'] is not None:
                assert height['frame'] >= height['content'], height
            report['iframe_autoheight']=height
        if args.gallery:
            page.set_viewport_size({'width':1440,'height':1080})
            for product_id in ['lamp','fan','speaker','clock','sensor','router']:
                frame.evaluate('''id=>{let seed=1;while(RepairShopEngine.offer(seed).product.id!==id)seed++;const s=RepairShopEngine.apply(RepairShopEngine.create(),{type:'accept',seed}).state;localStorage.setItem(RepairShopEngine.KEY,JSON.stringify(s));}''', product_id)
                page.reload(wait_until='domcontentloaded', timeout=120000)
                frame=find_frame()
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('diagram-'+product_id+'.png')))
                assert frame.locator('.rs-probe-picker button').count()==3
            report['six_diagrams']='checked'
        assert not errors, errors
        report.update(status='passed',rewards=True,mobile_fit=True,original_lessons=True,errors=errors)
        print(json.dumps(report, ensure_ascii=False), flush=True)
        (OUT / ('public-report.json' if args.public else 'local-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        context.close()
        browser.close()
