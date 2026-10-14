"""Play all 78 new missions via actual controls, check live WebGL and restored foundations."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'ocr-diagnostic-20261012/training-subtype-games';OUT.mkdir(parents=True,exist_ok=True)
prefix='formal' if args.public else 'local'
URL='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1024},reduced_motion='reduce')
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto(URL,wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+150;f=None
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingSubtypeGameMath!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f and f.evaluate('typeof TrainingSubtypeGameMath!=="undefined"'),'New games not loaded'
        def press(selector):
            loc=f.locator(selector)
            if selector=='#subgame-power' and not loc.is_visible():loc=f.locator('#subgame-action')
            assert loc.is_visible(),selector
            loc.focus();loc.press('Enter')
        def state():return f.evaluate('TrainingSubtypeGame.current().snapshot()')
        def fitted():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            dim=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
            assert dim['w']<=dim['c']+1 and dim['h']<=dim['v']+1,dim
            assert f.frame_element().get_attribute('scrolling')=='no'
        def choose(key,index):press('[data-subgame-field="'+key+'"][data-subgame-option="'+str(index)+'"]')
        def observe():
            press('#subgame-action');assert state()['progress']['started']
            assert state()['playing']
            press('#subgame-pause');assert not state()['playing']
            for _ in range(2):
                # Autoplay may already have observed part of the trial before
                # the native pause click; never restart a just-cleared mission.
                if f.locator('#subgame-action').is_visible():press('#subgame-action')
        press('#games-card>summary')
        chapters=f.evaluate('TrainingCatalog.lessons.filter(d=>!d.baseline).map(d=>({id:d.id,family:d.family,title:d.title}))')
        assert len(chapters)==26
        photo_ids={'res-thin','res-sense','res-sulfur','cap-aluminum','cap-safety','cap-film','cap-tantalum','ind-layered','ind-molded','ind-common','xtal-passive','xtal-active','xtal-tcxo','xtal-vcxo','mos-n','mos-p','mos-dual','dio-rectifier','dio-schottky','dio-zener','dio-tvs','dio-led','bjt-npn','bjt-pnp','bjt-darlington','bjt-digital'}
        total=0
        for chapter in chapters:
            id=chapter['id'];press('button[data-course="'+chapter['family']+'"]');press('button[data-subtype="'+id+'"]')
            assert f.locator('#games-card').is_visible()
            assert chapter['title'] in f.locator('#game-summary-title').inner_text()
            assert '3 关' in f.locator('#game-summary-count').inner_text()
            canvas=f.locator('#subgame-canvas');canvas.scroll_into_view_if_needed()
            f.wait_for_function('(id)=>document.getElementById("subgame-canvas").dataset.model===id&&Number(document.getElementById("subgame-canvas").dataset.frames)>1',arg=id)
            assert state()['scene']['renderer']=='WebGL'
            assert not state()['playing']
            assert f.locator('#subgame-power').is_hidden()
            assert f.locator('.play-console #subgame-action').is_visible()
            assert f.locator('.play-viewport button').count()==0
            assert f.locator('[data-subgame-level="1"]').is_disabled()
            assert f.locator('#subgame-next').is_hidden()
            if id=='cap-tantalum':
                assert canvas.get_attribute('data-positive-side')=='right'
                f.locator('.subtype-game .play-viewport').screenshot(path=str(OUT/f'{prefix}-tantalum-reversed.png'))
            # Observe the deliberately unsolved setup once; it must not unlock.
            observe();assert state()['progress']['cleared']==[],(id,state())
            assert '还未达到' in f.locator('#subgame-feedback').inner_text()
            for level in range(3):
                assert state()['progress']['index']==level
                if id=='ind-common' and level==1:
                    assert canvas.get_attribute('data-part-connected')=='false'
                    f.locator('.subtype-game .play-viewport').screenshot(path=str(OUT/f'{prefix}-common-uninstalled.png'))
                # Read-only enumerate valid model choices, then act through UI.
                winner=f.evaluate('''({id,index})=>{const m=TrainingSubtypeGameMath,d=m.profile(id),l=m.level(id,index),b=TrainingBeginner,allowed=b.supported(id)?b.fields(id,index):d.fields.map(f=>f.key);let choices=[{params:{...l.setup},indices:{}}];for(const field of d.fields.filter(f=>allowed.includes(f.key)))choices=choices.flatMap(o=>field.options.map(([v],i)=>({params:{...o.params,[field.key]:v},indices:{...o.indices,[field.key]:i}})));return choices.find(o=>l.check(o.params,m.evaluate(id,o.params).values)).indices;}''',{'id':id,'index':level})
                for key,index in winner.items():choose(key,index)
                assert state()['progress']['cleared']==list(range(level)),(id,level,state())
                assert not state()['progress']['started']
                observe();assert state()['progress']['cleared']==list(range(level+1)),(id,level,state())
                if id=='cap-tantalum':assert canvas.get_attribute('data-positive-side')=='left'
                if id=='ind-common':assert canvas.get_attribute('data-part-connected')=='true'
                assert f.locator('#subgame-next').is_visible()
                assert ('本关观察完成' if id in ('mos-n','mos-p') else '你刚刚学会了') in f.locator('.subtype-game .play-story').inner_text()
                fitted();total+=1
                if level==1 and id in photo_ids:
                    f.locator('.subtype-game .play-stage').screenshot(path=str(OUT/f'{prefix}-{id}-board.png'))
                    f.locator('.subtype-game .subgame-fields').screenshot(path=str(OUT/f'{prefix}-{id}-choices.png'))
                    f.locator('.subtype-game .play-action-row').screenshot(path=str(OUT/f'{prefix}-{id}-actions.png'))
                if level<2:press('#subgame-next')
            assert '全部通关' in f.locator('#subgame-next').inner_text()
            press('[data-subgame-level="0"]');assert len(state()['progress']['cleared'])==3
            press('[data-subgame-level="2"]');assert len(state()['progress']['cleared'])==3
            press('[data-subgame-mode="free"]');cfg=f.evaluate('(id)=>TrainingSubtypeGameMath.profile(id).fields',id)
            current_option=next(i for i,o in enumerate(cfg[0]['options']) if o[0]==state()['progress']['params'][cfg[0]['key']])
            choose(cfg[0]['key'],(current_option+1)%len(cfg[0]['options']))
            assert state()['mode']=='free';press('[data-subgame-mode="challenge"]');assert len(state()['progress']['cleared'])==3
            press('#subgame-next');assert state()['progress']['cleared']==[] and state()['progress']['index']==0
            assert not state()['progress']['started']
        assert total==78
        # Native drag, keyboard rotation and live pause/slow/recompute.
        press('button[data-course="diode"]');press('button[data-subtype="dio-led"]');press('[data-subgame-mode="free"]')
        choose('forward',0);choose('resistance',2);press('#subgame-power');canvas=f.locator('#subgame-canvas');canvas.scroll_into_view_if_needed()
        low=float(canvas.get_attribute('data-brightness'));canvas.screenshot(path=str(OUT/f'{prefix}-led-low.png'));f.locator('[data-subgame-field="resistance"][data-subgame-option="0"]').drag_to(canvas)
        assert state()['progress']['params']['resistance']==100 and not state()['progress']['started']
        press('#subgame-power');assert float(canvas.get_attribute('data-brightness'))>low;canvas.screenshot(path=str(OUT/f'{prefix}-led-high.png'))
        yaw=canvas.get_attribute('data-yaw');canvas.focus();canvas.press('ArrowRight');assert canvas.get_attribute('data-yaw')!=yaw
        assert state()['playing'];press('#subgame-pause');assert not state()['playing']
        press('#subgame-pause');assert state()['playing'];page.wait_for_timeout(250);phase=canvas.get_attribute('data-flow-phase');page.wait_for_timeout(250);assert canvas.get_attribute('data-flow-phase')!=phase
        press('#subgame-pause');phase=canvas.get_attribute('data-flow-phase');page.wait_for_timeout(200);assert canvas.get_attribute('data-flow-phase')==phase
        press('#subgame-speed');assert state()['speed']==.35
        choose('resistance',1);press('#subgame-power');assert abs(state()['result']['values']['current']-2/330)<1e-10
        press('#subgame-reset');assert not state()['progress']['started']
        # All four original chapter engines restore, without substituting a new game.
        for family,id in [('resistor','res-thick'),('capacitor','cap-mlcc'),('inductor','ind-wound'),('diode','dio-switch')]:
            press('button[data-course="'+family+'"]');press('button[data-subtype="'+id+'"]')
            assert f.locator('#playground-workbench').is_visible();assert f.locator('#subgame-root').count()==0
            assert f.evaluate('TrainingPlayground.current().snapshot().progress.index')==0
            assert '4 关' in f.locator('#game-summary-count').inner_text()
        # Responsive power/HUD layout and only outer host scrolling.
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1024})
            for family,id in [('capacitor','cap-aluminum'),('crystal','xtal-active'),('mos','mos-p')]:
                press('button[data-course="'+family+'"]');press('button[data-subtype="'+id+'"]');f.locator('#subgame-canvas').scroll_into_view_if_needed();fitted()
                assert f.locator('.play-console #subgame-action').is_visible()
                assert f.locator('.play-viewport button').count()==0
                f.locator('.subtype-game .play-viewport').screenshot(path=str(OUT/f'{prefix}-{id}-width-{width}.png'))
            f.locator('#subgame-root').scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'{prefix}-width-{width}.png'))
        page.reload(wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'):break
            page.wait_for_timeout(250)
        press('#games-card>summary');press('button[data-course="resistor"]');press('button[data-subtype="res-thin"]');assert state()['progress']['cleared']==[]
        # Honest no-WebGL fallback, still solvable via the same model and controls.
        fallback=browser.new_context(viewport={'width':1440,'height':1024},reduced_motion='reduce')
        try:
            fallback.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return /webgl/i.test(kind)?null:original.call(this,kind,...args)};")
            fp=fallback.new_page();fp.on('pageerror',lambda e:errors.append(str(e)));fp.goto(URL,wait_until='domcontentloaded',timeout=90000)
            deadline=time.monotonic()+150;ff=None
            while time.monotonic()<deadline:
                ff=next((x for x in fp.frames if x.locator('#training-app').count()),None)
                if ff and ff.evaluate('typeof TrainingCatalogUI!=="undefined"'):break
                fp.wait_for_timeout(250)
            def fallback_press(selector):
                b=ff.locator(selector);b.focus();b.press('Enter')
            fallback_press('#games-card>summary');fallback_press('button[data-subtype="res-thin"]')
            assert ff.locator('.subtype-game .play-fallback').is_visible()
            assert ff.locator('#subgame-canvas').is_hidden()
            fallback_press('[data-subgame-field="temperature"][data-subgame-option="1"]')
            for _ in range(3):fallback_press('#subgame-action')
            assert ff.evaluate('TrainingSubtypeGame.current().snapshot().progress.cleared')==[0]
        finally:fallback.close()
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'subtypes':26,'new_missions':78,'real_webgl':True,'locked_observed_trials':True,'wrong_retry_revisit':True,'free_mode_independent':True,'drag_keyboard_live_pause':True,'no_webgl_fallback':True,'foundation_games_kept':4,'single_scroll':[1440,900,390],'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'));print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
