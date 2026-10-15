"""Native Chrome cold-start texture regression; no business DBs or progress injection.

Delay only the real bundled PCB image, then release its native decoder. Check
the unpowered first frame and repaint without pointer interaction. --repro
records the old black-until-drag defect rather than expecting the repair.
Phone is Chrome iPhone 15 Pro emulation, not physical Safari.
"""
import argparse
import json
import platform
import time
from pathlib import Path

platform._wmi = None
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
for flag in ['public', 'phone', 'repro', 'quick', 'lifecycle-only']:
    parser.add_argument('--' + flag, action='store_true')
args = parser.parse_args()
out = Path(__file__).resolve().parents[2] / 'ocr-diagnostic-20261015/training-texture'
out.mkdir(parents=True, exist_ok=True)
label = ('formal' if args.public else 'local') + ('-phone' if args.phone else '-desktop')
if args.repro:
    label += '-before'

HOLD_IMAGE = """(()=>{
 const NativeImage=window.Image,src=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
 const pending=[];window.__pcbImages=pending;
 window.Image=function(...args){const image=new NativeImage(...args);
  Object.defineProperty(image,'src',{get(){return src.get.call(this);},set(value){
   if(value===window.TrainingPlaygroundAssets?.pcb)pending.push({image,value,released:false});
   else src.set.call(this,value);
  }});return image;
 };
 window.__releasePcb=async()=>{const batch=pending.filter(x=>!x.released);
  await Promise.all(batch.map(x=>new Promise((resolve,reject)=>{
   x.released=true;x.image.addEventListener('load',resolve,{once:true});
   x.image.addEventListener('error',reject,{once:true});src.set.call(x.image,x.value);
  })));return batch.length;
 };
})();"""

