"""Adversarial native learner flows; no injected credit, time or business data."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser()
for flag in ['before','public','phone','fallback']:parser.add_argument('--'+flag,action='store_true')
args=parser.parse_args()
OUT=Path(__file__).resolve().parents[2]/'ocr-diagnostic-20261015/game-audit'
OUT.mkdir(parents=True,exist_ok=True)
label=('formal' if args.public else 'local')+('-phone' if args.phone else '-desktop')+('-before' if args.before else '-after')+('-fallback' if args.fallback else '')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    device={k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'} if args.phone else {'viewport':{'width':1440,'height':1000}}
    ctx=browser.new_context(**device,reduced_motion='reduce')
    if args.fallback:ctx.add_init_script('const old=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(k,...a){return /webgl/i.test(k)?null:old.call(this,k,...a);};')
    page=ctx.new_page();errors=[];findings={};page.on('pageerror',lambda e:errors.append(str(e)))
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
    def state(base=True):return f.evaluate('TrainingPlayground.current().snapshot()' if base else 'TrainingSubtypeGame.current().snapshot()')
    def board():f.locator('.play-viewport').scroll_into_view_if_needed()
    def capture(name,selector='.play-console'):
        f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
        n=f.locator(selector);n.scroll_into_view_if_needed();page.wait_for_timeout(180);n.screenshot(path=str(OUT/(label+'-'+name+'.png')))
        if not args.before:
            for b in f.locator('.nightlight-actions button:visible').all():
                box=b.bounding_box();assert 44<=box['height']<=60,(name,b.inner_text(),box)
                if b.get_attribute('id'):assert box['width']>=110,(name,b.inner_text(),box)
            assert f.evaluate('document.documentElement.scrollWidth<=innerWidth'),name
    def record(key,bug):
        findings[key]=bug;assert bug if args.before else not bug,(key,bug)
        print(json.dumps({key:bug}),flush=True)
    def wait_clear(base,count):
        board();kind='TrainingPlayground' if base else 'TrainingSubtypeGame'
        f.wait_for_function('count=>'+kind+'.current().snapshot().progress.cleared.length===count',arg=count,timeout=10000)
        page.wait_for_timeout(120)
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/',wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+180;reload_at=time.monotonic()+15
        while time.monotonic()<deadline:
            f=next((f for f in page.frames if f.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingGameFeedback!=="undefined"'):
                if args.before or f.evaluate('TrainingPlayground.current().snapshot().canReplayCompleted===true'):break
            if args.public and time.monotonic()>reload_at:page.reload(wait_until='domcontentloaded',timeout=90000);reload_at=time.monotonic()+15
            page.wait_for_timeout(250)
        else:raise AssertionError('Audit version not loaded')
        select('resistor','res-thick');capture('01-entry')
        select('capacitor','cap-mlcc');press('[data-play-mode="free"]');press('#playground-action');press('#playground-task');board()
        f.wait_for_function('TrainingPlayground.current().snapshot().phase>1.2',timeout=6000)
        selected=f.locator('[data-play-choice][aria-pressed="true"]');selected.scroll_into_view_if_needed();page.wait_for_timeout(180)
        phase=state()['phase'];assert phase>1
        value=selected.get_attribute('data-play-choice');press('[data-play-choice="'+value+'"]')
        record('same_cap_choice_restarts_pulse',state()['phase']<phase);capture('02-same-cap-choice')
        select('resistor','res-thin');press('[data-subgame-mode="free"]');press('#subgame-action');board()
        f.wait_for_function('TrainingSubtypeGame.current().snapshot().progress.observed>.6',timeout=6000)
        option=f.locator('[data-subgame-field][aria-pressed="true"]').first;option.scroll_into_view_if_needed();page.wait_for_timeout(180)
        observed=state(False)['progress']['observed'];key=option.get_attribute('data-subgame-field');index=option.get_attribute('data-subgame-option')
        press('[data-subgame-field="'+key+'"][data-subgame-option="'+index+'"]')
        record('same_condition_restarts_timer',state(False)['progress']['observed']<observed);capture('03-same-condition')
        select('capacitor','cap-mlcc');press('[data-play-mode="challenge"]');press('#playground-action');press('#playground-task');wait_clear(True,1)
        press('#playground-action');press('#playground-action')
        record('completed_mlcc_cannot_replay',not f.locator('#playground-task').is_visible());capture('04-completed-cap-replay')
        if not args.before:press('#playground-task');assert state()['phase']>=1 and len(state()['progress']['cleared'])==1
        # Unlock the product by completing only its 13 real prerequisites.
        select('resistor','res-thick')
        for i in range(4):
            if i:press('[data-play-choice="'+str([330,100,330,1000][i])+'"]')
            press('#playground-action');wait_clear(True,i+1)
            if i<3:press('#playground-next')
        for family,id in [('diode','dio-schottky'),('capacitor','cap-aluminum'),('mos','mos-n')]:
            select(family,id)
            for i in range(3):
                winner=f.evaluate('''({id,index})=>{const d=TrainingSubtypeGameMath.profile(id),l=d.missions[index],allowed=TrainingBeginner.supported(id)?TrainingBeginner.fields(id,index):d.fields.map(f=>f.key);let values=[{params:{...l.setup},indices:{}}];for(const field of d.fields.filter(f=>allowed.includes(f.key)))values=values.flatMap(o=>field.options.map(([v],i)=>({params:{...o.params,[field.key]:v},indices:{...o.indices,[field.key]:i}})));return values.find(o=>l.check(o.params,TrainingSubtypeGameMath.evaluate(id,o.params).values)).indices;}''',{'id':id,'index':i})
                for key,index in winner.items():press('[data-subgame-field="'+key+'"][data-subgame-option="'+str(index)+'"]')
                press('#subgame-action');wait_clear(False,i+1)
                if i<2:press('#subgame-next')
        assert f.evaluate('TrainingGameProgress.eligible("nightlight")');press('#game-projects')
        night=lambda:f.evaluate('TrainingNightlight.current().snapshot()')
        choose=lambda key,v:press('[data-nightlight-field="'+key+'"][data-nightlight-value="'+str(v).lower()+'"]')
        choose('resistance',330);press('#nightlight-power');assert night()['state']['cleared']==1
        press('[data-nightlight-level="0"]');record('completed_product_review_hides_parts',not f.locator('.nightlight-options').is_visible());capture('05-product-review','.nightlight-console')
        if not args.before:
            choose('resistance',1000);press('#nightlight-power');assert night()['result']['current']==.003 and night()['state']['cleared']==1
        press('#nightlight-action');choose('resistance',330);press('#nightlight-power');press('#nightlight-action')
        choose('diode','forward');press('#nightlight-power');press('#nightlight-action');assert night()['state']['reverse']
        choose('diode','forward');record('same_diode_choice_changes_supply',not night()['state']['reverse']);capture('06-same-diode-choice','.nightlight-console')
        if not night()['state']['reverse']:press('#nightlight-action')
        press('#nightlight-action');assert night()['state']['cleared']==3;press('#nightlight-action')
        choose('capacitance',.01);press('#nightlight-power');press('#nightlight-power');f.locator('.nightlight-viewport').scroll_into_view_if_needed()
        f.wait_for_function('TrainingNightlight.current().snapshot().state.cleared===4',timeout=6000)
        press('#nightlight-action');choose('mos',True);press('#nightlight-power')
        for _ in range(3):press('#nightlight-action')
        assert night()['state']['cleared']==5;press('#nightlight-power')
        record('off_product_gate_button_enabled',f.locator('#nightlight-action').is_enabled());capture('07-product-power-off','.nightlight-console')
        if not args.before:
            press('#nightlight-power');press('#nightlight-action');assert night()['result']['current']==0
            press('#nightlight-action');assert night()['result']['current']>0 and night()['state']['cleared']==5
            press('[data-nightlight-level="2"]');choose('diode','forward');press('#nightlight-power');press('#nightlight-experiment')
            assert night()['state']['reverse'] and night()['result']['current']==0
            press('#nightlight-experiment');assert not night()['state']['reverse'] and night()['result']['current']>0
            assert night()['state']['cleared']==5;capture('08-protection-review','.nightlight-console')
            if args.phone:
                page.set_viewport_size({'width':320,'height':640});capture('09-narrow-protection-review','.nightlight-console')
            page.reload(wait_until='domcontentloaded',timeout=90000)
            f=next((f for f in page.frames if f.locator('#training-app').count()),None)
            if not f:
                page.wait_for_timeout(1500);f=next(f for f in page.frames if f.locator('#training-app').count())
            assert f.evaluate('TrainingGameProgress.eligible("nightlight")')
        assert not errors,errors
        result={'status':'passed','before':args.before,'public':args.public,'phone_emulation':args.phone,'fallback':args.fallback,'findings':findings,'errors':errors}
        (OUT/(label+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/(label+'-failure.png')));print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
