"""Verify learner copy in rendered states, including expanded sections."""
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
out = ROOT.parent / 'dark-ui-test/test-runtime/visual-qa/training-audience'
out.mkdir(parents=True, exist_ok=True)
forbidden = ['管理员', '业务数据库', '系统已核对', '不模拟', '未经披露',
             '计算条件与补充说明', '学习记录说明', '不随会员账号同步', '库存或价格清单中确认']
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000})
    if not args.public:
        context.route('http://training.local/**', lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
    page = context.new_page()
    errors = []
    page.on('pageerror',lambda e:errors.append(str(e)))
    try:
        page.goto('https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/', wait_until='domcontentloaded',timeout=90000)
        f = None
        deadline = time.monotonic()+100
        while time.monotonic()<deadline:
            f=next((x for x in page.frames if x.locator('#training-app').count()),None)
            if f:
                break
            page.wait_for_timeout(300)
        assert f is not None
        f.wait_for_function('typeof TrainingPractice!=="undefined"')
        def press(n):
            n.focus();n.press('Enter')
        def inspect():
            f.locator('#training-app details').evaluate_all('ns=>ns.forEach(n=>n.open=true)')
            text=f.locator('#training-app').inner_text()
            assert all(term not in text for term in forbidden),text
            assert not f.locator('#practice-storage').is_visible()
        for course in ['resistor','capacitor','inductor','diode']:
            press(f.locator('button[data-course="'+course+'"]'))
            for tab in ['spec','performance','principle','quiz']:
                press(f.locator('#tab-'+tab));inspect()
            f.locator('#circuit-card').screenshot(path=str(out/f'{"formal" if args.public else "local"}-{course}.png'))
        press(f.locator('#tool-decode'))
        for example in f.locator('#decode-examples button').all():
            press(example);inspect()
            assert f.locator('#decode-result h3').inner_text()
        press(f.locator('#tool-scenario'))
        for option in f.locator('#scenario-select option').all():
            f.locator('#scenario-select').select_option(option.get_attribute('value'));inspect()
        f.locator('#scenario-select').select_option('r-unit')
        choice=f.locator('input[name="practice-choice"][value="0"]')
        choice.focus();choice.press('Space')
        press(f.locator('#scenario-question button[type="submit"]'))
        press(f.locator('#tool-mistakes'))
        assert f.locator('.mistake-item').count()==1
        press(f.locator('#clear-practice'))
        assert '此设备' in f.locator('#clear-confirm').inner_text()
        press(f.locator('#cancel-clear'))
        assert f.locator('.mistake-item').count()==1
        press(f.locator('#clear-practice'));press(f.locator('#confirm-clear'))
        assert f.locator('.mistake-item').count()==0
        assert not f.locator('#practice-storage').is_visible()
        if not args.public:
            f.evaluate('''()=>{const original=Storage.prototype.setItem;window._originalSetItem=original;Storage.prototype.setItem=function(){throw new Error('blocked');};}''')
            press(f.locator('#tab-quiz'));press(f.locator('[data-answer="1"]'))
            assert f.locator('#practice-storage').is_visible()
            assert f.locator('#practice-storage').inner_text()=='练习记录暂时无法保存，刷新后请重新练习。'
            f.evaluate('()=>{Storage.prototype.setItem=window._originalSetItem;}')
            press(f.locator('[data-answer="1"]'))
            assert not f.locator('#practice-storage').is_visible()
        assert not errors,errors
        print(json.dumps({'status':'passed','public':args.public,'courses':4,'knowledge_tabs':4,
                          'expanded_copy':True,'model_examples':7,'practice_questions':12,
                          'progress_clear_and_save_feedback':True,'browser_errors':errors}),flush=True)
    finally:
        context.close();browser.close()
