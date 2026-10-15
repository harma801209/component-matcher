"""Explicit selection regression using real Chrome gestures, no injected credit.

All 30 cold starts, same-value first picks, mode/reload resets, and the MOS-N
three-stage user report. Phone is iPhone 15 Pro Chrome emulation, not Safari.
"""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--phone', action='store_true')
args = parser.parse_args()
out = Path(__file__).resolve().parents[2] / 'ocr-diagnostic-20261015/training-choices'
out.mkdir(parents=True, exist_ok=True)
label = ('formal' if args.public else 'local') + ('-phone' if args.phone else '-desktop')
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    device = {k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'} if args.phone else {'viewport': {'width':1440,'height':1000}}
    context = browser.new_context(**device)
    page = context.new_page(); errors = []
    page.on('pageerror', lambda e:errors.append(str(e)))
    url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
    def load():
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        deadline=time.monotonic()+180; again=time.monotonic()+15
        while time.monotonic()<deadline:
            frame=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if frame and frame.evaluate('typeof TrainingGameChoices!=="undefined"') and frame.locator('#playground-action').count():return frame
            if args.public and time.monotonic()>again:
                page.reload(wait_until='domcontentloaded',timeout=90000);again=time.monotonic()+15
            page.wait_for_timeout(200)
        raise AssertionError('Explicit-choice release not available')
    f=load()
    def press(selector):
        n=f.locator(selector);assert n.count()==1 and n.is_visible() and n.is_enabled(),selector
        if args.phone:
            n.scroll_into_view_if_needed();old=None;stable=0
            for _ in range(20):
                rect=n.bounding_box();stable=stable+1 if rect==old else 0
                if stable>=2:break
                old=rect;page.wait_for_timeout(60)
            n.tap()
        else:n.focus();n.press('Enter')
    def select(d):
        press('button[data-course="'+d['family']+'"]');press('button[data-subtype="'+d['id']+'"]');press('[data-learning-target="game"]')
    def state(base):return f.evaluate(('TrainingPlayground' if base else 'TrainingSubtypeGame')+'.current().snapshot()')
    def pending(base):
        s=state(base);assert s['selection']=={}
        selector='[data-play-choice]' if base else '[data-subgame-field]'
        assert f.locator(selector+'[aria-pressed="true"]').count()==0
        required=f.locator('.play-tray').is_visible() if base else any(g.is_visible() for g in f.locator('.subgame-field').all())
        assert f.locator('#playground-action' if base else '#subgame-action').is_disabled()==required
        assert not s['playing'] and not (s['params']['power'] if base else s['progress']['started'])
        if not base:assert all(x=='—' for x in f.locator('.subgame-metrics strong').all_text_contents())
        return s
    def pick_current(d):
        base=d['baseline'];s=state(base)
        if base:
            if f.locator('.play-tray').is_visible():press('[data-play-choice="'+str(s['params']['value']).lower()+'"]')
        else:
            for group in f.locator('.subgame-field').all():
                if not group.is_visible():continue
                key=group.get_attribute('data-beginner-field');value=s['progress']['params'][key]
                i=f.evaluate('''({id,key,value})=>TrainingSubtypeGameMath.profile(id).fields.find(f=>f.key===key).options.findIndex(o=>o[0]===value)''',{'id':d['id'],'key':key,'value':value})
                press('[data-subgame-field="'+key+'"][data-subgame-option="'+str(i)+'"]')
        assert f.locator('#playground-action' if base else '#subgame-action').is_enabled()
        after=state(base);assert after['params' if base else 'progress']==s['params' if base else 'progress']
    def capture(name):f.locator('.play-console').screenshot(path=str(out/(label+'-'+name+'.png')))
    chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:!!d.baseline}))')
    for d in chapters:
        select(d);before=pending(d['baseline']);pick_current(d)
        if d['id'] in ['res-thick','res-sense','mos-n']:
            prefix='data-play-mode' if d['baseline'] else 'data-subgame-mode'
            press('['+prefix+'="free"]');pending(d['baseline']);pick_current(d)
            press('['+prefix+'="challenge"]');pending(d['baseline'])
        assert state(d['baseline'])['progress']['cleared']==before['progress']['cleared']
        print(json.dumps({'cold_unselected':d['id'],'same_value_pick':True}),flush=True)
    mos=next(d for d in chapters if d['id']=='mos-n');select(mos)
    for index,option in [(0,2),(1,1)]:
        pending(False);press('[data-subgame-field="drive"][data-subgame-option="'+str(option)+'"]')
        press('#subgame-action');f.locator('.play-viewport').scroll_into_view_if_needed()
        f.wait_for_function('n=>TrainingSubtypeGame.current().snapshot().progress.cleared.length===n',arg=index+1,timeout=12000)
        press('#subgame-action');press('#subgame-next')
    s=pending(False);assert s['progress']['index']==2 and s['progress']['params']['load']==3
    assert '题设固定' in f.locator('.play-console>.play-fixed-condition').inner_text()
    capture('mos-third-unselected')
    press('[data-subgame-field="load"][data-subgame-option="2"]')
    assert state(False)['selection']=={'load':3}
    assert f.locator('[data-subgame-field="load"][data-subgame-option="2"]').get_attribute('aria-pressed')=='true'
    press('#subgame-action');f.locator('.play-viewport').scroll_into_view_if_needed()
    f.wait_for_function('TrainingSubtypeGame.current().snapshot().progress.observed>=1',timeout=12000)
    assert state(False)['progress']['cleared']==[0,1]
    press('[data-subgame-field="load"][data-subgame-option="0"]');f.locator('.play-viewport').scroll_into_view_if_needed()
    f.wait_for_function('TrainingSubtypeGame.current().snapshot().progress.cleared.length===3',timeout=12000)
    assert state(False)['selection']=={'load':1};capture('mos-third-passed')
    press('[data-subgame-level="0"]');pending(False);assert state(False)['progress']['cleared']==[0,1,2]
    f=load();select(mos);pending(False);assert state(False)['progress']['cleared']==[0,1,2]
    res=next(d for d in chapters if d['id']=='res-thick');select(res);pending(True)
    press('#playground-action');f.wait_for_function('TrainingPlayground.current().snapshot().progress.cleared.length===1')
    press('#playground-next');pending(True);capture('resistor-next-unselected')
    press('[data-play-choice="1000"]');assert state(True)['selection']=={'value':1000}
    press('#playground-action');assert state(True)['progress']['cleared']==[0]
    press('[data-play-choice="100"]');f.wait_for_function('TrainingPlayground.current().snapshot().progress.cleared.length===2')
    press('#playground-next');pending(True)
    assert not errors,errors
    report={'status':'passed','chapters':len(chapters),'all_fresh_choices_empty':True,'same_value_explicit_picks':True,'wrong_pick_not_passed':True,'mos_three_missions':True,'next_review_reload_mode_reset':True,'script_errors':errors}
    (out/(label+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
    context.close();browser.close()
