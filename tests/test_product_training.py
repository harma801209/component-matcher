import json
import shutil
import subprocess
import unittest
from pathlib import Path

from product_training import WEB_ROOT, build_training_html, render_training_page
from precision_theme import render_header


class ProductTrainingTests(unittest.TestCase):
    def test_learner_page_omits_admin_copy_and_keeps_explanations(self):
        page = build_training_html()
        for phrase in ['管理员', '业务数据库', '不写入会员', '不改业务数据', '同一浏览器的不同账号共用', '系统已核对', '不模拟', '未经披露', '计算条件与补充说明', '学习记录说明', '不随会员账号同步']:
            self.assertNotIn(phrase, page)
        for phrase in ['电路发生什么变化', '为什么会这样', '怎么向客户解释', '客户需求', '选型时还要注意']:
            self.assertIn(phrase, page)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_circuit_effects_follow_animation_time_and_options(self):
        script = r"""
const e=require(process.argv[1]),m=require(process.argv[2]),a=require('node:assert/strict');
const near=(x,y)=>a(Math.abs(x-y)<1e-10);
for(const c of ['resistor','capacitor','inductor','diode'])for(let s=0;s<3;s++)for(const u of [0,.4,1]){
 const r=m.evaluate(c,s,u),d=e.describe(c,s,r);
 for(const k of ['change','why','sales','note'])a(d[k].length>10);
 a.equal(d.comparison.length,2);for(const [label,value,unit] of d.comparison){a(label);a(Number.isFinite(value));a(['A','V'].includes(unit));}
 if(c==='capacitor'){near(d.comparison[0][1],r.v);near(d.comparison[1][1],m.evaluate(c,s,u,{cap:false}).v);}
 if(c==='inductor'){near(d.comparison[0][1],r.i);near(d.comparison[1][1],s===1?.5:0);}
 if(c==='diode'){near(d.comparison[0][1],r.input);near(d.comparison[1][1],r.output);}
}
const start=e.describe('capacitor',1,m.evaluate('capacitor',1,0));
near(start.comparison[0][1],3.295);near(start.comparison[1][1],3.2);
a(e.describe('capacitor',1,m.evaluate('capacitor',1,0,{cap:false})).change.includes('移除C1'));
a(e.describe('resistor',2,m.evaluate('resistor',2,0,{r:1000})).change.includes('变小'));
a(e.describe('resistor',2,m.evaluate('resistor',2,0,{r:220})).change.includes('更亮'));
a(e.describe('resistor',1,m.evaluate('resistor',1)).why.includes('不是电流进去多、出来少'));
a.throws(()=>e.describe('__proto__',0,{}),RangeError);a.throws(()=>e.describe('diode',4,{}),RangeError);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_effects.js'), str(WEB_ROOT / 'training_circuit_math.js')], check=True, capture_output=True)

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
        for term in ["不替代", "反向耐压", "DC偏压", "Isat", "Irms", "非温度", "约定电流", "选型时还要注意"]:
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
        for name in ["training.js", "training_math.js", "training_practice.js", "training_tools.js", "training_circuit.js", "training_circuit_math.js", "training_effects.js", "training_materials.js"]:
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

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_teaching_decoder_preserves_units_and_uncertainty(self):
        script = r"""
