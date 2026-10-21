"""Observed evidence, not hidden case answers, drives repair feedback."""
import unittest

from product_training import WEB_ROOT, build_training_html
import tests.test_repair_shop as repair_tests


class RepairShopEvidenceTests(unittest.TestCase):
    def node(self, source):
        return repair_tests.RepairShopTests().run_node("const V=require(process.argv[1]+'/repair_shop_evidence.js');\n" + source)

    def test_unmeasured_parts_do_not_reveal_faults(self):
        self.node(r'''
for(let seed=0;seed<90;seed++){if(!E.offer(seed).fault.enabled)continue;
 const j=E.offer(seed),s=act(E.create(),'accept',{seed}).state,before=JSON.stringify(s);
 for(const p of j.product.parts){const status=V.part(j,s.active,p.id);a.equal(status.tone,'unknown');a.equal(status.label,'尚未检测');}
 a.equal(V.report(j,s.active),null);a.equal(JSON.stringify(s),before);
 const fake=JSON.parse(JSON.stringify(s.active));fake.tested=true;a.equal(V.report(j,fake),null);
}
''')

    def test_voltage_and_visual_clues_never_prove_component_failure(self):
        self.node(r'''
for(let seed=0;seed<70;seed++){if(!E.offer(seed).fault.enabled)continue;
 const j=E.offer(seed);let s=act(E.create(),'accept',{seed}).state;s=open(s);s=act(s,'power').state;
 for(const p of j.product.parts){s=act(s,'measure',{id:p.id,mode:'voltage'}).state;const r=s.active.measurements.at(-1),f=V.describe(r);a(!f.proof);a(['reference','clue'].includes(f.tone));a(!['abnormal','repaired'].includes(V.part(j,s.active,p.id).tone));}
 s=act(s,'measure',{id:j.fault.component,mode:'visual'}).state;a.equal(V.describe(s.active.measurements.at(-1)).tone,'neutral');
 a(!V.checklist(s.active,j.fault.component)[1].done);
}
''')

    def test_isolated_evidence_marks_only_measured_parts_and_survives_restore(self):
        self.node(r'''
for(let seed=1;seed<90;seed++){if(!E.offer(seed).fault.enabled)continue;
 const j=E.offer(seed);let s=act(E.create(),'accept',{seed}).state;s=open(s);
 const healthy=j.product.parts.find(p=>p.id!==j.fault.component&&p.type!=='crystal');s=act(s,'measure',{id:healthy.id,mode:'component'}).state;
 a.equal(V.part(j,s.active,healthy.id).tone,'reference');a.equal(V.part(j,s.active,j.fault.component).tone,'unknown');
 s=act(s,'measure',{id:j.fault.component,mode:'component'}).state;a.equal(V.part(j,s.active,j.fault.component).tone,'abnormal');
 const copy=E.restore(JSON.parse(JSON.stringify(s)));a.deepEqual(V.part(j,copy.active,j.fault.component),V.part(j,s.active,j.fault.component));
 a(!V.checklist(s.active,j.fault.component)[0].done);a(V.checklist(s.active,j.fault.component)[1].done);a(!V.checklist(s.active,j.fault.component)[2].done);
}
''')

    def test_report_requires_repair_and_test_and_does_not_fabricate_prior_measurements(self):
        self.node(r'''
const seen=new Set();for(let seed=1;seed<400;seed++){if(!E.offer(seed).fault.enabled)continue;
 const j=E.offer(seed),key=j.product.id+':'+j.fault.component+':'+j.fault.reason;if(seen.has(key))continue;seen.add(key);
 const solved=solve(seed),s=solved.s,before=JSON.stringify(s),report=V.report(j,s.active);
 a(report);a.equal(report.rows.length,5);a(report.rows.every(r=>r.pass));a.equal(report.cost,solved.c.price);a.equal(report.net,j.fee-solved.c.price);
 const component=report.rows.find(r=>r.kind==='component');a.equal(component.before,j.fault.bad);a.equal(component.after,D.healthy(j.product.parts.find(p=>p.id===j.fault.component)));
 for(const r of report.rows.filter(r=>r.kind==='voltage'))a.equal(r.before,null,'Never invent unmeasured voltage history');
 const untested={...s.active,tested:false};a.equal(V.report(j,untested),null);a.equal(JSON.stringify(s),before);
 const pending={...s.active,tested:false};a.equal(V.part(j,pending,j.fault.component).tone,'pending');
 a.equal(V.part(j,s.active,j.fault.component).tone,'repaired');
 const copy=E.restore(JSON.parse(JSON.stringify(s)));a.deepEqual(V.report(j,copy.active),report);
 const paid=act(s,'deliver').state;a.deepEqual(V.report(j,paid.active),report);a.equal(paid.coins,150-solved.c.price+j.fee);
}
a.equal(seen.size,17);
''')

    def test_real_before_and_manual_after_records_remain_distinct(self):
        self.node(r'''
const seed=17,j=E.offer(seed),p=j.product.parts[0];let s=act(E.create(),'accept',{seed}).state;
s=open(s);s=act(s,'power').state;s=act(s,'measure',{id:p.id,mode:'voltage'}).state;const before=s.active.measurements[0].value;
s=act(s,'power').state;s=evidence(s,j);s=act(s,'diagnose',{id:j.fault.component,reason:j.fault.reason}).state;
const req=j.product.parts.find(p=>p.id===j.fault.component),c=j.candidates.find(c=>!E.compatible(req,c));s=act(s,'install',{stockId:c.stockId,orientation:'correct'}).state;
s=act(s,'power').state;s=act(s,'measure',{id:p.id,mode:'voltage'}).state;s=act(s,'test').state;
const row=V.report(j,s.active).rows.find(r=>r.kind==='voltage'&&r.id===p.id);a.equal(row.before,before);a.equal(row.after,j.product.normal[0].toFixed(2)+' V');
a(s.active.measurements.some(m=>m.key==='voltage:'+p.id+':false'));a(s.active.measurements.some(m=>m.key==='voltage:'+p.id+':true'));
''')

    def test_bundle_and_ui_do_not_select_diagnosis_when_measuring(self):
        page = build_training_html()
        source = (WEB_ROOT / 'repair_shop_evidence.js').read_text(encoding='utf-8')
        for forbidden in ('localStorage', 'document.', 'fetch(', 'sqlite', 'setTimeout(', 'E.apply('):
            self.assertNotIn(forbidden, source)
        self.assertLess(page.index('root.RepairShopEvidence=api'), page.index('window.RepairShop=Object.freeze'))
        ui = (WEB_ROOT / 'repair_shop_ui.js').read_text(encoding='utf-8')
        self.assertNotIn('diagnosis=part.id', ui)
        self.assertNotIn('diagnosis=p.id', ui)
        for text in ('维修前后对照', '尚未检测', '验收计算值', '未记录', '测量目标不等于故障答案'):
            self.assertIn(text, page)


if __name__ == '__main__':
    unittest.main()
