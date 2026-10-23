"""Beginner discovery is separate from paid jobs and backed by the existing physics."""
import unittest
from product_training import WEB_ROOT, build_training_html
from tests import test_repair_shop as repair_tests


class FirstStepsTests(unittest.TestCase):
    def node(self, body):
        repair_tests.RepairShopTests().run_node(r'''
const I=require(process.argv[1]+'/repair_shop_first_steps.js'),P=require(process.argv[1]+'/repair_shop_physics.js');
const step=(s,type,extra={})=>{const r=I.apply(s,{type,...extra});a(r.ok,r.message);return r.state;};
const inspect=(s,id)=>{if(s.power)s=step(s,'power',{on:false});if(!s.discharged)s=step(s,'discharge');return step(s,'inspect',{id});};
const repair=s=>{s=step(s,'fixture');s=step(s,'power',{on:true});s=step(s,'observe');s=inspect(s,'R1');s=step(s,'diagnose',{id:'R1',reason:s.episode===0?'open':'drift'});s=step(s,'install',{id:'original'});s=step(s,'power',{on:true});s=step(s,'test');return s;};
const compare=s=>{s=step(s,'predict',{answer:'lower'});s=step(s,'fixture');s=step(s,'power',{on:true});s=step(s,'observe');s=step(s,'power',{on:false});s=step(s,'discharge');s=step(s,'resistor',{value:440});s=step(s,'power',{on:true});s=step(s,'observe');return step(s,'principle',{answer:'series'});};
''' + body)

    def test_three_chapters_require_evidence_prediction_and_independent_transfer(self):
        self.node(r'''
let s=I.create();a(!I.apply(s,{type:'next'}).ok);s=repair(s);a(s.tested);s=step(s,'next');a.equal(s.episode,1);
a(!I.apply(s,{type:'observe'}).ok);s=compare(s);a(s.tested);s=step(s,'next');a.equal(s.episode,2);
a.equal(I.product(s).parts.find(p=>p.id==='R1').value,180);a(!s.helpUsed);s=repair(s);s=step(s,'next');a(s.done);a.equal(s.records.length,3);a(s.records[2].independent);a(s.records[1].firstPredictionCorrect);a(!s.power);
const restored=I.restore(JSON.parse(JSON.stringify(s)));a.deepEqual(restored,s);a(!I.apply(s,{type:'next'}).ok);
''')

    def test_safety_and_wrong_choices_do_not_become_success(self):
        self.node(r'''
let s=I.create();a(!I.apply(s,{type:'power',on:true}).ok);s=step(s,'fixture');s=step(s,'power',{on:true});a(!I.apply(s,{type:'inspect',id:'R1'}).ok);a(!I.apply(s,{type:'install',id:'original'}).ok);s=step(s,'observe');s=inspect(s,'F1');a(!s.inspected.F1.proof);a(!I.apply(s,{type:'diagnose',id:'R1',reason:'open'}).ok);
s=inspect(s,'R1');let r=I.apply(s,{type:'diagnose',id:'F1',reason:'open'});a(!r.ok);a(!r.state.diagnosed);s=step(r.state,'diagnose',{id:'R1',reason:'open'});
for(const id of ['higher','wrongpackage']){r=I.apply(s,{type:'install',id});a(!r.ok);a(!r.state.installed);a(r.message.length>12);}
s=step(s,'install',{id:'original'});a(!I.apply(s,{type:'test'}).ok);s=step(s,'power',{on:true});s=step(s,'test');a(I.result(s).pass);
''')

    def test_experiment_reuses_nonlinear_solver_not_a_brightness_or_half_current_rule(self):
        self.node(r'''
let s=step(repair(I.create()),'next');s=step(s,'predict',{answer:'same'});a(!I.apply(s,{type:'predict',answer:'lower'}).ok);s=step(s,'fixture');s=step(s,'power',{on:true});s=step(s,'observe');a(!I.apply(s,{type:'resistor',value:440}).ok);s=step(s,'power',{on:false});s=step(s,'discharge');s=step(s,'resistor',{value:440});s=step(s,'power',{on:true});s=step(s,'observe');
const x=s.comparisons['220'],y=s.comparisons['440'];a(x.current>y.current);a(Math.abs(y.current/x.current-.5)>.001);a.equal(y.current,P.solve(I.product(s)).metrics.current);a(y.resistorPower<=I.product(s).parts.find(p=>p.id==='R1').power);a(!s.tested);
let r=I.apply(s,{type:'principle',answer:'power'});a(!r.ok);a(!r.state.tested);s=step(r.state,'principle',{answer:'series'});s=step(s,'next');a.equal(s.records[1].firstPrediction,'same');a(!s.records[1].firstPredictionCorrect);
''')

    def test_transfer_help_and_retries_are_not_reported_as_unaided_mastery(self):
        self.node(r'''
let s=step(compare(step(repair(I.create()),'next')),'next');s=step(s,'help');a(s.helpUsed);s=repair(s);s=step(s,'next');a(!s.records[2].independent);a(s.records[2].helpUsed);a.equal(s.records[2].result,'completed-with-help');
''')

    def test_saved_flags_cannot_skip_lessons_and_invalid_events_fail_closed(self):
        self.node(r'''
let s=I.restore({version:1,episode:3,done:true,records:[1,2,3],events:[]});a.equal(s.episode,0);a(!s.done);
for(const raw of [null,{}, {version:1,events:[{type:'next'}]}, {version:1,events:[{type:'power',on:true}]},{version:1,events:[{type:'resistor',value:Infinity}]}])a.deepEqual(I.restore(raw),I.create());
s=repair(I.create());a.deepEqual(I.restore(JSON.parse(JSON.stringify(s))),s);a.equal(s.events.filter(e=>e.type==='observe').length,1);
''')

    def test_learning_has_no_access_to_formal_economy_or_runtime_storage(self):
        self.node(r'''
const economy=E.create(),before=JSON.stringify(economy);let s=step(repair(I.create()),'next');s=step(compare(s),'next');s=step(repair(s),'next');a.equal(JSON.stringify(economy),before);a.notEqual(I.KEY,E.KEY);a(!Object.hasOwn(s,'coins'));a(!Object.hasOwn(s,'points'));
''')
        source=(WEB_ROOT/'repair_shop_first_steps.js').read_text(encoding='utf-8')
        for forbidden in ('localStorage','document.', 'fetch(', 'sqlite', 'E.apply('):
            self.assertNotIn(forbidden,source)

    def test_ui_bundles_after_existing_physics_and_does_not_replace_free_jobs(self):
        page=build_training_html()
        self.assertLess(page.index('root.RepairShopFirstSteps=api'),page.index('root.RepairShopFirstStepsUI=api'))
        self.assertIn('第一次修好它',page)
        self.assertIn('不是照度测量',page)
        self.assertIn('自由接单',page)
        self.assertIn('仅保存本机练习进度',page)

    def test_phone_viewport_and_scene_markings_follow_real_context_not_fixed_values(self):
        ui=(WEB_ROOT/'repair_shop_first_steps_ui.js').read_text(encoding='utf-8')
        css=(WEB_ROOT/'repair_shop_first_steps.css').read_text(encoding='utf-8')
        scene=(WEB_ROOT/'repair_shop_scene.js').read_text(encoding='utf-8')
        self.assertIn('ownerDocument.defaultView',ui)
        self.assertIn('viewportOwner.removeEventListener',ui)
        self.assertIn('view?.dispose()',ui)
        self.assertNotIn('svh',css)
        self.assertNotIn('100vh',css)
        self.assertIn('overflow-y:auto',css)
        self.assertIn('TrainingResistorMarking.encode(part.value)',scene)
        self.node(r'''
const marking=require(process.argv[1]+'/training_resistor_marking.js');
for(const [value,code] of [[220,'221'],[440,'441'],[180,'181'],[4700,'472'],[10000,'103']])a.equal(marking.encode(value).code,code);
''')

    def test_paused_workbench_shortcuts_do_not_intercept_practice_keys(self):
        self.node(r'''
const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(process.argv[1]+'/repair_shop_ui.js','utf8');
const body=source.match(/shop\.addEventListener\('keydown',e=>\{(.+)\}\);/)[1];let calls=[];
const ctx={screen:'beginner',driverState:null,immersive:false,activeLead:'black',mode:'voltage',putDownProbe:()=>calls.push('down'),rotateProbe:(color,angle)=>calls.push([color,angle])};
vm.runInNewContext('globalThis.listen=e=>{'+body+'};',ctx);
const key=k=>ctx.listen({key:k,preventDefault:()=>calls.push('prevent'),target:{closest:()=>null}});
for(const k of ['q','e','Escape'])key(k);a.deepEqual(calls,[]);
ctx.screen='rewards';key('Escape');a.deepEqual(calls,[]);
ctx.screen='work';key('q');key('e');key('Escape');a.deepEqual(calls,['prevent',['black',-15],'prevent',['black',15],'prevent','down']);
''')


if __name__=='__main__':
    unittest.main()
