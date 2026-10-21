"""Teaching must explain a valid next action without silently doing the repair."""
import unittest

import tests.test_repair_shop as repair_tests
from product_training import WEB_ROOT, build_training_html


class RepairShopCoachTests(unittest.TestCase):
    def node(self, body):
        return repair_tests.RepairShopTests().run_node("const C=require(process.argv[1]+'/repair_shop_coach.js');\n" + body)

    def test_guidance_can_complete_all_eighteen_faults_without_skipping_safety(self):
        self.node(r'''
const seen=new Set();for(let seed=1;seed<400;seed++){
 const j=E.offer(seed),key=j.product.id+':'+j.fault.component+':'+j.fault.reason;if(seen.has(key))continue;seen.add(key);
 let s=act(E.create(),'accept',{seed}).state,c={selected:null,mode:'voltage',diagnosis:'',reason:'',stock:'',orientation:''},count=0;
 while(!s.active.delivered&&count++<80){
  const before=JSON.stringify(s),beforeC=JSON.stringify(c),g=C.step(j,s.active,c);a.equal(JSON.stringify(s),before);a.equal(JSON.stringify(c),beforeC);a(g.title&&g.body&&g.target&&g.group);
  if(g.id.startsWith('target-')){c.selected=g.id.slice(7);c.diagnosis=c.selected;}
  else if(['power-on','power-off'].includes(g.id))s=act(s,'power').state;
  else if(g.id==='voltage-mode')c.mode='voltage';else if(g.id==='scope-mode')c.mode='scope';else if(g.id==='component-mode')c.mode='component';
  else if(['voltage-read','scope-read','component-read'].includes(g.id)){const r=act(s,'measure',{id:c.selected,mode:c.mode});a(r.ok,r.message);s=r.state;}
  else if(g.id==='discharge')s=act(s,'discharge').state;
  else if(g.id==='diagnosis-id')c.diagnosis=s.active.measurements.find(m=>m.proof).id;
  else if(g.id==='diagnosis-reason')c.reason=j.fault.reason;
  else if(g.id==='diagnosis-submit'){const r=act(s,'diagnose',{id:c.diagnosis,reason:c.reason});a(r.ok,r.message);s=r.state;}
  else if(g.id==='stock'){const p=j.product.parts.find(p=>p.id===j.fault.component);c.stock=j.candidates.find(p2=>!E.compatible(p,p2)).stockId;}
  else if(g.id==='orientation')c.orientation='correct';
  else if(g.id==='install'){const r=act(s,'install',{stockId:c.stock,orientation:c.orientation});a(r.ok,r.message);s=r.state;}
  else if(g.id==='test'){const r=act(s,'test');a(r.ok,r.message);s=r.state;}
  else if(g.id==='deliver')s=act(s,'deliver').state;
  else a.fail('Unexpected guide step '+g.id);
 }
 a(s.active.delivered,j.product.id);a(count<80);a.equal(s.completed,1);a.equal(s.points,100);a.equal(C.step(j,s.active,c).id,'complete');
}
a.equal(seen.size,18);
''')

    def test_coach_recovers_after_reload_or_out_of_order_manual_actions(self):
        self.node(r'''
const seed=32,j=E.offer(seed);let s=evidence(act(E.create(),'accept',{seed}).state,j);s=E.restore(JSON.parse(JSON.stringify(s)));
const g=C.step(j,s.active,{selected:null,mode:'voltage',diagnosis:'',reason:''});a.equal(g.id,'diagnosis-id');a(g.body.includes(j.fault.bad));
s=act(s,'power').state;a.equal(C.step(j,s.active,{}).id,'power-off');
const fresh=act(E.create(),'accept',{seed}).state;a(C.step(j,fresh.active,{}).id.startsWith('target-'));a(!fresh.active.diagnosed);a.equal(fresh.active.measurements.length,0);
''')

    def test_each_case_has_suspects_reason_measurement_and_repair_explanations(self):
        self.node(r'''
for(let seed=0;seed<90;seed++){
 const j=E.offer(seed),s=act(E.create(),'accept',{seed}).state,before=JSON.stringify(s),overview=C.overview(j,s.active),detail=C.detail(j,s.active);
 a.deepEqual(overview.map(x=>x.title),['可能坏在哪里','为什么这样怀疑','如何检测出来','如何维修和验收']);a.equal(detail.length,4);
 for(const item of [...overview,...detail])a(item.title&&item.text.length>15);
 a(overview[1].text.includes(j.fault.symptom));a(overview[0].text.includes('候选'));a(detail[0].text.includes('仍需亲自测量'));a(detail[1].text.includes(j.fault.why));a(detail[2].text.includes(j.fault.bad));a(detail[3].text.includes(j.product.behavior));a.equal(JSON.stringify(s),before);
}
''')

    def test_wrong_part_and_polarity_get_actionable_guidance_without_auto_buy(self):
        self.node(r'''
const seed=23,j=E.offer(seed);let s=evidence(act(E.create(),'accept',{seed}).state,j);s=act(s,'diagnose',{id:j.fault.component,reason:j.fault.reason}).state;const before=JSON.stringify(s);
let g=C.step(j,s.active,{stock:'part-0',partError:'额定耐压不足'});a.equal(g.id,'stock-mismatch');a(g.body.includes('额定耐压不足'));a.equal(JSON.stringify(s),before);
for(let x=0;x<50;x++){const j2=E.offer(x),p=j2.product.parts.find(p=>p.id===j2.fault.component);if(!p.polar)continue;let s2=evidence(act(E.create(),'accept',{seed:x}).state,j2);s2=act(s2,'diagnose',{id:p.id,reason:j2.fault.reason}).state;a.equal(C.step(j2,s2.active,{stock:'part-0',orientation:'reverse'}).id,'orientation');}
''')

    def test_help_is_free_but_evidence_and_verification_are_still_required(self):
        self.node(r'''
let s=act(E.create(),'accept',{seed:31}).state;let r=act(s,'hint');a(r.ok);a.equal(r.state.coins,s.coins);a.equal(r.state.points,0);a(!r.state.active.diagnosed);a(r.message.includes('不扣积分'));
const j=E.offer(31);a(!act(r.state,'diagnose',{id:j.fault.component,reason:j.fault.reason}).ok);a(!act(r.state,'deliver').ok);
const solved=solve(31).s;const done=act(act(solved,'hint').state,'deliver').state;a.equal(done.points,100);
''')

    def test_teaching_is_bundled_and_keeps_browser_actions_in_the_ui(self):
        source=(WEB_ROOT/'repair_shop_coach.js').read_text(encoding='utf-8')
        for forbidden in ['localStorage','sessionStorage','document.','fetch(', 'setTimeout(', 'sqlite']:
            self.assertNotIn(forbidden, source)
        page=build_training_html()
        self.assertLess(page.index('root.RepairShopCoach=api'),page.index('window.RepairShop=Object.freeze'))
        for label in ['带我找到这一步','师傅提示','新手教学','操作教学不扣积分','回到维修操作']:
            self.assertIn(label,page)


if __name__=='__main__':
    unittest.main()
