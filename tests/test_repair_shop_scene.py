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
        self.assertIn("activeLead=color;probes[color]=null",ui)
        self.assertIn("'放下表笔（Esc）'",ui)
        self.assertIn("shop.addEventListener('keydown'",ui)


if __name__=='__main__':
    unittest.main()
