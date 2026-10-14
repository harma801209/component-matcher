"""Mobile game flow and responsive node restoration, using native Chrome touch.

iPhone 15 Pro descriptor (393x659 content viewport/DPR3); no real Safari claim.
"""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
parser.add_argument('--quick',action='store_true')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'ocr-diagnostic-20261014/training-mobile-layout'
OUT.mkdir(parents=True,exist_ok=True)
prefix='formal' if args.public else 'local'
URL='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
records=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    device={k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'}
    ctx=browser.new_context(**device,reduced_motion='reduce')
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto(URL,wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+150;f=None
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingPlaygroundLayout!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f and f.evaluate('typeof TrainingPlaygroundLayout!=="undefined"'),'Updated mobile layout unavailable'
        def tap(selector):
            n=f.locator(selector);assert n.count()==1 and n.is_visible(),selector
            n.scroll_into_view_if_needed();last=None;steady=0
            for _ in range(20):
                box=n.bounding_box();steady=steady+1 if box==last else 0
                if steady>=2:break
                last=box;page.wait_for_timeout(80)
            n.tap()
        def select(family,id):
            tap('button[data-course="'+family+'"]');tap('button[data-subtype="'+id+'"]')
            tap('[data-learning-target="game"]')
        def metrics():
            return f.evaluate('''()=>{const rect=s=>document.querySelector(s).getBoundingClientRect();const v=rect('.play-viewport'),t=rect('.play-tray'),a=rect('.play-action-row');return {workbench:rect('.play-workbench').height,board:v.height,board_to_choices:t.top-v.bottom,board_to_action:a.top-v.bottom,core_span:a.bottom-v.top,console:rect('.play-console').height};}''')
        def capture(name):
            f.locator('.play-mission').evaluate('e=>e.scrollIntoView({block:"start"})')
            page.wait_for_timeout(200)
            page.screenshot(path=str(OUT/f'{prefix}-{name}.png'))
            f.locator('.play-stage').screenshot(path=str(OUT/f'{prefix}-{name}-stage.png'))
        def fit():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            bounds=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
            assert bounds['w']<=bounds['c']+1 and bounds['h']<=bounds['v']+1,bounds
            assert f.frame_element().get_attribute('scrolling')=='no'
            assert f.locator('.play-console').evaluate('e=>getComputedStyle(e).overflowY!=="auto"&&e.scrollHeight<=e.clientHeight+1')
        select('resistor','res-thick')
        capture('01-start');fit()
        assert f.locator('#playground-action').bounding_box()['y']+f.locator('#playground-action').bounding_box()['height']<=659
        tap('#playground-action');assert f.evaluate('TrainingPlayground.current().snapshot().playing')
        tap('#playground-next');capture('02-choose');fit()
        assert f.locator('[data-play-choice="100"]').bounding_box()['y']+f.locator('[data-play-choice="100"]').bounding_box()['height']<=659
        tap('[data-play-choice="100"]');capture('03-completed');fit()
        m=metrics();assert m['board_to_choices']<160,m
        assert m['core_span']<600,m
        assert f.locator('#playground-next').bounding_box()['y']+f.locator('#playground-next').bounding_box()['height']<=659
        assert f.locator('.play-mobile-explanation .play-cause').count()==1
        assert not f.locator('.play-mobile-explanation').get_attribute('open')
        assert f.locator('.play-board-column .play-cause').count()==0
        tap('.play-mobile-explanation>summary')
        assert f.locator('.play-cause').is_visible()
        assert '90.0 mW' in f.locator('.play-cause').inner_text()
        assert '30.0 mA' in f.locator('.play-cause').inner_text()
        assert f.locator('.play-mobile-explanation .play-beginner-intro').is_visible()
        fit();f.locator('.play-mobile-explanation').screenshot(path=str(OUT/f'{prefix}-04-explanation.png'))
        tap('.play-mobile-explanation>summary')
        # Same nodes, live values and progress after a phone rotation / desktop resize.
        saved=f.evaluate('TrainingPlayground.current().snapshot().progress.cleared')
        page.set_viewport_size({'width':900,'height':659})
        f.wait_for_function('document.getElementById("playground").dataset.mobileLayout==="desktop"')
        assert f.locator('.play-board-column>.play-cause').is_visible()
        assert f.locator('.play-console>.play-beginner-intro').is_visible()
        assert f.locator('.play-mobile-explanation').is_hidden()
        assert f.evaluate('TrainingPlayground.current().snapshot().progress.cleared')==saved
        page.set_viewport_size({'width':393,'height':659})
        f.wait_for_function('document.getElementById("playground").dataset.mobileLayout==="compact"')
        assert f.locator('.play-mobile-explanation .play-cause').count()==1
        assert f.evaluate('TrainingPlayground.current().snapshot().result.current')==.03
        chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:d.baseline}))')
        if args.quick:chapters=[d for d in chapters if d['id'] in ('res-thick','cap-mlcc','ind-wound','dio-switch','xtal-active','mos-n','bjt-digital')]
        for d in chapters:
            select(d['family'],d['id']);fit()
            console=f.locator('.play-console');panel=f.locator('.play-mobile-explanation')
            assert console.count()==1 and panel.count()==1 and panel.is_visible(),d
            assert f.locator('.play-stage .play-viewport').count()==1,d
            assert not panel.get_attribute('open'),d
            assert console.locator('.play-action-row').count()==1,d
            assert panel.locator('button').count()==0,d
            assert f.locator('.play-level-nav').evaluate('e=>e.getBoundingClientRect().height<=45'),d
            assert all(n.evaluate('e=>e.getBoundingClientRect().height>=44') for n in console.locator('button:visible').all()),d
            assert f.locator('.play-viewport').evaluate('e=>e.getBoundingClientRect().height===230'),d
            if not d['baseline']:
                assert panel.locator('.subgame-metrics').count()==1,d
                assert console.locator('.subgame-fields').is_visible(),d
            if d['id'] in ('cap-mlcc','xtal-active','mos-n','bjt-digital'):
                capture(d['id'])
            records.append(d['id'])
        assert not errors,errors
        result={'status':'passed','public':args.public,'phone_descriptor':'iPhone 15 Pro / Chrome emulation','chapters':len(records),'metrics':m,'restored_same_nodes_progress':True,'host_only_scroll':True,'targets_44px':True,'errors':errors}
        (OUT/f'{prefix}-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'))
        print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
