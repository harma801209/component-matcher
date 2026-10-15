"""Single power-button acceptance via native Chrome; no injected progress/answers.

--full plays all 94 existing missions and the prerequisite-gated product chapter.
Default checks all 30 cold-start/on/off flows. --phone uses native touch at
iPhone 15 Pro dimensions, not physical Safari. --fallback covers the UI without
WebGL. Business databases are never opened by this tool.
"""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
for flag in ['public','phone','full','fallback']:parser.add_argument('--'+flag,action='store_true')
parser.add_argument('--requirements-only',action='store_true',help='Play the 13 real prerequisite missions and all 5 product stages')
args=parser.parse_args()
OUT=Path(__file__).resolve().parents[2]/'ocr-diagnostic-20261015/training-power'
OUT.mkdir(parents=True,exist_ok=True)
label=('formal' if args.public else 'local')+('-phone' if args.phone else '-desktop')+('-fallback' if args.fallback else '')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    device={k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'} if args.phone else {'viewport':{'width':1440,'height':1000}}
    ctx=browser.new_context(**device,reduced_motion='reduce')
    if args.fallback:ctx.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...rest){return /webgl/i.test(kind)?null:original.call(this,kind,...rest);};")
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    URL='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
    def load():
        page.goto(URL,wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+180;again=time.monotonic()+15
        while time.monotonic()<deadline:
            frame=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if frame and frame.evaluate('typeof TrainingPlayground!=="undefined"&&typeof TrainingGameChoices!=="undefined"') and frame.locator('#playground-action[aria-pressed]').count() and not frame.locator('.play-controls').count():return frame
            if args.public and time.monotonic()>again:
                page.reload(wait_until='domcontentloaded',timeout=90000);again=time.monotonic()+15
            page.wait_for_timeout(250)
        raise AssertionError('Single-power release not available')
    f=load();cases=[];missions=0;trials=0
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
    def state(base):return f.evaluate('TrainingPlayground.current().snapshot()' if base else 'TrainingSubtypeGame.current().snapshot()')
    def on(base):return state(base)['params']['power'] if base else state(base)['progress']['started']
    questions={}
    def question(base):
        data=f.evaluate('''base=>{const s=base?TrainingPlayground.current().snapshot():TrainingSubtypeGame.current().snapshot();if(s.mode!=="challenge")return null;const p=s.progress,l=base?TrainingPlaygroundLevels.level(p.course,p.index):TrainingSubtypeGameMath.level(s.id,p.index);return {key:(base?p.course:s.id)+":"+p.index,goal:base?TrainingGameFeedback.goal(p.course,p.index,l.goal):l.goal,learned:l.learned,done:p.cleared.includes(p.index)};}''',base)
        if data is None:
            assert f.locator('.play-takeaway').is_hidden();return
        f.wait_for_function('''d=>{const q=document.querySelector(".play-goal"),p=document.querySelector(".play-takeaway");return q&&!q.hidden&&q.textContent===d.goal&&p&&p.hidden===!d.done&&(!d.done||p.querySelector("p").textContent===d.learned);}''',arg=data,timeout=3000)
        actual=f.locator('.play-goal').inner_text();assert actual==questions.setdefault(data['key'],actual)
        assert f.locator('.play-goal').is_visible() and f.locator('.play-console>h4').inner_text()=='本关目标'
        if data['done']:assert f.locator('.play-takeaway').is_visible()
    def fresh_choices(base):
        assert state(base)['selection']=={}
        selector='[data-play-choice]' if base else '[data-subgame-field]'
        assert f.locator(selector+'[aria-pressed="true"]').count()==0
        button=f.locator('#playground-action' if base else '#subgame-action')
        required=f.locator('.play-tray').is_visible() if base else any(g.is_visible() for g in f.locator('.subgame-field').all())
        assert button.is_disabled()==required
    def toggle(base):
        if not on(base):
            if base:
                if f.locator('#playground-action').is_disabled():base_choice(state(True)['params']['value'])
            else:
                for group in f.locator('.subgame-field').all():
                    if not group.is_visible() or group.locator('[aria-pressed="true"]').count():continue
                    field=group.get_attribute('data-beginner-field');value=state(False)['progress']['params'][field]
                    option=f.evaluate('''({id,key,value})=>TrainingSubtypeGameMath.profile(id).fields.find(f=>f.key===key).options.findIndex(o=>o[0]===value)''',{'id':state(False)['id'],'key':field,'value':value})
                    press('[data-subgame-field="'+field+'"][data-subgame-option="'+str(option)+'"]')
        press('#playground-action' if base else '#subgame-action')
    def visible_board(base):
        f.locator('.play-viewport').scroll_into_view_if_needed();page.wait_for_timeout(80)
    def fit():
        f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
        dims=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
        assert dims['w']<=dims['c']+1 and dims['h']<=dims['v']+1,dims
        assert f.frame_element().get_attribute('scrolling')=='no'
    def structure(base):
        assert not f.locator('.play-controls,#playground-pause,#playground-speed,#playground-reset,#subgame-pause,#subgame-speed,#subgame-reset').count()
        n=f.locator('#playground-action' if base else '#subgame-action');assert n.is_visible()
        assert n.inner_text()==('关闭电源' if on(base) else '打开电源')
        assert n.get_attribute('aria-pressed')==str(on(base)).lower()
        assert n.bounding_box()['height']>=44
        for e in f.locator('.play-scene-caption,.play-scene-readout').all():
            assert e.evaluate('e=>{const r=e.getBoundingClientRect(),c=document.querySelector(".play-viewport canvas").getBoundingClientRect();return r.bottom<=c.top+1||r.top>=c.bottom-1;}')
        if not on(base):question(base)
        fit()
    def capture(name,selector='.play-console'):
        fit();f.locator(selector).scroll_into_view_if_needed();page.wait_for_timeout(200)
        f.locator(selector).screenshot(path=str(OUT/(label+'-'+name+'.png')))
    def wait_clear(base,count,timeout=12000):
        visible_board(base)
        expression='TrainingPlayground.current().snapshot().progress.cleared.length' if base else 'TrainingSubtypeGame.current().snapshot().progress.cleared.length'
        f.wait_for_function('n=>'+expression+'===n',arg=count,timeout=timeout)
        # Grade and DOM paint are separate frames; retain the original question
        # and show the takeaway separately after the real completion is painted.
        question(base);assert f.locator('.play-instruction').is_hidden()
    def check_cycle(d):
        base=d['baseline'];select(d);assert not on(base) and not state(base)['playing'];fresh_choices(base);structure(base)
        if not args.fallback:
            assert state(base)['scene']['markers']==0
            phase=state(base)['scene']['phase'];page.wait_for_timeout(200);assert state(base)['scene']['phase']==phase
        if d['id']=='res-thick':capture('01-cold');capture('01-board','.play-board-column')
        toggle(base);assert on(base) and state(base)['playing'];structure(base);visible_board(base)
        if not args.fallback:
            phase=state(base)['scene']['phase']
            live='TrainingPlayground' if base else 'TrainingSubtypeGame'
            # Scroll/iframe visibility and GPU scheduling need not settle in
            # exactly 250 ms. Require an actual advancing frame, not a sleep.
            f.wait_for_function('phase=>'+live+'.current().snapshot().scene.phase>phase',arg=phase,timeout=6000)
        if d['id']=='res-thick':
            expected=f"{state(base)['result']['current']*1000:.1f} mA"
            assert expected in f.locator('.play-hud').inner_text();capture('02-powered')
        cleared=state(base)['progress']['cleared']
        toggle(base);assert not on(base) and not state(base)['playing'];structure(base)
        # Native touch can finish a valid observation while scrolling to power.
        # Turning it off must retain every credit earned before the gesture.
        assert set(cleared)<=set(state(base)['progress']['cleared'])
        if not args.fallback:
            phase=state(base)['scene']['phase'];assert state(base)['scene']['markers']==0
            page.wait_for_timeout(250);assert state(base)['scene']['phase']==phase
        if d['id']=='res-thick':assert '0.0 mA' in f.locator('.play-hud').inner_text();capture('03-off')
        cases.append(d['id'])
        print(json.dumps({'power_cycle':d['id'],'checked':len(cases)}),flush=True)
    def base_choice(value):press('[data-play-choice="'+str(value).lower()+'"]')
    def play_base(d):
        select(d);course=d['family']
        for i in range(4):
            assert state(True)['progress']['index']==i and not on(True)
            assert state(True)['progress']['cleared']==list(range(i))
            fresh_choices(True)
            question(True)
            if course=='resistor':
                if i:base_choice([330,100,330,1000][i])
                toggle(True)
            elif course=='capacitor':
                if i==1:base_choice(1)
                toggle(True)
                if i==2:press('#playground-task')
                else:
                    press('#playground-task')
                    if i==1:
                        visible_board(True);f.wait_for_function('TrainingPlayground.current().snapshot().phase>=2',timeout=8000)
                        assert len(state(True)['progress']['cleared'])==1
                        base_choice(22);assert state(True)['phase']==0;press('#playground-task')
            elif course=='inductor':
                if i:base_choice([100,220,22,100][i])
                toggle(True)
            else:
                if i in (0,2,3):base_choice([True,True,False,True][i])
                toggle(True)
                if i in (1,3):press('#playground-task')
            wait_clear(True,i+1);structure(True)
            assert f.locator('#playground-next').is_visible()
            toggle(True);assert not on(True);assert len(state(True)['progress']['cleared'])==i+1
            question(True)
            assert f.locator('#playground-next').is_visible()
            if i==0:toggle(True);assert len(state(True)['progress']['cleared'])==1;toggle(True)
            if i<3:press('#playground-next')
    def winner(d,index):
        return f.evaluate('''({id,index})=>{const m=TrainingSubtypeGameMath,d=m.profile(id),l=m.level(id,index),b=TrainingBeginner,allowed=b.supported(id)?b.fields(id,index):d.fields.map(f=>f.key);let values=[{params:{...l.setup},indices:{}}];for(const field of d.fields.filter(f=>allowed.includes(f.key)))values=values.flatMap(o=>field.options.map(([v],i)=>({params:{...o.params,[field.key]:v},indices:{...o.indices,[field.key]:i}})));return values.find(o=>l.check(o.params,m.evaluate(id,o.params).values)).indices;}''',{'id':d['id'],'index':index})
    def play_sub(d):
        select(d)
        for i in range(3):
            assert state(False)['progress']['index']==i and not on(False)
            fresh_choices(False)
            question(False)
            for field,option in winner(d,i).items():press('[data-subgame-field="'+field+'"][data-subgame-option="'+str(option)+'"]')
            assert len(state(False)['progress']['cleared'])==i
            toggle(False);wait_clear(False,i+1);structure(False)
            toggle(False);assert not on(False);assert len(state(False)['progress']['cleared'])==i+1
            question(False)
            assert f.locator('#subgame-next').is_visible()
            if i<2:press('#subgame-next')
    def product():
        assert f.evaluate('TrainingGameProgress.eligible("nightlight")')
        press('#game-projects')
        snapshot=lambda:f.evaluate('TrainingNightlight.current().snapshot()')
        choose=lambda field,value:press('[data-nightlight-field="'+field+'"][data-nightlight-value="'+str(value).lower()+'"]')
        def project_fresh():
            assert snapshot()['selection']=={}
            assert f.locator('[data-nightlight-field][aria-pressed="true"]').count()==0
            assert f.locator('#nightlight-power').is_disabled()
        def product_question():
            data=f.evaluate('''()=>{const s=TrainingNightlight.current().snapshot().state,c=TrainingNightlightMath.chapters[s.index];return {goal:c.goal,learned:c.learned,done:s.cleared>s.index};}''')
            assert f.locator('.nightlight-console>h4').inner_text()==data['goal']
            assert f.locator('.nightlight-console>h4').is_visible()
            assert f.locator('.nightlight-console>.play-takeaway').is_visible()==data['done']
            if data['done']:assert f.locator('.nightlight-console>.play-takeaway p').inner_text()==data['learned']
        product_question()
        assert not snapshot()['state']['power'] and not snapshot()['playing'];project_fresh()
        assert f.locator('.nightlight-controls,#nightlight-pause,#nightlight-step,#nightlight-reset').count()==0
        assert f.locator('#nightlight-power').is_disabled()
        choose('resistance',330);press('#nightlight-power');assert snapshot()['state']['cleared']==1
        product_question()
        press('#nightlight-power');assert snapshot()['result']['current']==0 and snapshot()['state']['cleared']==1
        assert f.locator('#nightlight-action').is_visible();press('#nightlight-action')
        assert not snapshot()['state']['power'];project_fresh();choose('resistance',330);assert snapshot()['state']['cleared']==1
        press('#nightlight-power');assert snapshot()['state']['cleared']==2;product_question();press('#nightlight-action')
        product_question();project_fresh()
        choose('diode','forward');press('#nightlight-power');press('#nightlight-action')
        assert snapshot()['result']['current']==0;press('#nightlight-action');assert snapshot()['state']['cleared']==3
        product_question()
        press('#nightlight-action');project_fresh();choose('capacitance',.00047);assert not snapshot()['state']['power']
        press('#nightlight-power');press('#nightlight-power');f.locator('.nightlight-viewport').scroll_into_view_if_needed()
        f.wait_for_function('TrainingNightlight.current().snapshot().state.elapsed===2',timeout=6000)
        assert snapshot()['state']['cleared']==3
        choose('capacitance',.01);assert not snapshot()['state']['power'];press('#nightlight-power');press('#nightlight-power')
        assert snapshot()['result']['source']=='capacitor' and snapshot()['playing']
        f.locator('.nightlight-viewport').scroll_into_view_if_needed();f.wait_for_function('TrainingNightlight.current().snapshot().state.cleared===4',timeout=6000)
        assert snapshot()['result']['current']>=.004 and not snapshot()['playing'];capture('product-backup','.nightlight-console')
        if f.evaluate('typeof TrainingGameFeedback!=="undefined"'):
            assert snapshot()['comparison']['context'].endswith('断电2秒结果试算')
            product_question()
        press('#nightlight-action');project_fresh();choose('mos',True);press('#nightlight-power')
        for _ in range(3):press('#nightlight-action')
        assert snapshot()['state']['cleared']==5;press('#nightlight-power');assert snapshot()['result']['current']==0
        product_question()
        assert snapshot()['state']['cleared']==5;capture('product-finished','.nightlight-console')
    def transfer(d):
        base=d['baseline'];select(d)
        lesson={'res-thick':'resistor','cap-mlcc':'capacitor'}.get(d['id'],d['id'])
        for i in range(4 if base else 3):
            press(('[data-play-level="' if base else '[data-subgame-level="')+str(i)+'"]')
            assert not on(base)
            before=state(base)['progress']['cleared']
            press('.play-transfer>summary');press('[data-transfer-answer="1"]')
            assert f.locator('.play-transfer').get_attribute('data-correct')=='false'
            press('[data-transfer-answer="0"]');press('.play-transfer>.play-secondary')
            assert f.locator('.play-transfer').get_attribute('data-verified')=='true'
            expected=f.evaluate('({id,index})=>TrainingBeginner.practice(id,index).trial',{'id':lesson,'index':i})
            params=state(base)['params'] if base else state(base)['progress']['params']
            for key,value in expected.items():
                if key!='trigger':assert params[key]==value,(d['id'],i,key,params)
            if expected.get('trigger'):assert on(base) and state(base)['playing']
            assert set(before)<=set(state(base)['progress']['cleared'])
        return 4 if base else 3
    try:
        chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:!!d.baseline}))')
        targets=[d for d in chapters if d['id'] in f.evaluate('TrainingGameProgress.requirements')] if args.requirements_only else chapters
        if args.full or args.requirements_only:
            for d in targets:
                (play_base if d['baseline'] else play_sub)(d);missions+=4 if d['baseline'] else 3
                print(json.dumps({'chapter':d['id'],'missions':missions}),flush=True)
            assert missions==(13 if args.requirements_only else 94)
            if args.full and not args.requirements_only:
                for d in chapters:
                    if d['id'] in ['res-thick','cap-mlcc','mos-n','mos-p']:trials+=transfer(d)
                assert trials==14;print(json.dumps({'transfer_trials':trials}),flush=True)
            product()
            f=load();assert f.evaluate('TrainingGameProgress.eligible("nightlight")')
        for d in targets:check_cycle(d)
        select(next(d for d in chapters if d['id']=='res-thick'))
        press('[data-play-mode="free"]');assert not on(True);base_choice(1000);assert not on(True)
        toggle(True);assert state(True)['result']['current']==.003
        base_choice(100);assert state(True)['result']['current']==.03 and on(True)
        toggle(True);assert state(True)['result']['current']==0
        for width in [320,1440,393]:
            page.set_viewport_size({'width':width,'height':659 if width<760 else 1000});structure(True)
        assert not errors,errors
        result={'status':'passed','public':args.public,'phone_emulation':args.phone,'fallback':args.fallback,'chapters':len(cases),'missions':missions,'transfer_trials':trials,'product_steps':5 if args.full or args.requirements_only else 0,'cold_start_and_one_power':True,'off_stops_motion':True,'credits_preserved':True,'errors':errors}
        (OUT/(label+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/(label+'-failure.png')))
        print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
