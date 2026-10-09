import json
import shutil
import subprocess
import unittest
from pathlib import Path

from product_training import WEB_ROOT, build_training_html, render_training_page
from precision_theme import render_header


class ProductTrainingTests(unittest.TestCase):
    def test_page_has_all_four_lessons_and_inline_resources(self):
        page = build_training_html()
        for term in ["贴片电阻", "陶瓷电容", "电感", "二极管", "规格参数", "电气性能", "工作原理", "拆解", "TrainingMath", "function project"]:
            self.assertIn(term, page)
        self.assertNotIn("__TRAINING_", page)
        self.assertNotIn("<script src=", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn("XMLHttpRequest", page)
        self.assertIn('lang="zh-CN"', page)

    def test_sources_and_model_limitations_are_present(self):
        page = build_training_html()
        for domain in ["vishay.com", "murata.com", "coilcraft.com", "assets.nexperia.com"]:
            self.assertIn(domain, page)
        for term in ["不替代", "不模拟击穿", "DC偏压", "Isat", "Irms", "非温度", "约定电流", "不写入会员或业务数据库"]:
            self.assertIn(term, page)
        self.assertIn('rel="noopener noreferrer"', page)

    def test_training_navigation_keeps_current_page_semantics(self):
        rendered = []
        fake = type("Fake", (), {"markdown": lambda _, value, **kwargs: rendered.append(value)})()
        render_header(fake, "", "training", [("training", "产品培训", "?training=1"), ("member", "会员中心", "?member=1&training=0")], None)
        self.assertIn('class="active" aria-current="page"', rendered[-1])
        self.assertIn('class="wb-title">产品培训', rendered[-1])
        self.assertIn('aria-label="会员登录"', rendered[-1])

    def test_component_render_is_scrollable_and_stateless(self):
        calls = []
        fake = type("Components", (), {"html": lambda _, value, **kwargs: calls.append((value, kwargs))})()
        render_training_page(fake)
        self.assertEqual(calls[0][1], {"height": 1050, "scrolling": True})
        source = Path("product_training.py").read_text(encoding="utf-8")
        self.assertNotIn("sqlite", source)
        self.assertNotIn("requests", source)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable; formulas also receive browser verification")
    def test_javascript_syntax_and_physics(self):
        node = shutil.which("node")
        for name in ["training.js", "training_math.js"]:
            subprocess.run([node, "--check", str(WEB_ROOT / name)], check=True, capture_output=True)
        script = "const m=require(process.argv[1]); console.log(JSON.stringify({r:m.resistor({r:1000,v:5,rating:.125}),c:m.capacitor({c:1e-7,f:1000,v:5}),l:m.inductor({l:1e-5,f:1000,i:1,dcr:.1,isat:2}),zero:m.diode({v:0,is:1e-9,n:2,vt:.02585}),reverse:m.diode({v:-2,is:1e-9,n:2,vt:.02585}),forward:m.diode({v:.6,is:1e-9,n:2,vt:.02585}),units:[m.format(1e-3,'Ω'),m.format(1e6,'Ω'),m.format(1e-12,'F')]}));"
        result = subprocess.run([node, "-e", script, str(WEB_ROOT / "training_math.js")], check=True, capture_output=True, text=True, encoding="utf-8")
        data = json.loads(result.stdout)
        self.assertAlmostEqual(data["r"]["current"], .005)
        self.assertAlmostEqual(data["r"]["power"], .025)
        self.assertAlmostEqual(data["r"]["ratio"], .2)
        self.assertAlmostEqual(data["c"]["reactance"], 1591.5494309189535)
        self.assertAlmostEqual(data["c"]["charge"], 5e-7)
        self.assertAlmostEqual(data["c"]["energy"], 1.25e-6)
        self.assertAlmostEqual(data["l"]["reactance"], .06283185307179587)
        self.assertAlmostEqual(data["l"]["copperLoss"], .1)
        self.assertAlmostEqual(data["l"]["energy"], 5e-6)
        self.assertFalse(data["l"]["saturated"])
        self.assertEqual(data["zero"]["current"], 0)
        self.assertLess(data["reverse"]["current"], 0)
        self.assertLess(abs(data["reverse"]["current"]), 1.01e-9)
        self.assertGreater(data["forward"]["current"], 0)
        self.assertEqual(data["units"], ["1 mΩ", "1 MΩ", "1 pF"])

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_invalid_parameters_are_rejected_not_reported_as_real_results(self):
        script = "const m=require(process.argv[1]);for(const call of [()=>m.resistor({r:0,v:5,rating:.125}),()=>m.capacitor({c:1e-7,f:0,v:5}),()=>m.inductor({l:1e-5,f:1000,i:1,dcr:.1,isat:0}),()=>m.diode({v:Infinity,is:1e-9,n:2,vt:.02585})]){let failed=false;try{call();}catch(e){failed=e instanceof RangeError;}if(!failed)process.exit(1);}"
        subprocess.run([shutil.which("node"), "-e", script, str(WEB_ROOT / "training_math.js")], check=True, capture_output=True)
