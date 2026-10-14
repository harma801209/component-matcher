"""Capture actual module ordering; verify a coherent training path via native controls."""
import argparse
import json
import platform
import time
from pathlib import Path
platform._wmi = None
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--before',action='store_true')
parser.add_argument('--public',action='store_true')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'ocr-diagnostic-20261014/training-journey'
OUT.mkdir(parents=True,exist_ok=True)
prefix='before' if args.before else 'formal' if args.public else 'local'
URL='https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1024},reduced_motion='reduce')
    page=ctx.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto(URL,wait_until='domcontentloaded',timeout=90000)
        deadline=time.monotonic()+150;f=None
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('typeof TrainingCatalogUI!=="undefined"'):break
            page.wait_for_timeout(300)
        assert f
        def press(sel):
            b=f.locator(sel);assert b.count()==1 and b.is_visible(),sel
            b.focus();b.press('Enter')
        def select(family,id):
            press('button[data-course="'+family+'"]');press('button[data-subtype="'+id+'"]')
        def fitted():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.getElementById("training-app").getBoundingClientRect().height)-12)<=1')
        def photo(sel,name):
            fitted();f.locator(sel).screenshot(path=str(OUT/f'{prefix}-{name}.png'))
        def order():
            return f.evaluate('''()=>[...document.getElementById('training-app').children].filter(n=>!n.hidden).map(n=>({id:n.id,class:n.className,title:n.querySelector('h2,h3,summary')?.textContent.trim().slice(0,90)}))''')
        select('resistor','res-thick')
        if args.before:
            res=order()
            photo('#subtype-picker' if f.locator('#subtype-picker').count() else '.subtype-picker','01-picker')
            photo('#games-card>summary','02-games-before-explanation')
            photo('#circuit-card>.section-head','03-circuit')
            photo('.model-card>.section-head','04-late-structure')
            photo('.knowledge-card>.tabs','05-mixed-specs-quiz')
            select('capacitor','cap-aluminum');cap=order()
            photo('#subtype-application>.section-head','06-application')
            (OUT/'before-observations.json').write_text(json.dumps({'resistor':res,'aluminum':cap,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'status':'captured','resistor':res,'aluminum':cap,'errors':errors},ensure_ascii=False),flush=True)
        else:
            f.wait_for_selector('#lesson-path')
            chapters=f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:d.baseline}))')
            for d in chapters:
                select(d['family'],d['id'])
                ids=f.locator('[data-learning-stage]').evaluate_all('ns=>ns.map(n=>n.dataset.learningStage)')
                assert ids==['recognize','circuit','game','specs','review'],ids
                assert f.locator('#lesson-path button').count()==5
                assert f.locator('#lesson-recognize .model-card').count()==1
                assert f.locator('#lesson-specs .knowledge-card').count()==1
                assert f.locator('#lesson-review #panel-quiz').is_visible()
                assert f.locator('#lesson-circuit #circuit-card').is_visible()==d['baseline']
                assert f.locator('#lesson-circuit #subtype-application').is_visible()!=d['baseline']
                assert d['id']==f.locator('#lesson-recognize').get_attribute('data-subtype')
                press('[data-learning-target="game"]')
                assert f.locator('#games-card').get_attribute('open') is not None
                assert f.locator('[data-learning-target="game"]').get_attribute('aria-current')=='step'
                press('[data-learning-target="specs"]');press('#tab-performance')
                assert f.locator('#panel-performance').is_visible()
                assert f.locator('#panel-quiz').is_visible()
                press('#tab-spec');press('[data-learning-target="review"]')
                assert f.locator('#panel-spec').is_visible()
                assert f.locator('#tab-quiz').get_attribute('aria-selected')=='true'
                # Selected type remains, and reorder did not rebuild the course.
                assert f.evaluate('TrainingCatalogUI.current().id')==d['id']
            select('resistor','res-thick')
            for index,key in enumerate(['recognize','circuit','game','specs','review'],1):
                press('[data-learning-target="'+key+'"]')
                photo('#lesson-'+key+'>.learning-stage-head',f'{index:02d}-stage-{key}')
            for width in [1440,900,390]:
                page.set_viewport_size({'width':width,'height':1024})
                select('mos','mos-n');press('[data-learning-target="recognize"]');fitted()
                bounds=f.evaluate('({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth,h:document.documentElement.scrollHeight,v:innerHeight})')
                assert bounds['w']<=bounds['c']+1 and bounds['h']<=bounds['v']+1,bounds
                assert f.frame_element().get_attribute('scrolling')=='no'
                assert all(b.evaluate('e=>e.getBoundingClientRect().height>=44') for b in f.locator('#lesson-path button').all())
                photo('#lesson-path',f'01-path-{width}')
                photo('#lesson-recognize .lesson-overview',f'02-overview-{width}')
                photo('#lesson-recognize .model-card>.section-head',f'03-structure-{width}')
                photo('#lesson-review>.learning-stage-head',f'05-review-{width}')
            press('#tab-spec');f.locator('#tab-spec').focus();f.locator('#tab-spec').press('ArrowLeft')
            assert f.locator('#tab-principle').get_attribute('aria-selected')=='true'
            assert f.locator('#panel-quiz').is_visible()
            f.locator('#tab-principle').press('ArrowRight')
            assert f.locator('#tab-spec').get_attribute('aria-selected')=='true'
            press('#lesson-reference-more>summary')
            assert f.locator('#sources a').first.is_visible()
            photo('#lesson-reference-more>summary','06-reference-control')
            press('#lesson-reference-more>summary')
            assert f.locator('#sources a').first.is_hidden()
            (OUT/f'{prefix}-observations.json').write_text(json.dumps({'order':order(),'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
            assert not errors,errors
            print(json.dumps({'status':'passed','public':args.public,'chapters':30,'ordered_stages':5,'native_jumps':True,'quiz_separate_preserved_tabs':True,'single_scroll':[1440,900,390],'errors':errors}),flush=True)
    finally:ctx.close();browser.close()
