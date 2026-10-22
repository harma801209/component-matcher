"""Probe connections, learning progression and transfer review stay reproducible."""
import unittest
import tests.test_repair_shop as repair_tests


class RepairShopMeterTests(unittest.TestCase):
    def node(self, source):
        return repair_tests.RepairShopTests().run_node("const Meter=require(process.argv[1]+'/repair_shop_meter.js'),Learning=require(process.argv[1]+'/repair_shop_learning.js');\n"+source)

    def test_voltage_is_the_signed_difference_of_two_declared_ports(self):
        self.node(r'''
for(const product of D.products){let seed=0;while(E.offer(seed).product.id!==product.id||!E.offer(seed).fault.enabled)seed++;
 const j=E.offer(seed);let s=open(act(E.create(),'accept',{seed}).state);s=act(s,'power').state;
 const expected=require(process.argv[1]+'/repair_shop_physics.js').solve(j.product,j.fault);
 for(let i=0;i<3;i++)for(let k=0;k<3;k++){
  const r=Meter.voltage(j,s.active,{red:'TP'+(i+1),black:'TP'+(k+1),jack:'v'});
  a(!r.error);if(i===k)a.equal(r.numeric,0);else if(expected.volts[i]===null||expected.volts[k]===null)a.equal(r.numeric,null);else a(Math.abs(r.numeric-(expected.volts[i]-expected.volts[k]))<1e-10);
 }
 const r=Meter.voltage(j,s.active,{red:'TP1',black:'GND',jack:'v'}),reverse=Meter.voltage(j,s.active,{red:'GND',black:'TP1',jack:'v'});
 a.equal(reverse.numeric,-r.numeric);a.equal(r.id,product.parts[0].id);a.equal(reverse.id,'pair');
}
''')

    def test_missing_wrong_jack_and_unsafe_connections_never_record_evidence(self):
        self.node(r'''
let s=open(act(E.create(),'accept',{seed:32}).state);s=act(s,'power').state;
for(const leads of [{},{red:'TP1',black:'GND',jack:'ma'},{red:'bad',black:'GND',jack:'v'}]){
 const r=act(s,'probeMeasure',{mode:'voltage',leads});a(!r.ok);a.equal(r.state.active.measurements.length,0);a.equal(r.state.coins,s.coins);
}
a(!act(s,'probeMeasure',{mode:'component',id:'R1',leads:{fixture:'R1'}}).ok);
a(!act(s,'meterSeries',{leads:{red:'SRC',black:'LOAD',jack:'ma'}}).ok);
''')

    def test_current_setup_requires_power_off_and_survives_replay_without_changing_model(self):
        self.node(r'''
for(const product of D.products){let seed=0;while(E.offer(seed).product.id!==product.id||!E.offer(seed).fault.enabled)seed++;
 let s=open(act(E.create(),'accept',{seed}).state),j=E.offer(seed),leads={red:'SRC',black:'LOAD',jack:'ma'};
 a(!act(s,'meterSeries',{leads:{...leads,black:'GND'}}).ok);
 let r=act(s,'meterSeries',{leads});a(r.ok,r.message);s=act(r.state,'power').state;
 r=act(s,'probeMeasure',{mode:'current',leads});a(r.ok,r.message);const m=r.state.active.measurements[0];a(Number.isFinite(m.numeric)&&m.numeric>=0&&m.numeric<=.2);a(!m.proof);
 const copy=E.restore(JSON.parse(JSON.stringify(r.state)));a.equal(copy.active.measurements[0].value,m.value);a.deepEqual(copy.active.currentSetup,leads);
 a(!act(copy,'meterSeries',{leads:null}).ok);
 s=act(copy,'power').state;s=act(s,'discharge').state;r=act(s,'meterSeries',{leads:null});a(r.ok);a(!r.state.active.currentSetup);
}
''')

    def test_current_uses_declared_input_branch_not_output_power_divided_by_voltage(self):
        self.node(r'''
for(const id of ['speaker','router']){let seed=1;while(E.offer(seed).product.id!==id||E.offer(seed).fault.component==='F1')seed++;
 const j=E.offer(seed),p=require(process.argv[1]+'/repair_shop_physics.js').solve(j.product,j.fault);
 a(Math.abs(Meter.inputCurrent(j,p)-(id==='speaker'?.06:p.metrics.input/100))<1e-12);
}
''')

    def test_canonical_report_does_not_mislabel_differential_voltage_as_gnd_reading(self):
        self.node(r'''
const {s:done,j}=solve(31);let s=atBoardTest(done);s.active.tested=false;
const r=act(s,'probeMeasure',{mode:'voltage',leads:{red:'TP1',black:'TP2',jack:'v'}});a(r.ok);a.equal(r.state.active.measurements.at(-1).id,'pair');a(r.state.active.measurements.at(-1).key.startsWith('voltage:pair:'));
''')

    def test_progressive_guidance_and_six_transfer_questions_do_not_reveal_early(self):
        self.node(r'''
a.equal(Learning.support(0,'auto').level,'full');a.equal(Learning.support(1,'auto').level,'steps');a.equal(Learning.support(2,'auto').level,'off');a.equal(Learning.support(99,'full').level,'full');
for(const product of D.products){let seed=0;while(E.offer(seed).product.id!==product.id||!E.offer(seed).fault.enabled)seed++;const j=E.offer(seed),s=act(E.create(),'accept',{seed}).state;
 const q=Learning.quiz(j);a(q.question&&q.options.length===3&&q.explanation);a.equal(q.options.filter(x=>x.correct).length,1);
 a(!act(s,'review',{answer:q.options.find(o=>o.correct).id}).ok);
 const solved=solve(seed).s,before=JSON.stringify(solved),wrong=q.options.find(o=>!o.correct),right=q.options.find(o=>o.correct);
 const miss=act(solved,'review',{answer:wrong.id});a(miss.ok);a(!miss.state.active.review.correct);a.equal(miss.state.points,solved.points);a.equal(miss.state.coins,solved.coins);
 const pass=act(miss.state,'review',{answer:right.id});a(pass.ok);a(pass.state.active.review.correct);a.equal(pass.state.active.review.attempts,2);a.equal(E.restore(pass.state).active.review.correct,true);a.equal(JSON.stringify(solved),before);
}
''')

    def test_all_seventeen_faults_solve_with_explicit_connections_and_manual_review(self):
        self.node(r'''
const V=require(process.argv[1]+'/repair_shop_evidence.js'),seen=new Set();
for(let seed=0;seed<400;seed++){const j=E.offer(seed),key=j.product.id+':'+j.fault.component+':'+j.fault.reason;if(!j.fault.enabled||seen.has(key))continue;seen.add(key);
 let s=open(act(E.create(),'accept',{seed}).state);s=act(s,'power').state;
 const run=(type,args={})=>{const r=act(s,type,args);a(r.ok,r.message);s=r.state;};
 run('probeMeasure',{mode:'voltage',leads:{red:'TP1',black:'GND',jack:'v'}});
 run('probeMeasure',{mode:'scope',id:j.fault.component,leads:{scope:true}});run('power');run('discharge');
 run('probeMeasure',{mode:'component',id:j.fault.component,leads:{fixture:j.fault.component}});
 run('diagnose',{id:j.fault.component,reason:j.fault.reason});const required=j.product.parts.find(p=>p.id===j.fault.component),c=j.candidates.find(c=>!E.compatible(required,c));
 run('install',{stockId:c.stockId,orientation:'correct'});run('power');run('test');
 const report=V.report(j,s.active);a.equal(report.reasoning.length,6);a(report.reasoning[1].text.includes(s.active.measurements[0].value));a(report.reasoning[2].text.includes(j.fault.bad));
 a.equal(report.rows.filter(r=>r.kind==='voltage'&&r.before===null).length,2,'Do not invent unrecorded TP2/TP3 measurements');
 a.deepEqual(V.report(j,E.restore(s).active),report);s=close(s);run('deliver');const coins=s.coins,points=s.points,q=Learning.quiz(j);run('review',{answer:q.options.find(o=>o.correct).id});
 a.equal(s.coins,coins);a.equal(s.points,points);a(!act(s,'deliver').ok);a(E.restore(s).active.review.correct);
}a.equal(seen.size,17);
''')

    def test_differential_and_floating_feedback_keeps_connections_and_uncertainty(self):
        self.node(r'''
const V=require(process.argv[1]+'/repair_shop_evidence.js');
let seed=0;while(E.offer(seed).product.id!=='clock'||E.offer(seed).fault.component!=='R1')seed++;
const j=E.offer(seed),s=open(act(E.create(),'accept',{seed}).state),floating=Meter.voltage(j,s.active,{red:'TP2',black:'GND',jack:'v'});
a.equal(floating.numeric,null);a(floating.unsupported);a(V.describe(floating).text.includes('不强行设成0V'));
const pair=Meter.voltage(j,s.active,{red:'GND',black:'TP1',jack:'v'});a(V.describe(pair).text.includes('红 GND − 黑 TP1'));a(!V.describe(pair).proof);
''')

    def test_offline_bundle_orders_dependencies_and_ui_has_no_default_quiz_answer(self):
        from product_training import WEB_ROOT, build_training_html
        page=build_training_html()
        for dependency in ('RepairShopMeter=api', 'RepairShopLearning=api'):
            self.assertLess(page.index(dependency),page.index('RepairShopEngine=api'))
        self.assertLess(page.index('RepairShopProbes=Object.freeze'),page.index('RepairShopScene=api'))
        ui=(WEB_ROOT/'repair_shop_ui.js').read_text(encoding='utf-8')
        self.assertIn("String(review?.answer===option.id)",ui)
        self.assertIn("trainingPreference===value",ui)
        for text in ('先选择工具并接好表笔或夹具','展开这一步操作','换个情境，再判断一次','断电串入电流表'):
            self.assertIn(text,page)


if __name__=='__main__':
    unittest.main()
