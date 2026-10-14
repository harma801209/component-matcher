"""Native Chrome checks: game text stays outside the rotating model area."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
parser.add_argument('--before', action='store_true')
parser.add_argument('--quick', action='store_true')
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[2] / 'ocr-diagnostic-20261014/training-scene-labels'
OUT.mkdir(parents=True, exist_ok=True)
prefix = ('formal' if args.public else 'local') + ('-before' if args.before else '-after')
URL = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
records = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    device = {k:v for k,v in p.devices['iPhone 15 Pro'].items() if k != 'default_browser_type'}
    ctx = browser.new_context(**device, reduced_motion='reduce')
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto(URL, wait_until='domcontentloaded', timeout=90000)
        deadline = time.monotonic()+180
        reload_at = time.monotonic()+15
        f = None
        while time.monotonic() < deadline:
            f = next((x for x in page.frames if x.locator('#training-app').count()), None)
            if f and f.evaluate('typeof TrainingPlaygroundLayout!=="undefined"'):
                if args.before or f.locator('.play-scene-caption').count() and f.locator('.play-controls[aria-label="演示控制"]').count(): break
            if args.public and time.monotonic() > reload_at:
                page.reload(wait_until='domcontentloaded', timeout=90000)
                reload_at = time.monotonic()+15
            page.wait_for_timeout(250)
        assert f and (args.before or f.locator('.play-scene-caption').count()), 'Updated lesson unavailable'

        def press(selector):
            n = f.locator(selector)
            assert n.count()==1 and n.is_visible(), selector
            n.focus(); n.press('Enter')

        def select(family, id):
            press('button[data-course="'+family+'"]')
            press('button[data-subtype="'+id+'"]')
            press('[data-learning-target="game"]')
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')

        def metrics():
            return f.evaluate('''()=>{
                const v=document.querySelector('.play-viewport'),c=v.querySelector('canvas'),r=c.getBoundingClientRect();
                const text=[...document.querySelectorAll('.play-badge,.play-labels,.play-device-focus,.play-hud,.play-view-hint')].filter(e=>e.getClientRects().length);
                const items=text.map(e=>{const b=e.getBoundingClientRect();return {name:e.className,text:e.textContent,overlaps:b.left<r.right&&b.right>r.left&&b.top<r.bottom&&b.bottom>r.top,inside_canvas:e.closest('.play-viewport')!==null,width:b.width,height:b.height};});
                return {items,canvas:{width:r.width,height:r.height},scroll:{w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight},caption:document.querySelectorAll('.play-scene-caption').length,readout:document.querySelectorAll('.play-scene-readout').length};
            }''')

        def check(id, view):
            m = metrics()
            if not args.before:
                assert m['caption']==1 and m['readout']==1, m
                assert all(not x['overlaps'] and not x['inside_canvas'] for x in m['items']), m
                assert m['scroll']['w']<=m['scroll']['c']+1 and m['scroll']['h']<=m['scroll']['v']+1, m
                assert f.frame_element().get_attribute('scrolling')=='no'
                assert m['canvas']['height']==(230 if f.evaluate('innerWidth<=760') else 440), m
                assert f.locator('.play-console .play-action-row').count()==1
                assert f.locator('.play-controls[role="group"][aria-label="演示控制"]').count()==1
                assert f.locator('.play-controls button:visible').evaluate_all('es=>es.every(e=>e.getBoundingClientRect().height>=44&&getComputedStyle(e).borderTopStyle==="none")')
            records.append({'id':id,'view':view,**m})

        def capture(name):
            f.evaluate('''()=>{const im=new Image();im.src=TrainingPlaygroundAssets.pcb;return im.decode();}''')
            target = '.play-viewport' if args.before else '.play-board-column'
            f.locator(target).scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            f.locator(target).screenshot(path=str(OUT/f'{prefix}-{name}.png'))

        select('resistor','res-thick')
        check('res-thick','phone-start'); capture('phone-start')
        if args.before:
            page.set_viewport_size({'width':1440,'height':900})
            check('res-thick','desktop-start'); capture('desktop-start')
        else:
            # Real interaction, live values/motion, and preserved source/marking models.
            press('#playground-action')
            assert f.evaluate('TrainingPlayground.current().snapshot().params.power')
            assert '9.1 mA' in f.locator('.play-hud').inner_text()
            canvas=f.locator('#playground-canvas')
            phase=canvas.get_attribute('data-flow-phase')
            page.wait_for_timeout(350)
            assert canvas.get_attribute('data-flow-phase') != phase, 'Current motion stopped'
            check('res-thick','phone-powered'); capture('phone-powered')
            f.locator('.play-console').screenshot(path=str(OUT/f'{prefix}-phone-next-controls.png'))
            press('#playground-pause')
            assert not f.evaluate('TrainingPlayground.current().snapshot().playing')
            press('#playground-speed')
            assert f.evaluate('TrainingPlayground.current().snapshot().speed')==.35
            assert f.locator('#playground-speed').inner_text()=='0.35×'
            assert '0.35倍' in f.locator('#playground-speed').get_attribute('aria-label')
            press('#playground-speed')
            assert f.evaluate('TrainingPlayground.current().snapshot().speed')==1
            press('#playground-power')
            assert '0.0 mA' in f.locator('.play-hud').inner_text()
            assert f.locator('#playground-power').get_attribute('aria-pressed')=='false'
            press('#playground-power')
            assert '9.1 mA' in f.locator('.play-hud').inner_text()
            assert f.locator('#playground-power').get_attribute('aria-pressed')=='true'
            press('#playground-reset')
            assert '0.0 mA' in f.locator('.play-hud').inner_text()
            press('#playground-power')
            press('#playground-next')
            press('[data-play-choice="100"]')
            assert '30.0 mA' in f.locator('.play-hud').inner_text()
            cleared=f.evaluate('TrainingPlayground.current().snapshot().progress.cleared')
            for width in (320,1440,393):
                page.set_viewport_size({'width':width,'height':659 if width<760 else 900})
                f.wait_for_function('document.getElementById("playground").dataset.mobileLayout===(innerWidth<=760?"compact":"desktop")')
                check('res-thick',str(width))
                assert f.evaluate('TrainingPlayground.current().snapshot().progress.cleared')==cleared
                if width==320:capture('narrow-powered')
            chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family}))')
            if args.quick:chapters=[d for d in chapters if d['id'] in ('res-thick','cap-mlcc','mos-n','mos-p','xtal-active','ind-wound','dio-switch')]
            for d in chapters:
                select(d['family'],d['id'])
                check(d['id'],'phone-default')
                if d['id'] in ('res-thick','cap-mlcc','mos-n','mos-p'):
                    canvas=f.locator('.play-viewport canvas')
                    canvas.focus()
                    for key in ('ArrowDown','ArrowRight','ArrowUp','ArrowLeft','0'):
                        canvas.press(key);check(d['id'],'phone-'+key)
                    capture(d['id']+'-phone')
                    page.set_viewport_size({'width':1440,'height':900})
                    f.wait_for_function('innerWidth>760')
                    check(d['id'],'desktop')
                    capture(d['id']+'-desktop')
                    page.set_viewport_size({'width':393,'height':659})
                if d['id']=='mos-n':
                    press('#subgame-speed')
                    assert f.evaluate('TrainingSubtypeGame.current().snapshot().speed')==.35
                    assert f.locator('#subgame-speed').inner_text()=='0.35×'
                    assert f.locator('#subgame-speed').get_attribute('aria-pressed')=='true'
                    press('#subgame-speed')
                    assert f.evaluate('TrainingSubtypeGame.current().snapshot().speed')==1
            assert f.locator('.play-viewport .play-device-focus').count()==0
            assert not errors,errors
        result={'status':'captured' if args.before else 'passed','public':args.public,'cases':records,'browser_errors':errors,'phone':'iPhone 15 Pro Chrome emulation, not physical Safari'}
        (OUT/f'{prefix}-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'status':result['status'],'public':args.public,'cases':len(records),'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'))
        raise
    finally:
        ctx.close();browser.close()
