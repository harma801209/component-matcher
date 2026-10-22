"""3D is a read-only rendering/picking layer, not a second game engine."""
import unittest
import tests.test_repair_shop as repair_tests
from product_training import WEB_ROOT, build_training_html


class RepairShopSceneTests(unittest.TestCase):
    def test_all_layouts_are_finite_separated_and_copy_only(self):
        repair_tests.RepairShopTests().run_node(r'''
const S=require(process.argv[1]+'/repair_shop_scene.js');
for(const p of D.products){const points=S.layout(p.id);a.equal(points.length,p.parts.length);for(const pt of points){a(pt.every(Number.isFinite));a(Math.abs(pt[0])<3&&Math.abs(pt[1])<1.5);}
for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)a(Math.hypot(points[i][0]-points[j][0],points[i][1]-points[j][1])>2);
points[0][0]=1000;a.notEqual(S.layout(p.id)[0][0],1000);}
''')

    def test_bundling_lifecycle_and_physics_separation(self):
        scene=(WEB_ROOT/'repair_shop_scene.js').read_text(encoding='utf-8')
        for text in ['new T.WebGLRenderer','new T.ExtrudeGeometry','new T.Raycaster','pointerdown','wheel','keydown','webglcontextlost','observer.disconnect()','renderer.dispose()','renderer.forceContextLoss()']:
            self.assertIn(text,scene)
        for forbidden in ['RepairShopEngine','localStorage','fetch(','.fault','.apply(']:
            self.assertNotIn(forbidden,scene)
        page=build_training_html()
        self.assertLess(page.index('root.RepairShopScene=api'),page.index('window.RepairShop=Object.freeze'))
        self.assertIn('复位视角',page)
        self.assertIn('3D外观为放大教学模型',page)
        self.assertIn('设备暂不能显示3D',page)

    def test_held_probe_target_is_only_a_finite_nearby_declared_contact(self):
        repair_tests.RepairShopTests().run_node(r'''
const H=require(process.argv[1]+'/repair_shop_probes.js'),points={TP1:{x:100,y:200},GND:{x:300,y:200},behind:{x:100,y:200,visible:false}};
a.equal(H.nearest(points,{x:106,y:204}),'TP1');a.equal(H.nearest(points,{x:295,y:201}),'GND');
a.equal(H.nearest(points,{x:200,y:200}),null);a.equal(H.nearest(points,{x:125,y:200}),null);a.equal(H.nearest(points,{x:125,y:200},34),'TP1');
for(const pointer of [null,{}, {x:NaN,y:200},{x:Infinity,y:200}])a.equal(H.nearest(points,pointer),null);
a.equal(H.nearest({bad:{x:NaN,y:2}},{x:1,y:2}),null);a.equal(H.nearest(points,{x:100,y:200},-1),null);
''')

    def test_hover_mesh_is_passive_and_cursor_lifecycle_and_cancellation_are_explicit(self):
        probes=(WEB_ROOT/'repair_shop_probes.js').read_text(encoding='utf-8')
        scene=(WEB_ROOT/'repair_shop_scene.js').read_text(encoding='utf-8')
        ui=(WEB_ROOT/'repair_shop_ui.js').read_text(encoding='utf-8')
        for forbidden in ['RepairShopEngine','localStorage','fetch(','.fault','dispatch(']:
            self.assertNotIn(forbidden,probes)
        for text in ['function updateHover','worldToLocal','showHeld','pointerleave','pointerenter','probe:cancel','probe:miss','canvas.style.cursor=originalCursor']:
            self.assertIn(text,scene)
        self.assertIn("if(!probeActive||prior.button!==0)",scene)
        self.assertIn('if(probeActive&&inside){',scene)
        self.assertIn('if(!orbit)hoverContact=',scene)
        self.assertNotIn('if(probeActive&&inside&&!orbit)',scene)
        self.assertIn("activeLead=color;probes[color]=null",ui)
        self.assertIn("'放下表笔（Esc）'",ui)
        self.assertIn("shop.addEventListener('keydown'",ui)
        self.assertIn("canvas.dataset.repairFocus='board-canvas'",ui)
        rotation=ui.split('function rotateProbe(',1)[1].split('\n',1)[0]
        for forbidden in ('dispatch(', 'E.apply(', 'probes[color]=null', 'meter=null'):
            self.assertNotIn(forbidden,rotation)

    def test_phone_dock_reuses_validated_controls_and_keeps_animation_in_view(self):
        ui=(WEB_ROOT/'repair_shop_ui.js').read_text(encoding='utf-8')
        css=(WEB_ROOT/'repair_shop.css').read_text(encoding='utf-8')
        dock=ui.split('function mobileDock(',1)[1].split('function syncMobileControls',1)[0]
        for forbidden in ('E.apply(', 'save(', 'diagnose', 'stockId', 'setTimeout('):
            self.assertNotIn(forbidden,dock)
        self.assertIn('original.click();revealWorkbench();',ui)
        self.assertIn('b.disabled=!original||original.disabled',ui)
        self.assertIn('mobileDock(job,true)',ui)
        self.assertIn('mobileDock(job)',ui)
        self.assertIn('if(result.ok&&',ui)
        self.assertIn("scrollIntoView({block:'start',behavior:'instant'})",ui)
        self.assertLess(ui.index('window.TrainingEmbedLayout?.flush()'),ui.index("shop.querySelector('.rs-board-wrap')?.scrollIntoView"))
        self.assertIn('.rs-mobile-dock{display:none}',css)
        self.assertIn('height:260px',css)

    def test_probe_turns_match_renderer_and_pivot_at_the_unchanged_tip(self):
        repair_tests.RepairShopTests().run_node(r'''
const H=require(process.argv[1]+'/repair_shop_probes.js'),vm=require('node:vm'),fs=require('node:fs'),context={console};
vm.runInNewContext(fs.readFileSync(process.argv[1]+'/vendor/training-three.min.js','utf8'),context);const T=context.TrainingThree;
a.equal(H.normalizeTurn(-15),345);a.equal(H.normalizeTurn(375),15);a.equal(H.normalizeTurn(NaN),0);
for(const color of ['black','red'])for(let turn=0;turn<360;turn+=15)for(const scale of [.55,1]){
 const tip=[2,.1,-1],d=H.direction(tip,color,turn,scale),g=new T.Group();g.position.set(...tip);g.scale.setScalar(scale);g.rotation.set(-.65,d.yaw,-.6,'YXZ');
 const real=g.localToWorld(new T.Vector3(.48,1.7,.32)).toArray();a(real.every((x,i)=>Math.abs(x-d.rear[i])<1e-10));
 a(Math.abs(Math.hypot(...d.axis)-1)<1e-10);a.deepEqual(Array.from(g.localToWorld(new T.Vector3()).toArray()),tip);
}
a(H.direction([0,0,0],'black').rear[0]<0);a(H.direction([0,0,0],'red').rear[0]>0);
''')

    def test_soft_cable_exits_the_rear_and_does_not_fold_across_the_grip(self):
        repair_tests.RepairShopTests().run_node(r'''
const H=require(process.argv[1]+'/repair_shop_probes.js'),Meter=require(process.argv[1]+'/repair_shop_meter.js'),sub=(x,y)=>x.map((v,i)=>v-y[i]),dot=(x,y)=>x.reduce((s,v,i)=>s+v*y[i],0);
let cases=0;for(const product of D.products)for(const contact of Meter.contacts(product))for(const color of ['black','red'])for(const scale of [.55,1])for(let turn=0;turn<360;turn+=15){
 const tip=[contact.point[0],.1,contact.point[1]],d=H.direction(tip,color,turn,scale),points=H.cablePath(d.rear,d.axis,color==='black'?-1:1);
 a.equal(points.length,41);a.deepEqual(points[0],d.rear);a(points.flat().every(Number.isFinite));a(dot(sub(points[1],points[0]),d.axis)>0);
 const body=sub(d.rear,tip);for(const p of points.slice(5)){const t=Math.max(0,Math.min(1,dot(sub(p,tip),body)/dot(body,body))),distance=Math.hypot(...sub(p,tip.map((v,i)=>v+body[i]*t)));a(distance>.14,'Cable must clear the grip after its rear attachment');}
 cases++;
}a.equal(cases,2304);
''')

    def test_dynamic_tube_has_finite_normals_and_reuses_actual_geometry(self):
        repair_tests.RepairShopTests().run_node(r'''
const H=require(process.argv[1]+'/repair_shop_probes.js'),vm=require('node:vm'),fs=require('node:fs'),context={console};
vm.runInNewContext(fs.readFileSync(process.argv[1]+'/vendor/training-three.min.js','utf8'),context);const T=context.TrainingThree,pcb=new T.Group();globalThis.RepairShopMeter=require(process.argv[1]+'/repair_shop_meter.js');
const mesh=(g,m,p,group=pcb)=>{const n=new T.Mesh(g,m);n.position.set(...p);group.add(n);return n;};
const rod=(x,y,r,c,group=pcb)=>{const a0=new T.Vector3(...x),b0=new T.Vector3(...y),d=b0.clone().sub(a0),n=mesh(new T.CylinderGeometry(r,r,d.length(),8),new T.MeshStandardMaterial({color:c}),a0.add(b0).multiplyScalar(.5).toArray(),group);n.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return n;};
const p=H.create(T,pcb,D.products[0],{mesh,rod}),ids=()=>{const values=[];pcb.traverse(n=>{if(n.isMesh)values.push(n.geometry.id);});return values;},before=ids();
for(let turn=0;turn<360;turn+=15){p.update({black:'GND',red:'TP1'},true,{black:turn,red:360-turn});p.showHeld('black',[0,.1,0],null,true);const snap=p.cableSnapshot();
 for(const wire of Object.values(snap)){a(wire);a.equal(wire.samples,40);a(wire.start.every((v,i)=>Math.abs(v-wire.rear[i])<1e-5));a(wire.end.every((v,i)=>Math.abs(v-wire.points.at(-1)[i])<1e-5));}
 a.equal(p.heldSnapshot().turn,turn);a.deepEqual(ids(),before);
 pcb.traverse(n=>{if(n.isMesh&&n.geometry.attributes.normal){const array=n.geometry.attributes.normal.array;a([...array].every(Number.isFinite));}});
}
p.showHeld(null,null,null,false);a.equal(p.cableSnapshot().held,null);
const points=H.cablePath([0,1,0],[0,1,0],1),positions=new Float32Array(41*8*3),normals=new Float32Array(positions.length);H.fillTube(points,positions,normals);
for(let i=0;i<normals.length;i+=3)a(Math.abs(Math.hypot(normals[i],normals[i+1],normals[i+2])-1)<1e-6);
''')


if __name__=='__main__':
    unittest.main()
