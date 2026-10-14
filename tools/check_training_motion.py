"""Native mobile touch regression for explicit motion and source-first SVG arrows.

Chrome touch emulation, not a claim of physical iPhone/Safari verification.
Read-only lesson APIs inspect state; all changes use existing visible controls.
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
parser.add_argument('--scope', choices=['all','games','circuit'], default='all')
parser.add_argument('--preference', choices=['both','reduce','no-preference'], default='both')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'ocr-diagnostic-20261014/training-motion-fix'
OUT.mkdir(parents=True, exist_ok=True)
URL = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
prefix = 'formal' if args.public else 'local'
records = []
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    for preference in (['reduce','no-preference'] if args.preference=='both' else [args.preference]):
        ctx = browser.new_context(viewport={'width':390,'height':844}, is_mobile=True,
                                  has_touch=True, reduced_motion=preference)
        page = ctx.new_page()
        page.on('pageerror', lambda e:errors.append(str(e)))
        try:
            page.goto(URL, wait_until='domcontentloaded', timeout=90000)
            deadline = time.monotonic() + 150
            f = None
            while time.monotonic() < deadline:
                f = next((x for x in page.frames if x.locator('#training-app').count()), None)
                if f and f.evaluate('typeof TrainingSubtypeGame!=="undefined"'):break
                page.wait_for_timeout(250)
            assert f and f.evaluate('typeof TrainingSubtypeGame!=="undefined"'), 'Lesson not available'

            def tap(selector):
                loc = f.locator(selector)
                assert loc.is_visible(), selector
                # Nested iframe height changes when a mission clears. Wait for
                # settled real coordinates before a touchscreen hit-test.
                loc.scroll_into_view_if_needed()
                last_box=None
                steady=0
                for _ in range(20):
                    box=loc.bounding_box()
                    steady=steady+1 if box==last_box else 0
                    if steady>=2:break
                    last_box=box
                    page.wait_for_timeout(80)
                loc.tap()

            def source_position(selector):
                pos=f.locator(selector).evaluate('e=>{const m=e.transform.baseVal.consolidate().matrix;return [m.e,m.f]}')
                assert abs(pos[0]-80)<.001 and abs(pos[1]-125)<.001, pos

            chapters = f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:d.baseline}))')
            # All 30 chapters in the formerly failing reduced-motion setting;
            # both engines additionally checked with the ordinary setting.
            selected = chapters if preference == 'reduce' else [d for d in chapters if d['id'] in ('res-thick','cap-mlcc','ind-wound','dio-switch','dio-schottky','xtal-active')]
            if args.scope=='circuit':selected=[]
            for chapter in selected:
                id = chapter['id']
                tap('button[data-course="'+chapter['family']+'"]')
                tap('button[data-subtype="'+id+'"]')
                tap('[data-learning-target="game"]')
                baseline = chapter['baseline']
                engine = 'TrainingPlayground' if baseline else 'TrainingSubtypeGame'
                base = 'playground' if baseline else 'subgame'
                canvas = f.locator('#'+base+'-canvas')
                state = lambda:f.evaluate(engine+'.current().snapshot()')
                initial = state()
                assert initial['playing'] == (preference != 'reduce'), (id,'autoplay')
                if baseline:
                    tap('[data-play-mode="free"]')
                    if id == 'dio-switch':tap('[data-play-choice="true"]')
                    # Free mode starts with a powered circuit; stop, then start
                    # through the same visible CTA used by a mobile learner.
                    tap('#playground-power')
                    assert not state()['params']['power']
                else:
                    # Pick a valid first lesson setup using actual option taps,
                    # without mutating params/progress or injecting a solution.
                    winner = f.evaluate('''id=>{const m=TrainingSubtypeGameMath,d=m.profile(id),l=m.level(id,0),b=TrainingBeginner,allowed=b.supported(id)?b.fields(id,0):d.fields.map(f=>f.key);let choices=[{params:{...l.setup},indices:{}}];for(const field of d.fields.filter(f=>allowed.includes(f.key)))choices=choices.flatMap(o=>field.options.map(([v],i)=>({params:{...o.params,[field.key]:v},indices:{...o.indices,[field.key]:i}})));return choices.find(o=>l.check(o.params,m.evaluate(id,o.params).values)).indices;}''', id)
                    for key,index in winner.items():
                        tap('[data-subgame-field="'+key+'"][data-subgame-option="'+str(index)+'"]')
                tap('#'+base+'-action')
                assert state()['playing'], (id,'explicit start remained paused')
                assert f.locator('#'+base+'-pause').get_attribute('aria-label') == '暂停动画'
                canvas.scroll_into_view_if_needed()
                page.wait_for_timeout(140)
                one = state()
                page.wait_for_timeout(280)
                two = state()
                assert two['scene']['renderer'] == 'WebGL', id
                assert two['scene']['phase'] > one['scene']['phase'], (id,'stationary arrows')
                # A finite discharging capacitor still stops honestly at the
                # end of its stored energy; it is not an endless animation.
                if id != 'cap-tantalum':
                    tap('#'+base+'-pause')
                    assert not state()['playing']
                    assert '动画已暂停' in f.locator('#'+base+'-instruction').inner_text()
                    canvas.scroll_into_view_if_needed()
                    page.wait_for_timeout(150)
                    frozen = state()['scene']['phase']
                    page.wait_for_timeout(180)
                    assert state()['scene']['phase'] == frozen, (id,'pause did not freeze')
                    tap('#'+base+'-pause')
                    assert state()['playing']
                    canvas.scroll_into_view_if_needed()
                    page.wait_for_timeout(140)
                    resumed = state()['scene']['phase']
                    page.wait_for_timeout(200)
                    assert state()['scene']['phase'] > resumed, (id,'resume did not move')
                records.append({'preference':preference,'id':id,'explicit_start':True,'moving':True})
                print(json.dumps({'checked':id,'preference':preference,'moving':True}),flush=True)
                if id in ('res-thick','dio-schottky'):
                    canvas.screenshot(path=str(OUT/f'{prefix}-{preference}-{id}.png'))

            # Setting changes may pause; a deliberate gesture can still resume.
            if selected:
                page.emulate_media(reduced_motion='no-preference')
                f.wait_for_function('!matchMedia("(prefers-reduced-motion:reduce)").matches')
                # Deliver the first native media change before requesting its
                # opposite; remote nested frames can coalesce rapid flips.
                f.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                page.emulate_media(reduced_motion='reduce')
                f.wait_for_function(engine+'.current().snapshot().playing===false')
                tap('#'+base+'-pause')
                assert state()['playing']
            if args.scope=='games':continue

            # Source-first 2D demonstration, independent of page elapsed time.
            tap('button[data-course="resistor"]')
            tap('button[data-subtype="res-thick"]')
            tap('[data-learning-target="circuit"]')
            f.wait_for_function('"visualTime" in TrainingCircuit.current()')
            page.wait_for_timeout(1200)
            for view in ['pcb','schematic']:
                tap('#circuit-'+view)
                tap('[data-circuit-step="1"]')
                arrow = f.locator('#arrow-main')
                assert float(arrow.get_attribute('data-distance')) == 0
                source_position('#arrow-main')
                assert float(f.locator('#flow-main').get_attribute('data-current')) == f.evaluate('TrainingCircuit.current().result.i')
                assert f.locator('#circuit-r-drop').text_content() == '电阻压降 3 V'
                assert f.locator('#circuit-led').evaluate('e=>e.classList.contains("lit")')
                assert f.evaluate('TrainingCircuit.current().visualTime') == 0
                tap('#circuit-play')
                f.locator('#circuit-drawing').scroll_into_view_if_needed()
                page.wait_for_timeout(350)
                assert float(arrow.get_attribute('data-distance')) > 0
                tap('#circuit-play')
                stopped = arrow.get_attribute('transform')
                frozen = f.evaluate('TrainingCircuit.current().visualTime')
                page.wait_for_timeout(200)
                assert arrow.get_attribute('transform') == stopped
                tap('#circuit-'+('schematic' if view == 'pcb' else 'pcb'))
                assert f.locator('#arrow-main').get_attribute('transform') == stopped
                assert f.evaluate('TrainingCircuit.current().visualTime') == frozen
                tap('#circuit-play')
                f.locator('#circuit-drawing').scroll_into_view_if_needed()
                page.wait_for_timeout(200)
                assert f.evaluate('TrainingCircuit.current().visualTime') > frozen
                tap('#circuit-play')
                tap('#circuit-reset')
                tap('[data-circuit-step="1"]')
                assert float(f.locator('#arrow-main').get_attribute('data-distance')) == 0
            f.locator('#circuit-drawing').screenshot(path=str(OUT/f'{prefix}-{preference}-source-start.png'))
            # Other source branches start at the source, without moving the
            # two capacitor contributions out of their shared IC lanes.
            for family,id,flow_id in [('capacitor','cap-mlcc','source'),('inductor','ind-wound','supply'),('diode','dio-switch','main')]:
                tap('button[data-course="'+family+'"]')
                tap('button[data-subtype="'+id+'"]')
                tap('[data-learning-target="circuit"]')
                tap('[data-circuit-step="1"]')
                assert float(f.locator('#flow-'+flow_id).get_attribute('data-arrow-position')) == 0
                source_position('#arrow-'+flow_id)
                if family == 'capacitor':
                    assert f.locator('#arrow-cap-load').evaluate('e=>e.style.opacity') == '1'
                    assert float(f.locator('#flow-cap-load').get_attribute('data-arrow-position')) == .55
            assert not errors, errors
        finally:
            ctx.close()
    browser.close()

(OUT/f'{prefix}-{args.scope}-{args.preference}-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'passed','public':args.public,'touch_mobile':True,
                  'reduced_motion_chapters':sum(r['preference']=='reduce' for r in records),
                  'ordinary_motion_chapters':sum(r['preference']=='no-preference' for r in records),
                  'source_first_pause_resume_views_replay':args.scope!='games',
                  'synchronous_readouts':args.scope!='games','errors':errors}),flush=True)
