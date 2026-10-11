"""Training iframe expands/shrinks; only its host page owns vertical scrolling."""
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
out=ROOT.parent/'dark-ui-test/test-runtime/visual-qa/training-single-scroll'
out.mkdir(parents=True,exist_ok=True)
host='''<!doctype html><html><head><style>html,body{margin:0;overflow:hidden}section{height:100vh;overflow:auto;padding:20px;box-sizing:border-box}iframe{width:100%;border:0}header{height:70px}#training-wrap{height:1050px}#other-wrap{height:82px}footer{height:70px}</style></head><body><section data-testid="stMain"><header>Training host</header><div id="training-wrap" data-testid="stElementContainer"><iframe src="/lesson" height="1050" scrolling="no" title="Training"></iframe></div><footer>After training</footer><div id="other-wrap" data-testid="stElementContainer"><iframe src="/other" height="82" scrolling="auto" title="Unrelated preview"></iframe></div></section></body></html>'''
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000})
    if not args.public:
        def route(r):
            body=build_training_html() if r.request.url.endswith('/lesson') else '<div style="height:250px">Unrelated</div>' if r.request.url.endswith('/other') else host
            r.fulfill(body=body,content_type='text/html')
        context.route('http://training.local/**',route)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/',wait_until='domcontentloaded',timeout=90000)
        f=None;deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f and f.evaluate('document.documentElement.dataset.trainingEmbedded==="autoheight"'):break
            page.wait_for_timeout(300)
        assert f is not None
        assert f.evaluate('document.documentElement.dataset.trainingEmbedded')=='autoheight'
        frame=f.frame_element();parent=f.parent_frame
        scroller=parent.locator('[data-testid="stMain"]')
        assert scroller.count()==1
        def press(n):n.focus();n.press('Enter')
        def fitted():
            f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.querySelector("#training-app").getBoundingClientRect().height)-12)<=1')
            dimensions=f.evaluate('({viewport:innerHeight,scroll:document.documentElement.scrollHeight,bottom:document.querySelector(".references").getBoundingClientRect().bottom})')
            assert dimensions['scroll']<=dimensions['viewport']+1,dimensions
            assert dimensions['bottom']<=dimensions['viewport'],dimensions
            assert f.evaluate('getComputedStyle(document.documentElement).overflowY')=='hidden'
            assert frame.get_attribute('scrolling')=='no'
            assert frame.evaluate('e=>Math.abs(e.parentElement.getBoundingClientRect().height-e.getBoundingClientRect().height)<=1')
            return dimensions['viewport']
        fitted()
        # A regular wheel over the embedded introduction scrolls the host, not the lesson.
        scroller.evaluate('e=>e.scrollTop=0')
        f.locator('.intro h1').hover()
        page.mouse.wheel(0,500);page.wait_for_timeout(250)
        assert scroller.evaluate('e=>e.scrollTop')>100
        assert f.evaluate('document.scrollingElement.scrollTop')==0
        for width in [1440,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            for course in ['resistor','capacitor','inductor','diode']:
                press(f.locator('button[data-course="'+course+'"]'));fitted()
                for tab in ['performance','principle','quiz','spec']:
                    press(f.locator('#tab-'+tab));fitted()
                closed=fitted()
                press(f.locator('#cross-section-card>.reference-section-toggle'))
                opened=fitted();assert opened>closed+200,(closed,opened)
                press(f.locator('#cross-section-card>.reference-section-toggle'))
                assert abs(fitted()-closed)<=2
                press(f.locator('#show-cross-section'));fitted()
                press(f.locator('#model-exterior'));fitted()
            press(f.locator('#tool-decode'))
            press(f.locator('#decode-examples button').first);fitted()
            before=fitted();page.wait_for_timeout(250)
            assert fitted()==before,'Unexpected height growth'
            # Last reference text is reachable through the outer scroll area.
            f.locator('.references .source-note').scroll_into_view_if_needed()
            box=f.locator('.references .source-note').bounding_box()
            assert box and box['y']>=-1 and box['y']+box['height']<=1001,box
            assert f.evaluate('document.scrollingElement.scrollTop')==0
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-bottom-{width}.png'))
            scroller.evaluate('e=>e.scrollTop=0');page.wait_for_timeout(100)
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-top-{width}.png'))
        if not args.public:
            assert page.locator('#other-wrap iframe').get_attribute('scrolling')=='auto'
            assert page.locator('#other-wrap').evaluate('e=>e.getBoundingClientRect().height')==82
            assert page.locator('#other-wrap iframe').get_attribute('data-training-autoheight') is None
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'only_host_scroll':True,'wheel_and_bottom_reachability':True,'courses':4,'modes_and_tabs':True,'expansion_and_shrink':True,'widths':[1440,900,390],'browser_errors':errors}),flush=True)
    finally:context.close();browser.close()
