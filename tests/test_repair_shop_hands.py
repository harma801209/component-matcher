"""Hands-on steps cannot substitute for electrical evidence or real physics."""
import unittest
from tests import test_repair_shop as base
from product_training import WEB_ROOT, build_training_html


class HandsOnTests(unittest.TestCase):
    def node(self, body):
        base.RepairShopTests().run_node(r'''
const H=require(process.argv[1]+'/repair_shop_hands.js'),W=require(process.argv[1]+'/repair_shop_waveforms.js'),P=require(process.argv[1]+'/repair_shop_physics.js');
const go=(s,event)=>{const r=E.apply(s,event);a(r.ok,r.message);return r.state;};
function ready(chosen){let seed=chosen??1;while(!E.offer(seed).fault.enabled)seed++;let s=go(E.create(),{type:'accept',seed});s=go(s,{type:'discharge'});for(let n=0;n<12&&!Mechanics.onTable(s.active.mechanics);n++){const step=Mechanics.next(s.active.mechanics);s=go(s,{type:'mechanical',op:step.op,id:step.id,tool:'phillips'});}s=go(s,{type:'power'});const j=E.offer(seed),id=j.fault.component;s=go(s,{type:'measure',id,mode:'voltage'});s=go(s,{type:'power'});s=go(s,{type:'discharge'});s=go(s,{type:'measure',id,mode:'component'});s=go(s,{type:'diagnose',id,reason:j.fault.reason});return s;}
''' + body)

    def test_hold_is_bounded_cancellable_and_not_an_engine_event(self):
        self.node(r'''
let s=H.tool('S1');a.equal(H.tick(s,1000),s);s={...s,active:true};s=H.tick(s,1e9);a(s.turns<=.125);a(!s.complete);s={...s,active:false};a.equal(H.tick(s,1000),s);for(let i=0;i<8;i++)s=H.turn(s,.25);a(s.complete);a.equal(s.turns,2);a.equal(H.turn(s,.25),s);
''')

    def test_original_stays_visible_until_the_player_removes_it(self):
        self.node(r'''
const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(process.argv[1]+'/repair_shop_scene.js','utf8');
const body=source.match(/function updateService\(s\)\{([\s\S]*?)\n  \}/)[1];
const nodes={F1:{group:{visible:true}},C1:{group:{visible:true}}},oldParts={F1:{visible:false},C1:{visible:false}},ctx={nodes,oldParts,serviceSignature:'',serviceState:null};
vm.runInNewContext('globalThis.update=s=>{'+body+'};',ctx);
ctx.update({id:'F1',index:0,installed:false});a(nodes.F1.group.visible,'Starting repair must not silently remove the original');a(!oldParts.F1.visible);a(nodes.C1.group.visible);
ctx.update({id:'F1',index:3,installed:false});a(!nodes.F1.group.visible);a(oldParts.F1.visible);
ctx.update({id:'F1',index:5,installed:true});a(nodes.F1.group.visible);a(oldParts.F1.visible);
''')

    def test_service_requires_all_steps_safe_power_and_single_charge(self):
        self.node(r'''
let s=ready(),j=E.offer(s.active.seed),c=j.candidates.find(c=>!E.compatible(j.product.parts.find(p=>p.id===j.fault.component),c)),coins=s.coins;
s=go(s,{type:'beginRepair',stockId:c.stockId,orientation:'correct'});a.equal(s.coins,coins);a(!s.active.installed);a(!E.apply(s,{type:'power'}).ok);a(!E.apply(s,{type:'repairStep',op:'place'}).ok);a(!E.apply(s,{type:'install',stockId:c.stockId,orientation:'correct'}).ok);
for(const step of H.STEPS){s=go(s,{type:'repairStep',op:step.op});a.equal(s.coins,coins);a(!s.active.installed);}
s=go(s,{type:'install',stockId:c.stockId,orientation:'correct'});a.equal(s.coins,coins-c.price);a(!E.apply(s,{type:'install',stockId:c.stockId,orientation:'correct'}).ok);a.deepEqual(E.restore(JSON.parse(JSON.stringify(s))),s);
''')

    def test_legacy_install_replay_still_works_and_abandon_does_not_refund_unpaid_stock(self):
        self.node(r'''
let s=ready(),j=E.offer(s.active.seed),c=j.candidates.find(c=>c.kind==='original')||j.candidates.find(c=>!E.compatible(j.product.parts.find(p=>p.id===j.fault.component),c)),coins=s.coins;
const pending=go(s,{type:'beginRepair',stockId:c.stockId,orientation:'correct'});a.equal(go(pending,{type:'abandon'}).coins,coins);
s=go(s,{type:'install',stockId:c.stockId,orientation:'correct'});a(s.active.installed);a.deepEqual(E.restore(JSON.parse(JSON.stringify(s))),s);
''')

    def test_waveform_periodic_extremes_match_existing_solver(self):
        self.node(r'''
for(const id of ['speaker','router']){const p=D.products.find(p=>p.id===id);for(const f of [null,...p.faults.filter(f=>f.enabled)]){const t=W.capture(p,f,null,{mode:'ripple',load:'specified'}),r=P.solve(p,f);a(t.points.every(p=>Number.isFinite(p.v)));a(Math.abs(t.min-r.metrics.min)<.001);a(Math.abs(t.max-r.metrics.max)<.001);a(Math.abs((t.max-t.min)-r.metrics.ripple)<.001);}}
''')

    def test_rlc_transition_matches_independent_runge_kutta(self):
        self.node(r'''
const q={vs:3.3,rs:1.5,esr:.08,c:470e-6,l:10e-6},initial=[.02,3.27],load=.3,time=.0001;
const f=x=>[(q.vs-(q.rs+q.esr)*x[0]-x[1]+q.esr*load)/q.l,(x[0]-load)/q.c],add=(x,k,d)=>x.map((v,i)=>v+k[i]*d);let x=[...initial];const n=10000,dt=time/n;
for(let i=0;i<n;i++){const k1=f(x),k2=f(add(x,k1,dt/2)),k3=f(add(x,k2,dt/2)),k4=f(add(x,k3,dt));x=x.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);}
const exact=W.propagate(q,initial,load,time);a(exact.every((v,i)=>Math.abs(v-x[i])<1e-9));
''')

    def test_startup_is_explicit_no_load_experiment_and_steady_devices_do_not_get_fake_dynamics(self):
        self.node(r'''
for(const p of D.products){if(W.dynamic(p)){const t=W.capture(p,null,null,{mode:'startup',load:'specified'});a(t.conditions.some(s=>s.includes('无负载')));a(t.points[t.points.length-1].v>t.points[0].v);a(t.limits.includes('不是实物采样'));}else{const t=W.capture(p,null,null,{mode:'steady',load:'specified'});a.equal(t.min,t.max);a(t.limits.includes('没有启动'));a.throws(()=>W.capture(p,null,null,{mode:'startup',load:'specified'}));}}
''')

    def test_capture_load_does_not_mutate_job_and_half_assembled_measurements_are_blocked(self):
        self.node(r'''
const p=D.products.find(p=>p.id==='speaker'),before=JSON.stringify(p),x=W.capture(p,null,null,{mode:'ripple',load:'light'}),y=W.capture(p,null,null,{mode:'ripple',load:'specified'});a(x.max-x.min<y.max-y.min);a.equal(JSON.stringify(p),before);
let s=ready(),j=E.offer(s.active.seed),c=j.candidates.find(c=>!E.compatible(j.product.parts.find(p=>p.id===j.fault.component),c));s=go(s,{type:'beginRepair',stockId:c.stockId,orientation:'correct'});a(!E.apply(s,{type:'measure',id:j.fault.component,mode:'component'}).ok);
''')

    def test_ui_bundle_contains_real_controls_and_reversible_host_fullscreen(self):
        page=build_training_html()
        for text in ['全屏维修','松手暂停','转1/4圈','模型示波器','本次换件操作记录','客户反馈','核对备件并开始维修']:
            self.assertIn(text,page)
        script=(WEB_ROOT/'training_embed.js').read_text(encoding='utf-8')
        self.assertIn('undo.reverse()',script)
        self.assertIn('setImmersive',script)
        self.assertNotIn('window.top',script)
        waves=(WEB_ROOT/'repair_shop_waveforms.js').read_text(encoding='utf-8')
        self.assertNotIn('Math.random',waves)
        self.assertNotIn('document.',waves)

    def test_all_seventeen_jobs_allow_staged_repair_assembly_and_one_payment(self):
        self.node(r'''
const V=require(process.argv[1]+'/repair_shop_evidence.js'),seen=new Set();
for(let seed=1;seed<1000&&seen.size<17;seed++){
 const j=E.offer(seed),key=j.product.id+'/'+j.fault.component+'/'+j.fault.reason;if(!j.fault.enabled||seen.has(key))continue;seen.add(key);
 let s=ready(seed),part=j.product.parts.find(p=>p.id===j.fault.component),c=j.candidates.find(c=>!E.compatible(part,c)),orientation=part.polar?'correct':'none';
 if(part.polar){const bad=E.apply(s,{type:'beginRepair',stockId:c.stockId,orientation:'reverse'});a(!bad.ok&&!bad.state.active.rework);a.equal(bad.state.coins,s.coins);}
 s=go(s,{type:'beginRepair',stockId:c.stockId,orientation});for(const step of H.STEPS)s=go(s,{type:'repairStep',op:step.op});s=go(s,{type:'install',stockId:c.stockId,orientation});s=go(s,{type:'power'});s=go(s,{type:'test'});a(V.report(j,s.active).service.every(s=>s.done));a(!V.report(j,s.active).customer.delivered);
 s=go(s,{type:'power'});s=go(s,{type:'discharge'});for(let n=0;n<12&&!Mechanics.assembled(s.active.mechanics);n++){const step=Mechanics.next(s.active.mechanics,s.active.tested);s=go(s,{type:'mechanical',op:step.op,id:step.id,tool:'phillips'});}
 s=go(s,{type:'power'});s=go(s,{type:'testAssembly'});s=go(s,{type:'deliver'});a(V.report(j,s.active).customer.delivered);a.equal(s.coins,150-c.price+j.fee);a.equal(s.completed,1);a(!E.apply(s,{type:'deliver'}).ok);a.deepEqual(E.restore(JSON.parse(JSON.stringify(s))),s);
}a.equal(seen.size,17);
''')

    def test_immersive_embedding_freezes_autoheight_and_restores_only_own_styles(self):
        self.node(r'''
const fs=require('node:fs'),vm=require('node:vm');const style=()=>({setProperty(k,v){this[k]=v;},getPropertyValue(k){return this[k]||'';},getPropertyPriority(){return '';},removeProperty(k){delete this[k];}});
const app={height:4200,style:style(),getBoundingClientRect(){return {height:this.height};}},container={style:style()},body={style:style()},owner={innerHeight:390,visualViewport:{height:390},addEventListener(){}};body.style.overflow='auto';
const frame={dataset:{},style:style(),ownerDocument:{defaultView:owner,body},setAttribute(){},closest(){return container;}},w={frameElement:frame,innerHeight:4200,addEventListener(){}},document={getElementById(){return app;},documentElement:{dataset:{},style:style()},body:{style:style()},addEventListener(){}};
vm.runInNewContext(fs.readFileSync(process.argv[1]+'/training_embed.js','utf8'),{window:w,document,requestAnimationFrame(){},ResizeObserver:class{observe(){}}});
w.TrainingEmbedLayout.setImmersive(true);a.equal(container.style.position,'fixed');a.equal(frame.style.height,'390px');a.equal(body.style.overflow,'hidden');app.height=9000;w.TrainingEmbedLayout.flush();a.equal(frame.style.height,'390px');
w.TrainingEmbedLayout.setImmersive(false);a(!container.style.position);a.equal(container.style.height,'auto');a.equal(body.style.overflow,'auto');a.equal(frame.style.height,'9012px');
''')


if __name__=='__main__':
    unittest.main()
