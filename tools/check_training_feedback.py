"""Capture and verify concise goals/takeaways and same-condition comparisons."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
for flag in ['before','public','phone']:parser.add_argument('--'+flag,action='store_true')
args=parser.parse_args()
OUT=Path(__file__).resolve().parents[2]/'ocr-diagnostic-20261015/training-feedback'
OUT.mkdir(parents=True,exist_ok=True)
label=('formal' if args.public else 'local')+('-phone' if args.phone else '-desktop')+('-before' if args.before else '-after')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    device={k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'} if args.phone else {'viewport':{'width':1440,'height':1000}}
    ctx=browser.new_context(**device,reduced_motion='reduce');page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        url='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
        page.goto(url,wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+180;reload_at=time.monotonic()+15
        while time.monotonic()<deadline:
            f=next((f for f in page.frames if f.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingPlayground!=="undefined"'):
                if args.before or f.evaluate('typeof TrainingGameFeedback!=="undefined"'):break
            if args.public and time.monotonic()>reload_at:page.reload(wait_until='domcontentloaded',timeout=90000);reload_at=time.monotonic()+15
            page.wait_for_timeout(250)
        else:raise AssertionError('Expected feedback version is not available')
        def press(selector):
            n=f.locator(selector);assert n.count()==1 and n.is_visible() and n.is_enabled(),selector
            if args.phone:
                n.scroll_into_view_if_needed();old=None;stable=0
                for _ in range(20):
                    box=n.bounding_box();stable=stable+1 if box==old else 0
                    if stable>=2:break
                    old=box;page.wait_for_timeout(60)
                n.tap()
            else:n.focus();n.press('Enter')
        def select(family,id):
            press('button[data-course="'+family+'"]');press('button[data-subtype="'+id+'"]');press('[data-learning-target="game"]')
        def snap(base=True):return f.evaluate('TrainingPlayground.current().snapshot()' if base else 'TrainingSubtypeGame.current().snapshot()')
        def fit():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            assert f.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1')
        def capture(name):
            fit();n=f.locator('.play-console');n.scroll_into_view_if_needed();page.wait_for_timeout(200)
            n.screenshot(path=str(OUT/(label+'-'+name+'.png')))
        select('resistor','res-thick');capture('01-cold')
        if not args.before:
            assert f.locator('.play-goal').is_visible() and f.locator('.play-instruction').is_visible()
            assert f.locator('.play-comparison').is_hidden()
            assert f.locator('.play-fixed-condition:visible,.play-outcome:visible,.play-result-title:visible').count()==0
        press('#playground-action');capture('02-learned')
        if not args.before:
            assert '电阻不是电源' in f.locator('.play-goal').inner_text()
            assert f.locator('.play-instruction').is_hidden()
            assert not any(t in f.locator('.play-console').inner_text() for t in ['这关通过','已解锁','本关观察完成','完成了！'])
        press('#playground-next');press('#playground-action');press('[data-play-choice="330"]')
        capture('03-compare')
        if not args.before:
            pair=snap()['comparison'];assert pair['before']['metrics'][0][1]=='3.0 mA'
            assert pair['after']['metrics'][0][1]=='9.1 mA'
            assert pair['after']['brightness']>pair['before']['brightness']
            assert f.locator('.play-comparison').is_visible() and f.locator('.play-comparison-columns>section').count()==2
            before=pair;press('[data-play-choice="330"]');assert snap()['comparison']==before
            press('#playground-action');assert f.locator('.play-comparison').is_hidden()
            press('#playground-action');assert snap()['comparison']==before and f.locator('.play-comparison').is_visible()
            press('[data-play-choice="100"]');assert len(snap()['progress']['cleared'])==2
            press('#playground-next');assert snap()['comparison'] is None and f.locator('.play-comparison').is_hidden()
            chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:!!d.baseline}))')
            for d in chapters:
                select(d['family'],d['id'])
                if d['baseline']:
                    press('[data-play-mode="free"]');assert snap()['comparison'] is None
                    options=f.locator('[data-play-choice]');current=snap()['params']['value']
                    choice=next(n for n in options.all() if n.get_attribute('data-play-choice')!=str(current).lower())
                    press('[data-play-choice="'+choice.get_attribute('data-play-choice')+'"]');press('#playground-action');s=snap()
                else:
                    press('[data-subgame-mode="free"]');assert snap(False)['comparison'] is None
                    option=f.locator('[data-subgame-field][aria-pressed="false"]').first
                    field=option.get_attribute('data-subgame-field');index=option.get_attribute('data-subgame-option')
                    press('[data-subgame-field="'+field+'"][data-subgame-option="'+index+'"]');press('#subgame-action');s=snap(False)
                assert s['comparison'] is not None,d['id']
                assert f.locator('.play-comparison:visible').count()==1,d['id']
                assert f.locator('.play-comparison-columns>section').count()==2
                fit()
                print(json.dumps({'comparison':d['id']}),flush=True)
            for width in [320,1440,393]:
                page.set_viewport_size({'width':width,'height':659 if width<760 else 1000});fit()
            assert not errors,errors
        result={'status':'passed','before':args.before,'public':args.public,'phone_emulation':args.phone,'comparisons':0 if args.before else 30,'errors':errors}
        (OUT/(label+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/(label+'-failure.png')));print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
