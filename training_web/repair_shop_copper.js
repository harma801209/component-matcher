/* Read-only copper, pad and test-point meshes, built from the explicit PCB graph. */
(function(root){
 'use strict';
 function create(T,pcb,plan,h){
  const {mesh,box,print,material}=h,B=root.RepairShopBoard,netMaterials={},overlay=new T.Group(),labels=new T.Group(),auxMaterials=[],runs=[],samples={};let highlighted=[];pcb.add(overlay,labels);
  for(const net of plan.nets){const color=net.kind==='unmodeled'?0x929e9f:0xe5ac60;netMaterials[net.id]={top:new T.MeshBasicMaterial({color}),bottom:new T.MeshBasicMaterial({color:net.kind==='unmodeled'?0x929e9f:0x61d5f1}),unmodeled:net.kind==='unmodeled'};}
  function strip(a,b,y,width,mat,group=pcb,pick){const length=Math.hypot(b[0]-a[0],b[1]-a[1]);if(length<1e-6)return;const n=mesh(new T.BoxGeometry(length,.012,width),mat,[(a[0]+b[0])/2,y,(a[1]+b[1])/2],group);n.rotation.y=-Math.atan2(b[1]-a[1],b[0]-a[0]);n.castShadow=false;if(pick)n.userData.pick=pick;return n;}
  function dashed(a,b,y,width,mat,pick){const length=Math.hypot(b[0]-a[0],b[1]-a[1]);for(let at=0;at<length;at+=.27){const to=Math.min(length,at+.18),point=t=>[a[0]+(b[0]-a[0])*t/length,a[1]+(b[1]-a[1])*t/length];strip(point(at),point(to),y,width,mat,overlay,pick);}}
  // Merge shared/collinear grid edges; a trunk is not drawn repeatedly for each pad.
  const lines=new Map();for(const r of plan.routes)for(let i=1;i<r.cells.length;i++){const a=r.cells[i-1],b=r.cells[i];if(a[2]!==b[2])continue;const horizontal=a[0]!==b[0],fixed=horizontal?a[1]:a[0],start=Math.min(horizontal?a[0]:a[1],horizontal?b[0]:b[1]),key=[r.net,a[2],horizontal?'x':'z',fixed].join('|');if(!lines.has(key))lines.set(key,new Set());lines.get(key).add(start);}
  let segments=0;for(const [key,starts] of lines){const [net,layer,axis,f]=key.split('|'),values=[...starts].sort((a,b)=>a-b),mat=netMaterials[net],fixed=Number(f),l=Number(layer);let i=0;while(i<values.length){const start=values[i];let end=start+1;while(++i<values.length&&values[i]===end)end++;const a=B.world(axis==='x'?[start,fixed,l]:[fixed,start,l]),b=B.world(axis==='x'?[end,fixed,l]:[fixed,end,l]);runs.push({net,layer:l,a,b});strip(a,b,l?-.13:.022,.085,mat.top,pcb,'net:'+net);if(l||mat.unmodeled)dashed(a,b,.055,.055,mat.bottom,'net:'+net);segments++;}}
  // Every logical contact has a physical pad and an exact-to-grid neck.
  for(const [ref,pin] of Object.entries(plan.pins)){
   const n=pin.net&&netMaterials[pin.net],m=n?.top||material(0x79837b),[x,z]=pin.point,pad=mesh(new T.BoxGeometry(.25,.025,.25),m,[x,.035,z]);pad.castShadow=false;if(pin.net)pad.userData.pick=plan.ports.find(p=>p.ref===ref)?.part||'net:'+pin.net;
   if(pin.net){strip(pin.point,B.world(pin.cell),.025,.085,n.top,pcb,'net:'+pin.net);}
   if(!ref.startsWith('TP')){const label=print(pin.label,[x,.072,z+.27],Math.max(.4,pin.label.length*.13),.25,labels,'#ecf4df');label.userData.pin=ref;}
  }
  for(const via of plan.vias){const [x,z]=via.point,m=netMaterials[via.net].top,ring=mesh(new T.TorusGeometry(.075,.026,8,16),m,[x,.047,z]);ring.rotation.x=-Math.PI/2;ring.castShadow=false;ring.userData.pick='net:'+via.net;mesh(new T.CylinderGeometry(.038,.038,.15,10),m,[x,-.035,z]);const hole=mesh(new T.CylinderGeometry(.035,.035,.003,12),new T.MeshBasicMaterial({color:0x082e29}),[x,.05,z]);hole.castShadow=false;}
  for(const port of [...plan.ports,{id:'GND',part:null,net:'GND',point:plan.pins['TP_GND.1'].point}]){const [x,z]=port.point,ring=mesh(new T.TorusGeometry(.13,.035,10,20),new T.MeshBasicMaterial({color:0xffdc8a}),[x,.085,z]);ring.rotation.x=-Math.PI/2;ring.userData.pick=port.part||'net:GND';ring.castShadow=false;print(port.id,[x,.08,z+(z>1.5?-.3:.33)],.68,.24,pcb,'#fff2ba');}
  for(const c of plan.components.filter(c=>!c.main)){const [x,z]=c.point,n=box([x,.19,z],[c.size[0],.28,c.size[1]],0x344f51);auxMaterials.push(n.material);print(c.id,[x,.34,z-.12],Math.max(.5,c.size[0]-.07),.19);print(c.label,[x,.34,z+.12],c.size[0]*1.2,.19);}
  function update(selected,net,inspection){const active=new Set(net?[net]:selected?Object.entries(plan.pins).filter(([ref,p])=>ref.startsWith(selected+'.')&&p.net).map(([,p])=>p.net):[]);highlighted=[...active];for(const [id,m] of Object.entries(netMaterials)){const on=!active.size||active.has(id);m.top.color.setHex(on?(active.size?0xffed98:m.unmodeled?0x929e9f:0xe5ac60):0x526456);m.bottom.color.setHex(on?(active.size?0xffed98:m.unmodeled?0x929e9f:0x61d5f1):0x315658);}overlay.visible=inspection;labels.visible=inspection;for(const m of auxMaterials){if(m.transparent!==inspection){m.transparent=inspection;m.needsUpdate=true;}m.opacity=inspection?.28:1;m.depthWrite=!inspection;} }
  for(const r of runs.filter(r=>r.layer===0)){if(samples[r.net])continue;for(const t of [.5,.3,.7]){const q=[r.a[0]+(r.b[0]-r.a[0])*t,r.a[1]+(r.b[1]-r.a[1])*t];if(Math.hypot(r.a[0]-r.b[0],r.a[1]-r.b[1])<.4)continue;
    if(plan.components.some(c=>Math.abs(q[0]-c.point[0])<(c.main?.9:c.size[0]/2+.15)&&Math.abs(q[1]-c.point[1])<(c.main?.7:c.size[1]/2+.15)))continue;
    if(Object.values(plan.pins).some(p=>Math.hypot(q[0]-p.point[0],q[1]-p.point[1])<.24))continue;
    if(plan.routes.some(path=>path.net!==r.net&&path.cells.some(c=>{const p=B.world(c);return Math.hypot(q[0]-p[0],q[1]-p[1])<.16;})))continue;
    samples[r.net]=q;break;
  }}
  return {update,snapshot:()=>({version:B.VERSION,nets:plan.nets.length,pads:Object.keys(plan.pins).length,segments,vias:plan.vias.length,projectionVisible:overlay.visible,highlighted:[...highlighted],samples})};
 }
 root.RepairShopCopper=Object.freeze({create});
})(typeof globalThis!=='undefined'?globalThis:this);
