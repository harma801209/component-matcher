import json
import shutil
import subprocess
import unittest
from pathlib import Path

from product_training import WEB_ROOT, build_training_html, render_training_page
from precision_theme import render_header


class ProductTrainingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_resistor_local_drop_heat_and_equal_current_do_not_wait_for_arrow(self):
        script=r'''
const m=require(process.argv[1]),e=require(process.argv[2]),a=require('node:assert/strict');
const eq=(x,y)=>a(Math.abs(x-y)<1e-12);
for(const step of [0,1,2])for(const resistance of [220,1000]){
 const start=m.evaluate('resistor',step,0,{r:resistance});
 for(const time of [.01,.5,1])a.deepEqual(m.evaluate('resistor',step,time,{r:resistance}),start);
 eq(start.vs,5);eq(start.drop,start.before-start.after);eq(start.p,start.drop*start.i);
 eq(start.i,m.currentFlows('resistor',start).main);
 const text=e.describe('resistor',step,start);
 if(step===0){eq(start.i,0);eq(start.drop,0);eq(start.p,0);a(text.change.includes('电源本身仍为5 V'));}
 else{eq(start.before,5);eq(start.after,2);eq(start.drop,3);eq(start.i,3/start.r);a(text.change.includes('电阻前后电流相同'));a(text.change.includes('3 V压降'));}
}
const low=m.evaluate('resistor',2,0,{r:1000}),high=m.evaluate('resistor',2,0,{r:220});
a(low.i<high.i);a(low.p<high.p);a(low.brightness<high.brightness);eq(low.p,.009);
'''
        subprocess.run([shutil.which('node'),'-e',script,str(WEB_ROOT/'training_circuit_math.js'),str(WEB_ROOT/'training_effects.js')],check=True,capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_all_remaining_subtypes_have_observation_gated_solvable_missions(self):
        script=r'''
const m=require(process.argv[1]),c=require(process.argv[2]),a=require('node:assert/strict');
a.equal(m.ids.length,26);a.deepEqual([...m.ids].sort(),c.lessons.filter(d=>!d.baseline).map(d=>d.id).sort());
let count=0;for(const id of m.ids){const d=m.profile(id);a(Object.isFrozen(d));a.equal(d.missions.length,3);
 let combinations=[{}];for(const f of d.fields)combinations=combinations.flatMap(p=>f.options.map(([x])=>({...p,[f.key]:x})));
 let s=m.create(id);a(!m.judge(s).passed);a.strictEqual(m.visit(s,1),s);
 for(const [i,l] of d.missions.entries()){
  a.equal(s.index,i);a(!l.check(l.setup,m.evaluate(id,l.setup).values),id+' initial solution '+i);
  const win=combinations.find(p=>l.check(p,m.evaluate(id,p).values));a(win,id+' unsolvable '+i);
  for(const p of combinations){const r=m.evaluate(id,p);a(r.story);a(r.metrics.length);for(const value of Object.values(r.values))if(typeof value==='number')a(Number.isFinite(value));a(Number.isFinite(r.visual.brightness));}
  for(const [k,v] of Object.entries(win))s=m.change(s,k,v);a(!m.judge(s).passed);a.equal(s.cleared.length,i);
  a.strictEqual(m.observe(s,.6),s);s=m.start(s);s=m.observe(s,.6);a.equal(s.cleared.length,i);s=m.observe(s,.6);a(m.judge(s).passed);a.equal(s.cleared.length,i+1);
  s=m.observe(s,.6);a.equal(s.cleared.length,i+1);count++;if(i<2)s=m.visit(s,i+1);
 }
 a.equal(s.cleared.length,3);s=m.visit(s,0);a.equal(s.cleared.length,3);a.equal(s.observed,0);
 for(const bad of [null,{},NaN])a.throws(()=>m.evaluate(id,bad),RangeError);
 a.throws(()=>m.change(s,'unknown',0),RangeError);a.throws(()=>m.observe(s,Infinity),RangeError);a.throws(()=>m.observe(s,-1),RangeError);
 a.throws(()=>m.judge({...s,cleared:[1]}),RangeError);a.throws(()=>m.visit(s,3),RangeError);
}a.equal(count,78);for(const bad of ['__proto__','constructor','missing'])a.throws(()=>m.profile(bad),RangeError);
'''
        subprocess.run([shutil.which('node'),'-e',script,str(WEB_ROOT/'training_subtype_game_math.js'),str(WEB_ROOT/'training_catalog.js')],check=True,capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_subtype_game_physics_distinguish_signal_storage_switching_and_limits(self):
        script=r'''
const m=require(process.argv[1]),a=require('node:assert/strict'),r=(id,p)=>m.evaluate(id,p),near=(x,y)=>a(Math.abs(x-y)<1e-8);
near(r('res-thin',{tcr:25,temperature:40}).values.drift,1);near(r('res-sense',{resistance:10,load:2}).values.voltage,.02);
let t=m.change(m.create('res-thin'),'temperature',40);t=m.start(t);t=m.observe(m.observe(t,.6),.6);a.deepEqual(t.cleared,[0]);
near(r('cap-aluminum',{esr:.2,ripple:2}).values.loss,.8);a(r('cap-safety',{category:'Y',position:'earth'}).values.match);
const storage=r('cap-tantalum',{forward:true,capacitance:10}).visual;near(storage.source-storage.storage,storage.load);
near(r('cap-film',{capacitance:.1,slew:100}).values.current,10);near(r('cap-tantalum',{forward:true,capacitance:10}).values.voltage,4.9);
a.equal(r('cap-tantalum',{forward:false,capacitance:10}).values.voltage,null);
a(r('ind-molded',{isat:2,load:3}).values.boundary);a.equal(r('ind-common',{mode:'differential',installed:true}).values.flux,0);
a(!r('xtal-passive',{amplifier:false,load:15}).values.clock);near(r('xtal-passive',{amplifier:true,load:15}).values.cl,9.5);
a(!r('xtal-active',{vdd:false,oe:true}).values.clock);a(r('xtal-active',{vdd:true,oe:true}).values.clock);
near(r('xtal-tcxo',{design:'compensated',temperature:85}).values.offset,65);near(r('xtal-vcxo',{offset:-50}).values.frequency,25998700);
near(r('mos-p',{drive:10,load:2}).values.vgs,-10);a.equal(r('mos-n',{drive:2.5,load:2}).values.loss,null);
near(r('mos-dual',{gates:'both',load:2}).values.loss,.16);a(!r('mos-dual',{gates:'one',load:2}).values.known);
near(r('dio-rectifier',{forward:false,load:1000}).values.peak,-4.3);near(r('dio-schottky',{vf:.3,load:2}).values.loss,.6);
const z=r('dio-zener',{input:12,series:1000}).values;near(z.voltage,5.1);a(z.shunt>0&&z.loss<.02);
const tvs=r('dio-tvs',{clamp:10,event:'surge'}).values;near(tvs.voltage,10);near(tvs.shunt,1);a(!tvs.within);
near(r('dio-led',{forward:true,resistance:1000}).values.current,.002);a(!r('bjt-npn',{base:.1,load:20}).values.known);
near(r('bjt-darlington',{base:20,load:2}).values.loss,2);a(r('bjt-digital',{input:3.3,load:2}).values.on);
'''
        subprocess.run([shutil.which('node'),'-e',script,str(WEB_ROOT/'training_subtype_game_math.js')],check=True,capture_output=True)

    def test_all_subtype_games_load_offline_and_keep_the_unified_board(self):
        page=build_training_html()
        for name in ['training_subtype_game_math.js','training_subtype_game_scene.js','training_subtype_game.js']:
            text=(WEB_ROOT/name).read_text(encoding='utf-8')
            for forbidden in ['fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
                self.assertNotIn(forbidden,text)
        self.assertIn('window.TrainingSubtypeGame=Object.freeze',page)
        self.assertIn("$('games-card').hidden=false",page)
        self.assertIn('training-subtype-change',page)
        self.assertTrue('play-story play-console' in page)
        self.assertTrue('viewport.append(power)' not in page)
        self.assertIn('renderer.forceContextLoss()',page)
        self.assertIn("canvas.dataset.positiveSide=params.forward?'left':'right'",page)
        self.assertIn("canvas.dataset.partConnected=String(id!=='ind-common'||p.installed)",page)
        builder=(WEB_ROOT.parent/'tools/build_training_playground_vendor.mjs').read_text(encoding='utf-8')
        self.assertIn('BufferGeometry,BufferAttribute,Line,LineBasicMaterial',builder)

    def test_guided_controls_are_in_the_board_workbench_not_an_upper_module(self):
        ui=(WEB_ROOT/'training_playground.js').read_text(encoding='utf-8')
        for text in ['playground-workbench','playground-action','playground-instruction','play-story play-console','story.append(instruction,actionRow,hintText)','story.append(controls','这一关不用换电阻','这关怎么玩']:
            self.assertIn(text,ui)
        self.assertNotIn('viewport.append(power)',ui)
        self.assertNotIn('workbench.append(tray)',ui)
        self.assertNotIn('mission.append(controls)',ui)
        self.assertIn('next.hidden=!done',ui)
        self.assertIn("tray.hidden=mode==='challenge'&&course==='resistor'&&campaign.progress.index===0",ui)

    def test_all_game_engines_group_controls_without_duplicate_start_or_inner_scroll(self):
        for file in ['training_playground.js','training_subtype_game.js']:
            ui=(WEB_ROOT/file).read_text(encoding='utf-8')
            self.assertIn('play-story play-console',ui)
            self.assertIn("setAttribute('aria-controls'",ui)
            self.assertNotIn('viewport.append(power)',ui)
        ui=(WEB_ROOT/'training_subtype_game.js').read_text(encoding='utf-8')
        self.assertIn('story.append(fields)',ui)
        self.assertIn('story.append(instruction,row,hint)',ui)
        self.assertIn('power.hidden=!s.started',ui)
        self.assertNotIn('打开电源 / 开始观察',ui)
        css=(WEB_ROOT/'training_playground.css').read_text(encoding='utf-8')
        self.assertIn('.play-console .play-action-row',css)
        self.assertIn('.play-console .subgame-fields{grid-template-columns:1fr',css)
        self.assertNotIn('overflow-y:auto',css)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_sixteen_sequential_missions_require_actions_and_real_model_goals(self):
        script=r'''
const L=require(process.argv[1]),a=require('node:assert/strict');
const answers={resistor:[[330,{},0],[100,{},0],[330,{},0],[1000,{},0]],capacitor:[[10,{},1],[22,{},2],[22,{near:true},0],[22,{},3]],inductor:[[100,{},1.5],[220,{},3],[22,{},3],[100,{},3]],diode:[[true,{},0],[true,{reverse:true},0],[false,{reverse:true},0],[true,{reverse:false},0]]};
let total=0;
for(const [c,cases] of Object.entries(answers)){
 let s=L.create(c);a.equal(L.list(c).length,4);a(Object.isFrozen(L.list(c)));a.equal(L.visit(s,3),s);
 for(let i=0;i<4;i++){
  const l=L.level(c,i);a(Object.isFrozen(l));a(Object.isFrozen(l.setup));a(l.title&&l.goal&&l.hint&&l.learned);
  s=L.visit(s,i);a.equal(s.index,i);a.equal(L.judge(s,l.setup,0).passed,false);
  let trial=L.action(s,'change');a.equal(L.judge(trial,l.setup,0).passed,false,'Mission seed must not auto-complete '+c+i);
  const [value,extra,phase]=cases[i],p={...l.setup,power:true,value,...extra};trial=L.action(trial,'trigger');a.equal(L.judge(trial,p,phase).passed,true,c+i);
  const next=L.record(trial,p,phase);a.equal(next.cleared.length,i+1);a.equal(L.record(next,p,phase).cleared.length,i+1);a.equal(trial.cleared.length,i);s=next;total++;
  a.equal(L.judge({...s,index:i,interacted:true},{...p,power:false},phase).passed,false);
 }
 a.deepEqual(s.cleared,[0,1,2,3]);const back=L.visit(s,0);a.equal(back.cleared.length,4);a.equal(L.attempt(back).interacted,false);a.equal(L.create(c).cleared.length,0);
}
a.equal(total,16);a.throws(()=>L.level('__proto__',0),RangeError);a.throws(()=>L.level('resistor',4),RangeError);a.throws(()=>L.visit(L.create('resistor'),-1),RangeError);a.throws(()=>L.action(L.create('resistor'),'admin'),RangeError);a.throws(()=>L.record({...L.create('resistor'),cleared:[1]},L.level('resistor',0).setup,0),RangeError);
const s=L.action(L.create('capacitor'),'trigger');a.equal(L.judge({...s,index:0},{...L.level('capacitor',0).setup},3).passed,false);
'''
        completed=subprocess.run([shutil.which('node'),'-e',script,str(WEB_ROOT/'training_playground_levels.js')],capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)

    def test_missions_stay_page_only_and_offer_free_experiments(self):
        source=(WEB_ROOT/'training_playground_levels.js').read_text(encoding='utf-8')
        for forbidden in ['fetch(', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
            self.assertNotIn(forbidden,source)
        ui=(WEB_ROOT/'training_playground.js').read_text(encoding='utf-8')
        for text in ['闯关挑战','自由实验','playground-mission','playground-outcome','观察下一阶段','L.record','b.disabled=i>']:
            self.assertIn(text,ui)
        self.assertLess(build_training_html().index('root.TrainingPlaygroundLevels=api'),build_training_html().index('window.TrainingPlayground=Object.freeze'))

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_playground_live_values_validate_choices_and_preserve_current(self):
        script=r'''
const m=require(process.argv[1]),a=require('node:assert/strict'),p=value=>({value,power:true,reverse:false,near:true});
for(const c of m.courses){const d=m.lesson(c);a(Object.isFrozen(d));for(const [value] of d.choices)for(const phase of [0,.3,1,1.5,2,2.5,3]){const r=m.evaluate(c,p(value),phase);for(const k of ['current','voltage','brightness','storage','source','load','power'])a(Number.isFinite(r[k]));a(Math.abs(r.source-r.load-r.storage)<1e-10);a(r.story&&r.stage);a.equal(m.evaluate(c,{...p(value),power:false},phase).current,0);}a.throws(()=>m.evaluate(c,p(NaN)),RangeError);a.throws(()=>m.evaluate(c,p(d.initial),-1),RangeError);a.throws(()=>m.evaluate(c,p(d.initial),NaN),RangeError);}
a.throws(()=>m.lesson('__proto__'),RangeError);a.throws(()=>m.evaluate('resistor',{value:330}),RangeError);
const low=m.evaluate('resistor',p(1000)),mid=m.evaluate('resistor',p(330)),high=m.evaluate('resistor',p(100));a(low.brightness<mid.brightness&&mid.brightness<high.brightness);a.equal(high.current,.03);a.equal(high.power,.09);a.equal(low.current,.003);
const cap=m.evaluate('capacitor',p(10),1.5);a.equal(cap.storage,-.02);a(Math.abs(cap.source-.005)<1e-12);a.equal(cap.load,.025);a(Math.abs(cap.voltage-3.25)<1e-10);a.equal(m.evaluate('capacitor',{...p(10),near:false},1.5).voltage,cap.voltage);
const recover=m.evaluate('capacitor',p(10),2.5);a.equal(recover.storage,.02);a.equal(recover.source,.025);a.equal(recover.load,.005);a.equal(recover.voltage,cap.voltage);a.equal(m.evaluate('capacitor',p(10),3).storage,0);a.equal(m.evaluate('capacitor',p(10),3).voltage,3.3);
const bad=m.evaluate('inductor',p(22),3);a(bad.unknown);a.equal(bad.value,'不再预测');a.equal(m.evaluate('inductor',p(220),3).unknown,false);
a(m.evaluate('diode',p(true)).current>0);a.equal(m.evaluate('diode',p(false)).current,0);a(m.evaluate('diode',{...p(false),reverse:true}).current<0);a.equal(m.evaluate('diode',{...p(true),reverse:true}).current,0);
'''
        completed=subprocess.run([shutil.which('node'),'-e',script,str(WEB_ROOT/'training_playground_math.js')],capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)

    def test_playground_is_self_contained_not_a_video_or_remote_service(self):
        page=build_training_html()
        self.assertIn('window.TrainingPlaygroundAssets=',page)
        self.assertIn('data:image/webp;base64,',page)
        self.assertIn('new T.WebGLRenderer',page)
        self.assertNotIn('<video',page)
        self.assertNotIn('<script src=',page)
        for name in ['training_playground.js','training_playground_scene.js','training_playground_math.js']:
            text=(WEB_ROOT/name).read_text(encoding='utf-8')
            for forbidden in ['fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
                self.assertNotIn(forbidden,text)
        self.assertTrue((WEB_ROOT/'vendor/three-LICENSE.txt').is_file())
        self.assertTrue((WEB_ROOT/'assets/heroicons-LICENSE.txt').is_file())
        self.assertLess(page.index('globalThis.TrainingPlaygroundMath') if 'globalThis.TrainingPlaygroundMath' in page else page.index('root.TrainingPlaygroundMath'),page.index('window.TrainingPlayground=Object.freeze'))

    def test_catalog_assets_are_ordered_and_keep_one_viewer(self):
        page = build_training_html()
        self.assertEqual(page.count('<canvas'), 1)
        for asset in ['training_catalog.js', 'training_catalog_geometry.js', 'training_catalog_labs.js', 'training_catalog_ui.js']:
            content = (WEB_ROOT / asset).read_text(encoding='utf-8')
            self.assertNotIn('fetch(', content)
            self.assertNotIn('localStorage', content)
            self.assertNotIn('member_token', content)
        self.assertLess(page.index('root.TrainingCatalog=api'), page.index('root.TrainingCatalogGeometry=api'))
        self.assertLess(page.index('root.TrainingCatalogLabs=api'), page.index('window.TrainingCatalogUI=Object.freeze'))
        self.assertIn('id="subtypes"', page)
        self.assertNotIn('id="material-leaders"', page)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_catalog_seven_families_and_thirty_complete_scoped_chapters(self):
        script = r'''
const c=require(process.argv[1]),a=require('node:assert/strict');
a.deepEqual(c.families.map(f=>f.name),['电容','电阻','电感','晶振','MOS管','二极管','三极管']);
a.deepEqual(c.families.map(f=>c.children(f.id).length),[5,4,4,4,3,6,4]);
a.equal(c.lessons.length,30);a.equal(new Set(c.lessons.map(d=>d.id)).size,30);
a.equal(c.lessons.filter(d=>d.baseline).length,4);
for(const f of c.families)a.equal(c.lesson(f.default).family,f.id);
for(const d of c.lessons){a(Object.isFrozen(d));a(Object.isFrozen(d.layers));
 for(const k of ['title','kind','summary','use','scope','lab'])a(d[k]);
 a(d.specs.length>=3);a(d.principle.length>=2);a(d.ask.length>=2);a(d.sources.length);
 a.equal(d.quiz.options.length,3);a(Number.isInteger(d.quiz.answer)&&d.quiz.answer>=0&&d.quiz.answer<3);a(d.quiz.explain);
 a.equal(new Set(d.layers.map(p=>p.id)).size,d.layers.length);a(d.layers.length>=3);
 for(const p of d.layers)for(const k of ['id','name','composition','role'])a(p[k]);
 for(const id of d.outerIds)a(d.layers.some(p=>p.id===id));
 for(const s of d.sources)a(s[0]&&s[1].startsWith('https://'));
}
for(const bad of ['__proto__','constructor','other',null]){a.throws(()=>c.lesson(bad),RangeError);a.throws(()=>c.children(bad),RangeError);}
const material=(id,p)=>c.lesson(id).layers.find(l=>l.id===p).composition;
a.match(material('res-thin','element'),/NiCr/);a.match(material('res-sulfur','element'),/RuO₂/);
a.match(material('mos-n','regions'),/N⁺/);a.match(material('mos-p','regions'),/P⁺/);
a.match(material('bjt-npn','base'),/P型/);a.match(material('bjt-pnp','base'),/N型/);
a.match(c.lesson('xtal-tcxo').layers.find(p=>p.id==='ic').name,/温度补偿/);
a.match(c.lesson('xtal-vcxo').layers.find(p=>p.id==='ic').name,/压控调谐/);
a.match(c.lesson('dio-schottky').principle.join(''),/不画成普通PN结/);
a.match(c.lesson('cap-aluminum').scope,/卷绕芯局部展开/);
a.match(c.lesson('cap-tantalum').scope,/不按真实孔隙/);
'''
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_catalog.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_catalog_meshes_have_finite_numbered_parts_and_sealed_exteriors(self):
        script = r'''
const dir=process.argv[1],c=require(dir+'/training_catalog.js'),g=require(dir+'/training_catalog_geometry.js'),a=require('node:assert/strict');
const primitives={box(f,p,s,color,id){a(s.every(v=>v>0));f.push({id,color,p:[p,p.map((v,i)=>v+s[i]),p.map((v,i)=>v-s[i])]});},tube(f,p,q,r,color,id){a(r>0);f.push({id,color,p:[p,q,p.map(v=>v+r)]});}};
for(const d of c.lessons)for(const mode of ['exterior','materials'])for(const e of [0,.5,1]){
 const m=g.build(d.id,mode,e,primitives);a(m.faces.length);a(m.anchors.length);
 const ids=d.layers.filter(p=>mode==='materials'||d.outerIds.includes(p.id)).map(p=>p.id);
 a.deepEqual(m.anchors.map(p=>p.id),ids);
 for(const p of m.anchors)a(p.point.every(Number.isFinite));
 for(const f of m.faces){a(d.layers.some(p=>p.id===f.id));a(f.p.flat().every(Number.isFinite));a(f.color.every(Number.isFinite));}
 if(!d.baseline&&mode==='exterior')for(const f of m.faces)a(ids.includes(f.id),d.id+' leaked internal part '+f.id);
}
for(const bad of [-1,NaN,Infinity,1.1])a.throws(()=>g.build('mos-n','materials',bad,primitives),RangeError);
a.throws(()=>g.build('mos-n','other',0,primitives),RangeError);
'''
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT)], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_catalog_labs_are_subtype_specific_and_validate_inputs(self):
        script = r'''
const l=require(process.argv[1]),c=require(process.argv[2]),a=require('node:assert/strict');
for(const d of c.lessons){const cfg=l.config(d.id);a(cfg.options.some(o=>o[0]===cfg.initial));
 for(const [x] of cfg.options){const r=l.evaluate(d.id,x);a(r.status);a(r.metrics.length);a(r.series.flat().every(Number.isFinite));}
 for(const bad of [NaN,null,{},'bad'])a.throws(()=>l.evaluate(d.id,bad),RangeError);
 cfg.options.length=0;a(l.config(d.id).options.length);
}
const text=(id,x)=>l.evaluate(id,x).metrics.flat().join(' ');
a.match(text('res-thin',40),/1001 Ω/);a.match(text('res-sense',2),/20 mV.*40 mW/);
a.match(text('cap-aluminum',.2),/0.2 W.*0.2 V/);a.match(text('cap-film',100),/10 A/);
a.match(text('xtal-passive',15),/9.5 pF/);a.match(text('xtal-passive',20),/12 pF/);
a.equal(l.evaluate('xtal-passive',0).signal,'none');a.match(l.evaluate('xtal-passive',15).status,/假设其余振荡条件已满足/);
a.match(text('xtal-active','on'),/24 MHz.*41.667 ns/);a.equal(l.evaluate('xtal-active','off').signal,'none');
a.match(text('xtal-tcxo',2.5),/65 Hz/);a.match(text('xtal-vcxo',50),/26.001 MHz/);
a.match(text('mos-n',2.5),/Ron未提供/);a.match(text('mos-n',10),/10 V.*0.08 W/);a.match(text('mos-p',10),/-10 V/);
a.match(text('mos-dual',2),/0.16 W/);a.match(text('dio-zener',3),/2.5 V.*0 mA/);
a.match(text('dio-tvs','surge'),/10 V@1 A/);a.match(text('bjt-digital',3.3),/404.26 µA/);
a(l.evaluate('bjt-npn',.1).warn);a(!l.evaluate('bjt-npn',2).warn);
const r=l.evaluate('dio-rectifier','output');a(r.series[0].some(v=>v<0));a(r.series[1].every(v=>v>=0));
'''
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_catalog_labs.js'), str(WEB_ROOT / 'training_catalog.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_games_electrical_goals_validate_full_parameters_and_teach_limits(self):
        script = r'''
const g=require(process.argv[1]),a=require('node:assert/strict'),near=(x,y)=>a(Math.abs(x-y)<1e-10);
const winners={resistor:{r:330,rating:.063},capacitor:{c:10,near:true},inductor:{l:220,isat:1.5},diode:{forward:true,vf:.3}};
for(const c of g.courses){const d=g.lesson(c);a(Object.isFrozen(d));a(Object.isFrozen(d.fields));a.equal(d.pairs.length,4);a.equal(new Set(d.pairs.flatMap(p=>p.slice(0,2))).size,8);a(!g.evaluate(c,d.defaults).passed);a(g.evaluate(c,winners[c]).passed);a(d.note);a(d.source[1].startsWith('https://'));for(const f of d.fields)for(const [v] of f.options){const p={...d.defaults,[f.id]:v};const r=g.evaluate(c,p);a(r.metrics.length>=3);a(r.why);}a.throws(()=>g.evaluate(c,{}),RangeError);a.throws(()=>g.evaluate(c,Object.fromEntries(d.fields.map(f=>[f.id,NaN]))),RangeError);}
const r=g.evaluate('resistor',winners.resistor);near(r.values.i,3/330);near(r.values.power,9/330);
a(!g.evaluate('resistor',{r:330,rating:.02}).passed);a(!g.evaluate('resistor',{r:470,rating:.125}).passed);
const c=g.evaluate('capacitor',winners.capacitor);near(c.values.droop,.1);near(c.values.v,3.2);a(!g.evaluate('capacitor',{c:10,near:false}).passed);a(!g.evaluate('capacitor',{c:4.7,near:true}).passed);a(g.evaluate('capacitor',{c:.1,near:true}).metrics[1][1]==='储备不足');
a(g.evaluate('capacitor',{c:.1,near:true}).metrics[0][1].includes('不能外推'));near(g.evaluate('capacitor',{c:10,near:false}).values.v,c.values.v);
const l=g.evaluate('inductor',winners.inductor);near(l.values.delta,3*20/220);a(!g.evaluate('inductor',{l:220,isat:1}).passed);a(!g.evaluate('inductor',{l:100,isat:3}).passed);
const d=g.evaluate('diode',winners.diode);near(d.values.output,3);near(d.values.i,3/33);a(d.values.reverseBlocked);a(!g.evaluate('diode',{forward:true,vf:.7}).passed);a(!g.evaluate('diode',{forward:false,vf:.3}).values.reverseBlocked);
for(const bad of ['__proto__','other',''])a.throws(()=>g.lesson(bad),RangeError);
'''
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_games_math.js')], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which('node'), 'Node is unavailable')
    def test_games_flip_pair_progress_is_lossless_and_not_repeatable(self):
        script = r'''
const g=require(process.argv[1]),a=require('node:assert/strict');
for(const c of g.courses){let s=g.deck(c,()=>.3);a.equal(s.cards.length,8);a.equal(new Set(s.cards.map(c=>c.id)).size,8);
let t=g.flip(s,0);a.equal(t.outcome,'first');a.deepEqual(s.selected,[]);s=t.state;a.equal(g.flip(s,0).outcome,'unchanged');t=g.flip(s,3);a.equal(t.outcome,'miss');s=t.state;a.equal(s.turns,1);a.equal(s.matched.length,0);s=g.flip(s,0).state;a.deepEqual(s.selected,[0]);
for(let pair=0;pair<4;pair++){s=g.flip(s,pair*2).state;t=g.flip(s,pair*2+1);a.equal(t.outcome,'match');a(t.explain);s=t.state;}a.equal(s.matched.length,8);a.equal(new Set(s.matched).size,8);a.equal(g.flip(s,0).outcome,'unchanged');a.equal(s.turns,5);a.throws(()=>g.flip(s,99),RangeError);}
a.throws(()=>g.deck('resistor',()=>1),RangeError);a.throws(()=>g.deck('resistor',()=>NaN),RangeError);
'''
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_games_math.js')], check=True, capture_output=True)

    def test_games_are_optional_local_only_and_separate_from_existing_practice(self):
        page=build_training_html()
        self.assertIn('<details id="games-card" class="games-card">',page)
        self.assertLess(page.index('id="games-card"'),page.index('id="circuit-card"'))
        for text in ['闯关挑战','自由实验','4 关挑战','training-course-change','prefers-reduced-motion:reduce']:
            self.assertIn(text,page)
        for text in ['data-game-mode=', 'id="game-progress"', 'id="game-restart"', 'id="game-feedback"', '知识翻牌', '3D动手实验', 'window.TrainingGamesMath']:
            self.assertNotIn(text,page)
        game_js=(WEB_ROOT/'training_playground_entry.js').read_text(encoding='utf-8')
        for term in ['fetch(', 'localStorage', 'sessionStorage', 'member_token', 'sqlite', 'setInterval(', 'setTimeout(']:
            self.assertNotIn(term,game_js)
        self.assertIn('TrainingPlayground.mount',game_js)
        self.assertIn('[x,Y,.77]',(WEB_ROOT/'training_playground_scene.js').read_text(encoding='utf-8'))

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
        self.assertIn('电容、电阻、电感、晶振、MOS管、二极管和三极管', rendered[-1])
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

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_beginner_examples_follow_live_models_and_preserve_unknowns(self):
        script = r"""
const b=require(process.argv[1]),m=require(process.argv[2]),s=require(process.argv[3]),a=require('node:assert/strict');
for(const id of ['resistor','capacitor','mos-n','mos-p']){
 a(b.supported(id));a(Object.isFrozen(b.lesson(id)));a(b.lesson(id).purpose);a.equal(b.lesson(id).words.length,3);
 const questions=new Set();
 for(let i=0;i<(id.startsWith('mos-')?3:4);i++){a(b.fixed(id,i));a(b.hint(id,i));const p=b.practice(id,i);a.equal(p.answers.length,3);a(p.explanation);a(p.verify);a(p.trial);}
 for(let i=0;i<(id.startsWith('mos-')?3:4);i++)questions.add(b.practice(id,i).question);
 a.equal(questions.size,id.startsWith('mos-')?3:4);
}
a(!b.supported('__proto__'));a(!b.supported('res-thin'));a.throws(()=>b.lesson('x'),RangeError);a.throws(()=>b.fields('mos-n',3),RangeError);
for(const value of [100,330,1000])for(const power of [true,false]){
 const p={value,power,near:true,reverse:false},r=m.evaluate('resistor',p),t=b.explain('resistor',p,r);
 a(t.change.includes(power?(r.current*1000).toFixed(1)+' mA':'电源仍是5 V'));
 if(power){a(t.change.includes('压降3 V'));a(t.change.includes((r.power*1000).toFixed(1)+' mW'));a(t.why.includes('前后')||t.why.includes('流入'));}
}
for(const phase of [0,1,1.5,2,2.5,3]){const p={value:22,power:true,near:true,reverse:false},r=m.evaluate('capacitor',p,phase),t=b.explain('capacitor',p,r,phase);a(t.title);a(t.change);a(t.why);if(phase>=1&&phase<2)a(t.change.includes('5 mA + 电容20 mA = 芯片25 mA'));if(phase>=2&&phase<3)a(t.change.includes('芯片5 mA + 电容回充20 mA'));}
for(const id of ['mos-n','mos-p'])for(const drive of [0,2.5,10]){
 const p={drive,load:2},r=s.evaluate(id,p),t=b.explain(id,p,r,0,true);a(t.change.includes((id==='mos-p'?-drive:drive)+' V'));
 if(drive===2.5){a(t.title.includes('未知'));a(t.change.includes('不能据此计算'));a(!t.change.includes('电流为0'));}
 if(drive===10)a(t.change.includes('80 mW'));
 a.deepEqual(b.fields(id,0),['drive']);a.deepEqual(b.fields(id,1),['drive']);a.deepEqual(b.fields(id,2),['load']);
 a(b.optionLabel(id,'drive',10,'').includes(id==='mos-p'?'−10 V':'+10 V'));
}
"""
        subprocess.run([shutil.which('node'), '-e', script, str(WEB_ROOT / 'training_beginner.js'), str(WEB_ROOT / 'training_playground_math.js'), str(WEB_ROOT / 'training_subtype_game_math.js')], check=True, capture_output=True)

    def test_beginner_examples_are_bundled_without_business_storage(self):
        script = (WEB_ROOT / 'training_beginner.js').read_text(encoding='utf-8')
        page = build_training_html()
        self.assertIn('window.TrainingBeginner', page)
        self.assertLess(page.index('root.TrainingBeginner=api'), page.index('const B=window.TrainingBeginner'))
        for term in ['fetch(', 'localStorage', 'sessionStorage', 'member_token', 'sqlite']:
            self.assertNotIn(term, script)
        for term in ['play-cause', 'play-transfer', '换个场景', '控制端', '回充']:
            self.assertIn(term, script)

    def test_pcb_demo_is_separate_from_structure_and_device_labs(self):
        page=build_training_html()
        for word in ['PCB电路工作演示','限流电阻','电源接反','电容回充','续流路径','内部示意动画','约定电流方向','负载10 Ω','不是固定导通门槛']:
            self.assertIn(word,page)
        self.assertLess(page.index('id="circuit-card"'),page.index('class="workspace"'))
        self.assertIn('training-course-change',page)
        self.assertNotIn('<script src=',page)