def green_fraction(path):
    image = Image.open(path).convert('RGB')
    return sum(g > r * 1.15 and g > b * 1.08 and g > 50 for r, g, b in image.get_flattened_data()) / (image.width * image.height)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    device = {k: v for k, v in p.devices['iPhone 15 Pro'].items() if k != 'default_browser_type'} if args.phone else {'viewport': {'width': 1440, 'height': 1000}}
    context = browser.new_context(**device)
    context.add_init_script(HOLD_IMAGE)
    page = context.new_page()
    errors = []
    warnings = []
    stage = 'chapters'
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: warnings.append({'stage': stage, 'message': m.text}) if 'INVALID_' in m.text or 'GL_INVALID' in m.text else errors.append(m.text) if m.type == 'error' else None)
    url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://127.0.0.1:8534/'
    page.goto(url, wait_until='domcontentloaded', timeout=90000)
    deadline = time.monotonic() + 180
    again = time.monotonic() + 15
    f = None
    while time.monotonic() < deadline:
        f = next((x for x in page.frames if x.locator('#training-app').count()), None)
        if f and f.evaluate('typeof TrainingCatalog!=="undefined" && typeof __releasePcb==="function"') and f.locator('#playground-action').count() and (args.repro or f.evaluate('TrainingPlaygroundScene.create.toString().includes("pcbFallback")')):
            break
        if args.public and time.monotonic() > again:
            page.reload(wait_until='domcontentloaded', timeout=90000)
            again = time.monotonic() + 15
        page.wait_for_timeout(250)
    else:
        raise AssertionError('Training not available')

    def press(selector):
        node = f.locator(selector)
        assert node.count() == 1 and node.is_visible() and node.is_enabled(), selector
        if args.phone:
            node.scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            node.tap()
        else:
            node.focus()
            node.press('Enter')

    def select(d):
        press('button[data-course="' + d['family'] + '"]')
        press('button[data-subtype="' + d['id'] + '"]')
        press('[data-learning-target="game"]')

    def snapshot(d):
        engine = 'TrainingPlayground' if d['baseline'] else 'TrainingSubtypeGame'
        return f.evaluate(engine + '.current().snapshot()')

    def capture(canvas, name):
        path = out / (label + '-' + name + '.png')
        canvas.screenshot(path=str(path))
        return green_fraction(path)

    catalog = f.evaluate('TrainingCatalog.lessons.map(d=>({id:d.id,family:d.family,baseline:!!d.baseline}))')
    if args.lifecycle_only:
        catalog = []
    if args.repro:
        catalog = [next(d for d in catalog if d['id'] == 'mos-n')]
    elif args.quick:
        catalog = [d for d in catalog if d['id'] in ['res-thick', 'cap-mlcc', 'cap-aluminum', 'ind-wound', 'xtal-passive', 'mos-n', 'mos-p', 'dio-switch', 'bjt-npn']]
    cases = []
    for d in catalog:
        select(d)
        canvas = f.locator('.play-viewport canvas').first
        canvas.scroll_into_view_if_needed()
        page.wait_for_timeout(350)
        before = snapshot(d)
        assert before['scene']['markers'] == 0 and before['scene']['phase'] == 0
        assert not (before['params']['power'] if d['baseline'] else before['progress']['started'])
        assert not before['playing']
        phase = before['scene']['phase']
        pending = capture(canvas, d['id'] + '-pending')
        frames = int(canvas.get_attribute('data-frames'))
        released = f.evaluate('__releasePcb()')
        assert released >= 1
        page.wait_for_timeout(180)
        loaded = capture(canvas, d['id'] + '-loaded')
        after_frames = int(canvas.get_attribute('data-frames'))
        after = snapshot(d)
        assert after['scene']['phase'] == phase and after['scene']['markers'] == 0
        assert after['progress'] == before['progress'] and not after['playing']
        row = {'id': d['id'], 'pending_green': pending, 'loaded_green': loaded, 'frames': [frames, after_frames], 'phase': phase}
        if args.repro:
            assert loaded < .025 and after_frames == frames, row
            rect = canvas.bounding_box()
            page.mouse.move(rect['x'] + rect['width'] * .5, rect['y'] + rect['height'] * .5)
            page.mouse.down()
            page.mouse.move(rect['x'] + rect['width'] * .5 + 30, rect['y'] + rect['height'] * .5 + 12, steps=4)
            page.mouse.up()
            row['drag_green'] = capture(canvas, d['id'] + '-drag')
            assert row['drag_green'] > .04, row
        else:
            assert pending > .04 and loaded > .04 and after_frames > frames, row
            assert canvas.get_attribute('data-texture-loaded') == 'true'
            # A new frame must contain the real texture, not just the placeholder.
            first = Image.open(out / (label + '-' + d['id'] + '-pending.png')).convert('RGB')
            second = Image.open(out / (label + '-' + d['id'] + '-loaded.png')).convert('RGB')
            row['texture_difference'] = sum(ImageStat.Stat(ImageChops.difference(first, second)).mean)
            assert row['texture_difference'] > 1, row
        cases.append(row)
        print(json.dumps(row), flush=True)

    lifecycle = []
    assert not errors and not warnings, {'errors': errors, 'warnings': warnings}
    if not args.repro:
        # Exercise each actual renderer directly without unlocking a project or
        # changing any course state. Simulate native WebGL context loss while
        # its real Image decoder is held, then restore without a camera gesture.
        for engine in ['foundation', 'subtype', 'project']:
            def create_probe():
                f.evaluate('''engine=>{
                 const canvas=document.createElement('canvas');canvas.id='texture-probe';
                 canvas.style.cssText='display:block;width:100%;max-width:600px;height:400px;';document.getElementById('training-app').append(canvas);
                 let scene;
                 if(engine==='foundation'){
                  scene=TrainingPlaygroundScene.create(canvas,TrainingPlaygroundAssets.pcb,()=>{});
                  const p={value:330,power:false,near:true,reverse:false};scene.update('resistor',p,TrainingPlaygroundMath.evaluate('resistor',p));
                 }else if(engine==='subtype'){
                  scene=TrainingSubtypeGameScene.create(canvas,'mos-n',()=>{});const s=TrainingSubtypeGameMath.create('mos-n');
                  scene.update(s.params,TrainingSubtypeGameMath.evaluate('mos-n',s.params),false);
                 }else{
                  scene=TrainingNightlightScene.create(canvas,()=>{});const s={...TrainingNightlightMath.setup(0),resistance:330,power:false};
                  scene.update(s,TrainingNightlightMath.result(s));
                 }
                 window.__probe={canvas,scene,lost:false,restored:false};
                 canvas.addEventListener('webglcontextlost',()=>{__probe.lost=true;});
                 canvas.addEventListener('webglcontextrestored',()=>{__probe.restored=true;});scene.resize();
                }''', engine)
                probe = f.locator('#texture-probe')
                probe.scroll_into_view_if_needed()
                page.wait_for_timeout(250)
                return probe

            probe = create_probe()
            stage = engine + '-pending'
            pending = capture(probe, engine + '-context-pending')
            assert pending > .04
            stage = engine + '-context-lost'
            f.evaluate('''()=>{__probe.ext=__probe.canvas.getContext('webgl2').getExtension('WEBGL_lose_context');if(!__probe.ext)throw Error('Context-loss extension unavailable');__probe.ext.loseContext();}''')
            f.wait_for_function('__probe.lost', timeout=6000)
            frames = probe.get_attribute('data-frames')
            f.evaluate('__releasePcb()')
            assert probe.get_attribute('data-texture-loaded') == 'true'
            assert probe.get_attribute('data-frames') == frames
            page.wait_for_timeout(150)
            f.evaluate('__probe.ext.restoreContext()')
            f.wait_for_function('__probe.restored', timeout=6000)
            stage = engine + '-restored'
            loaded = capture(probe, engine + '-context-restored')
            assert loaded > .04 and int(probe.get_attribute('data-frames')) > int(frames)
            assert f.evaluate('__probe.scene.snapshot().phase') == 0
            stage = engine + '-restored-dispose'
            f.evaluate('__probe.scene.dispose();__probe.canvas.remove()')

            probe = create_probe()
            stage = engine + '-pending-dispose'
            frames = probe.get_attribute('data-frames')
            f.evaluate('__probe.scene.dispose()')
            f.evaluate('__releasePcb()')
            assert probe.get_attribute('data-texture-loaded') == 'false'
            assert probe.get_attribute('data-frames') == frames
            assert f.evaluate('__pcbImages.at(-1).image.onload===null')
            f.evaluate('__probe.canvas.remove()')
            lifecycle.append({'engine': engine, 'restore_green': loaded, 'load_during_context_loss': True, 'late_load_after_disposal_ignored': True})
            print(json.dumps(lifecycle[-1]), flush=True)
    (out / (label + '.json')).write_text(json.dumps({'cases': cases, 'lifecycle': lifecycle, 'errors': errors, 'warnings': warnings}, indent=2), encoding='utf-8')
    assert not errors, errors
    # Forced recovery then disposal also emits these vendor cleanup warnings
    # on the unchanged pre-fix renderers. Record them, but keep all normal
    # chapters and any upload/draw warnings strict (including texSubImage).
    cleanup_messages = {'WebGL: INVALID_OPERATION: delete: object does not belong to this context', 'WebGL: INVALID_OPERATION: deleteVertexArray: object does not belong to this context'}
    unexpected = [w for w in warnings if not (w['stage'].endswith('-restored-dispose') and w['message'] in cleanup_messages)]
    assert not unexpected, unexpected[:5]
    print(json.dumps({'status': 'passed', 'chapters': len(cases), 'renderer_lifecycles': len(lifecycle), 'script_errors': len(errors), 'recorded_existing_cleanup_warnings': len(warnings)}), flush=True)
    browser.close()