const p=require(process.argv[1]),assert=require('node:assert/strict');
const fields=x=>p.decode(x).fields.map(f=>f.value).join('|');
assert.match(fields('FRC0603J221 TS'),/220 Ω/);
assert.match(fields('FRC1206F1005TS'),/10 MΩ/);
assert.match(fields('FRL1206FR470TS'),/470 mΩ/);
assert.match(fields('FRM253WFR120TM'),/120 mΩ/);
assert.match(fields('FCM25123WF0M30TM'),/0.3 mΩ/);
assert.equal(p.decode('FCM25123W0M30TM').status,'suspected');
assert.match(p.decode('FCM25123W0M30TM').message,/缺少精度码/);
assert.equal(p.decode('FRC0603J221T').status,'suspected');
assert.equal(p.decode('FRC1206F100TS').status,'suspected');
assert.equal(p.decode('FRC0603J22-1TS').fields.length,0);
assert.equal(p.decode('FRC0402F22R6TS').status,'decoded');
assert.equal(p.decode('FRC0603J221 TS extra').fields.length,0);
assert.match(fields('RC0603FR-0710KL'),/10 kΩ/);
assert.match(fields('GRM188R71H104KA93D'),/100 nF/);
assert.match(p.decode('GRM188R71H104KA93').message,/基础型号/);
assert.match(p.decode('1N4148').message,/不能确定厂家/);
assert.equal(p.decode('FQV1206J126 TS').status,'unsupported');
assert.equal(p.decode('SOME-NEW-MODEL').status,'unsupported');
assert.equal(p.decode('<img src=x>').status,'input');
assert.equal(p.decode('0603 220Ω 5%').status,'input');
assert.equal(p.decode('x'.repeat(97)).status,'input');
assert.equal(p.decode('FRC0603J221TS\nFRL1206FR470TS').status,'input');
assert.equal(p.decode('').status,'input');
assert(p.oneEdit('ABC','ABCD'));assert(p.oneEdit('ABC','AXC'));assert(!p.oneEdit('ABC','ABC'));assert(!p.oneEdit('ABC','AXD'));
"""
        subprocess.run([shutil.which("node"), "-e", script, str(WEB_ROOT / "training_practice.js")], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_scenarios_and_untrusted_progress_records(self):
        script = r"""
const p=require(process.argv[1]),assert=require('node:assert/strict');
assert.equal(p.scenarios.length,8);assert.equal(new Set(p.scenarios.map(q=>q.id)).size,8);
for(const q of p.scenarios){assert.equal(q.options.length,3);assert.equal(q.why.length,3);for(let i=0;i<3;i++)assert.equal(p.grade(q,i),i===q.answer);assert.throws(()=>p.grade(q,-1),RangeError);assert.throws(()=>p.grade(q,NaN),RangeError);}
assert.equal(p.scenarios.find(q=>q.id==='l-loss').answer,0);
const data=JSON.parse('{"r-power":{"choice":0,"correct":false,"attempts":1},"fake":{"choice":0,"correct":true,"attempts":1},"r-unit":{"choice":99,"correct":true,"attempts":1},"__proto__":{"polluted":true}}');
assert.deepEqual(Object.keys(p.validRecords(data)),['r-power']);assert.equal({}.polluted,undefined);
for(const d of [null,[],1,'bad',{'r-power':{choice:0,correct:'true',attempts:1}},{'r-power':{choice:0,correct:true,attempts:10001}}])assert.deepEqual(p.validRecords(d),{});
"""
        subprocess.run([shutil.which("node"), "-e", script, str(WEB_ROOT / "training_practice.js")], check=True, capture_output=True)

    def test_practice_panels_are_separate_and_data_is_browser_only(self):
        page = build_training_html()
        for term in ['型号拆解', '选型实战', '错题本', '不自动修正', '暂未覆盖', '确认清除']:
            self.assertIn(term, page)
        self.assertIn(".knowledge-card [role=\"tabpanel\"]", page)
        self.assertIn("fruition_training_practice_v1", page)
        tools = (WEB_ROOT / 'training_tools.js').read_text(encoding='utf-8')
        self.assertNotIn('innerHTML', tools)
        self.assertNotIn('fetch(', tools)
        self.assertNotIn('member_token', tools)

    def test_record_implementation_is_not_shown_as_training_content(self):
        page = build_training_html()
        self.assertNotIn('practice-record-help', (WEB_ROOT / 'index.html').read_text(encoding='utf-8'))
        self.assertIn('id="practice-storage" class="storage-note" role="status" hidden', page)
        tools = (WEB_ROOT / 'training_tools.js').read_text(encoding='utf-8')
        self.assertIn('message.hidden=storageOK', tools)
        self.assertIn('localStorage.setItem', tools)
        self.assertIn('练习记录暂时无法保存', tools)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_circuit_current_conservation_and_continuous_energy_states(self):
        script = r"""
