import json
import shutil
import subprocess
import unittest
from pathlib import Path

from product_training import WEB_ROOT, build_training_html, render_training_page
from precision_theme import render_header


class ProductTrainingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_capacitor_internal_overlay_reuses_exposed_layers_and_cover_anchors(self):
        script = r"""
const g=require(process.argv[1]),a=require('node:assert/strict');
const box=(f,p,size,color,id)=>f.push({id,color,p:[p,p.map((v,i)=>v+size[i]),p.map((v,i)=>v-size[i])]});
for(const e of [0,.05,.1,.5,1]){
 const detailed=g.build('capacitor',e,{box}),intro=g.buildCapacitorStructure(e,{box});
 const mapping={dielectric:'dielectric',internal:'electrode',base:'terminal',barrier:'terminal',tin:'terminal',upper_cover:'upper_cover',lower_cover:'lower_cover'};
 a.deepEqual(intro.faces,detailed.faces.map(f=>({...f,id:mapping[f.id]})));
 a.deepEqual(intro.anchors.map(p=>p.id),['dielectric','electrode','terminal','upper_cover','lower_cover']);
 a.equal(intro.faces.filter(f=>f.id==='electrode').length,6);
 const metal=detailed.faces.filter(f=>f.id==='internal');
 a.deepEqual(intro.electrodeY,metal.map(f=>f.p[0][1]));
 a.deepEqual(intro.anchors[1].point,detailed.anchors.find(p=>p.id==='internal').point);
 a.equal(intro.anchors[1].point[2],.3);
}
a.throws(()=>g.buildCapacitorStructure(-1,{box}),RangeError);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_material_geometry.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_capacitor_exterior_is_sealed_body_with_two_end_caps_only(self):
        script = r"""
const g=require(process.argv[1]),a=require('node:assert/strict');
const b=[],box=(f,p,size,color,id)=>{b.push({p,size,color,id});f.push({p:[p],size,color,id});};
const m=g.buildCapacitorExterior({box});
a.equal(b.length,3);a.deepEqual(m.anchors.map(p=>p.id),['body','terminal']);
a.deepEqual([...new Set(m.faces.map(f=>f.id))].sort(),['body','terminal']);
a.equal(b.filter(p=>p.id==='body').length,1);a.equal(b.filter(p=>p.id==='terminal').length,2);
const body=b[0];for(const cap of b.slice(1)){a(cap.size[1]>=body.size[1]);a(cap.size[2]>=body.size[2]);a(Math.abs(cap.p[0])-cap.size[0]/2<body.size[0]/2);a(Math.abs(cap.p[0])+cap.size[0]/2>body.size[0]/2);}
for(const p of m.anchors)a(p.point.every(Number.isFinite));
const cut=g.build('capacitor',0,{box:(f,p,size,color,id)=>f.push({p,size,color,id}),tube:()=>{}});
a(cut.faces.some(f=>f.id==='internal'));a(cut.faces.some(f=>f.id==='upper_cover'));a(cut.faces.some(f=>f.id==='lower_cover'));
a.notDeepEqual(m.faces,cut.faces);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_material_geometry.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_mlcc_cut_exposes_alternating_electrodes_without_shorting_ends(self):
        script = r"""
const g=require(process.argv[1]),a=require('node:assert/strict'),near=(x,y)=>a(Math.abs(x-y)<1e-10);
for(const e of [0,.5,1]){
 const blocks=[],box=(f,p,size,color,id)=>{blocks.push({p,size,color,id});f.push({p:[p],color,id});};
 const result=g.build('capacitor',e,{box,tube:()=>{}}),active=blocks.filter(p=>p.id==='dielectric'),ceramics=[blocks.find(p=>p.id==='lower_cover'),...active,blocks.find(p=>p.id==='upper_cover')],metal=blocks.filter(p=>p.id==='internal'),ends=blocks.filter(p=>p.id==='base');
 a.equal(active.length,5);a.equal(ceramics.length,7);a.equal(metal.length,6);
 const minX=b=>b.p[0]-b.size[0]/2,maxX=b=>b.p[0]+b.size[0]/2;
 for(let i=0;i<6;i++){
  const m=metal[i],lo=ceramics[i],hi=ceramics[i+1],left=ends[0],right=ends[1];
  a(m.size[1]>=.06);near(m.p[2]+m.size[2]/2,lo.p[2]+lo.size[2]/2);
  if(i>0&&i<5)near(m.p[1],(lo.p[1]+hi.p[1])/2);
  a(m.p[1]-m.size[1]/2>=lo.p[1]+lo.size[1]/2-1e-10);
  a(m.p[1]+m.size[1]/2<=hi.p[1]-hi.size[1]/2+1e-10);
  if(e===0){near(m.p[1]-m.size[1]/2,lo.p[1]+lo.size[1]/2);near(m.p[1]+m.size[1]/2,hi.p[1]-hi.size[1]/2);}
  if(i%2===0){a(minX(m)>minX(left)&&minX(m)<maxX(left));a(maxX(m)<minX(right)-.1);}
  else{a(maxX(m)>minX(right)&&maxX(m)<maxX(right));a(minX(m)>maxX(left)+.1);}
 }
 const anchor=result.anchors.find(p=>p.id==='internal');
 near(anchor.point[2],.3);
 a(metal.some(m=>Math.abs(m.p[1]-anchor.point[1])<1e-10));
}
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_material_geometry.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_mlcc_upper_lower_covers_are_non_electroded_protection_regions(self):
        script = r"""
