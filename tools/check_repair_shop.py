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
                        if frame.locator('.academy-switch').count() and frame.evaluate("typeof RepairShopPhysics!=='undefined' && RepairShopPhysics.VERSION===2 && typeof RepairShopMeter!=='undefined' && RepairShopScene.VIEW_VERSION===6"):
                            return frame
                    except Exception:
                        pass
                page.wait_for_timeout(400)
            raise AssertionError('Repair-shop entrance did not load')

        def activate(locator):
            locator.focus()
            if locator.get_attribute('data-screw-id'):
                old=frame.evaluate('JSON.stringify(RepairShop.snapshot().active.mechanics)')
                page.keyboard.down('Enter')
                try:
                    frame.wait_for_function('old=>JSON.stringify(RepairShop.snapshot().active.mechanics)!==old',arg=old,timeout=15000)
                finally:
                    page.keyboard.up('Enter')
            else:
                locator.press('Enter')

        def lead(color, contact, picking=False):
            activate(frame.locator('[data-repair-focus="lead-'+color+'"]'))
            if picking:
                canvas=frame.locator('.rs-board-canvas')
                canvas.scroll_into_view_if_needed()
                canvas.click(position=frame.evaluate('id=>RepairShop.sceneSnapshot().contactProjections[id]',contact))
                assert frame.evaluate('RepairShop.sceneSnapshot().probeContacts')[color]==contact
            else:
                activate(frame.locator('[data-repair-focus="contact-'+contact+'"]'))

        def mechanical_steps(opening, picking=False):
            # Exercise visible controls, never inject a completed repair.
            def state():
                return frame.evaluate('RepairShop.snapshot().active')
            if state()['power']:
                activate(frame.locator('[data-repair-focus="power"]'))
            activate(frame.locator('[data-repair-focus="discharge"]'))
            if picking:
                canvas=frame.locator('.rs-board-canvas')
                canvas.scroll_into_view_if_needed()
                canvas.click(position=frame.evaluate('RepairShop.sceneSnapshot().mechanicalProjections["@driver"]'))
            else:
                activate(frame.locator('[data-repair-focus="mechanic-tool"]'))
            for _ in range(12):
                done=frame.evaluate('RepairShopMechanics.'+('onTable' if opening else 'assembled')+'(RepairShop.snapshot().active.mechanics)')
                if done:
                    break
                step=frame.evaluate('RepairShopMechanics.next(RepairShop.snapshot().active.mechanics,RepairShop.snapshot().active.tested)')
                target='mechanic-'+(step.get('id') or step['op'])
                if picking and step['op'] in ['unscrew','cover-out','brace-out','unplug']:
                    frame.wait_for_function('!RepairShop.sceneSnapshot().assembly.moving')
                    key='@screw:'+step['id'] if step['op']=='unscrew' else {'cover-out':'@cover','brace-out':'@brace','unplug':'@connector'}[step['op']]
                    prior=state()['mechanics']
                    canvas.scroll_into_view_if_needed()
                    point=frame.evaluate('key=>RepairShop.sceneSnapshot().mechanicalProjections[key]',key)
                    if step['op']=='unscrew':
                        box=canvas.bounding_box();old=frame.evaluate('JSON.stringify(RepairShop.snapshot().active.mechanics)')
                        page.mouse.move(box['x']+point['x'],box['y']+point['y']);page.mouse.down()
                        try:
                            frame.wait_for_function('old=>JSON.stringify(RepairShop.snapshot().active.mechanics)!==old',arg=old,timeout=15000)
                        finally:
                            page.mouse.up()
                    else:
                        canvas.click(position=point)
                    assert state()['mechanics']!=prior,(step,'Raycast must operate the visible part')
                else:
                    activate(frame.locator('[data-repair-focus="'+target+'"]'))
            else:
                raise AssertionError('Mechanical flow did not finish')
            frame.wait_for_function('RepairShop.sceneSnapshot() && !RepairShop.sceneSnapshot().assembly.moving')
            if not opening:
                activate(frame.locator('[data-repair-focus="power"]'))
                activate(frame.locator('[data-repair-focus="assembly-test"]'))
                assert state()['finalTested']

        page.goto(URL, wait_until='domcontentloaded', timeout=120000)
        frame = find_frame()
        assert frame.evaluate("RepairShopData.products.find(p=>p.id==='lamp').parts.find(p=>p.id==='D1').name") == '红光LED'
        report['teaching_led']='红光LED / nonlinear calculated I-V model'
        activate(frame.get_by_role('button', name='电子维修店', exact=True))
        shop = frame.locator('#repair-shop')
        assert shop.is_visible()
        assert frame.locator('#academy-lessons').is_hidden()
        assert shop.locator('.rs-order').count() == 3
        page.screenshot(path=str(OUT / ('public-lobby.png' if args.public else 'local-lobby.png')), full_page=True)
        activate(shop.get_by_role('button', name='接下这单').first)
        job = frame.evaluate('RepairShopEngine.offer(RepairShop.snapshot().active.seed)')
        culprit = job['fault']['component']
        assert frame.locator('#repair-diagnosis').count()==0
        assert frame.evaluate('RepairShop.sceneSnapshot().renderer')=='WebGL',frame.evaluate('RepairShop.sceneSnapshot()')
        assert not frame.evaluate('RepairShop.sceneSnapshot().assembly.boardVisible')
        mechanical_steps(True)
        assert frame.locator('#repair-reason').input_value() == ''
        assert frame.locator('#repair-diagnosis').input_value() == ''
        assert not frame.evaluate('RepairShop.snapshot().active.power')
        activate(shop.locator('[data-repair-focus="target-'+culprit+'"]'))
        assert frame.locator('#repair-diagnosis').input_value() == '', 'Probe choice must not answer the diagnosis'
        assert shop.get_by_role('button', name='记录一次测量', exact=True).is_disabled()
        before_connections=frame.evaluate('RepairShop.snapshot()')
        lead('black','GND',True)
        lead('red','TP1',True)
        assert frame.evaluate('RepairShop.snapshot()')==before_connections
        frame.locator('.rs-board-wrap').screenshot(path=str(OUT/('probes-public.png' if args.public else 'probes-local.png')))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        assert '电压测量需要' in frame.locator('#repair-status').inner_text()
        activate(shop.get_by_role('button', name='开启模拟电源', exact=True))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        forward=frame.evaluate('RepairShop.snapshot().active.measurements.at(-1).numeric')
        lead('red','GND')
        lead('black','TP1')
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        assert frame.evaluate('RepairShop.snapshot().active.measurements.at(-1).numeric')==-forward
        activate(shop.get_by_role('button', name='关闭模拟电源', exact=True))
        activate(shop.get_by_role('button', name='断电后放电', exact=True))
        activate(frame.locator('[data-repair-focus="probe-clear"]'))
        activate(frame.locator('[data-repair-focus="jack-ma"]'))
        lead('black','GND')
        assert '不能跨接' in frame.locator('#repair-status').inner_text()
        assert shop.get_by_role('button', name='记录一次测量', exact=True).is_disabled()
        activate(frame.locator('[data-repair-focus="mode-current"]'))
        lead('red','SRC')
        lead('black','LOAD')
        activate(frame.locator('[data-repair-focus="series-connect"]'))
        assert frame.evaluate('!!RepairShop.snapshot().active.currentSetup')
        activate(frame.locator('[data-repair-focus="power"]'))
        activate(frame.locator('[data-repair-focus="measure"]'))
        assert frame.evaluate('RepairShop.snapshot().active.measurements.at(-1).mode')=='current'
        activate(frame.locator('[data-repair-focus="series-remove"]'))
        assert frame.evaluate('!!RepairShop.snapshot().active.currentSetup')
        activate(frame.locator('[data-repair-focus="power"]'))
        activate(frame.locator('[data-repair-focus="discharge"]'))
        activate(frame.locator('[data-repair-focus="series-remove"]'))
        assert not frame.evaluate('RepairShop.snapshot().active.currentSetup')
        activate(frame.locator('[data-repair-focus="jack-v"]'))
        activate(shop.locator('[data-repair-focus="target-'+culprit+'"]'))
        activate(shop.get_by_role('button', name='开启模拟电源', exact=True))
        activate(shop.get_by_role('button', name='运行 / 负载读数', exact=True))
        activate(frame.locator('[data-repair-focus="dock-scope"]'))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        activate(shop.get_by_role('button', name='关闭模拟电源', exact=True))
        activate(shop.get_by_role('button', name='断电后放电', exact=True))
        activate(shop.get_by_role('button', name='隔离元件检测', exact=True))
        activate(frame.locator('[data-repair-focus="dock-component"]'))
        activate(shop.get_by_role('button', name='记录一次测量', exact=True))
        assert job['fault']['bad'] in frame.locator('#repair-meter').inner_text()
        assert frame.locator('#repair-diagnosis').input_value() == ''
        frame.locator('#repair-diagnosis').select_option(culprit)
        frame.locator('#repair-reason').select_option(job['fault']['reason'])
        activate(shop.get_by_role('button', name='提交诊断', exact=True))
        assert frame.evaluate('RepairShop.snapshot().active.diagnosed')
        page.screenshot(path=str(OUT / ('public-workbench.png' if args.public else 'local-workbench.png')), full_page=True)
        before = frame.evaluate('RepairShop.snapshot()')
        assert not frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible')
        assert frame.evaluate('RepairShop.sceneSnapshot().componentOpacityMin')>=.8
        activate(frame.locator('[data-repair-focus="board-inspection"]'))
        assert frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible')
        assert frame.evaluate('RepairShop.snapshot()')==before
        page.reload(wait_until='domcontentloaded', timeout=120000)
        frame = find_frame()
        # A resumed unfinished job opens directly, without revealing/preselecting a part.
        shop = frame.locator('#repair-shop')
        assert shop.is_visible()
        after = frame.evaluate('RepairShop.snapshot()')
        assert after['active']['diagnosed'] and after['active']['seed'] == before['active']['seed']
        assert after['coins'] == before['coins']
        assert not frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible'),'Reload restores the solid view, not prior transparency'
        assert frame.evaluate('RepairShop.sceneSnapshot().componentOpacityMin')>=.8
        assert not shop.locator('.rs-stock [aria-pressed=true]').count()
        stock_id = frame.evaluate('''() => {const j=RepairShopEngine.offer(RepairShop.snapshot().active.seed),p=j.product.parts.find(p=>p.id===j.fault.component);return j.candidates.find(c=>!RepairShopEngine.compatible(p,c)).stockId;}''')
        activate(shop.locator('[data-repair-focus="'+stock_id+'"]'))
        if frame.locator('#repair-orientation').count():
            frame.locator('#repair-orientation').select_option('correct')
        activate(shop.locator('[data-repair-focus="install"]'))
        for op in ['remove','clean','orient','place','inspect']:
            activate(shop.locator('[data-repair-focus="repair-'+op+'"]'))
        activate(shop.locator('[data-repair-focus="install-confirm"]'))
        assert frame.evaluate('!!RepairShop.snapshot().active.installed')
        activate(shop.get_by_role('button', name='运行功能与负载测试', exact=True))
        assert '先通电' in frame.locator('#repair-status').inner_text()
        activate(shop.get_by_role('button', name='开启模拟电源', exact=True))
        activate(shop.get_by_role('button', name='运行功能与负载测试', exact=True))
        assert frame.locator('#repair-verification .rs-verification-row').count() == 5
        assert '维修前后对照' in frame.locator('#repair-verification').inner_text()
        assert not frame.evaluate('RepairShop.snapshot().active.finalTested')
        mechanical_steps(False)
        activate(shop.get_by_role('button', name='交付并领取报酬', exact=True))
        done = frame.evaluate('RepairShop.snapshot()')
        assert done['completed'] == 1 and done['points'] == 100 and done['active']['delivered']
        assert frame.locator('#repair-reasoning-chain article').count()==6
        assert frame.locator('#repair-transfer-quiz [aria-pressed=true]').count()==0
        quiz=frame.evaluate('RepairShopLearning.quiz(RepairShopEngine.offer(RepairShop.snapshot().active.seed))')
        wrong=next(o for o in quiz['options'] if not o['correct'])
        right=next(o for o in quiz['options'] if o['correct'])
        activate(frame.locator('[data-repair-focus="review-'+wrong['id']+'"]'))
        assert not frame.evaluate('RepairShop.snapshot().active.review.correct')
        activate(frame.locator('[data-repair-focus="review-'+right['id']+'"]'))
        reviewed=frame.evaluate('RepairShop.snapshot()')
        assert reviewed['active']['review']['correct']
        assert reviewed['coins']==done['coins'] and reviewed['points']==done['points']
        report['manual_probes']='3D red/black contacts, signed voltage, wrong-jack rejection, off/discharged series setup and removal'
        report['transfer_review']='six evidence stages; manual wrong/right answers after delivery, no extra currency'
        assert job['fault']['symptom'] in shop.locator('.rs-settlement').inner_text()
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
                frame.evaluate('''id=>{let seed=1;while(RepairShopEngine.offer(seed).product.id!==id||!RepairShopEngine.offer(seed).fault.enabled)seed++;const s=RepairShopEngine.apply(RepairShopEngine.create(),{type:'accept',seed}).state;localStorage.setItem(RepairShopEngine.KEY,JSON.stringify(s));}''', product_id)
                page.reload(wait_until='domcontentloaded', timeout=120000)
                frame=find_frame()
                frame.wait_for_function('RepairShop.sceneSnapshot() && RepairShop.sceneSnapshot().renderer==="WebGL"')
                assert not frame.evaluate('RepairShop.sceneSnapshot().assembly.boardVisible')
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('finished-'+product_id+'.png')))
                mechanical_steps(True, picking=product_id=='lamp')
                assembly=frame.evaluate('RepairShop.sceneSnapshot().assembly')
                assert assembly['removedOnDesk']=={'cover':True,'brace':True,'board':True,'screws':4},assembly
                assert '零件盘' in frame.locator('#repair-desk-parts').inner_text()
                activate(frame.locator('[data-repair-focus="board-reset"]'))
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('disassembled-'+product_id+'.png')))
                activate(frame.locator('[data-repair-focus="board-focus"]'))
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('diagram-'+product_id+'.png')))
                assert frame.locator('.rs-probe-picker button').count()==3
                canvas=frame.locator('.rs-board-canvas')
                assert canvas.count()==1,'A real WebGL canvas, not the old SVG, is required'
                frame.wait_for_function('document.querySelector(".rs-board-canvas").dataset.textureLoaded==="true"')
                scene=frame.evaluate('RepairShop.sceneSnapshot()')
                assert scene['renderer']=='WebGL' and scene['meshCount']>25 and scene['frames']>0,scene
                original=frame.evaluate('RepairShop.snapshot()')
                canvas.scroll_into_view_if_needed()
                for part_id in scene['projections']:
                    projected=frame.evaluate('RepairShop.sceneSnapshot()')['projections'][part_id]
                    canvas.click(position=projected)
                    assert frame.evaluate('RepairShop.sceneSnapshot().selected')==part_id
                    assert frame.locator('#repair-diagnosis').input_value()==''
                    assert frame.evaluate('RepairShop.snapshot()')==original,'3D picking must not measure, answer or spend'
                assert scene['copper']['version']==1 and scene['copper']['segments']>4
                assert not scene['copper']['projectionVisible']
                assert scene['componentOpacityMin']>=.8
                assert scene['copper']['auxOpacityMin']==1
                assert frame.locator('[data-repair-focus="board-inspection"]').get_attribute('aria-pressed')=='false'
                activate(frame.locator('[data-repair-focus="net-GND"]'))
                assert not frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible'),'Network selection must not turn transparency on'
                activate(frame.locator('[data-repair-focus="net-all"]'))
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('opaque-default-'+product_id+'.png')))
                activate(frame.locator('[data-repair-focus="board-inspection"]'))
                assert frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible')
                assert frame.evaluate('RepairShop.sceneSnapshot().componentOpacityMin')==.24
                assert frame.evaluate('RepairShop.sceneSnapshot().copper.auxOpacityMin')==.28
                activate(frame.locator('[data-repair-focus="net-GND"]'))
                assert frame.evaluate('RepairShop.sceneSnapshot().copper.highlighted')==['GND']
                assert 'J_PWR.GND' in frame.locator('.rs-net-members').inner_text()
                assert frame.evaluate('RepairShop.snapshot()')==original
                samples=frame.evaluate('RepairShop.sceneSnapshot().netProjections')
                assert samples,(product_id,'Need at least one unobscured actual trace pick')
                net=next(iter(samples))
                canvas.scroll_into_view_if_needed()
                canvas.click(position=samples[net])
                assert frame.evaluate('RepairShop.sceneSnapshot().copper.highlighted')==[net],(product_id,net)
                for port_id,position in frame.evaluate('RepairShop.sceneSnapshot().portProjections').items():
                    canvas.click(position=position)
                    expected=frame.evaluate('(p)=>RepairShopBoard.get(RepairShop.sceneSnapshot().product).ports.find(x=>x.id===p).part',port_id)
                    assert frame.evaluate('RepairShop.sceneSnapshot().selected')==expected,(product_id,port_id)
                    assert frame.locator('#repair-diagnosis').input_value()==''
                activate(frame.locator('[data-repair-focus="board-inspection"]'))
                assert not frame.evaluate('RepairShop.sceneSnapshot().copper.projectionVisible')
                assert frame.evaluate('RepairShop.sceneSnapshot().componentOpacityMin')>=.8
                assert frame.evaluate('RepairShop.sceneSnapshot().copper.auxOpacityMin')==1
                activate(frame.locator('[data-repair-focus="board-inspection"]'))
                activate(frame.locator('[data-repair-focus="net-all"]'))
                activate(frame.locator('[data-repair-focus="board-top"]'))
                assert frame.evaluate('RepairShop.sceneSnapshot().elevation')>1.5
                assert frame.evaluate('RepairShop.snapshot()')==original,'Tracing cannot measure, choose diagnosis, spend or alter saved repair'
                frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('copper-'+product_id+'-top.png')))
                canvas.focus()
                yaw=frame.evaluate('RepairShop.sceneSnapshot().yaw')
                canvas.press('ArrowRight')
                assert frame.evaluate('RepairShop.sceneSnapshot().yaw')>yaw
                before_zoom=frame.evaluate('RepairShop.sceneSnapshot().zoom')
                canvas.press('+')
                assert frame.evaluate('RepairShop.sceneSnapshot().zoom')<before_zoom
                activate(frame.locator('[data-repair-focus="board-reset"]'))
                assert abs(frame.evaluate('RepairShop.sceneSnapshot().yaw')+.28)<1e-9
                assert frame.evaluate('RepairShop.sceneSnapshot().zoom')==1
                model=frame.locator('#repair-physical-model')
                assert model.is_visible() and '未建模范围' in model.inner_text()
                assert model.locator('.rs-circuit-netlist').is_visible()
                model.screenshot(path=str(OUT / ('model-'+product_id+'.png')))
                page.set_viewport_size({'width':393,'height':960})
                activate(frame.locator('[data-repair-focus="board-top"]'))
                bounds=frame.evaluate('({width:document.querySelector(".rs-board-canvas").clientWidth,height:document.querySelector(".rs-board-canvas").clientHeight,ports:RepairShop.sceneSnapshot().portProjections})')
                assert all(0<q['x']<bounds['width'] and 0<q['y']<bounds['height'] for q in bounds['ports'].values()),(product_id,bounds)
                sizes=frame.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
                assert sizes['scroll']<=sizes['client']+1,(product_id,sizes)
                if product_id in ['speaker','router']:
                    model.screenshot(path=str(OUT / ('model-phone-'+product_id+'.png')))
                    frame.locator('#repair-shop .rs-board-wrap').screenshot(path=str(OUT / ('copper-phone-'+product_id+'.png')))
                page.set_viewport_size({'width':1440,'height':1080})
            report['six_diagrams']='checked'
            report['finished_and_retained_parts']='all six closed products hide PCB; four screws, cover, brace and board remain on desk after disassembly'
            report['mechanical_raycast']='screwdriver, all four screws, cover, brace and J1 operated with actual 3D picks'
            report['six_physical_models']='v2 visible, netlist/limits and phone containment checked'
            report['six_webgl_boards']='real meshes, raycast selection, camera rotation/zoom/reset; no game-state mutation'
            report['copper_networks']='six explicit graphs; actual copper trace and all three testpoint picks, GND/network highlights, bottom projection toggle, top inspection and phone fit; no game-state mutation'
            report['inspection_default']='six products and resumed repair default solid; explicit click enables transparency; click again restores it; network selection does not auto-enable it'
        assert not errors, errors
        report.update(status='passed',rewards=True,mobile_fit=True,original_lessons=True,errors=errors)
        print(json.dumps(report, ensure_ascii=False), flush=True)
        (OUT / ('public-report.json' if args.public else 'local-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        context.close()
        browser.close()