const m=require(process.argv[1]),a=require('node:assert/strict'),eq=(x,y)=>a(Math.abs(x-y)<1e-10);
let r=m.evaluate('resistor',0);eq(r.i,0);r=m.evaluate('resistor',1);eq(r.i,3/220);eq(r.p,r.i*r.i*220);a(m.evaluate('resistor',2).i<r.i);
let c0=m.evaluate('capacitor',0),c1=m.evaluate('capacitor',1,0),c2=m.evaluate('capacitor',1,1),c3=m.evaluate('capacitor',2,0);
eq(c0.v,c1.v);eq(c1.icap,-.095);eq(c2.v,c3.v);a(c3.icap>0);
for(let s=0;s<3;s++)for(const t of [0,.2,.8,1]){const c=m.evaluate('capacitor',s,t);eq(c.source,c.load+c.icap);a(c.energy>=0);}
a(m.evaluate('capacitor',1,0,{cap:false}).v<c1.v);eq(m.evaluate('capacitor',1,0,{cap:false}).icap,0);
let l1=m.evaluate('inductor',1,0),l2=m.evaluate('inductor',1,1),l3=m.evaluate('inductor',2,0),l4=m.evaluate('inductor',2,1);
eq(l1.i,0);eq(l2.i,l3.i);a(l3.vl<0);a(l4.energy<l3.energy);a(l4.i>0);a(l4.freewheel);a(!l4.closed);
eq(m.evaluate('diode',0).i,0);eq(m.evaluate('diode',1).output,4.3);eq(m.evaluate('diode',2).output,0);eq(m.evaluate('diode',2).i,0);
for(const call of [()=>m.evaluate('unknown',0),()=>m.evaluate('diode',3),()=>m.evaluate('capacitor',1,NaN),()=>m.evaluate('resistor',1,-.1)])a.throws(call,RangeError);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_circuit_math.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_capacitor_visual_contributions_complete_the_load_loop(self):
        script = r"""
const m=require(process.argv[1]),a=require('node:assert/strict'),eq=(x,y)=>a(Math.abs(x-y)<1e-10);
for(const cap of [true,false])for(let step=0;step<3;step++)for(const u of [0,.01,.2,.8,1]){
 const r=m.evaluate('capacitor',step,u,{cap}),f=m.currentFlows('capacitor',r);
 eq(f.load+f['cap-load'],r.load);eq(f.source,f.return);
 eq(f.source-r.icap,r.load);eq(f['cap-up'],r.icap);eq(f['cap-down'],r.icap);
 a(f.load>=0);a(f['cap-load']>=0);
 if(cap&&step===1){a(f['cap-load']>0);eq(f.load,r.source);eq(f['cap-load'],-r.icap);}
 else{eq(f['cap-load'],0);eq(f.load,r.load);}
 if(cap&&step===2){a(f['cap-up']>0);a(f.source>f.load);}
 if(!cap||step===0){eq(f['cap-up'],0);eq(f['cap-down'],0);}
}
const r=m.evaluate('capacitor',1),f=m.currentFlows('capacitor',r);
eq(f.load,.005);eq(f['cap-load'],.095);eq(f.load+f['cap-load'],.1);
eq(m.currentFlows('resistor',m.evaluate('resistor',0)).main,0);
eq(m.currentFlows('diode',m.evaluate('diode',2)).main,0);
a(m.currentFlows('inductor',m.evaluate('inductor',2)).freewheel>0);
eq(m.currentFlows('inductor',m.evaluate('inductor',2)).supply,0);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_circuit_math.js')], check=True, capture_output=True)

    def test_circuit_media_controls_are_icon_only_with_accessible_names(self):
        from html.parser import HTMLParser

        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.buttons, self.current = {}, None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'button' and attrs.get('id') in ('circuit-play', 'circuit-next', 'circuit-reset'):
                    self.current = attrs['id']
                    self.buttons[self.current] = {'attrs': attrs, 'icons': [], 'text': ''}
                elif tag == 'svg' and self.current:
                    self.buttons[self.current]['icons'].append(attrs)

            def handle_endtag(self, tag):
                if tag == 'button':
                    self.current = None

            def handle_data(self, value):
                if self.current:
                    self.buttons[self.current]['text'] += value

        parser = Controls()
        parser.feed(build_training_html())
        for name, label in [('circuit-play', '播放分步演示'), ('circuit-next', '下一步'), ('circuit-reset', '重新开始')]:
            button = parser.buttons[name]
            self.assertEqual(button['text'].strip(), '')
            self.assertEqual(button['attrs']['aria-label'], label)
            self.assertEqual(button['attrs']['title'], label)
            self.assertIn('circuit-icon-button', button['attrs']['class'])
            self.assertTrue(button['icons'])
            for icon in button['icons']:
                self.assertEqual(icon['aria-hidden'], 'true')
                self.assertEqual(icon['focusable'], 'false')
        self.assertEqual(len(parser.buttons['circuit-play']['icons']), 2)
        script = (WEB_ROOT / 'training_circuit.js').read_text(encoding='utf-8')
        self.assertNotIn(".textContent='播放分步演示'", script)
        self.assertNotIn(".textContent='暂停演示'", script)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_material_lessons_have_source_scoped_components_not_fixed_recipes(self):
        script = r"""