const g=require(process.argv[1]),d=require(process.argv[2]),a=require('node:assert/strict'),near=(x,y)=>a(Math.abs(x-y)<1e-10);
for(const e of [0,.05,.5,1]){
 const b=[],box=(f,p,size,color,id)=>{b.push({p,size,color,id});f.push({id,color,p:[p]});};
 const m=g.build('capacitor',e,{box}),covers=b.filter(p=>['upper_cover','lower_cover'].includes(p.id)),inner=b.filter(p=>p.id==='internal'),ceramic=b.filter(p=>p.id==='dielectric');
 a.equal(covers.length,2);a.equal(ceramic.length,5);a.equal(inner.length,6);
 const upper=covers.find(p=>p.id==='upper_cover'),lower=covers.find(p=>p.id==='lower_cover');
 near(upper.p[1],-lower.p[1]);near(upper.size[1],lower.size[1]);a(upper.size[1]>ceramic[0].size[1]);a.notDeepEqual(upper.color,ceramic[0].color);
 for(const c of covers){
  const lo=c.p[1]-c.size[1]/2,hi=c.p[1]+c.size[1]/2;
  for(const i of inner)a(i.p[1]+i.size[1]/2<=lo+1e-10||i.p[1]-i.size[1]/2>=hi-1e-10);
  const point=m.anchors.find(p=>p.id===c.id).point;near(point[1],c.p[1]);near(point[2],c.p[2]+c.size[2]/2);
  const info=d.lesson('capacitor').layers.find(p=>p.id===c.id);a(info.name.includes('陶瓷盖层'));a(info.composition.includes('不含内电极'));a(info.scope.includes('一体'));a(info.refs.includes(2));
 }
 near(m.anchors.find(p=>p.id==='dielectric').point[1],0);
 const base=b.find(p=>p.id==='base');near(base.size[1]/2,upper.p[1]+upper.size[1]/2);
 if(e===0){near(upper.p[1]-upper.size[1]/2,inner.at(-1).p[1]+inner.at(-1).size[1]/2);near(lower.p[1]+lower.size[1]/2,inner[0].p[1]-inner[0].size[1]/2);}
}
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_material_geometry.js'), str(WEB_ROOT / 'training_material_data.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_visible_print_and_underline_are_centered_on_actual_cover(self):
        script = r"""
const m=require(process.argv[1]),a=require('node:assert/strict'),near=(x,y)=>a(Math.abs(x-y)<1e-10);
for(const [r,profile] of [[1000,'three'],[1000,'four'],[220,'underline'],[.1,'three'],[.1,'four'],[4.7,'three']])
for(const [cx,y,cz] of [[0,.35,0],[0,1.85,0],[0,.49,-.2],[0,1.49,-.2],[.6,2.3,-.7]]){
 const face={id:'cover',p:[[cx-1.24,y,cz-.45],[cx+1.24,y,cz-.45],[cx+1.24,y,cz+.45],[cx-1.24,y,cz+.45]]};
 m.attach([face],r,true,profile);
 const points=face.ink.flat(),x=points.map(p=>p[0]),z=points.map(p=>p[2]);
 near((Math.min(...x)+Math.max(...x))/2,cx);near((Math.min(...z)+Math.max(...z))/2,cz);
 for(const p of points){near(p[1],y);a(p[0]>=cx-1.24&&p[0]<=cx+1.24);a(p[2]>=cz-.45&&p[2]<=cz+.45);}
 if(profile==='underline'){
  const line=face.ink.at(-1),digits=face.ink.slice(0,-1).flat(),xs=digits.map(p=>p[0]);
  near(line[0][0],Math.min(...xs));near(line[1][0],Math.max(...xs));near((line[0][0]+line[1][0])/2,cx);
 }
}
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_resistor_marking.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_resistor_print_code_is_exact_and_ink_belongs_to_cover(self):
        script = r"""
