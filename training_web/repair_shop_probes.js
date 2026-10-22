/* Two movable 3D probes on declared voltage contacts; no automatic measurement. */
(function(root){
 'use strict';
 function create(T,pcb,product,h){
  const contacts=root.RepairShopMeter.contacts(product),nodes={},placed={};
  for(const [color,hex,side] of [['black',0x252a2b,-1],['red',0xc74332,1]]){
   const g=new T.Group();pcb.add(g);g.visible=false;
   h.rod([0,0,0],[.16,.35,.1],.025,0xc9d1d1,g);
   h.rod([.16,.35,.1],[.35,.78,.22],.07,hex,g);
   h.rod([.14,.32,.09],[.19,.41,.12],.105,hex,g);
   const wires=[0,1].map(()=>h.rod([0,0,0],[0,1,0],.025,hex));wires.forEach(w=>w.visible=false);
   nodes[color]={g,wires,side};
  }
  function segment(n,a,b){const v=x=>new T.Vector3(...x),d=v(b).sub(v(a));n.position.copy(v(a).add(v(b)).multiplyScalar(.5));n.scale.y=d.length();n.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());}
  function update(leads,visible){
   for(const [color,n] of Object.entries(nodes)){const contact=contacts.find(c=>c.id===leads?.[color]);n.g.visible=Boolean(visible&&contact);n.wires.forEach(w=>w.visible=n.g.visible);placed[color]=n.g.visible?contact.id:null;
    if(!n.g.visible)continue;const [x,z]=contact.point;n.g.position.set(x,.1,z);const a=[n.side*3.6,.18,2.05],b=[x+.4,1,z+.55],c=[x+.35,.88,z+.22];segment(n.wires[0],a,b);segment(n.wires[1],b,c);
   }
  }
  return {update,snapshot:()=>({...placed})};
 }
 root.RepairShopProbes=Object.freeze({create});
})(typeof globalThis!=='undefined'?globalThis:this);