const m=require(process.argv[1]),a=require('node:assert/strict');
for(const course of ['resistor','capacitor','inductor','diode']){
 const d=m.lesson(course);a(Object.isFrozen(d));a(Object.isFrozen(d.layers));
 a(d.layers.length>=4);a.equal(new Set(d.layers.map(p=>p.id)).size,d.layers.length);
 a(d.scope);a(d.caption);a(d.sources.length>=2);
 for(const p of d.layers){for(const key of ['name','brief','composition','role','scope'])a(p[key]);a(p.refs.length);for(const ref of p.refs)a(d.sources[ref][1].startsWith('https://'));}
}
a.throws(()=>m.lesson('other'),RangeError);
a.throws(()=>m.lesson('__proto__'),RangeError);
a(m.lesson('resistor').layers.find(p=>p.id==='film').composition.includes('RuO₂'));
a(m.lesson('capacitor').scope.includes('C0G'));
a(m.lesson('capacitor').layers.find(p=>p.id==='dielectric').composition.includes('BaTiO₃'));
a(m.lesson('inductor').scope.includes('一体成型'));
a(m.lesson('diode').layers.find(p=>p.id==='junction').composition.includes('不是夹入'));
a(m.lesson('diode').layers.find(p=>p.id==='glass').composition.includes('原厂文件'));
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_materials.js')], check=True, capture_output=True)

    def test_cross_sections_are_additive_and_do_not_persist_business_data(self):
        page = build_training_html()
        self.assertIn('id="show-cross-section"', page)
        self.assertIn('id="cross-section-card"', page)
        self.assertIn('id="model-canvas"', page)
        self.assertLess(page.index('class="workspace"'), page.index('id="cross-section-card"'))
        self.assertLess(page.index('id="cross-section-card"'), page.index('class="practice-card"'))
        script = (WEB_ROOT / 'training_materials.js').read_text(encoding='utf-8')
        for term in ['fetch(', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
            self.assertNotIn(term, script)
        for term in ['training-course-change', 'aria-pressed', 'noopener noreferrer', '材料声明', '配比']:
            self.assertIn(term, script)

    def test_pcb_demo_is_separate_from_structure_and_device_labs(self):
        page=build_training_html()
        for word in ['PCB电路工作演示','限流电阻','电源接反','电容回充','续流路径','内部示意动画','约定电流方向','负载10 Ω','不是固定导通门槛']:
            self.assertIn(word,page)
        self.assertLess(page.index('id="circuit-card"'),page.index('class="workspace"'))
        self.assertIn('training-course-change',page)
        self.assertNotIn('<script src=',page)
