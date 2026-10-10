"""Verify PCB topology/flows, teaching stages, controls and original-tool coexistence."""
import argparse
import platform
import sys
import time
import json
from pathlib import Path
platform._wmi=None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from product_training import build_training_html
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
out=Path(__file__).resolve().parents[2]/'dark-ui-test/test-runtime/visual-qa/training-circuit'
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce')
    if not args.public:context.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=None;deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#circuit-card').count()),None)
            if f:break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingCircuit!=="undefined"')
        def press(loc):loc.focus();loc.press('Enter')
        def icon_controls(playing=False):
            controls=f.locator('.circuit-controls .circuit-icon-button')
            assert controls.count()==3
            for button in controls.all():
                assert button.inner_text().strip()==''
                assert button.get_attribute('aria-label')
                assert button.get_attribute('title')
                assert button.locator('svg:visible').count()==1
                assert button.evaluate('e=>e.offsetWidth>=44&&e.offsetHeight>=44')
                assert button.locator('svg[aria-hidden="true"][focusable="false"]').count()>=1
            play=f.locator('#circuit-play')
            label='暂停演示' if playing else '播放分步演示'
            assert play.get_attribute('aria-label')==play.get_attribute('title')==label
            assert play.get_attribute('aria-pressed')==str(playing).lower()
            assert play.locator('.control-pause').is_visible()==playing
            assert play.locator('.control-play').is_visible()!=playing
            assert f.locator('#circuit-next').is_disabled()==(f.evaluate('TrainingCircuit.current().step')==2)
        icon_controls()
        for course in ['resistor','capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            assert f.evaluate('TrainingCircuit.current().course')==course
            assert f.evaluate('TrainingCircuit.current().step')==0
            assert f.locator('[data-circuit-step]').count()==3
            for s in [1,2,0]:
                press(f.locator('[data-circuit-step="'+str(s)+'"]'))
                assert f.evaluate('TrainingCircuit.current().step')==s
                assert f.locator('#circuit-headline').inner_text()
                icon_controls()
            press(f.locator('#circuit-next'));assert f.evaluate('TrainingCircuit.current().step')==1
            press(f.locator('#circuit-schematic'));assert f.locator('#circuit-svg').get_attribute('class')=='schematic'
            press(f.locator('#circuit-pcb'));assert f.locator('#circuit-svg').get_attribute('class')=='pcb'
            if course=='resistor':
                assert f.evaluate('TrainingCircuit.current().result.i')>0
                f.locator('#circuit-resistance').select_option('1000')
                assert abs(f.evaluate('TrainingCircuit.current().result.i')-.003)<1e-12
            elif course=='capacitor':
                r=f.evaluate('TrainingCircuit.current().result');assert r['icap']<0
                for view in ['pcb','schematic']:
                    press(f.locator('#circuit-'+view))
                    for step,progress in [(0,0),(1,0),(1,.4),(1,1),(2,0),(2,.5),(2,1)]:
                        f.evaluate('([s,u])=>TrainingCircuit.selectStep(s,u)',[step,progress])
                        # The two colored contributions sum to the IC load, not two full loads.
                        f.evaluate('''()=>{
                            const r=TrainingCircuit.current().result;
                            const current=id=>Number(document.getElementById('flow-'+id).dataset.current);
                            if(Math.abs(current('load')+current('cap-load')-r.load)>1e-10)throw Error('IC current balance');
                            if(Math.abs(current('source')-current('return'))>1e-10)throw Error('Supply return');
                            const orange=document.getElementById('flow-cap-load');
                            if(orange.style.opacity!==(r.icap<0?'1':'0'))throw Error('Orange IC phase');
                            if(r.icap<0){
                                if(current('cap-up')>=0||current('cap-down')>=0||current('cap-load')<=0)throw Error('Discharge direction');
                                const points=[];
                                for(const id of ['load','cap-load']){
                                    const path=document.getElementById('flow-'+id),arrow=document.getElementById('arrow-'+id);
                                    if(path.style.opacity!=='1'||arrow.style.opacity!=='1')throw Error('Missing IC flow');
                                    const p=path.getPointAtLength(path.getTotalLength()*Number(path.dataset.arrowPosition));
                                    if(p.x<409||p.x>491||p.y<125||p.y>195)throw Error('Arrow must pass inside IC');
                                    const matrix=arrow.transform.baseVal.consolidate().matrix;
                                    if(matrix.b<.99)throw Error('IC arrow must point towards GND');
                                    points.push(p);
                                    const start=path.getPointAtLength(0),end=path.getPointAtLength(path.getTotalLength());
                                    if(start.x!==310||start.y!==95||end.x!==310||end.y!==220)throw Error('Load loop endpoints');
                                }
                                if(Math.abs(points[0].x-points[1].x)<20)throw Error('Color lanes overlap');
                            }
                            if(r.icap>0&&(current('cap-up')<=0||current('cap-down')<=0))throw Error('Recharge direction');
                        }''')
                    # No animated path is drawn through the capacitor dielectric gap.
                    assert f.locator('#flow-cap-up').get_attribute('d')=='M310 95V150'
                    assert f.locator('#flow-cap-down').get_attribute('d')=='M310 170V220'
                    f.evaluate('TrainingCircuit.selectStep(1,0)')
                    f.locator('#circuit-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-capacitor-discharge-{view}.png'))
                    press(f.locator('#circuit-remove-cap'))
                    for step in [0,1,2]:
                        f.evaluate('s=>TrainingCircuit.selectStep(s,.3)',step)
                        for path in ['cap-up','cap-down','cap-load']:
                            assert f.locator('#flow-'+path).evaluate('e=>e.style.opacity')=='0'
                    press(f.locator('#circuit-remove-cap'))
                f.evaluate('TrainingCircuit.selectStep(1,0)')
                press(f.locator('#circuit-remove-cap'))
                assert f.evaluate('TrainingCircuit.current().result.v')<r['v']
                assert f.locator('#flow-cap-up').evaluate('e=>e.style.opacity')=='0'
                press(f.locator('#circuit-remove-cap'))
            elif course=='inductor':
                press(f.locator('[data-circuit-step="2"]'))
                assert f.locator('#flow-supply').evaluate('e=>e.style.opacity')=='0'
                assert f.locator('#flow-freewheel').evaluate('e=>e.style.opacity')=='1'
                assert '续流' in f.locator('#circuit-story').inner_text()
            else:
                press(f.locator('[data-circuit-step="2"]'))
                assert f.evaluate('TrainingCircuit.current().result.reverse')
                assert f.locator('#flow-main').evaluate('e=>e.style.opacity')=='0'
                assert f.locator('#circuit-output-value').text_content()=='负载 0.0 V'
            f.locator('#circuit-card').scroll_into_view_if_needed()
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}.png'),full_page=True)
            # Clicking original tabs must not hide the PCB lesson or practice panel.
            press(f.locator('#tab-principle'))
            assert f.locator('#circuit-card').is_visible()
            assert f.locator('#tool-panel-decode').is_visible()
        press(f.locator('button[data-course="capacitor"]'))
        f.locator('#circuit-play').focus();f.locator('#circuit-play').press('Space')
        icon_controls(playing=True)
        f.locator('#circuit-card').scroll_into_view_if_needed()
        f.wait_for_function('TrainingCircuit.current().step===1',timeout=7000)
        icon_controls(playing=True)
        press(f.locator('#circuit-play'))
        state=f.evaluate('TrainingCircuit.current()');assert not state['playing']
        icon_controls()
        f.locator('.circuit-controls').screenshot(path=str(out/f'{"formal" if args.public else "local"}-icon-controls.png'))
        page.wait_for_timeout(300)
        assert f.evaluate('TrainingCircuit.current().u')==state['u']
        press(f.locator('#circuit-play'))
        f.locator('#circuit-card').scroll_into_view_if_needed()
        f.wait_for_function('TrainingCircuit.current().step===2&&!TrainingCircuit.current().playing',timeout=14000)
        assert f.evaluate('TrainingCircuit.current().u')==1
        icon_controls()
        assert f.locator('#circuit-next').get_attribute('title')=='已是最后一步'
        press(f.locator('#circuit-play'))
        assert f.evaluate('TrainingCircuit.current().step')==0
        icon_controls(playing=True)
        press(f.locator('#circuit-reset'));assert f.evaluate('TrainingCircuit.current().step')==0
        icon_controls()
        for width in [900,390]:
            page.set_viewport_size({'width':width,'height':1100})
            f.locator('#circuit-card').scroll_into_view_if_needed()
            size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert size['scroll']<=size['client']+1,size
            icon_controls()
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{width}.png'),full_page=True)
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'courses':4,'views':2,'stages':3,'play_pause_finish':True,'icon_controls':True,'flow_topology':True,'mobile':True,'errors':errors}),flush=True)
    finally:context.close();browser.close()
