"""Follow only the displayed teaching prompts through one real browser repair."""
import argparse
import json
import platform
import re
import time
from pathlib import Path

platform._wmi=None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
OUT=Path(__file__).resolve().parents[2]/'repair-shop-qa'
OUT.mkdir(exist_ok=True)
tag='coach-public' if args.public else 'coach-local'
url='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8558/'

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1080},device_scale_factor=1)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        def frame_now():
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                for f in page.frames:
                    try:
                        if f.locator('.academy-switch').count() and f.evaluate("typeof RepairShopPhysics!=='undefined' && RepairShopPhysics.VERSION===2"):
                            return f
                    except Exception:
                        pass
                page.wait_for_timeout(400)
            raise AssertionError('New teaching assets did not load')

        def activate(locator):
            locator.focus()
            locator.press('Enter')

        def snapshot():
            return frame.evaluate('RepairShop.snapshot()')

        def contains_page():
            widths=frame.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert widths['scroll']<=widths['client']+1,widths

        def capture(panel,name):
            if args.public:
                frame.wait_for_function('!window.frameElement || parseFloat(window.frameElement.style.height)>=document.querySelector("#training-app").getBoundingClientRect().height',timeout=15000)
                panel.scroll_into_view_if_needed()
                page.screenshot(path=str(OUT/(tag+name)))
            else:
                panel.screenshot(path=str(OUT/(tag+name)))

        page.goto(url,wait_until='domcontentloaded',timeout=120000)
        frame=frame_now()
        activate(frame.get_by_role('button',name='电子维修店',exact=True))
        activate(frame.get_by_role('button',name='新手教学 · 一步步带着做',exact=True))
        activate(frame.get_by_role('button',name='接下这单',exact=False).first)
        assert frame.locator('#repair-coach').is_visible()
        assert frame.locator('#repair-diagnosis').input_value()==''
        assert frame.locator('#repair-reason').input_value()==''
        assert frame.locator('.rs-probe-picker [data-evidence="unknown"]').count()==3
        assert frame.locator('#repair-verification').count()==0
        before=snapshot()
        activate(frame.get_by_role('button',name='师傅提示',exact=True))
        hint=frame.locator('#repair-case-hints')
        assert hint.locator('.rs-hint-grid article').count()==4
        assert '可能坏在哪里' in hint.inner_text()
        assert '如何检测出来' in hint.inner_text()
        assert '如何维修和验收' in hint.inner_text()
        assert snapshot()['coins']==before['coins'] and snapshot()['points']==before['points']
        assert not snapshot()['active']['diagnosed']
        activate(hint.locator('summary'))
        assert hint.locator('.rs-hint-detail').get_attribute('open') is not None
        assert hint.locator('.rs-hint-detail article').count()==4
        page.set_viewport_size({'width':393,'height':960})
        contains_page()
        capture(frame.locator('#repair-coach'),'-phone-instruction.png')
        capture(hint.get_by_role('heading',name='师傅提示 · 当前工单的维修思路'),'-phone-hints.png')
        before_return=snapshot()
        activate(hint.get_by_role('button',name='回到维修操作',exact=True))
        assert snapshot()==before_return,'Returning from hints must not execute a repair'
        assert frame.locator('#repair-case-hints').count()==0
        assert frame.evaluate('document.activeElement.classList.contains("rs-coach-target")')
        assert frame.locator('#repair-coach-mini').is_visible()
        traversed=[]
        resumed=False
        checked_stock=False
        chose_diagnosis=False
        evidence_seen=False
        comparison_seen=False
        for number in range(80):
            guide=frame.locator('#repair-coach')
            step=guide.get_attribute('data-step')
            target=guide.get_attribute('data-target')
            instruction=guide.inner_text()
            traversed.append(step)
            assert guide.locator('h3').inner_text()
            if step=='complete':
                break
            if not chose_diagnosis:
                assert frame.locator('#repair-diagnosis').input_value()==''
            if step=='deliver':
                report=frame.locator('#repair-verification')
                assert report.locator('.rs-verification-row').count()==5
                assert '验收计算值' in report.inner_text()
                assert frame.locator('.rs-probe-picker [data-evidence="repaired"]').count()==1
                page.set_viewport_size({'width':393,'height':960})
                contains_page()
                capture(report,'-phone-comparison.png')
                page.set_viewport_size({'width':1440,'height':1080})
                comparison_seen=True
            if step.startswith('diagnosis-') and not resumed:
                saved=snapshot()
                page.reload(wait_until='domcontentloaded',timeout=120000)
                frame=frame_now()
                assert frame.locator('#repair-coach').is_visible()
                assert snapshot()['active']['seed']==saved['active']['seed']
                assert snapshot()['coins']==saved['coins']
                resumed=True
                chose_diagnosis=False
                continue
            state_before=snapshot()
            activate(guide.get_by_role('button',name='带我找到这一步',exact=True))
            assert snapshot()==state_before,'Locating a control must not execute it'
            focus=frame.evaluate('({id:document.activeElement.id,key:document.activeElement.dataset.repairFocus,marked:document.activeElement.classList.contains("rs-coach-target")})')
            assert focus['marked'],focus
            assert focus['id']==target.removeprefix('id:') if target.startswith('id:') else focus['key']==target
            if target.startswith('id:'):
                control=frame.locator('#'+target[3:])
                options=control.locator('option').all_text_contents()[1:]
                if step=='diagnosis-id':
                    code=re.search(r'选择 ([A-Z]\d)',instruction).group(1)
                    label=next(label for label in options if label.startswith(code+' '))
                    chose_diagnosis=True
                elif step=='diagnosis-reason':
                    label=next(label for label in options if '“'+label+'”' in instruction)
                else:
                    label='与本板A/K或正负极标记一致'
                control.select_option(label=label)
            elif target=='stock-list':
                if not checked_stock:
                    activate(frame.get_by_role('button',name=re.compile('^相近规格备件')))
                    assert frame.locator('#repair-coach').get_attribute('data-step')=='stock-mismatch'
                    assert snapshot()['coins']==state_before['coins']
                    checked_stock=True
                activate(frame.get_by_role('button',name=re.compile('^原规格备件')))
            else:
                activate(frame.locator('[data-repair-focus="'+target+'"]'))
                if target=='measure':
                    assert frame.locator('#repair-meter-feedback').is_visible()
                    assert frame.locator('.rs-notebook [data-reading-phase="before"]').count()>0
                    evidence_seen=True
            contains_page()
            if number==8:
                frame.locator('#repair-coach-mini').screenshot(path=str(OUT/(tag+'-phone-tools-guide.png')))
                page.set_viewport_size({'width':1440,'height':1080})
        else:
            raise AssertionError('Teaching loop did not complete: '+str(traversed))
        done=snapshot()
        assert done['completed']==1 and done['points']==100,done
        assert done['active']['delivered']
        assert resumed and checked_stock
        assert evidence_seen and comparison_seen
        frame.locator('#repair-coach').screenshot(path=str(OUT/(tag+'-complete.png')))
        assert not errors,errors
        report={'status':'passed','public':args.public,'followed_visible_prompts':traversed,'free_hints':True,'resume':True,'no_auto_actions':True,'manual_diagnosis':True,'evidence_feedback':evidence_seen,'before_after_report':comparison_seen,'wrong_stock_explained':True,'phone_containment':True,'points':done['points'],'errors':errors}
        (OUT/(tag+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    finally:
        context.close()
        browser.close()
