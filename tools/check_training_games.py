"""Presentation-only browser acceptance; --public verifies deployed training games."""
import argparse
import json
import platform
import sys
import time
from pathlib import Path
platform._wmi=None
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from product_training import build_training_html
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
OUT=ROOT.parent/'ocr-diagnostic-20261012/training-games'
OUT.mkdir(parents=True,exist_ok=True)
winners={'resistor':{'r':'330','rating':'0.063'},'capacitor':{'c':'10','near':'true'},'inductor':{'l':'220','isat':'1.5'},'diode':{'forward':'true','vf':'0.3'}}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1000})
    if not args.public:ctx.route('http://training.local/**',lambda route:route.fulfill(body=build_training_html(),content_type='text/html'))
    page=ctx.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def frame():
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            f=next((f for f in page.frames if f.locator('#games-card').count()),None)
            if f:
                f.wait_for_function('typeof TrainingGamesMath!=="undefined" && document.querySelector("#game-board svg")')
                return f
            page.wait_for_timeout(400)
        raise AssertionError('Games not ready')
    def activate(loc):loc.focus();loc.press('Enter')
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=frame()
        assert f.locator('#games-card').get_attribute('open') is None
        assert not f.locator('#game-run').is_visible()
        activate(f.locator('#games-card>summary'))
        for course,parameters in winners.items():
            activate(f.locator('button[data-course='+course+']'))
            activate(f.locator('[data-game-mode=circuit]'))
            assert '0 / 2' in f.locator('#game-progress').inner_text()
            activate(f.locator('#game-run'))
            assert '还差一点' in f.locator('#game-feedback').inner_text()
            for key,value in parameters.items():f.locator('#game-param-'+key).select_option(value)
            assert '参数已满足' in f.locator('#game-hints').inner_text()
            activate(f.locator('#game-run'))
            assert '闯关成功' in f.locator('#game-feedback').inner_text()
            assert '1 / 2' in f.locator('#game-progress').inner_text()
            f.locator('#games-card').screenshot(path=str(OUT/(('formal-' if args.public else 'local-')+course+'-circuit.png')))
            if course=='capacitor':
                assert f.locator('#game-board .game-flow.energy').count()==1
                assert 'H450V250' in f.locator('#game-board .game-flow.energy').get_attribute('d')
            if course=='diode':
                activate(f.locator('#game-reverse'))
                assert '被阻断' in f.locator('#game-board').inner_text()
                assert f.locator('#game-board .game-flow').count()==0
                activate(f.locator('#game-reverse'))
                assert f.locator('#game-board .game-flow').count()==1
            activate(f.locator('[data-game-mode=memory]'))
            activate(f.locator('[data-game-card="0"]'))
            activate(f.locator('[data-game-card="0"]'))
            assert '已尝试 0 次' in f.locator('.game-card-count').inner_text()
            activate(f.locator('[data-game-card="3"]'))
            assert '不是一对' in f.locator('#game-feedback').inner_text()
            for pair in range(4):
                activate(f.locator('[data-game-card="'+str(pair*2)+'"]'))
                activate(f.locator('[data-game-card="'+str(pair*2+1)+'"]'))
                assert f.locator('[data-game-card="'+str(pair*2)+'"]').is_disabled()
            assert '全部配对完成' in f.locator('#game-feedback').inner_text()
            assert '2 / 2' in f.locator('#game-progress').inner_text()
            f.locator('#games-card').scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/(('formal-' if args.public else 'local-')+course+'.png')),full_page=True)
            activate(f.locator('#game-restart'))
            assert f.locator('.game-deck button:disabled').count()==0
            assert '2 / 2' in f.locator('#game-progress').inner_text()
        # Course switching preserves this page's progress; unrelated training remains usable.
        activate(f.locator('button[data-course=resistor]'))
        assert '2 / 2' in f.locator('#game-progress').inner_text()
        activate(f.locator('[data-game-mode=circuit]'))
        assert f.locator('#game-param-r').input_value()=='330'
        activate(f.locator('#tab-performance'))
        assert f.locator('#panel-performance').is_visible()
        activate(f.locator('#show-cross-section'))
        assert f.locator('.model-card').get_attribute('data-mode')=='materials'
        activate(f.locator('#tool-scenario'))
        assert f.locator('#scenario-question').is_visible()
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            activate(f.locator('[data-game-mode=memory]'))
            f.locator('#games-card').scroll_into_view_if_needed()
            size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert size['scroll']<=size['client']+1,size
            page.screenshot(path=str(OUT/f'{"formal" if args.public else "local"}-width-{width}.png'),full_page=True)
            if args.public:
                box=f.evaluate('({h:document.getElementById("training-app").getBoundingClientRect().height,frame:window.frameElement.getBoundingClientRect().height,scrolling:window.frameElement.getAttribute("scrolling")})')
                assert box['scrolling']=='no' and box['frame']>=box['h'],box
        page.emulate_media(reduced_motion='reduce')
        activate(f.locator('[data-game-mode=circuit]'))
        assert f.locator('.game-flow').first.evaluate('(e)=>getComputedStyle(e).animationName')=='none'
        page.reload(wait_until='domcontentloaded',timeout=90000)
        f=frame()
        f.wait_for_function('document.querySelector("#game-progress").textContent.includes("0 / 2")')
        assert '0 / 2' in f.locator('#game-progress').text_content()
        assert f.locator('#games-card').get_attribute('open') is None
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'circuit_games':4,'memory_games':4,'wrong_correct_reset_switch':True,'keyboard':True,'responsive':[1440,900,390],'single_scroll':args.public,'refresh_reset':True,'browser_errors':errors}),flush=True)
    finally:
        ctx.close();browser.close()
