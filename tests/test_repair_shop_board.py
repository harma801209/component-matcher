"""Visible PCB copper must be a routed, explicit electrical graph, not decoration."""
import unittest
import tests.test_repair_shop as repair_tests


class RepairShopBoardTests(unittest.TestCase):
    def node(self, source):
        return repair_tests.RepairShopTests().run_node("const B=require(process.argv[1]+'/repair_shop_board.js');\n"+source)

    def test_networks_match_the_declared_six_equivalent_circuits(self):
        self.node(r'''
const checks={
 lamp:[['F1.2','R1.1'],['R1.2','D1.A'],['D1.K','J_PWR.GND']],
 fan:[['F1.2','M1.+','D1.K'],['M1.-','Q1.D','D1.A'],['Q1.S','J_PWR.GND'],['Q1.G','J_GATE.OUT']],
 speaker:[['F1.2','RS.1'],['RS.2','C1.+','U_AMP.VCC','LOAD.+'],['U_AMP.OUT','RF.1'],['RF.2','U_AMP.IN-','R1.1'],['R1.2','VREF.OUT']],
 clock:[['J_PWR.VIN','C1.1','R1.1','U_CTRL.VCC','RLOAD.1'],['R1.2','U_CTRL.RESET'],['C1.2','RLOAD.2','J_PWR.GND']],
 sensor:[['J_PWR.VIN','U1.IN','U1.EN'],['U1.OUT','C1.1','R1.1','RLOAD.1'],['R1.2','BUS.IN'],['C1.2','RLOAD.2','U1.GND','J_PWR.GND']],
 router:[['F1.2','MODULE.IN'],['MODULE.OUT','RS.1'],['RS.2','L1.1'],['L1.2','C1.+','LOAD.+'],['C1.-','LOAD.-','MODULE.GND','J_PWR.GND']]
};
for(const [id,groups] of Object.entries(checks)){
 const p=B.get(id),net=ref=>p.nets.find(n=>n.members.includes(ref))?.id;
 for(const group of groups){a(net(group[0]),group[0]);a(group.every(ref=>net(ref)===net(group[0])),id+group);}
 a.notEqual(net('J_PWR.VIN'),net('J_PWR.GND'));a.equal(p.ports.length,3);
 for(const port of p.ports)a.equal(net(port.ref),port.net);
 for(const c of D.products.find(p=>p.id===id).parts)a(p.components.some(x=>x.id===c.id&&x.main));
 if(id==='clock'){a(p.nets.filter(n=>n.kind==='unmodeled').length===2);a.notEqual(net('U_CTRL.RESET'),net('J_PWR.GND'));}
 if(id==='sensor'){a(!net('U1.NC'));a.notEqual(net('BUS.IN'),net('J_PWR.GND'));}
}
''')

    def test_routes_are_complete_separated_and_connected_only_by_plated_vias(self):
        self.node(r'''
for(const product of D.products){
 const p=B.get(product.id),seen=new Map();a(p.routes.length>0);a(p.vias.length>=0);
 const pins=Object.entries(p.pins);for(let i=0;i<pins.length;i++)for(let j=i+1;j<pins.length;j++){const [r,x]=pins[i],[s,y]=pins[j];if(x.net!==y.net)a(Math.abs(x.point[0]-y.point[0])>=.25||Math.abs(x.point[1]-y.point[1])>=.25,product.id+' pad short '+r+' '+s);}
 for(const r of p.routes){a(p.nets.some(n=>n.id===r.net));a(r.cells.length>1);
  for(let i=0;i<r.cells.length;i++){const c=r.cells[i];a(c.length===3&&c.every(Number.isFinite));
   const key=c.join(',');if(seen.has(key))a.equal(seen.get(key),r.net,'No copper short '+key);seen.set(key,r.net);
   if(i){const q=r.cells[i-1],distance=Math.abs(c[0]-q[0])+Math.abs(c[1]-q[1]);a(c[2]===q[2]?distance===1:distance===0);
    if(c[2]!==q[2])a(p.vias.some(v=>v.net===r.net&&v.cell[0]===c[0]&&v.cell[1]===c[1]));}
  }
  a.deepEqual(r.cells[0],p.pins[r.from].cell);a.deepEqual(r.cells.at(-1),p.pins[r.to].cell);
 }
 for(const n of p.nets)for(const ref of n.members){const pin=p.pins[ref];a(pin,ref);a.equal(pin.net,n.id);a(seen.get(pin.cell.join(','))===n.id,'Every pad must reach copper '+ref);}
 a(p.pins['TP_GND.1']);a.equal(p.pins['TP_GND.1'].net,'GND');
 // Independently flood the actual routed-edge graph (including via edges).
 for(const n of p.nets){const adjacency=new Map(),put=(x,y)=>{const k=x.join(',');if(!adjacency.has(k))adjacency.set(k,new Set());adjacency.get(k).add(y.join(','));};
  for(const r of p.routes.filter(r=>r.net===n.id))for(let i=1;i<r.cells.length;i++){put(r.cells[i-1],r.cells[i]);put(r.cells[i],r.cells[i-1]);}
  const visited=new Set(),queue=[p.pins[n.members[0]].cell.join(',')];while(queue.length){const k=queue.pop();if(visited.has(k))continue;visited.add(k);for(const next of adjacency.get(k)||[])queue.push(next);}
  for(const ref of n.members)a(visited.has(p.pins[ref].cell.join(',')),product.id+': isolated pad '+ref);
 }
 const copy=B.get(product.id);copy.nets[0].label='forged';a.notEqual(B.get(product.id).nets[0].label,'forged');
}
''')

    def test_bundle_and_inspection_do_not_replace_the_physics_or_reveal_faults(self):
        from product_training import WEB_ROOT, build_training_html
        page=build_training_html()
        self.assertLess(page.index('root.RepairShopBoard=api'),page.index('root.RepairShopScene=api'))
        self.assertLess(page.index('root.RepairShopCopper=Object.freeze'),page.index('root.RepairShopScene=api'))
        for name in ['repair_shop_board.js','repair_shop_copper.js']:
            source=(WEB_ROOT/name).read_text(encoding='utf-8')
            for forbidden in ['RepairShopEngine','localStorage','fetch(','.fault','sqlite','eval(']:
                self.assertNotIn(forbidden,source)
        for text in ['铜箔检修','俯视查线','同一网络连接','交叉线不一定相连','灰色支路未建模']:
            self.assertIn(text,page)

    def test_main_contact_map_matches_rendered_package_pins(self):
        self.node(r'''
const K=require(process.argv[1]+'/training_game_packages.js');
const ids={resistor:'res-thick',capacitor:'cap-aluminum',ceramic:'cap-mlcc',mos:'mos-n',inductor:'ind-molded'};
for(const product of D.products){const plan=B.get(product.id);
 for(const part of product.parts){if(!ids[part.type])continue;const c=plan.components.find(c=>c.id===part.id),pins=Object.entries(plan.pins).filter(([ref])=>ref.startsWith(part.id+'.'));
  for(const pin of K.layout(ids[part.type]).pins)a(pins.some(([,p])=>Math.abs(p.point[0]-c.point[0]-pin.point[0])<1e-8&&Math.abs(p.point[1]-c.point[1]-pin.point[2])<1e-8),product.id+part.id+pin.number);
 }
}
''')

    def test_transparent_inspection_is_off_until_explicitly_clicked(self):
        import re
        from product_training import WEB_ROOT
        ui=(WEB_ROOT/'repair_shop_ui.js').read_text(encoding='utf-8')
        self.assertTrue(re.search(r"let mechanicalTool='',[^;]*inspection=false",ui),'Initial inspection must be explicitly off')
        reset=ui.split('function clearChoices(){',1)[1].split('\n',1)[0]
        self.assertIn('inspection=false',reset)
        self.assertNotIn('inspection=true',ui)
        self.assertIn('inspection=!inspection',ui)


if __name__=='__main__':
    unittest.main()
