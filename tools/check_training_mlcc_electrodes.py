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
            const d=boxes.filter(b=>b.id==='dielectric'),m=boxes.filter(b=>b.id==='internal'),cu=boxes.filter(b=>b.id==='base'),covers=boxes.filter(b=>['upper_cover','lower_cover'].includes(b.id));
            if(d.length!==5||m.length!==6||covers.length!==2)throw Error('Missing dielectric/electrode/cover layers');
            m.forEach((b,i)=>{
                if(b.s[1]<.06||Math.abs(b.c[2]+b.s[2]/2-(d[0].c[2]+d[0].s[2]/2))>1e-9)throw Error('Recessed/invisible electrode');
                const side=i%2?1:-1,own=cu.find(t=>Math.sign(t.c[0])===side),other=cu.find(t=>Math.sign(t.c[0])!==side);
                const overlap=t=>Math.min(b.c[0]+b.s[0]/2,t.c[0]+t.s[0]/2)-Math.max(b.c[0]-b.s[0]/2,t.c[0]-t.s[0]/2);
                if(overlap(own)<=0||overlap(other)>=0)throw Error('Incorrect alternating termination');
            });
            covers.forEach(c=>{
                if(c.s[1]<=d[0].s[1]||JSON.stringify(c.col)===JSON.stringify(d[0].col))throw Error('Indistinct cover');
                m.forEach(b=>{if(Math.min(c.c[1]+c.s[1]/2,b.c[1]+b.s[1]/2)-Math.max(c.c[1]-c.s[1]/2,b.c[1]-b.s[1]/2)>1e-9)throw Error('Electrode in cover');});
            });
            return {explosion:e,dielectric:d.length,electrodes:m.length,covers:covers.length,thickness:m[0].s[1]};
        })''')
        assert f.evaluate('''()=>{
            const box=(f,p,s,color,id)=>f.push({p,s,color,id}),primitives={box,tube:()=>{}};
            return [0,.05,.1,.5,1].every(e=>{
                const a=TrainingMaterialGeometry.build('capacitor',e,primitives),b=TrainingMaterialGeometry.buildCapacitorStructure(e,primitives),map={dielectric:'dielectric',internal:'electrode',base:'terminal',barrier:'terminal',tin:'terminal',upper_cover:'upper_cover',lower_cover:'lower_cover'};
                return JSON.stringify(b.faces)===JSON.stringify(a.faces.map(f=>({...f,id:map[f.id]})))&&JSON.stringify(b.anchors.map(a=>a.id))==='["dielectric","electrode","terminal","upper_cover","lower_cover"]';
            });
        }''')

        def visible_bands():
            return f.evaluate('''()=>{
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

        def check_markers():
            assert f.locator('#model-labels').is_visible()
            assert f.locator('#model-labels button').evaluate_all('''ns=>ns.every((n,i)=>{
                const a=n.getBoundingClientRect(),p=n.parentElement.getBoundingClientRect();
                return a.width>=44&&a.height>=44&&a.left>=p.left&&a.right<=p.right+1&&a.top>=p.top&&a.bottom<=p.bottom+1&&ns.slice(i+1).every(m=>{
                    const b=m.getBoundingClientRect();return a.right<=b.left+.1||b.right<=a.left+.1||a.bottom<=b.top+.1||b.bottom<=a.top+.1;
                });
            })''')

        observations = []
        for mode in ['materials']:
            press(f.locator('#model-exterior' if mode == 'exterior' else '#show-cross-section'))
            assert '内电极' in f.locator('.model-note').inner_text()
            assert f.locator('#model-labels button').count() == (5 if mode == 'exterior' else 7)
            assert '上陶瓷盖层 → 内电极与介质叠层 → 下陶瓷盖层' in f.locator('.model-note').inner_text()
            assert '真实内电极被陶瓷包覆' in f.locator('.model-note').inner_text()
            selector = '[data-model-part="electrode"]' if mode == 'exterior' else '[data-model-material="internal"]'
            selected = 'electrode' if mode == 'exterior' else 'internal'
            for width in [1440, 900, 390]:
                page.set_viewport_size({'width': width, 'height': 1100})
                for exploded in [False, True]:
                    old_frame = int(canvas.get_attribute('data-frames') or '0')
                    press(f.locator('#reset-view'))
                    f.locator('#explode').focus()
                    f.locator('#explode').press('End' if exploded else 'Home')
                    press(f.locator('#parts [data-part="dielectric"]'))
                    reveal()
                    f.wait_for_function('''v=>{
                        const c=document.querySelector('#model-canvas'),r=c.getBoundingClientRect();
                        return c.dataset.mode===v[0]&&c.dataset.course==='capacitor'&&TrainingLesson.current().explosion===v[1]&&Number(c.dataset.frames)>v[2]&&Math.abs(c.width/r.width-Math.min(devicePixelRatio,2))<.02;
                    }''', arg=[mode, 1 if exploded else 0, old_frame])
                    bands = visible_bands()
                    assert bands['max'] >= 6, (mode, width, exploded, bands)
                    check_markers()
                    assert f.locator(selector).is_visible()
                    assert f.locator(selector).inner_text() == '2'
                    assert f.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1')
                    prefix = f'{"formal" if args.public else "local"}-{mode}-{width}-{"exploded" if exploded else "closed"}'
                    f.locator('.model-card').screenshot(path=str(out / f'{prefix}.png'))
                    observations.append({'mode': mode, 'width': width, 'exploded': exploded, 'bands': bands})
                    # Native activation of the number, not only the bottom list/API.
                    press(f.locator(selector))
                    assert f.evaluate('TrainingLesson.current().part') == selected
                    assert f.locator('#part-detail>strong').inner_text().startswith('2 · ')
                    assert f.locator(selector).get_attribute('aria-pressed') == 'true'
                    if mode == 'materials':
                        assert '镍' in f.locator('#part-detail').inner_text()
                    for cover_id, cover_name, number in [('upper_cover', '上陶瓷盖层', 4 if mode == 'exterior' else 6), ('lower_cover', '下陶瓷盖层', 5 if mode == 'exterior' else 7)]:
                        attr = 'data-model-part' if mode == 'exterior' else 'data-model-material'
                        marker = f.locator(f'[{attr}="{cover_id}"]')
                        assert marker.is_visible()
                        assert marker.inner_text() == str(number)
                        marker.click() if not args.public else press(marker)
                        assert f.evaluate('TrainingLesson.current().part') == cover_id
                        assert marker.get_attribute('aria-pressed') == 'true'
                        detail = f.locator('#part-detail').inner_text()
                        assert cover_name in detail and ('不含内电极' in detail or '保护区域' in detail)
                        if mode == 'materials':
                            assert '一体' in detail
                            assert f.locator('#part-detail a[href*="AVX-Hi-CV"]').count() == 1
                        if not exploded and width in [1440, 390]:
                            reveal()
                            f.locator('.model-card').screenshot(path=str(out / f'{prefix}-{cover_id}.png'))
                    press(f.locator(selector))
                    reveal()
                    old_yaw = canvas.get_attribute('data-yaw')
                    canvas.press('ArrowRight')
                    canvas.press('+')
                    f.wait_for_function('v=>document.querySelector("#model-canvas").dataset.yaw!==v', arg=old_yaw)
                    check_markers()
                    assert f.locator(selector).is_visible()
                    assert float(canvas.get_attribute('data-zoom')) > 1
                    assert f.locator('#cross-section-card,#material-leaders').count() == 0
            # Also reproduce the user's upper-facing angle at 0%, with no hidden 2.
            press(f.locator('#reset-view'))
            f.locator('#explode').focus()
            f.locator('#explode').press('Home')
            reveal()
            old_frame = int(canvas.get_attribute('data-frames'))
            for _ in range(8):
                canvas.press('ArrowDown')
            f.wait_for_function('v=>Number(document.querySelector("#model-canvas").dataset.frames)>v', arg=old_frame)
            check_markers()
            assert f.locator(selector).is_visible()
            f.locator('.model-card').screenshot(path=str(out / f'{"formal" if args.public else "local"}-{mode}-upper-angle.png'))
        # The field lesson remains available only inside, never through a sealed body.
        press(f.locator('#animate'))
        reveal()
        assert f.locator('#animate').get_attribute('aria-pressed') == 'true'
        old_frame = int(canvas.get_attribute('data-frames'))
        f.wait_for_function('v=>Number(document.querySelector("#model-canvas").dataset.frames)>v+2', arg=old_frame)
        check_markers()
        assert f.locator('[data-model-material="internal"]').is_visible()
        assert f.evaluate('''()=>{
            const boxes=[],box=(f,p,s,color,id)=>{boxes.push({p,s,color,id});f.push({p,s,color,id});};
            const ext=TrainingMaterialGeometry.buildCapacitorExterior({box});
            return boxes.length===3&&boxes.filter(b=>b.id==='body').length===1&&boxes.filter(b=>b.id==='terminal').length===2&&JSON.stringify(ext.anchors.map(a=>a.id))==='["body","terminal"]';
        }''')
        f.locator('#explode').focus()
        f.locator('#explode').press('End')
        old_state = f.evaluate('TrainingLesson.current()')
        press(f.locator('#model-exterior'))
        for width in [1440, 900, 390]:
            page.set_viewport_size({'width': width, 'height': 1100})
            reveal()
            press(f.locator('#reset-view'))
            press(f.locator('#parts [data-part="body"]'))
            f.wait_for_function('document.querySelector("#model-canvas").dataset.mode==="exterior"&&document.querySelector("#model-canvas").dataset.meshFaces==="18"')
            assert f.locator('#parts button').count() == 2
            assert f.locator('#model-labels button').count() == 2
            assert f.locator('[data-model-part="electrode"],[data-model-part="upper_cover"],[data-model-part="lower_cover"]').count() == 0
            assert not f.locator('.explode-control').is_visible()
            assert not f.locator('#animate').is_visible()
            assert f.locator('#animate').get_attribute('aria-pressed') == 'false'
            assert f.locator('#state-badge').inner_text() == '完整外观'
            assert '完整外观' in f.locator('.model-note').inner_text()
            # Sample the middle of the ceramic face, not the grey end caps
            # that intersect full-height perspective columns at the edges.
            # Actual mesh count separately proves only the three closed boxes.
            assert f.evaluate('''()=>{
                const c=document.querySelector('#model-canvas'),b=TrainingLesson.bounds(),scale=c.width/c.getBoundingClientRect().width;
                const x=Math.round((b.left+b.right)/2*scale),y=Math.round((b.top+(b.bottom-b.top)*.3)*scale),h=Math.max(1,Math.round((b.bottom-b.top)*.4*scale));
                const p=c.getContext('2d').getImageData(x,y,1,h).data;
                for(let i=0;i<p.length;i+=4){const R=p[i],G=p[i+1],B=p[i+2];if(R<145&&G>R+8&&B>G+8&&B-R<80&&G<180)return false;}
                return true;
            }'''), 'Electrode-coloured stripe inside the external ceramic face'
            check_markers()
            for part in ['body', 'terminal']:
                marker = f.locator('[data-model-part="'+part+'"]')
                marker.click() if not args.public else press(marker)
                assert f.evaluate('TrainingLesson.current().part') == part
                assert marker.get_attribute('aria-pressed') == 'true'
            f.locator('.model-card').screenshot(path=str(out / f'{"formal" if args.public else "local"}-sealed-exterior-{width}.png'))
            reveal()
            old_yaw = canvas.get_attribute('data-yaw')
            canvas.press('ArrowRight')
            canvas.press('+')
            f.wait_for_function('v=>document.querySelector("#model-canvas").dataset.yaw!==v', arg=old_yaw)
            check_markers()
            assert f.evaluate('TrainingLesson.current().params') == old_state['params']
            assert f.evaluate('TrainingLesson.current().explosion') == old_state['explosion']
        press(f.locator('#show-cross-section'))
        reveal()
        f.wait_for_function('document.querySelector("#model-canvas").dataset.mode==="materials"')
        assert f.locator('#model-labels button').count() == 7
        assert f.locator('.explode-control').is_visible()
        assert f.locator('#animate').is_visible() and not f.locator('#animate').is_disabled()
        assert f.evaluate('TrainingLesson.current().explosion') == 1
        press(f.locator('#model-exterior'))
        for course in ['resistor', 'inductor', 'diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            assert not f.locator('#model-labels').is_visible()
            assert f.locator('[data-model-part]').count() == 0
        assert not errors, errors
        print(json.dumps({'status': 'passed', 'public': args.public, 'geometry': geometry, 'sealed_exterior_distinct_from_cutaway': True, 'upper_lower_cover_selection': True, 'visible_electrode_bands': observations, 'browser_errors': errors}), flush=True)
    finally:
        context.close()
        browser.close()
