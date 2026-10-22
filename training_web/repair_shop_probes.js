/* Real scene meshes: hovering is visual only; contact needs a deliberate click. */
(function(root){
 'use strict';
 function nearest(points,pointer,radius=24){
  if(!pointer||![pointer.x,pointer.y,radius].every(Number.isFinite)||radius<0)return null;
  let best=null,distance=radius*radius;
  for(const [id,p] of Object.entries(points)){if(!p||![p.x,p.y].every(Number.isFinite)||p.visible===false)continue;const d=(p.x-pointer.x)**2+(p.y-pointer.y)**2;if(d<=distance){best=id;distance=d;}}
  return best;
 }
 function create(T,pcb,product,h){
  const contacts=root.RepairShopMeter.contacts(product),nodes={},heldNodes={},placed={};let held={visible:false,color:null,target:null,valid:false,tip:null};
  function model(hex,side,overlay){
   const g=new T.Group();pcb.add(g);g.visible=false;g.rotation.set(-.65,0,-.6);
   h.rod([0,0,0],[.12,.4,.08],.018,0xd9e1e0,g);
   h.rod([.12,.4,.08],[.2,.65,.14],.048,hex,g);
   h.rod([.2,.65,.14],[.48,1.7,.32],.105,hex,g);
   h.rod([.17,.54,.12],[.22,.7,.15],.17,hex,g);
   for(let i=0;i<5;i++){const t=.83+i*.13;h.rod([.2+(t-.65)*.267,t,.14+(t-.65)*.171],[.2+(t-.63)*.267,t+.02,.14+(t-.63)*.171],.116,hex===0xc74332?0x6e2822:0x4a5555,g);}
   const wires=[0,1,2].map(()=>h.rod([0,0,0],[0,1,0],.025,hex));wires.forEach(w=>w.visible=false);
   if(overlay){g.traverse(o=>{if(o.isMesh){o.renderOrder=200;o.material.depthTest=false;o.material.depthWrite=false;o.castShadow=false;o.receiveShadow=false;}});for(const w of wires){w.renderOrder=190;w.material.depthTest=false;w.material.depthWrite=false;w.castShadow=false;}}
   return {g,wires,side};
  }
  for(const [color,hex,side] of [['black',0x252a2b,-1],['red',0xc74332,1]]){
   nodes[color]=model(hex,side,false);heldNodes[color]=model(hex,side,true);
  }
  const marker=h.mesh(new T.TorusGeometry(.23,.028,12,36),new T.MeshBasicMaterial({color:0x7ee6b0,depthTest:false,depthWrite:false}),[0,.14,0]);marker.rotation.x=-Math.PI/2;marker.visible=false;marker.renderOrder=180;marker.castShadow=false;
  function segment(n,a,b){const v=x=>new T.Vector3(...x),d=v(b).sub(v(a));n.position.copy(v(a).add(v(b)).multiplyScalar(.5));n.scale.y=d.length();n.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());}
  function pose(n,point,scale){n.g.position.set(...point);n.g.scale.setScalar(scale);const end=new T.Vector3(.48,1.7,.32).applyEuler(n.g.rotation).multiplyScalar(scale).add(n.g.position),a=[n.side*5.3,.6,3.4],b=[n.side*4.6,1.2,3],c=end.clone().add(new T.Vector3(.3,.2,.25)).toArray();segment(n.wires[0],a,b);segment(n.wires[1],b,c);segment(n.wires[2],c,end.toArray());}
  function update(leads,visible){
   for(const [color,n] of Object.entries(nodes)){const contact=contacts.find(c=>c.id===leads?.[color]);n.g.visible=Boolean(visible&&contact);n.wires.forEach(w=>w.visible=n.g.visible);placed[color]=n.g.visible?contact.id:null;
    if(n.g.visible)pose(n,[contact.point[0],.1,contact.point[1]],.55);
   }
  }
  function showHeld(color,point,target,valid){
   const visible=Boolean(heldNodes[color]&&point?.every(Number.isFinite));for(const [id,n] of Object.entries(heldNodes)){n.g.visible=visible&&id===color;n.wires.forEach(w=>w.visible=n.g.visible);if(n.g.visible)pose(n,point,1);}
   marker.visible=visible&&Boolean(target);if(marker.visible){marker.position.set(...point);marker.material.color.setHex(valid?0x7ee6b0:0xff785e);}
   held={visible,color:visible?color:null,target:visible?target:null,valid:visible&&Boolean(target)&&valid,tip:visible?[...point]:null};
  }
  return {update,showHeld,snapshot:()=>({...placed}),heldSnapshot:()=>({...held,tip:held.tip&&[...held.tip]})};
 }
 root.RepairShopProbes=Object.freeze({create,nearest,VERSION:2});if(typeof module!=='undefined'&&module.exports)module.exports=root.RepairShopProbes;
})(typeof globalThis!=='undefined'?globalThis:this);
