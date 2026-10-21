"""Repair-shop teaching loop, compatibility, replay and financial isolation."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from product_training import WEB_ROOT, build_training_html


class RepairShopTests(unittest.TestCase):
    def run_node(self, body):
        node = shutil.which('node') or 'D:/New Folder/node.exe'
        if not Path(node).exists():
            self.skipTest('Node is unavailable')
        prefix = r'''
const a=require('node:assert/strict'),E=require(process.argv[1]+'/repair_shop_engine.js'),D=require(process.argv[1]+'/repair_shop_data.js'),Mechanics=require(process.argv[1]+'/repair_shop_mechanics.js');
const act=(s,type,extra={})=>E.apply(s,{type,...extra});
const open=s=>{if(Mechanics.onTable(s.active.mechanics))return s;if(s.active.power)s=act(s,'power').state;s=act(s,'discharge').state;for(let k=0;k<12&&!Mechanics.onTable(s.active.mechanics);k++){const n=Mechanics.next(s.active.mechanics,s.active.tested),r=act(s,'mechanical',{op:n.op,id:n.id,tool:'phillips'});a(r.ok,r.message);s=r.state;}return s;};
const close=s=>{if(s.active.power)s=act(s,'power').state;s=act(s,'discharge').state;for(let k=0;k<12&&!Mechanics.assembled(s.active.mechanics);k++){const n=Mechanics.next(s.active.mechanics,s.active.tested),r=act(s,'mechanical',{op:n.op,id:n.id,tool:'phillips'});a(r.ok,r.message);s=r.state;}s=act(s,'power').state;const r=act(s,'testAssembly');a(r.ok,r.message);return r.state;};
const atBoardTest=s=>{const copy=JSON.parse(JSON.stringify(s)),end=copy.active.events.findIndex(e=>e.type==='test');a(end>=0);copy.active.events=copy.active.events.slice(0,end+1);return E.restore(copy);};
const evidence=(s,j)=>{s=open(s);if(!s.active.power)s=act(s,'power').state;s=act(s,'measure',{id:j.fault.component,mode:'scope'}).state;s=act(s,'power').state;s=act(s,'discharge').state;return act(s,'measure',{id:j.fault.component,mode:'component'}).state;};
const solve=(seed)=>{let s=act(E.create(),'accept',{seed}).state,j=E.offer(seed);s=evidence(s,j);let r=act(s,'diagnose',{id:j.fault.component,reason:j.fault.reason});a(r.ok);s=r.state;const p=j.product.parts.find(p=>p.id===j.fault.component),c=j.candidates.find(c=>!E.compatible(p,c));r=act(s,'install',{stockId:c.stockId,orientation:'correct'});a(r.ok);s=r.state;s=act(s,'power').state;r=act(s,'test');a(r.ok);return {s:close(r.state),j,c};};
'''
        result = subprocess.run([node, '-e', prefix + body, str(WEB_ROOT)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_all_seventeen_random_faults_have_a_solvable_repair_loop(self):
        self.run_node(r'''
const seen=new Set();
for(let seed=1;seed<400;seed++){if(!E.offer(seed).fault.enabled)continue;
 const j=E.offer(seed),key=j.product.id+':'+j.fault.component+':'+j.fault.reason;if(!j.fault.enabled||seen.has(key))continue;seen.add(key);
 const {s,c}=solve(seed),before=s.coins,r=act(s,'deliver');a(r.ok);a.equal(r.state.coins,150-c.price+j.fee);a.equal(r.state.completed,1);a.equal(r.state.points,100);a.equal(r.state.coins,before+j.fee);a(r.state.active.delivered);
 const copy=E.restore(JSON.parse(JSON.stringify(r.state)));a(copy.active.delivered);a.equal(copy.coins,r.state.coins);a.equal(copy.points,100);a.equal(act(copy,'deliver').state.coins,copy.coins);
 a(!act(copy,'accept',{seed}).ok);a.equal(act(copy,'accept',{seed}).state.completed,1);
}
a.equal(seen.size,17);a.equal(D.products.length,6);
const lamp=D.products.find(p=>p.id==='lamp');a.equal(lamp.parts.find(p=>p.id==='D1').name,'红光LED');a(lamp.normal[2]>1.9&&lamp.normal[2]<2);
''')

    def test_cannot_skip_diagnosis_safety_or_verification(self):
        self.run_node(r'''
const seed=23,j=E.offer(seed);let s=act(E.create(),'accept',{seed}).state;
a.equal(s.active.measurements.length,0);a(!s.active.power);a(!s.active.installed);a(!s.active.diagnosed);
for(const [type,args] of [['measure',{id:j.fault.component,mode:'voltage'}],['measure',{id:j.fault.component,mode:'component'}],['diagnose',{id:j.fault.component,reason:j.fault.reason}],['install',{stockId:j.candidates[0].stockId}],['test',{}],['deliver',{}]])a(!act(s,type,args).ok,type);
s=act(s,'power').state;a(!act(s,'discharge').ok);a(!act(s,'measure',{id:j.fault.component,mode:'component'}).ok);
s=evidence(act(s,'power').state,j);s=act(s,'diagnose',{id:j.fault.component,reason:j.fault.reason}).state;
s=act(s,'power').state;const p=j.product.parts.find(p=>p.id===j.fault.component),c=j.candidates.find(c=>!E.compatible(p,c));a(!act(s,'install',{stockId:c.stockId,orientation:'correct'}).ok);
const {s:test}=solve(seed);a(!act(act(test,'power').state,'test').ok);a.equal(act(test,'deliver').state.completed,1);
''')

    def test_compatible_parts_not_price_decide_suitability(self):
        self.run_node(r'''
const types=new Set();for(const product of D.products)for(const p of product.parts){types.add(p.type);const options=D.candidates(p,44);a.equal(options.length,4);a.equal(options.filter(c=>!E.compatible(p,c)).length,2,p.type);a.equal(new Set(options.map(c=>c.stockId)).size,4);for(const c of options)a(D.spec(c));}
a.equal(types.size,9);
const req=D.products[0].parts[1],candidate=D.candidates(req,1)[0];for(const field of ['voltage','tolerance','power'])a(E.compatible(req,{...candidate,[field]:undefined}));
for(let seed=1;seed<80;seed++){if(!E.offer(seed).fault.enabled)continue;const j=E.offer(seed),p=j.product.parts.find(p=>p.id===j.fault.component);let s=evidence(act(E.create(),'accept',{seed}).state,j);s=act(s,'diagnose',{id:p.id,reason:j.fault.reason}).state;const bad=j.candidates.find(c=>E.compatible(p,c));const r=act(s,'install',{stockId:bad.stockId,orientation:'correct'});a(!r.ok);a.equal(r.state.coins,150);a(!r.state.active.installed);if(p.polar){const c=j.candidates.find(c=>!E.compatible(p,c));const rev=act(s,'install',{stockId:c.stockId,orientation:'reverse'});a(!rev.ok);a.equal(rev.state.coins,150);}}
''')

    def test_fault_and_healthy_readings_are_distinct_and_repaired_readings_restore(self):
        self.run_node(r'''
for(let seed=0;seed<80;seed++){if(!E.offer(seed).fault.enabled)continue;const j=E.offer(seed);let s=act(E.create(),'accept',{seed}).state;s=open(s);for(const p of j.product.parts){const r=E.measurement(s.active,'component',p.id);a.equal(r.proof,p.id===j.fault.component);if(r.proof)a.notEqual(r.value,r.normal);else a.equal(r.value,r.normal);}const fixed=atBoardTest(solve(seed).s);for(const p of j.product.parts){const r=E.measurement(fixed.active,'voltage',p.id);a.equal(r.value,r.normal);}a.equal(E.measurement(fixed.active,'scope',j.fault.component).value,j.product.behavior);}
''')

    def test_save_replays_actions_and_ignores_forged_completion_flags(self):
        self.run_node(r'''
let s=act(E.create(),'accept',{seed:15}).state;s.active.tested=true;s.active.diagnosed=true;s.active.installed='part-0';s.active.delivered=true;const restored=E.restore(s);a(!restored.active.diagnosed);a(!restored.active.installed);a(!restored.active.delivered);a.equal(restored.coins,150);
for(const bad of [null,[],{},NaN,{version:1,coins:-1,points:0,completed:0,revision:0,owned:[]}])a.deepEqual(E.restore(bad),E.create());
const {s:valid}=solve(31);const copy=E.restore(JSON.parse(JSON.stringify(valid)));a(copy.active.tested);a.equal(copy.coins,valid.coins);a.equal(copy.active.measurements.length,valid.active.measurements.length);a(!act(copy,'install',{stockId:copy.active.installed}).ok);
const legacy={...E.create(),history:[{id:'R-OLD',product:'USB阅读台灯',component:'R1',points:100,fee:95}]};a.equal(E.restore(legacy).history[0].product,'USB小夜灯');
const malicious=JSON.parse('{"__proto__":{"polluted":true},"version":1,"coins":150,"points":0,"completed":0,"revision":0,"owned":["__proto__"],"active":{"seed":1,"events":[{"type":"redeem","id":"mint"}]}}');a(!E.restore(malicious).active);a.equal({}.polluted,undefined);
''')

    def test_rewards_reserve_money_and_abandoned_parts_are_returned(self):
        self.run_node(r'''
let s={...E.create(),coins:200,points:200};let r=act(s,'redeem',{id:'mint'});a(r.ok);a.equal(r.state.coins,120);a.equal(r.state.points,200);a.equal(r.state.theme,'mint');a(!act(r.state,'redeem',{id:'mint'}).ok);a(!act(r.state,'redeem',{id:'sign'}).ok);
s=solve(31).s;const returned=act(s,'abandon');a(returned.ok);a.equal(returned.state.coins,150);a.equal(returned.state.completed,0);a(!returned.state.active);
const {s:test}=solve(12);r=act(test,'deliver');const dup=act(r.state,'deliver');a(!dup.ok);a.equal(dup.state.coins,r.state.coins);a.equal(dup.state.points,r.state.points);
''')

    def test_missing_answers_and_unknown_inputs_are_rejected(self):
        self.run_node(r'''
for(const seed of [-1,NaN,Infinity,'12',4294967296])a.throws(()=>E.offer(seed),RangeError);
let s=act(E.create(),'accept',{seed:4}).state;for(const e of [null,[],{type:'__proto__'},{type:'measure',id:'__proto__',mode:'component'},{type:'diagnose',id:'',reason:''}])a(!E.apply(s,e).ok);a(!s.active.diagnosed);
const j=E.offer(4);s=evidence(s,j);s=act(s,'hint').state;s=act(s,'diagnose',{id:j.fault.component,reason:'not-real'}).state;a(!s.active.diagnosed);
''')

    def test_independent_entry_is_bundled_without_business_access(self):
        page = build_training_html()
        self.assertIn('开门营业', page)
        self.assertIn('academy-lessons', page)
        self.assertLess(page.index('root.RepairShopData=api'), page.index('root.RepairShopEngine=api'))
        self.assertLess(page.index('window.RepairShop=Object.freeze'), page.index('frame.dataset.trainingAutoheight'))
        for name in ['repair_shop_data.js', 'repair_shop_engine.js', 'repair_shop_ui.js']:
            source = (WEB_ROOT / name).read_text(encoding='utf-8')
            for forbidden in ['fetch(', 'XMLHttpRequest', 'member_token', 'sqlite', 'eval(']:
                self.assertNotIn(forbidden, source)
            subprocess.run([shutil.which('node') or 'D:/New Folder/node.exe', '--check', str(WEB_ROOT / name)], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
