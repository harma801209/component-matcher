"""Independent laws/numerical references for the declared teaching circuits."""
import unittest

import tests.test_repair_shop as repair_tests


class RepairShopPhysicsTests(unittest.TestCase):
    def node(self, body):
        return repair_tests.RepairShopTests().run_node(
            "const P=require(process.argv[1]+'/repair_shop_physics.js');"
            "const near=(x,y,e=1e-9)=>a(Math.abs(x-y)<e,`${x} != ${y}`);\n" + body
        )

    def test_led_kvl_power_nonlinearity_and_calibration(self):
        self.node(r'''
near(P.diodeVoltage(.02),2);near(P.diodeVoltage(.001,false),.28);a(D.healthy(D.products[1].parts[2]).includes('0.28 V'));const p=D.products[0],good=P.solve(p),dim=P.solve(p,p.faults[1]);
for(const [z,r] of [[good,220],[dim,2200]]){const i=z.metrics.i,v=z.metrics.vd;near(5,i*(r+.2)+v);near(5*i,i*i*(r+.2)+i*v);a(z.metrics.resistorPower>0);}
a(good.metrics.i>.013&&good.metrics.i<.014);a(dim.metrics.i>.0014&&dim.metrics.i<.0015);
a(dim.metrics.vd<good.metrics.vd);a(Math.abs(good.metrics.i/dim.metrics.i-10)>.1);
near(P.solve(p,p.faults[0]).volts[2],0);near(P.solve(p,p.faults[2]).volts[2],5);
''')

    def test_motor_kvl_kcl_torque_and_energy_in_cv_cc_and_open_modes(self):
        self.node(r'''
const p=D.products.find(p=>p.id==='fan');for(const f of [null,...p.faults]){const z=P.solve(p,f),m=z.metrics;
near(m.pin,m.loss,1e-9);near(m.vm,m.motorCurrent*10+.05*m.omega);near(.05*m.motorCurrent,.00005*m.omega);
near(m.va,m.vb+m.vm);if(f?.reason==='short'){near(m.current,.15);a(m.limited);near(m.current,m.motorCurrent+m.vm/.05);a(m.supply<.1);}else if(!f){near(m.current,m.motorCurrent);a(!m.limited);a(m.rpm>790&&m.rpm<800);}}
''')

    def test_rc_closed_form_against_independent_time_domain_rk4(self):
        self.node(r'''
// Independent KCL form and fourth-order time stepping, not the analytic recurrence.
function reference(q){let vc=q.vs,samples=[],area=0,energy=0;const v=(x,i)=>(q.vs/q.rs+x/q.esr-i)/(1/q.rs+1/q.esr);
const deriv=(x,i)=>(v(x,i)-x)/(q.esr*q.c);
for(let cycle=0;cycle<300;cycle++){
 if(cycle===299){samples=[v(vc,q.low),v(vc,q.high)];area=0;energy=0;}
 for(const [i,d] of [[q.high,q.duty],[q.low,1-q.duty]]){const dt=d/q.frequency/100;
  for(let k=0;k<100;k++){const before=v(vc,i),k1=deriv(vc,i),k2=deriv(vc+dt*k1/2,i),k3=deriv(vc+dt*k2/2,i),k4=deriv(vc+dt*k3,i);vc+=dt*(k1+2*k2+2*k3+k4)/6;
   if(cycle===299){area+=dt*(before+v(vc,i))/2;energy+=dt*i*(before+v(vc,i))/2;}}
  if(cycle===299&&i===q.high)samples.push(v(vc,q.high),v(vc,q.low));
 }}return {samples,mean:area*q.frequency,power:energy*q.frequency};}
for(const q of [
 {vs:5,rs:4,c:470e-6,esr:.3,low:.02,high:.1,frequency:1000,duty:.5},
 {vs:5,rs:4,c:460e-6,esr:6.8,low:.02,high:.1,frequency:1000,duty:.5},
 {vs:3.3,rs:1.5,c:220e-6,esr:.2,low:.02,high:.3,frequency:2000,duty:.1},
 {vs:3.3,rs:1.5,c:210e-6,esr:4.2,low:.02,high:.3,frequency:2000,duty:.1}]){
 const z=P.pulse(q),n=reference(q);for(let i=0;i<4;i++)near(z.samples[i],n.samples[i],1e-8);
 near(z.mean,n.mean,1e-6);near(z.loadPower,n.power,1e-6);
 near((q.vs-z.mean)/q.rs,q.high*q.duty+q.low*(1-q.duty),1e-10);
 near(z.samples[0]-z.samples[1],(q.high-q.low)*q.rs*q.esr/(q.rs+q.esr),1e-10);
}
''')

    def test_rlc_states_and_energy_against_independent_rk4(self):
        self.node(r'''
for(const [c,esr] of [[220e-6,.2],[210e-6,4.2]]){
 const q={vs:3.3,rs:1.5,l:10e-6,c,esr,low:.02,high:.3,frequency:2000,duty:.1},z=P.rlcPulse(q);
 let x=[0,3.3],samples=[],sumI=0,power=0,loss=0;
 const v=(x,i)=>x[1]+esr*(x[0]-i),f=(x,i)=>[(3.3-1.5*x[0]-v(x,i))/q.l,(x[0]-i)/c],step=(x,k,t)=>[x[0]+k[0]*t,x[1]+k[1]*t];
 for(let cycle=0;cycle<150;cycle++){
  if(cycle===149){near(x[0],z.x0[0],1e-8);near(x[1],z.x0[1],1e-8);samples=[v(x,.02),v(x,.3)];}
  for(const [i,n] of [[.3,200],[.02,1800]]){const dt=.0005/2000;
   for(let k=0;k<n;k++){const before=[...x],k1=f(x,i),x2=step(x,k1,dt/2),k2=f(x2,i),x3=step(x,k2,dt/2),k3=f(x3,i),x4=step(x,k3,dt),k4=f(x4,i);x=[x[0]+dt*(k1[0]+2*k2[0]+2*k3[0]+k4[0])/6,x[1]+dt*(k1[1]+2*k2[1]+2*k3[1]+k4[1])/6];
    if(cycle===149){samples.push(v(x,i));const integrate=g=>dt*(g(before)+2*g(x2)+2*g(x3)+g(x4))/6;sumI+=integrate(y=>y[0]);power+=integrate(y=>i*v(y,i));
     loss+=integrate(y=>1.5*y[0]*y[0]+esr*(y[0]-i)**2);}}
   if(cycle===149&&i===.3){near(x[0],z.x1[0],1e-8);near(x[1],z.x1[1],1e-8);samples.push(v(x,.02));}
  }
 }
 near(sumI*2000,.048,2e-7);near(power*2000,z.loadPower,1e-6);near(3.3*sumI*2000,(power+loss)*2000,1e-6);
 near(Math.min(...samples),z.min,1e-6);near(Math.max(...samples),z.max,1e-6);
 // At a current-sink step only the ESR terminal drop jumps; iL and vC
 // remain the same. Unlike an RC approximation the jump is ESR*deltaI.
 near(z.samples[0]-z.samples[1],esr*(.3-.02),1e-10);a(z.samples.length>4);
}a.throws(()=>P.rlcPulse({vs:3.3,rs:.001,l:.1,c:.000001,esr:0,low:0,high:.1,frequency:100,duty:.5}),RangeError);
''')

    def test_amplifier_feedback_gain_bias_and_headroom(self):
        self.node(r'''
const p=D.products.find(p=>p.id==='speaker'),good=P.solve(p),bad=P.solve(p,p.faults[1]);
near(good.metrics.gain,10);near(bad.metrics.gain,1.9);near(good.metrics.outputRms,1);near(bad.metrics.outputRms,.19);near(good.volts[2],good.metrics.mean/2);
a(good.pass);a(!bad.pass);a(!P.solve(p,p.faults[0]).pass);a(good.metrics.ripple<.08);a(P.solve(p,p.faults[0]).metrics.ripple>.2);
''')

    def test_floating_inputs_are_null_not_fabricated_low_levels(self):
        self.node(r'''
for(const id of ['clock','sensor']){const p=D.products.find(p=>p.id===id),f=p.faults.find(f=>f.component==='R1'),z=P.solve(p,f);a.equal(z.metrics[id==='clock'?'reset':'bus'],null);a(z.volts.includes(null));a(!z.pass);a(P.voltage(null).includes('浮空'));
const seed=Array.from({length:200},(_,i)=>i).find(i=>{const j=E.offer(i);return j.product.id===id&&j.fault===f;});let s=act(E.create(),'accept',{seed}).state;s=act(s,'power').state;
const r=E.measurement(s.active,'voltage','R1');a(r.value.includes('浮空'));a(!r.proof);}
''')

    def test_current_limited_short_readings_and_ldo_power_conserve_energy(self):
        self.node(r'''
const c=D.products.find(p=>p.id==='clock'),z=P.solve(c,c.faults[2]);near(z.metrics.current,.05);near(z.metrics.supply,.05/(1/1000+1/.4));a(z.metrics.limited);
const p=D.products.find(p=>p.id==='sensor');for(const f of [null,...p.faults]){const z=P.solve(p,f),m=z.metrics;near(5*m.current,m.ldoPower+m.supply*m.current);a(m.current<=.1);}
const short=P.solve(p,p.faults[1]);near(short.metrics.current,.1);near(short.metrics.supply,.1/(1/100+1/.3));a(short.metrics.ldoPower>.49);
const good=P.solve(p);near(good.metrics.supply,3.3*100/101);a(good.pass);
''')

    def test_all_supported_faults_fail_before_and_pass_only_with_repaired_parameters(self):
        self.node(r'''
let count=0;for(const p of D.products){a(P.solve(p).pass,p.id);for(const f of p.faults){if(!f.enabled)continue;count++;a(!P.solve(p,f).pass,p.id+':'+f.reason);const req=p.parts.find(p=>p.id===f.component);a(P.isolated(req,P.parameters(p,f)[f.component]).proof);
for(const candidate of D.candidates(req,9).filter(c=>!E.compatible(req,c))){const z=P.verify(p,f,candidate);a(z.pass,p.id+f.reason);a(z.checks.every(c=>c.pass));}}
}a.equal(count,17);
''')

    def test_acceptance_can_fail_after_installation_and_report_cannot_invent_pass(self):
        self.node(r'''
const {s,j,c}=solve(31),V=require(process.argv[1]+'/repair_shop_evidence.js'),req=j.product.parts.find(p=>p.id===j.fault.component);
a(!P.verify(j.product,j.fault,{...c,value:2200}).pass);a(!P.verify(j.product,j.fault,{...c,power:.001}).pass);
const sensor=D.products.find(p=>p.id==='sensor'),f=sensor.faults[1],cap=sensor.parts[1];a(!P.verify(sensor,f,{...cap,voltage:2.5}).pass);
// Inject a failed model evaluation (not completion flags). The state machine
// must independently reject the test and never permit delivery or a report.
const physicsPath=require.resolve(process.argv[1]+'/repair_shop_physics.js'),enginePath=require.resolve(process.argv[1]+'/repair_shop_engine.js');
const saved=require.cache[physicsPath].exports;require.cache[physicsPath].exports={...saved,verify:()=>({pass:false,checks:[{pass:false,label:'测试负载不合格',actual:'超限'}]})};delete require.cache[enginePath];const failing=require(enginePath);
const pending=JSON.parse(JSON.stringify(s));pending.active.tested=false;const result=failing.apply(pending,{type:'test'});a(!result.ok);a(!result.state.active.tested);a(!failing.apply(result.state,{type:'deliver'}).ok);a.equal(V.report(j,result.state.active),null);
''')

    def test_paused_crystal_jobs_excluded_and_old_progress_refunded_once(self):
        self.node(r'''
const seed=34,j=E.offer(seed);a.equal(j.product.id,'clock');a(!j.fault.enabled);a(!act(E.create(),'accept',{seed}).ok);
for(let i=0;i<100;i++){const seeds=E.nextSeeds(i);a.equal(seeds.length,3);a.equal(new Set(seeds).size,3);a(seeds.every(s=>E.offer(s).fault.enabled));}
const c=j.candidates.find(c=>!E.compatible(j.product.parts[0],c)),old={...E.create(),coins:150-c.price,points:200,completed:2,active:{seed,installed:c.stockId,events:[{type:'install',stockId:c.stockId,orientation:'correct'}]}};
let s=E.restore(old);a(s.active.paused);a.equal(s.coins,old.coins);s=E.restore(s);a.equal(s.coins,old.coins);
const returned=act(s,'abandon').state;a.equal(returned.coins,150);a.equal(returned.points,200);a.equal(returned.completed,2);a.equal(E.restore(returned).coins,150);a(!act(returned,'abandon').ok);
const history={...old,history:[{id:j.id,product:j.product.name,component:'X1',points:100,fee:j.fee}]};const paid=E.restore(history);a.equal(paid.coins,old.coins);a.equal(paid.points,200);a.equal(paid.active,null);a.equal(paid.history.length,1);
''')

    def test_fresh_bundle_labels_calculation_limits_and_no_fixture_voltages(self):
        from product_training import WEB_ROOT, build_training_html
        page = build_training_html()
        self.assertLess(page.index('root.RepairShopPhysics=api'), page.index('root.RepairShopData=api'))
        for text in ['验收计算值', '未建模范围', '17种已建模故障', '非接线图', '浮空']:
            self.assertIn(text, page)
        data = (WEB_ROOT / 'repair_shop_data.js').read_text(encoding='utf-8')
        self.assertNotIn('normal:[', data)
        self.assertNotIn('pass:true', (WEB_ROOT / 'repair_shop_evidence.js').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