const m=require(process.argv[1]),a=require('node:assert/strict');
for(const [r,code] of [[1000,'102'],[100,'101'],[10,'100'],[4700,'472'],[.1,'R10'],[4.7,'4R7'],])a.equal(m.encode(r).code,code);
for(const r of [NaN,Infinity,-1,0,12.5892541179,.0001])a.equal(m.encode(r),null);
a.equal(m.encode(999.9999999999999).code,'102');
for(const [r,code] of [[1000,'1001'],[100,'1000'],[.1,'R100'],[4.7,'4R70'],[6.19,'6R19'],[12.4,'12R4'],[6190,'6191']])a.equal(m.encode(r,'four').code,code);
for(const r of [1000,100,10,13,15,20,75,1020,12.5892541179])a.equal(m.encode(r,'underline'),null);
const under=m.encode(220,'underline');a.equal(under.code,'221');a(under.underline);
const cover=()=>({id:'cover',p:[[-1.24,.49,-.65],[1.24,.49,-.65],[1.24,.49,.25],[-1.24,.49,.25]]});
const plain=cover(),lined=cover();m.attach([plain],220,true);m.attach([lined],220,true,'underline');a.equal(lined.ink.length,plain.ink.length+1);a(lined.markingUnderline);
a.throws(()=>m.encode(220,'unknown'),RangeError);
for(const y of [.35,1.85,.49,1.49]){
 const top={id:'cover',p:[[-1.24,y,-.65],[1.24,y,-.65],[1.24,y,.25],[-1.24,y,.25]]},side={id:'cover',p:[[-1.24,y,-.65],[-1.24,y-.12,-.65],[-1.24,y-.12,.25],[-1.24,y,.25]]},f=[top,side];
 a.equal(m.attach(f,1000,true),f);a.equal(top.markingCode,'102');a(top.ink.length>20);a.equal(side.ink,undefined);
 for(const q of top.ink)for(const p of q){a.equal(p[1],y);a(p[0]>=-1.24&&p[0]<=1.24);a(p[2]>=-.65&&p[2]<=.25);a(p.every(Number.isFinite));}
}
const f=[{id:'film',p:[[0,0,0],[1,0,0],[1,0,1]]}];a.equal(m.attach(f,1000,false),f);a.equal(f[0].ink,undefined);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_resistor_marking.js')], check=True, capture_output=True)

    def test_resistor_print_uses_face_pass_and_learner_scope_notes(self):
        page=build_training_html()
        for phrase in ['id="resistor-marking"', '101＝10×10¹＝100 Ω', '4R7＝4.7 Ω', 'R10＝0.1 Ω', '部分0402', '不能仅凭印字判断精度', 'Vishay · 表面阻值标识规则']:
            self.assertIn(phrase,page)
        self.assertIn('if(f.ink)',page)
        self.assertIn('window.TrainingResistorMarking.attach(materialMesh.faces,params.r,true,markingProfile)',page)
        self.assertIn("section.hidden=active!=='resistor'",page)
        self.assertNotIn('id="cross-section-card"',page)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_material_volume_parts_and_anchors_share_the_source_lesson(self):
        script = r"""
const g=require(process.argv[1]),d=require(process.argv[2]),a=require('node:assert/strict');
const box=(f,p,size,color,id)=>f.push({id,color,p:[p,p.map((v,i)=>v+size[i]),p.map((v,i)=>v-size[i])]});
const tube=(f,p,q,r,color,id)=>f.push({id,color,p:[p,q,p.map(v=>v+r)]});
for(const course of ['resistor','capacitor','inductor','diode'])for(const e of [0,.5,1]){
 const result=g.build(course,e,{box,tube}),ids=d.lesson(course).layers.map(p=>p.id);
 a.deepEqual(result.anchors.map(p=>p.id),ids);a.deepEqual([...new Set(result.faces.map(f=>f.id))].sort(),[...ids].sort());
 for(const p of result.anchors){a(p.name);a(p.material);a.equal(p.point.length,3);a(p.point.every(Number.isFinite));}
 for(const f of result.faces){a(f.color.every(Number.isFinite));for(const p of f.p)a(p.every(Number.isFinite));}
 if(course==='diode'){a.equal(result.anchors.find(p=>p.id==='p').point[0],-.46);a.equal(result.anchors.find(p=>p.id==='n').point[0],.46);}
}
a.throws(()=>g.build('other',0,{box,tube}),RangeError);a.throws(()=>g.build('resistor',NaN,{box,tube}),RangeError);
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_material_geometry.js'), str(WEB_ROOT / 'training_material_data.js')], check=True, capture_output=True)

    def test_material_mode_uses_same_canvas_numbered_markers_without_duplicate(self):
        page = build_training_html()
        self.assertEqual(page.count('<canvas'), 1)
        self.assertIn('id="model-exterior"', page)
        self.assertIn('内部材料结构', page)
        self.assertNotIn('id="cross-section-card"', page)
        self.assertNotIn('material-leaders', page)
        self.assertNotIn('data-label-leader', page)
        self.assertNotIn('展开平面剖面参考图', page)
        self.assertIn('button.textContent=String(i+1)', page)
        self.assertIn('data-model-material', page)
        self.assertIn('TrainingMaterialGeometry.build', page)

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

    def test_component_render_uses_host_scrolling_and_is_stateless(self):
        calls = []
        fake = type("Components", (), {"html": lambda _, value, **kwargs: calls.append((value, kwargs))})()
        render_training_page(fake)
        self.assertEqual(calls[0][1], {"height": 1050, "scrolling": False})
        source = Path("product_training.py").read_text(encoding="utf-8")
        self.assertNotIn("sqlite", source)
        self.assertNotIn("requests", source)

    def test_embed_height_tracks_content_without_affecting_other_frames(self):
        script=(WEB_ROOT / 'training_embed.js').read_text(encoding='utf-8')
        for term in ['window.frameElement', 'app.getBoundingClientRect().height', 'ResizeObserver', 'trainingAutoheight', "setAttribute('scrolling','no')", "setProperty('flex','0 0 auto','important')"]:
            self.assertIn(term,script)
        self.assertNotIn('window.top',script)
        self.assertNotIn('document.querySelectorAll',script)
        self.assertNotIn('app.scrollHeight',script)
        self.assertIn('if(!frame||!app)return',script)
        self.assertIn('training_embed.js',(Path('product_training.py')).read_text(encoding='utf-8'))

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable; formulas also receive browser verification")
    def test_javascript_syntax_and_physics(self):
        node = shutil.which("node")
        for name in ["training.js", "training_math.js", "training_practice.js", "training_tools.js", "training_circuit.js", "training_circuit_math.js", "training_effects.js", "training_material_data.js", "training_material_geometry.js", "training_materials.js", "training_embed.js", "training_resistor_marking.js"]:
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

    def test_material_mode_keeps_sources_without_business_data_access(self):
        page = build_training_html()
        self.assertIn('id="show-cross-section"', page)
        self.assertNotIn('id="cross-section-card"', page)
        self.assertIn('id="model-canvas"', page)
        self.assertLess(page.index('class="workspace"'), page.index('class="practice-card"'))
        script = (WEB_ROOT / 'training_material_geometry.js').read_text(encoding='utf-8') + (WEB_ROOT / 'training_material_data.js').read_text(encoding='utf-8')
        for term in ['fetch(', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
            self.assertNotIn(term, script)
        for term in ['材料声明', '配比']:
            self.assertIn(term, script)

    def test_pcb_demo_is_separate_from_structure_and_device_labs(self):
        page=build_training_html()
        for word in ['PCB电路工作演示','限流电阻','电源接反','电容回充','续流路径','内部示意动画','约定电流方向','负载10 Ω','不是固定导通门槛']:
            self.assertIn(word,page)
        self.assertLess(page.index('id="circuit-card"'),page.index('class="workspace"'))
        self.assertIn('training-course-change',page)
        self.assertNotIn('<script src=',page)
