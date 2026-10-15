"""Model label occlusion checks in real Chrome. No business DBs or game writes."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi=None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
for flag in ['public','phone','all']:parser.add_argument('--'+flag,action='store_true')
args=parser.parse_args();out=Path(__file__).resolve().parents[2]/'ocr-diagnostic-20261015/model-labels';out.mkdir(parents=True,exist_ok=True)
label=('formal' if args.public else 'local')+('-phone' if args.phone else '-desktop')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    device={k:v for k,v in p.devices['iPhone 15 Pro'].items() if k!='default_browser_type'} if args.phone else {'viewport':{'width':1440,'height':1000}}
    context=browser.new_context(**device);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    url='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
    page.goto(url,wait_until='domcontentloaded',timeout=90000);deadline=time.monotonic()+180;again=time.monotonic()+15
    while time.monotonic()<deadline:
        f=next((x for x in page.frames if x.locator('#training-app').count()),None)
        if f and f.evaluate('typeof TrainingModelLabels!=="undefined"') and f.locator('#model-canvas[data-label-layout]').count():break
        if args.public and time.monotonic()>again:
            page.reload(wait_until='domcontentloaded',timeout=90000);again=time.monotonic()+15
        page.wait_for_timeout(200)
    else:raise AssertionError('Callout release not ready')
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
    canvas=f.locator('#model-canvas')
    def settle(previous):f.wait_for_function('n=>Number(document.getElementById("model-canvas").dataset.frames)>n',arg=previous,timeout=6000)
    def key(value):
        old=int(canvas.get_attribute('data-frames'));canvas.focus();canvas.press(value);settle(old)
    def inspect():
        d=f.evaluate('''()=>{const c=document.getElementById('model-canvas'),r=c.getBoundingClientRect(),b=TrainingLesson.bounds(),labels=JSON.parse(c.dataset.labelLayout),buttons=[...document.querySelectorAll('#model-labels button')].filter(n=>n.getClientRects().length).map(n=>{const p=n.getBoundingClientRect();return {x:p.left-r.left,y:p.top-r.top,w:p.width,h:p.height,id:n.dataset.modelMaterial||n.dataset.modelPart};});return {b,labels,buttons};}''')
        b=d['b'];assert b['left']>=54 and b['right']<=b['width']-54,d
        assert b['top']>=48 and b['bottom']<=b['height']-48,d
        for i,n in enumerate(d['labels']):
            assert n['x']+22<=b['left']-6 or n['x']-22>=b['right']+6,d
            assert n['x']-22>=0 and n['x']+22<=b['width'] and n['y']-22>=48 and n['y']+22<=b['height']-30,d
            for q in d['labels'][:i]:assert abs(n['x']-q['x'])>=44 or abs(n['y']-q['y'])>=44,d
        if d['buttons']:
            assert len(d['buttons'])==len(d['labels']),d
            for n in d['buttons']:
                assert n['w']>=43.5 and n['h']>=43.5,d
                assert n['x']+n['w']<=b['left']-5 or n['x']>=b['right']+5,d
        return len(d['labels'])
    selected=['res-thick','res-thin','cap-mlcc','cap-aluminum','ind-wound','xtal-passive','mos-n','mos-dual','dio-switch','bjt-npn']
    chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family}))');cases=[]
    for d in chapters:
        if not args.all and d['id'] not in selected:continue
        press('button[data-course="'+d['family']+'"]');press('button[data-subtype="'+d['id']+'"]');press('[data-learning-target="recognize"]')
        canvas.scroll_into_view_if_needed();key('0')
        for mode in ['exterior','materials']:
            old=int(canvas.get_attribute('data-frames'));press('#model-exterior' if mode=='exterior' else '#show-cross-section');canvas.scroll_into_view_if_needed();settle(old)
            count=inspect()
            if d['id']=='mos-n' and mode=='exterior':
                press('#model-labels button:nth-child(2)');assert '2 ·' in f.locator('#part-detail strong').inner_text()
                f.locator('.model-card .viewport').screenshot(path=str(out/(label+'-mos-terminal.png')))
            for k in ['ArrowLeft','ArrowLeft','ArrowUp','+','+','+','+','+','+']:key(k);inspect()
            if mode=='materials':
                old=int(canvas.get_attribute('data-frames'));f.locator('#explode').focus();f.locator('#explode').press('End');canvas.scroll_into_view_if_needed();settle(old);inspect()
                if d['id']=='cap-mlcc':f.locator('.model-card .viewport').screenshot(path=str(out/(label+'-mlcc-exploded.png')))
                f.locator('#explode').focus();f.locator('#explode').press('Home')
            key('0');cases.append({'id':d['id'],'mode':mode,'labels':count});print(json.dumps(cases[-1]),flush=True)
    assert not errors,errors
    report={'status':'passed','cases':len(cases),'labels_outside_geometry':True,'all_labels_retained':True,'rotation_zoom_explosion':True,'script_errors':errors}
    (out/(label+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True);context.close();browser.close()
