"""Play all 16 real-UI 3D missions; do not inject answers or alter progress."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'ocr-diagnostic-20261012/training-levels';OUT.mkdir(parents=True,exist_ok=True)
prefix='formal' if args.public else 'local'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1024},reduced_motion='reduce')
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/',wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+150;f=None
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingPlaygroundLevels!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f and f.evaluate('typeof TrainingPlaygroundLevels!=="undefined"')
        def press(selector):
            loc=f.locator(selector)
            # The single contextual CTA replaces a matching secondary control.
            if not loc.is_visible() and selector.startswith('#playground-'):
                action=f.locator('#playground-action')
                if action.is_visible() and action.get_attribute('data-target')==selector.removeprefix('#playground-'):loc=action
            assert loc.is_visible(),selector
            starts=loc.get_attribute('id') in ('playground-power','playground-trigger') or loc.get_attribute('data-target') in ('power','trigger')
            loc.focus();loc.press('Enter')
            # Explicit starts now play even under reduced-motion. Pause through
            # the real control before this test's deterministic manual steps.
            if starts and state()['playing']:
                pause=f.locator('#playground-pause');pause.focus();pause.press('Enter')
                assert not state()['playing']
        def state():return f.evaluate('TrainingPlayground.current().snapshot()')
        def choose(value):press('[data-play-choice="'+str(value).lower()+'"]')
        def step(n):
            for _ in range(n):
                if state()['progress']['index'] in state()['progress']['cleared']:break
                press('#playground-step')
        def passed(count):
            assert len(state()['progress']['cleared'])==count,state()
            assert not f.locator('#playground-next').is_disabled()
        press('#games-card>summary')
        assert f.locator('#playground-workbench #playground-power').count()==1
        assert f.locator('#playground-mission #playground-power').count()==0
        assert f.locator('.play-viewport #playground-power').count()==0
        assert f.locator('.play-console #playground-power').count()==1
        assert f.locator('#playground-power').is_hidden()
        assert f.locator('#playground-action').inner_text()=='打开电源'
        assert '不用换电阻' in f.locator('#playground-instruction').inner_text()
        assert f.locator('.play-tray').is_hidden()
        assert state()['mode']=='challenge' and state()['progress']['cleared']==[]
        assert f.locator('[data-play-level="1"]').is_disabled()
        assert f.locator('#playground-next').is_disabled()
        f.locator('[data-play-level="3"]').evaluate('e=>e.click()')
        assert state()['progress']['index']==0
        press('#playground-help');assert f.locator('.play-mission-hint').is_visible()
        assert not state()['progress']['interacted']
        total=0
        for course in ['resistor','capacitor','inductor','diode']:
            press('button[data-course="'+course+'"]')
            assert state()['mode']=='challenge' and state()['progress']['index']==0
            assert not state()['playing']
            for level in range(4):
                assert state()['progress']['index']==level
                if course=='resistor':
                    if level==0:press('#playground-action')
                    else:
                        if level==1:
                            choose(330);assert f.locator('#playground-next').is_disabled()
                        choose([None,100,330,1000][level])
                elif course=='capacitor':
                    if level==0:press('#playground-action')
                    elif level==1:
                        choose(1);press('#playground-trigger');step(2)
                        assert f.locator('#playground-next').is_disabled()
                        choose(22);assert state()['phase']==0
                        assert f.locator('#playground-next').is_disabled()
                        press('#playground-action');step(2)
                    elif level==2:press('#playground-action')
                    else:press('#playground-trigger');step(4)
                elif course=='inductor':
                    if level==0:press('#playground-action');step(1)
                    else:
                        choose([None,220,22,100][level]);press('#playground-trigger');step(2)
                else:
                    if level==0:choose(True)
                    elif level==1:press('#playground-action')
                    elif level==2:choose(False)
                    else:
                        choose(True);assert f.locator('#playground-next').is_disabled()
                        press('#playground-reverse')
                passed(level+1);total+=1
                f.evaluate('document.activeElement?.blur()')
                f.locator('#playground-mission').screenshot(path=str(OUT/f'{prefix}-{course}-{level+1}-mission.png'))
                f.locator('.play-stage').screenshot(path=str(OUT/f'{prefix}-{course}-{level+1}-board.png'))
                f.locator('.play-action-row').screenshot(path=str(OUT/f'{prefix}-{course}-{level+1}-actions.png'))
                if level<3:press('#playground-next')
            assert '全部通关' in f.locator('#playground-outcome').inner_text()
            # A completed task can be revisited without duplicate completion credit.
            press('[data-play-level="0"]');passed(4)
            press('[data-play-level="3"]');passed(4)
        assert total==16
        # Each course remembers its own level; free mode has independent parameter state.
        press('button[data-course="resistor"]');assert len(state()['progress']['cleared'])==4
        press('[data-play-mode="free"]');choose(1000)
        assert state()['result']['current']==.003
        press('[data-play-mode="challenge"]');assert len(state()['progress']['cleared'])==4
        press('[data-play-level="3"]');press('#playground-next')
        assert state()['progress']['cleared']==[] and state()['progress']['index']==0
        assert not state()['params']['power']
        assert f.locator('#playground-next').is_disabled()
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1024})
            f.locator('#playground-mission').scroll_into_view_if_needed()
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
            dims=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
            assert dims['w']<=dims['c']+1 and dims['h']<=dims['v']+1,dims
            assert f.frame_element().get_attribute('scrolling')=='no'
            f.locator('#playground-mission').screenshot(path=str(OUT/f'{prefix}-width-{width}-mission.png'))
            f.locator('#playground-canvas').screenshot(path=str(OUT/f'{prefix}-width-{width}-board.png'))
            f.locator('.play-heading').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/f'{prefix}-width-{width}.png'))
        page.reload(wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingPlaygroundLevels!=="undefined"'):break
            page.wait_for_timeout(250)
        assert state()['mode']=='challenge' and state()['progress']['cleared']==[]
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'missions':16,'locked_until_complete':True,'hints_wrong_retry_revisit':True,'independent_free_mode':True,'reduced_motion_manual_steps':True,'refresh_reset':True,'single_scroll':[1440,900,390],'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'));print(json.dumps({'errors':errors}),flush=True);raise
    finally:ctx.close();browser.close()
