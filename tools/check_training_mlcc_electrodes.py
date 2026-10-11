"""Verify exposed MLCC electrodes in the real training canvas and release bundle."""
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
out = ROOT.parent / 'dark-ui-test/test-runtime/visual-qa/training-mlcc-electrodes'
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1100})
    if not args.public:
        context.route('http://training.local/**', lambda r: r.fulfill(body=build_training_html(), content_type='text/html'))
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/', wait_until='domcontentloaded', timeout=90000)
        f = None
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            f = next((x for x in page.frames if x.locator('#show-cross-section').count()), None)
            if f:
                break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingLesson!=="undefined"')
        canvas = f.locator('#model-canvas')

        def press(locator):
            locator.focus()
            locator.press('Enter')

        def reveal():
            canvas.scroll_into_view_if_needed()
            canvas.focus()
            if args.public:
                f.wait_for_function('Math.abs(innerHeight-Math.ceil(document.querySelector("#training-app").getBoundingClientRect().height)-12)<=1')
                host = f.parent_frame.locator('[data-testid="stMain"]')
                assert host.count() == 1
                box, host_box = canvas.bounding_box(), host.bounding_box()
                host.evaluate('(e,dy)=>e.scrollTop+=dy', box['y'] + box['height'] / 2 - host_box['y'] - host_box['height'] / 2)

        press(f.locator('button[data-course="capacitor"]'))
        press(f.locator('#show-cross-section'))
        assert '深灰色薄片是镍内电极' in f.locator('.model-note').inner_text()
        # Check the actual published geometry, not only the local test fixture.
        geometry = f.evaluate('''()=>[0,.5,1].map(e=>{
            const boxes=[];
            TrainingMaterialGeometry.build('capacitor',e,{box:(faces,c,s,col,id)=>{boxes.push({id,c,s,col});},tube:()=>[]});
            const d=boxes.filter(b=>b.id==='dielectric'),m=boxes.filter(b=>b.id==='internal'),cu=boxes.filter(b=>b.id==='base');
            if(d.length!==7||m.length!==6)throw Error('Missing dielectric/electrode layers');
            m.forEach((b,i)=>{
                if(b.s[1]<.06||Math.abs(b.c[2]+b.s[2]/2-(d[i].c[2]+d[i].s[2]/2))>1e-9)throw Error('Recessed/invisible electrode');
                const side=i%2?1:-1,own=cu.find(t=>Math.sign(t.c[0])===side),other=cu.find(t=>Math.sign(t.c[0])!==side);
                const overlap=t=>Math.min(b.c[0]+b.s[0]/2,t.c[0]+t.s[0]/2)-Math.max(b.c[0]-b.s[0]/2,t.c[0]-t.s[0]/2);
                if(overlap(own)<=0||overlap(other)>=0)throw Error('Incorrect alternating termination');
            });
            return {explosion:e,dielectric:d.length,electrodes:m.length,thickness:m[0].s[1]};
        })''')
        observations = []
        for width in [1440, 900, 390]:
            page.set_viewport_size({'width': width, 'height': 1100})
            for exploded in [False, True]:
                press(f.locator('#reset-view'))
                f.locator('#explode').focus()
                f.locator('#explode').press('End' if exploded else 'Home')
                press(f.locator('#parts [data-part="dielectric"]'))
                reveal()
                f.wait_for_function('v=>{const c=document.querySelector("#model-canvas");return c.dataset.mode==="materials"&&c.dataset.course==="capacitor"&&TrainingLesson.current().explosion===v;}', arg=1 if exploded else 0)
                # Wait for resized/selected geometry to be visibly painted.
                f.wait_for_function('''()=>{
                    const c=document.querySelector('#model-canvas'),r=c.getBoundingClientRect();
                    return Math.abs(c.width/r.width-devicePixelRatio)<.02&&Number(c.dataset.meshFaces)>0;
                }''')
                bands = f.evaluate('''()=>{
                    const c=document.querySelector('#model-canvas'),ctx=c.getContext('2d'),r=c.getBoundingClientRect(),scale=c.width/r.width,b=TrainingLesson.bounds();
                    const counts=[];
                    for(const offset of [-.12,-.06,0,.06,.12]){
                        const x=Math.round(((b.left+b.right)/2+offset*b.width)*scale),p=ctx.getImageData(x,0,1,c.height).data;
                        let run=0,count=0; const end=()=>{if(run>=Math.ceil(2*scale))count++;run=0;};
                        for(let y=0;y<c.height;y++){
                            const i=y*4,R=p[i],G=p[i+1],B=p[i+2];
                            if(R<145&&G>R+8&&B>G+8&&B-R<80&&G<180)run++;else end();
                        }
                        end();counts.push(count);
                    }
                    return {counts,max:Math.max(...counts),scale};
                }''')
                assert bands['max'] >= 6, (width, exploded, bands)
                assert f.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1')
                f.locator('.model-card').screenshot(path=str(out / f'{"formal" if args.public else "local"}-{width}-{"exploded" if exploded else "closed"}.png'))
                observations.append({'width': width, 'exploded': exploded, 'bands': bands})
                press(f.locator('[data-model-material="internal"]'))
                assert f.evaluate('TrainingLesson.current().part') == 'internal'
                assert '镍' in f.locator('#part-detail').inner_text()
                assert f.locator('[data-model-material="internal"]').get_attribute('aria-pressed') == 'true'
                assert f.locator('#cross-section-card,#material-leaders').count() == 0
        assert not errors, errors
        print(json.dumps({'status': 'passed', 'public': args.public, 'geometry': geometry, 'visible_electrode_bands': observations, 'browser_errors': errors}), flush=True)
    finally:
        context.close()
        browser.close()
