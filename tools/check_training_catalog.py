"""Read-only browser acceptance for the seven-family training catalogue."""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

platform._wmi = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from product_training import build_training_html
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--public', action='store_true')
args = parser.parse_args()
OUT = ROOT.parent / 'ocr-diagnostic-20261012/training-catalog'
OUT.mkdir(parents=True, exist_ok=True)
host = '''<!doctype html><html><head><style>html,body{margin:0;overflow:hidden}section{height:100vh;overflow:auto;padding:20px;box-sizing:border-box;display:flex;flex-direction:column}iframe{width:100%;border:0}header,footer{height:70px;flex:0 0 70px}#training-wrap{height:1050px;flex:0 0 1050px}</style></head><body><section data-testid="stMain"><header>Training host</header><div id="training-wrap" data-testid="stElementContainer"><iframe src="/lesson" height="1050" scrolling="no" title="Training"></iframe></div><footer>After training</footer></section></body></html>'''
prefix = 'formal' if args.public else 'local'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    ctx = browser.new_context(viewport={'width':1440, 'height':1000})
    if not args.public:
        ctx.route('http://training.local/**', lambda r:r.fulfill(body=build_training_html() if r.request.url.endswith('/lesson') else host, content_type='text/html'))
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/', wait_until='domcontentloaded', timeout=90000)
        f = None
        deadline = time.monotonic()+150
        while time.monotonic()<deadline:
            f = next((x for x in page.frames if x.locator('#training-app').count()), None)
            if f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'), 'New catalogue not ready'
        f.wait_for_function('document.documentElement.dataset.trainingEmbedded==="autoheight"')
        families = f.evaluate('TrainingCatalog.families')
        assert [x['name'] for x in families]==['电容','电阻','电感','晶振','MOS管','二极管','三极管']
        assert f.locator('#courses button').count()==7
        assert f.locator('canvas').count()==1
        scroller = f.parent_frame.locator('[data-testid="stMain"]')
        frame = f.frame_element()
        def activate(loc):
            loc.focus()
            loc.press('Enter')
        def fitted():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.querySelector("#training-app").getBoundingClientRect().height)-12)<=1')
            size = f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
            assert size['w']<=size['c']+1, size
            assert size['h']<=size['v']+1, size
            assert frame.get_attribute('scrolling')=='no'
            assert f.evaluate('document.scrollingElement.scrollTop')==0
        def rendered(id, baseline):
            f.locator('#model-canvas').scroll_into_view_if_needed()
            if baseline:
                f.wait_for_function('!document.getElementById("model-canvas").dataset.subtype')
            else:
                f.wait_for_function('(id)=>document.getElementById("model-canvas").dataset.subtype===id', arg=id)
            fitted()
        seen = []
        photos = {'cap-aluminum','cap-tantalum','xtal-passive','xtal-active','mos-n','mos-p','dio-schottky','bjt-npn'}
        for family in families:
            activate(f.locator('button[data-course="'+family['id']+'"]'))
            children = f.evaluate('(k)=>TrainingCatalog.children(k)', family['id'])
            assert f.locator('#subtypes button').count()==len(children)
            for d in children:
                id = d['id']
                activate(f.locator('button[data-subtype="'+id+'"]'))
                rendered(id, d['baseline'])
                assert f.evaluate('TrainingCatalogUI.current().id')==id
                assert f.locator('button[data-subtype="'+id+'"]').get_attribute('aria-pressed')=='true'
                assert f.locator('button[data-course="'+family['id']+'"]').get_attribute('aria-pressed')=='true'
                assert f.locator('#subtype-application').is_visible()!=d['baseline']
                assert f.locator('#circuit-card').is_visible()==d['baseline']
                assert f.locator('#games-card').is_visible()==d['baseline']
                assert f.locator('.practice-card').is_visible()==d['baseline']
                assert f.locator('.model-card').get_attribute('data-mode')=='exterior'
                if not d['baseline']:
                    assert d['title'] in f.locator('#model-title').inner_text()
                    expected = [p['id'] for p in d['layers'] if p['id'] in d['outerIds']]
                    assert f.locator('#parts button').evaluate_all('(bs)=>bs.map(b=>b.dataset.part)')==expected
                    assert not f.locator('#animate').is_visible()
                    assert not f.locator('#resistor-marking').is_visible()
                    assert d['principle'][0] in f.locator('#subtype-application').inner_text()
                activate(f.locator('#show-cross-section'))
                f.wait_for_function('document.getElementById("model-canvas").dataset.mode==="materials"')
                fitted()
                assert f.locator('#cross-section-card,#material-leaders').count()==0
                if not d['baseline']:
                    assert f.locator('#model-labels button').count()==len(d['layers'])
                    for i, layer in enumerate(d['layers']):
                        marker = f.locator('#model-labels [data-model-material="'+layer['id']+'"]')
                        assert marker.inner_text()==str(i+1)
                        assert marker.is_visible(), (id, layer['id'])
                        activate(marker)
                        assert layer['composition'] in f.locator('#part-detail').inner_text()
                        assert layer['role'] in f.locator('#part-detail').inner_text()
                    canvas = f.locator('#model-canvas')
                    yaw = canvas.get_attribute('data-yaw')
                    canvas.focus();canvas.press('ArrowRight')
                    f.wait_for_function('(old)=>document.getElementById("model-canvas").dataset.yaw!==old', arg=yaw)
                    f.locator('#explode').evaluate('(e)=>{e.value="0.6";e.dispatchEvent(new Event("input",{bubbles:true}));}')
                    assert f.locator('#explode-value').inner_text()=='60%'
                    activate(f.locator('#tab-spec'))
                    assert d['specs'][0][0] in f.locator('#panel-spec').inner_text()
                    activate(f.locator('#tab-performance'))
                    config = f.evaluate('(id)=>TrainingCatalogLabs.config(id)', id)
                    for val, text in config['options']:
                        jsval = 'true' if val is True else 'false' if val is False else str(val)
                        f.locator('#catalog-lab-choice').select_option(jsval)
                        expected = f.evaluate('(x)=>TrainingCatalogLabs.evaluate(x.id,x.value)', {'id':id,'value':val})
                        for _,value in expected['metrics']:
                            assert value in f.locator('#catalog-lab-results').inner_text(), (id,value)
                    activate(f.locator('#tab-principle'))
                    assert d['principle'][0] in f.locator('#panel-principle').inner_text()
                    activate(f.locator('#tab-quiz'))
                    activate(f.locator('[data-catalog-answer="'+str((d['quiz']['answer']+1)%3)+'"]'))
                    assert '再想一想' in f.locator('#catalog-quiz-feedback').inner_text()
                    activate(f.locator('[data-catalog-answer="'+str(d['quiz']['answer'])+'"]'))
                    assert '回答正确' in f.locator('#catalog-quiz-feedback').inner_text()
                    assert '已答对' in f.locator('#subtypes [data-subtype="'+id+'"]').inner_text()
                    assert f.locator('#sources a').evaluate_all('(as)=>as.map(a=>a.href)')==[s[1] for s in d['sources']]
                    activate(f.locator('#tab-spec'))
                    if id in photos:
                        f.locator('.model-card').screenshot(path=str(OUT/f'{prefix}-{id}-materials.png'))
                    activate(f.locator('#model-exterior'))
                    f.wait_for_function('document.getElementById("model-canvas").dataset.mode==="exterior"')
                    if id in photos:
                        f.locator('.model-card').screenshot(path=str(OUT/f'{prefix}-{id}-exterior.png'))
                seen.append(id)
            # Returning to the family remembers the last chapter, not an unrelated default.
            activate(f.locator('button[data-course="resistor"]'))
            activate(f.locator('button[data-course="'+family['id']+'"]'))
            assert f.evaluate('TrainingCatalogUI.current().id')==children[-1]['id']
        assert len(seen)==30
        # Programmatic chapter selection also selects the proper family/carrier.
        f.evaluate('TrainingCatalogUI.choose("xtal-passive")')
        rendered('xtal-passive',False)
        assert f.locator('button[data-course="crystal"]').get_attribute('aria-pressed')=='true'
        assert '时钟由放大器输出端取出' in f.locator('#subtype-application').inner_text()
        f.evaluate('TrainingCatalogUI.choose("cap-mlcc")')
        rendered('cap-mlcc',True)
        assert f.evaluate('TrainingLesson.current().course')=='capacitor'
        # Foundations restore their original calculator, markings, games and quiz bank.
        activate(f.locator('button[data-course="resistor"]'))
        activate(f.locator('button[data-subtype="res-thick"]'))
        rendered('res-thick',True)
        activate(f.locator('#tab-performance'))
        assert f.locator('#catalog-lab-choice').count()==0
        assert f.locator('#resistor-marking').is_visible()
        activate(f.locator('#tab-quiz'))
        assert f.locator('[data-answer]').count()==3
        assert f.locator('[data-catalog-answer]').count()==0
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            activate(f.locator('button[data-course="crystal"]'))
            activate(f.locator('button[data-subtype="xtal-active"]'))
            activate(f.locator('#show-cross-section'))
            activate(f.locator('#tab-performance'))
            fitted()
            f.locator('.model-card').screenshot(path=str(OUT/f'{prefix}-width-{width}-model.png'))
            f.locator('.knowledge-card').screenshot(path=str(OUT/f'{prefix}-width-{width}-lab.png'))
            scroller.evaluate('e=>e.scrollTop=0')
            page.wait_for_timeout(120)
            page.screenshot(path=str(OUT/f'{prefix}-width-{width}-top.png'))
            f.locator('.intro h1').hover()
            page.mouse.wheel(0,350);page.wait_for_timeout(150)
            assert scroller.evaluate('e=>e.scrollTop')>100
            assert f.evaluate('document.scrollingElement.scrollTop')==0
            f.locator('.references .source-note').scroll_into_view_if_needed()
            bounds=f.locator('.references .source-note').bounding_box()
            assert bounds and bounds['y']>=-1 and bounds['y']+bounds['height']<=1001, bounds
            fitted()
        page.reload(wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#subtypes').count()),None)
            if f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f.evaluate('TrainingCatalogUI.current().id')=='res-thick'
        assert not f.locator('#subtypes').inner_text().count('已答对')
        assert not errors, errors
        print(json.dumps({'status':'passed','public':args.public,'families':7,'chapters':len(seen),'numbered_3d_parts':True,'labs_quizzes_sources':True,'baseline_preserved':True,'single_outer_scroll':True,'widths':[1440,900,390],'errors':errors}),flush=True)
    except Exception:
        page.screenshot(path=str(OUT/f'{prefix}-failure.png'))
        print(json.dumps({'browser_errors':errors}),flush=True)
        raise
    finally:
        ctx.close();browser.close()
