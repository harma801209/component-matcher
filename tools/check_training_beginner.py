"""Actual learner controls: novice scopes, causal feedback and transfer trials."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'ocr-diagnostic-20261014/training-beginner'
OUT.mkdir(parents=True, exist_ok=True)
prefix = 'formal' if args.public else 'local'
URL = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    ctx = browser.new_context(viewport={'width':1440,'height':1024}, reduced_motion='reduce')
    page = ctx.new_page(); errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def lesson_frame(pg):
        deadline = time.monotonic()+150; next_reload = time.monotonic()+12
        while time.monotonic()<deadline:
            found = next((x for x in pg.frames if x.locator('#training-app').count()), None)
            if found and found.evaluate('typeof TrainingBeginner!=="undefined" && TrainingBeginner.create.toString().includes("legend.offsetTop")'):return found
            if args.public and time.monotonic()>next_reload:
                pg.reload(wait_until='domcontentloaded',timeout=90000);next_reload=time.monotonic()+12
            pg.wait_for_timeout(250)
        raise AssertionError('Updated lesson did not load')
    try:
        page.goto(URL, wait_until='domcontentloaded', timeout=90000)
        f = lesson_frame(page)
        def press(selector):
            b=f.locator(selector);assert b.count()==1 and b.is_visible(),selector
            starts=b.get_attribute('id') in ('playground-power','playground-trigger','subgame-action') or b.get_attribute('data-target') in ('power','trigger') or selector=='.play-transfer>.play-secondary'
            b.focus();b.press('Enter')
            if starts:
                base=f.locator('#playground-canvas').count()>0
                current=state(base)
                if current['playing']:
                    pause=f.locator('#playground-pause' if base else '#subgame-pause')
                    pause.focus();pause.press('Enter')
                    assert not state(base)['playing']
        def select(family,id):
            press('button[data-course="'+family+'"]');press('button[data-subtype="'+id+'"]')
        def fitted():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
        def capture(name):
            fitted()
            board=f.locator('.play-viewport');board.scroll_into_view_if_needed()
            f.evaluate('''()=>{const im=new Image();im.src=TrainingPlaygroundAssets.pcb;return im.decode();}''')
            sel='#playground-canvas' if f.locator('#playground-canvas').count() else '#subgame-canvas'
            frames=int(f.locator(sel).get_attribute('data-frames') or 0)
            f.wait_for_function('({sel,frames})=>Number(document.querySelector(sel).dataset.frames)>frames+2',arg={'sel':sel,'frames':frames})
            focus=f.locator('.play-device-focus');legend=f.locator('.play-labels')
            assert focus.bounding_box()['y']>=legend.bounding_box()['y']+legend.bounding_box()['height']-1
            if page.viewport_size['width']<760:
                # Tall iframe element screenshots can clip offscreen regions.
                # Capture individually visible board and action areas instead.
                f.locator('.play-viewport').screenshot(path=str(OUT/f'{prefix}-{name}-board.png'))
                f.locator('.play-cause').screenshot(path=str(OUT/f'{prefix}-{name}-cause.png'))
                f.locator('.play-action-row').screenshot(path=str(OUT/f'{prefix}-{name}-actions.png'))
            else:
                f.locator('.play-stage').screenshot(path=str(OUT/f'{prefix}-{name}.png'))
                # The formal proxy may clip a long iframe element screenshot;
                # these short, individually visible regions are the QA evidence.
                board.screenshot(path=str(OUT/f'{prefix}-{name}-board.png'))
                f.locator('.play-cause').screenshot(path=str(OUT/f'{prefix}-{name}-cause.png'))
                if f.locator('.play-transfer').is_visible() and f.locator('.play-transfer').get_attribute('open') is not None:
                    f.locator('.play-transfer').screenshot(path=str(OUT/f'{prefix}-{name}-exercise.png'))
        def state(base):
            return f.evaluate('TrainingPlayground.current().snapshot()' if base else 'TrainingSubtypeGame.current().snapshot()')
        def observe():
            for _ in range(3):
                if f.locator('#subgame-action').is_visible():press('#subgame-action')
        def step(count=1):
            for _ in range(count):press('#playground-step' if f.locator('#playground-step').is_visible() else '#playground-action')
        def prediction():
            press('.play-transfer>summary');press('[data-transfer-answer="1"]')
            assert f.locator('.play-transfer').get_attribute('data-correct')=='false'
            press('[data-transfer-answer="0"]');press('.play-transfer>.play-secondary')
            assert f.locator('.play-transfer').get_attribute('data-verified')=='true'
        press('#games-card>summary')
        for family,id,base in [('resistor','res-thick',True),('capacitor','cap-mlcc',True),('mos','mos-n',False),('mos','mos-p',False)]:
            select(family,id)
            assert f.locator('.play-beginner-intro').is_visible()
            assert f.locator('.play-cause').is_visible()
            assert f.locator('.play-transfer').is_hidden()
            canvas=f.locator('#playground-canvas' if base else '#subgame-canvas')
            canvas.scroll_into_view_if_needed()
            f.wait_for_function('(sel)=>Number(document.querySelector(sel).dataset.frames)>1',arg='#playground-canvas' if base else '#subgame-canvas')
            f.evaluate('''()=>{const im=new Image();im.src=TrainingPlaygroundAssets.pcb;return im.decode();}''')
            assert state(base)['progress']['cleared']==[]
            press('.play-beginner-intro summary')
            assert f.locator('.play-beginner-intro details').get_attribute('open') is not None
            assert len(f.locator('.play-beginner-intro details p').all())==3
            press('.play-beginner-intro summary')
            help_sel='#playground-help' if base else '#subgame-help'
            hint_sel='#playground-hint' if base else '#subgame-hint'
            press(help_sel);first=f.locator(hint_sel).inner_text();assert '再点一次' in first
            press(help_sel);assert f.locator(hint_sel).is_visible() and f.locator(hint_sel).inner_text()!=first
            press(help_sel);assert f.locator(hint_sel).is_hidden()
            capture(id+'-01-intro')
            if base:
                assert f.locator('.play-tray').is_hidden()
                press('#playground-action')
                assert state(True)['progress']['cleared']==[0]
                if id=='res-thick':
                    assert '5 V → 2 V' in f.locator('.play-cause').inner_text()
                    assert '9.1 mA' in f.locator('.play-cause').inner_text()
                else:
                    assert '电源5 mA + 电容20 mA = 芯片25 mA' in f.locator('.play-cause').inner_text()
                    assert canvas.get_attribute('data-energy-through-load')=='true'
            else:
                assert f.locator('.subgame-field:visible').count()==1
                assert state(False)['progress']['params']['load']==2
                press('[data-subgame-field="drive"][data-subgame-option="1"]')
                observe();assert state(False)['progress']['cleared']==[]
                cause=f.locator('.play-cause').inner_text()
                assert '未知' in cause and '不能据此计算' in cause
                assert '持续负载电流为0' not in cause
                press('[data-subgame-field="drive"][data-subgame-option="2"]')
                assert state(False)['progress']['cleared']==[]
                observe();assert state(False)['progress']['cleared']==[0]
                assert ('供电侧' if id=='mos-p' else '返回侧') in f.locator('.play-cause').inner_text()
            capture(id+'-02-observed')
            before=list(state(base)['progress']['cleared'])
            press('.play-transfer>summary')
            press('[data-transfer-answer="1"]')
            assert f.locator('.play-transfer').get_attribute('data-correct')=='false'
            assert '再想一想' in f.locator('.play-transfer-feedback').inner_text()
            press('[data-transfer-answer="0"]')
            assert f.locator('.play-transfer').get_attribute('data-correct')=='true'
            press('.play-transfer>.play-secondary')
            assert f.locator('.play-transfer').get_attribute('data-verified')=='true'
            assert state(base)['progress']['cleared']==before
            if id=='res-thick':
                assert not state(True)['params']['power']
                assert '电源仍是5 V' in f.locator('.play-cause').inner_text()
            elif id=='cap-mlcc':
                assert state(True)['params']['value']==22
                step(2)
                assert '回充' in f.locator('.play-cause').inner_text()
            else:
                assert state(False)['progress']['params']=={'drive':0,'load':2}
                assert '本例持续负载电流为0' in f.locator('.play-cause').inner_text()
            capture(id+'-03-transfer')
            if base:
                for level in range(1,4):
                    press('#playground-next')
                    if id=='res-thick':press('[data-play-choice="'+str([None,100,330,1000][level])+'"]')
                    elif level==1:
                        press('[data-play-choice="22"]');press('#playground-action')
                        step(2)
                    elif level==2:press('#playground-action')
                    else:
                        press('#playground-action')
                        step(4)
                    assert state(True)['progress']['cleared']==list(range(level+1))
                    prediction()
                    assert state(True)['progress']['cleared']==list(range(level+1))
                    expected_trial=f.evaluate('({id,index})=>TrainingBeginner.practice(id,index).trial',{'id':'resistor' if id=='res-thick' else 'capacitor','index':level})
                    for key,value in expected_trial.items():
                        if key!='trigger':assert state(True)['params'][key]==value
            else:
                press('#subgame-next')
                assert f.locator('.subgame-field:visible').count()==1
                press('[data-subgame-field="drive"][data-subgame-option="1"]');observe()
                assert state(False)['progress']['cleared']==[0,1]
                prediction();assert state(False)['progress']['params']=={'drive':10,'load':2}
                assert state(False)['progress']['cleared']==[0,1]
                press('#subgame-next')
                assert f.locator('[data-beginner-field="load"]').is_visible()
                assert f.locator('[data-beginner-field="drive"]').is_hidden()
                canvas.focus();canvas.press('Enter')
                assert state(False)['progress']['params']['drive']==10
                press('[data-subgame-field="load"][data-subgame-option="0"]');observe()
                assert state(False)['progress']['cleared']==[0,1,2]
                prediction();assert state(False)['progress']['params']=={'drive':10,'load':2}
                assert state(False)['progress']['cleared']==[0,1,2]
            press('[data-play-mode="free"]' if base else '[data-subgame-mode="free"]')
            assert f.locator('.play-transfer').is_hidden() and f.locator('.play-fixed-condition').is_hidden()
            if base:assert f.locator('.play-tray').is_visible()
            else:assert f.locator('.subgame-field:visible').count()==2
        select('inductor','ind-wound')
        assert '尚未开始' in f.locator('.play-console>small').inner_text()
        press('#playground-help');assert '开始电流上升' in f.locator('#playground-hint').inner_text()
        assert '重播电流上升' not in f.locator('#playground-hint').inner_text()
        press('#playground-action');assert '尚未开始' not in f.locator('.play-console>small').inner_text()
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1024})
            for family,id in [('resistor','res-thick'),('capacitor','cap-mlcc'),('mos','mos-n'),('mos','mos-p')]:
                select(family,id);fitted()
                dims=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
                assert dims['w']<=dims['c']+1 and dims['h']<=dims['v']+1,dims
                assert f.frame_element().get_attribute('scrolling')=='no'
                assert f.locator('.play-console').evaluate('e=>e.scrollHeight<=e.clientHeight+1')
                assert all(b.evaluate('e=>e.getBoundingClientRect().height>=44') for b in f.locator('.play-console button:visible').all())
                assert f.locator('.play-viewport button').count()==0
                capture(f'{id}-{width}')
        fallback=browser.new_context(viewport={'width':1440,'height':1024},reduced_motion='reduce')
        try:
            fallback.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return /webgl/i.test(kind)?null:original.call(this,kind,...args)};")
            fp=fallback.new_page();fp.on('pageerror',lambda e:errors.append(str(e)));fp.goto(URL,wait_until='domcontentloaded',timeout=90000)
            ff=lesson_frame(fp)
            def fallback_press(selector):
                b=ff.locator(selector);assert b.is_visible();b.focus();b.press('Enter')
            fallback_press('#games-card>summary')
            for family,id in [('resistor','res-thick'),('capacitor','cap-mlcc'),('mos','mos-n'),('mos','mos-p')]:
                fallback_press('button[data-course="'+family+'"]');fallback_press('button[data-subtype="'+id+'"]')
                assert ff.locator('.play-fallback').is_visible()
                assert ff.locator('.play-device-focus').is_hidden()
                assert ff.locator('.play-cause').is_visible()
                if family=='mos':
                    fallback_press('[data-subgame-field="drive"][data-subgame-option="2"]')
                    for _ in range(3):fallback_press('#subgame-action')
                    assert ff.evaluate('TrainingSubtypeGame.current().snapshot().progress.cleared')==[0]
                else:
                    fallback_press('#playground-action')
                    assert ff.evaluate('TrainingPlayground.current().snapshot().progress.cleared')==[0]
                fallback_press('.play-transfer>summary');fallback_press('[data-transfer-answer="0"]');fallback_press('.play-transfer>.play-secondary')
                assert ff.locator('.play-transfer').get_attribute('data-verified')=='true'
        finally:fallback.close()
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'examples':['res-thick','cap-mlcc','mos-n','mos-p'],'purpose_glossary':True,'single_variable_keyboard':True,'graded_hints':True,'causal_model_unknowns':True,'transfer_trials':14,'transfer_retry_verify_no_credit':True,'inductor_copy':True,'no_webgl_fallback':True,'single_scroll':[1440,900,390],'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'));print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
