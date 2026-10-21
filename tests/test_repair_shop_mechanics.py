"""Disassembly/reassembly is persisted game state, never a visibility-only shortcut."""
import unittest
import tests.test_repair_shop as repair_tests


class RepairShopMechanicsTests(unittest.TestCase):
    def node(self, source):
        return repair_tests.RepairShopTests().run_node("const M=require(process.argv[1]+'/repair_shop_mechanics.js');\n"+source)

    def test_pure_order_preserves_all_removed_pieces_and_fasteners(self):
        self.node(r'''
let m=M.create();a.equal(M.next(m,false).op,'unscrew');a(!M.onTable(m));
const original=JSON.stringify(m);a(M.apply(m,{op:'cover-out'}).error);a.equal(JSON.stringify(m),original);
for(const id of M.SCREWS){a(M.apply(m,{op:'unscrew',id,tool:'finger'}).error);const r=M.apply(m,{op:'unscrew',id,tool:'phillips'});a(!r.error);m=r.state;a(M.apply(m,{op:'unscrew',id,tool:'phillips'}).error);}
for(const op of ['cover-out','brace-out','unplug','board-out']){a.equal(M.next(m,false).op,op);m=M.apply(m,{op}).state;}
a(M.onTable(m));a.equal(m.loose.length,4);a(m.cover&&m.brace&&m.unplugged&&m.board);a.equal(M.next(m,false).op,'service');
for(const op of ['board-in','plug','brace-in','cover-in']){a.equal(M.next(m,true).op,op);m=M.apply(m,{op},true).state;}
for(const id of M.SCREWS)m=M.apply(m,{op:'tighten',id,tool:'phillips'},true).state;
a(M.assembled(m));a.equal(M.next(m,true).op,'final');a.equal(m.loose.length,0);a(!M.onTable(m));
''')

    def test_fresh_orders_cannot_measure_or_skip_structure(self):
        self.node(r'''
const j=E.offer(31);let s=act(E.create(),'accept',{seed:31}).state;
a.equal(M.next(s.active.mechanics,false).op,'unscrew');a(!act(s,'measure',{mode:'visual',id:'R1'}).ok);
a(!act(s,'mechanical',{op:'unscrew',id:'S1',tool:'phillips'}).ok);s=act(s,'discharge').state;
a(!act(s,'mechanical',{op:'cover-out'}).ok);const coins=s.coins;
for(const id of M.SCREWS){const r=act(s,'mechanical',{op:'unscrew',id,tool:'phillips'});a(r.ok,r.message);s=r.state;}
a(!act(s,'power').ok);s=act(s,'mechanical',{op:'cover-out'}).state;
a(!act(s,'mechanical',{op:'board-out'}).ok);a.equal(s.coins,coins);a(!s.active.diagnosed);
''')

    def test_disassembly_save_replays_not_forged_flags(self):
        self.node(r'''
let s=act(E.create(),'accept',{seed:31}).state;s=act(s,'discharge').state;s=act(s,'mechanical',{op:'unscrew',id:'S2',tool:'phillips'}).state;
const copy=E.restore(JSON.parse(JSON.stringify(s)));a.deepEqual(copy.active.mechanics,s.active.mechanics);a.equal(copy.coins,150);
const raw=JSON.parse(JSON.stringify(s));raw.active.mechanics={...M.create('legacy-open'),entry:'closed'};
const restored=E.restore(raw);a.deepEqual(restored.active.mechanics,s.active.mechanics);a(!M.onTable(restored.active.mechanics));
''')

    def test_board_acceptance_does_not_allow_delivery_until_reassembled_and_retested(self):
        self.node(r'''
const solved=solve(31);let s=solved.s;
a(s.active.finalTested);a(M.assembled(s.active.mechanics));
// Inspect the actual saved action boundary at electrical board acceptance.
const raw=JSON.parse(JSON.stringify(s)),index=raw.active.events.findIndex(e=>e.type==='test');raw.active.events=raw.active.events.slice(0,index+1);
s=E.restore(raw);a(s.active.tested);a(!s.active.finalTested);a(M.onTable(s.active.mechanics));a(!act(s,'deliver').ok);a(!act(s,'testAssembly').ok);
a(!act(s,'mechanical',{op:'board-in'}).ok);s=act(s,'power').state;s=act(s,'discharge').state;
for(const op of ['board-in','plug','brace-in','cover-in'])s=act(s,'mechanical',{op}).state;
for(const id of M.SCREWS)s=act(s,'mechanical',{op:'tighten',id,tool:'phillips'}).state;
a(!act(s,'testAssembly').ok);s=act(s,'power').state;let r=act(s,'testAssembly');a(r.ok,r.message);s=r.state;r=act(s,'deliver');a(r.ok);a.equal(r.state.completed,1);a(!act(r.state,'deliver').ok);
''')

    def test_legacy_progress_is_opened_not_erased_or_recharged(self):
        self.node(r'''
const solved=solve(31),old=JSON.parse(JSON.stringify(solved.s));delete old.active.mechanics;delete old.active.finalTested;
old.active.events=old.active.events.filter(e=>!['mechanical','testAssembly'].includes(e.type));
const restored=E.restore(old);a.equal(restored.coins,old.coins);a(restored.active.diagnosed);a(restored.active.installed);a(restored.active.tested);a(M.onTable(restored.active.mechanics));a(!restored.active.finalTested);
const again=E.restore(JSON.parse(JSON.stringify(restored)));a.equal(again.coins,old.coins);a.deepEqual(again.active.mechanics,restored.active.mechanics);
''')

    def test_old_paid_orders_cannot_be_paid_again_after_mechanical_migration(self):
        self.node(r'''
const solved=solve(31),paid=act(solved.s,'deliver').state,old=JSON.parse(JSON.stringify(paid));
delete old.active.mechanics;delete old.active.finalTested;
old.active.events=old.active.events.filter(e=>!['mechanical','testAssembly'].includes(e.type));
const restored=E.restore(old);a(restored.active.delivered);a(restored.active.legacyCompleted);
a.equal(restored.coins,paid.coins);a.equal(restored.points,paid.points);
a(!act(restored,'deliver').ok);a(!act(restored,'abandon').ok);
const copy=E.restore(JSON.parse(JSON.stringify(restored)));a.equal(copy.coins,paid.coins);a(copy.active.delivered);
''')

    def test_bundle_order_and_visual_layer_are_separate_from_business_and_physics(self):
        from product_training import WEB_ROOT, build_training_html
        page=build_training_html()
        self.assertLess(page.index('root.RepairShopMechanics=api'),page.index('root.RepairShopEngine=api'))
        self.assertLess(page.index('root.RepairShopEnclosure=Object.freeze'),page.index('root.RepairShopScene=api'))
        source=(WEB_ROOT/'repair_shop_enclosure.js').read_text(encoding='utf-8')
        for forbidden in ['fetch(', 'localStorage', 'RepairShopEngine', 'sqlite', '.fault', 'eval(']:
            self.assertNotIn(forbidden,source)
        for text in ['prefers-reduced-motion', 'removedOnDesk', '螺丝盘', '固定支架']:
            self.assertIn(text,source)
        self.assertIn('cancelAnimationFrame(frame)',(WEB_ROOT/'repair_shop_scene.js').read_text(encoding='utf-8'))
        self.assertIn('通用低压教学结构示例',page)


if __name__=='__main__':
    unittest.main()
