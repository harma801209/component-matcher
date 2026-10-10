"""Isolated Chrome context; no business DB imports or writes. --public checks release."""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

platform._wmi = None
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from product_training import build_training_html
from playwright.sync_api import sync_playwright

args = argparse.ArgumentParser()
args.add_argument('--public', action='store_true')
args = args.parse_args()
out = Path(__file__).resolve().parents[2] / 'dark-ui-test/test-runtime/visual-qa/training-practice'
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width':1280,'height':1000})
    if not args.public:
        context.route('http://training.local/**', lambda r: r.fulfill(body=build_training_html(), content_type='text/html'))
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    url = 'https://fruition-component.pages.dev/?training=1' if args.public else 'http://training.local/'
    def lesson_frame():
        deadline = time.monotonic()+100
        while time.monotonic()<deadline:
            for f in page.frames:
                if f.locator('#tool-decode').count():
                    f.wait_for_function('typeof TrainingLesson!=="undefined" && document.querySelector("#practice-storage").textContent.length>0')
                    return f
            page.wait_for_timeout(350)
        raise AssertionError('Training practice tools did not appear')
    def activate(loc):
        loc.focus()
        loc.press('Enter')
    def choose(loc):
        # Trusted keyboard avoids nested iframe auto-scroll coordinate mismatches.
        loc.focus()
        loc.press('Space')
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        f = lesson_frame()
        def decode(model):
            f.locator('#decode-input').fill(model)
            f.locator('#decode-input').press('Enter')
            return f.locator('#decode-result').inner_text()
        assert '220 Ω' in decode('FRC0603J221 TS')
        assert '10 MΩ' in decode('FRC1206F1005TS')
        assert '0.3 mΩ' in decode('FCM25123WF0M30TM')
        assert '缺少精度码' in decode('FCM25123W0M30TM')
        assert '暂未覆盖' in decode('OTHER-9999')
        assert '不能确定厂家' in decode('1N4148')
        assert '请确认搜索内容是否正确' in decode('<img src=x onerror=alert(1)>')
        assert f.locator('#decode-result img').count()==0
        decode('FRC0603J221 TS')
        activate(f.locator('#tab-performance'))
        assert f.locator('#tool-panel-decode').is_visible(), 'Knowledge tab hid practice panel'
        activate(f.locator('#tool-scenario'))
        assert f.locator('#panel-performance').is_visible(), 'Practice tab hid knowledge panel'
        choose(f.locator('[name="practice-choice"][value="0"]'))
        activate(f.locator('#scenario-question button[type="submit"]'))
        assert '暂未答对' in f.locator('.practice-feedback').inner_text()
        assert f.locator('#mistake-count').inner_text()=='1'
        activate(f.locator('#tool-mistakes'))
        assert f.locator('.mistake-item').count()==1
        activate(f.locator('.mistake-item summary'))
        assert '正确选择' in f.locator('.mistake-item').inner_text()
        activate(f.locator('[data-retry="r-power"]'))
        choose(f.locator('[name="practice-choice"][value="1"]'))
        activate(f.locator('#scenario-question button[type="submit"]'))
        assert '回答正确' in f.locator('.practice-feedback').inner_text()
        assert f.locator('#mistake-count').inner_text()=='0'
        activate(f.locator('#tab-quiz'))
        activate(f.locator('[data-answer="0"]'))
        assert f.locator('#mistake-count').inner_text()=='1'
        activate(f.locator('#tool-mistakes'))
        activate(f.locator('[data-retry="quiz-resistor"]'))
        choose(f.locator('[name="practice-choice"][value="1"]'))
        activate(f.locator('#scenario-question button[type="submit"]'))
        assert f.locator('#mistake-count').inner_text()=='0'
        # Eight scenarios, including a non-B answer, must all grade/review correctly.
        for q in f.evaluate('TrainingPractice.scenarios'):
            f.locator('#scenario-select').select_option(q['id'])
            wrong = (q['answer']+1)%3
            choose(f.locator(f'[name="practice-choice"][value="{wrong}"]'))
            activate(f.locator('#scenario-question button[type="submit"]'))
            assert '暂未答对' in f.locator('.practice-feedback').inner_text()
            choose(f.locator(f'[name="practice-choice"][value="{q["answer"]}"]'))
            activate(f.locator('#scenario-question button[type="submit"]'))
            assert '回答正确' in f.locator('.practice-feedback').inner_text()
        page.reload(wait_until='domcontentloaded')
        f = lesson_frame()
        activate(f.locator('#tool-mistakes'))
        assert '9 / 12' in f.locator('#practice-progress').inner_text()
        assert f.locator('#mistake-count').inner_text()=='0'
        # Repeat wrong answer after reload and check persistence + cancel/clear.
        activate(f.locator('#tool-scenario'))
        choose(f.locator('[name="practice-choice"][value="0"]'))
        activate(f.locator('#scenario-question button[type="submit"]'))
        page.reload(wait_until='domcontentloaded')
        f=lesson_frame()
        assert f.locator('#mistake-count').inner_text()=='1'
        activate(f.locator('#tool-mistakes'))
        activate(f.locator('#clear-practice'))
        activate(f.locator('#cancel-clear'))
        assert f.locator('#mistake-count').inner_text()=='1'
        activate(f.locator('#clear-practice'))
        activate(f.locator('#confirm-clear'))
        assert f.locator('#mistake-count').inner_text()=='0'
        assert '0 / 12' in f.locator('#practice-progress').inner_text()
        for width in [1280,900,390]:
            page.set_viewport_size({'width':width,'height':1000})
            activate(f.locator('#tool-decode'))
            f.locator('#decode-input').fill('FCM25123WF0M30TM')
            f.locator('#decode-input').press('Enter')
            f.locator('#decode-result').scroll_into_view_if_needed()
            size=f.evaluate('({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})')
            assert size['scroll']<=size['client']+1, size
            page.screenshot(path=str(out/f'{"formal" if args.public else "local"}-{width}.png'),full_page=True)
        f.locator('#tool-decode').focus()
        f.locator('#tool-decode').press('ArrowRight')
        assert f.locator('#tool-scenario').get_attribute('aria-selected')=='true'
        assert not errors, errors
        print(json.dumps({'status':'passed','public':args.public,'decoder':True,'scenarios':8,'quiz_integration':True,'wrong_answer_retry':True,'refresh_persistence':True,'clear_confirmation':True,'mobile_fit':True,'errors':errors}),flush=True)
        if not args.public:
            # Browser storage denial/corruption must not stop lessons or calculations.
            for script in ['Object.defineProperty(window,"localStorage",{get(){throw new Error("denied")}})',
                           'localStorage.setItem("fruition_training_practice_v1","not-json")']:
                fallback=browser.new_context(viewport={'width':900,'height':1000})
                fallback.add_init_script(script)
                fallback.route('http://training.local/**',lambda r:r.fulfill(body=build_training_html(),content_type='text/html'))
                fp=fallback.new_page()
                fp.goto('http://training.local/')
                assert '刷新后记录可能丢失' in fp.locator('#practice-storage').inner_text()
                assert fp.locator('#model-title').inner_text()
                fallback.close()
            print('Storage denial and corruption fallbacks passed.',flush=True)
    finally:
        context.close()
        browser.close()
