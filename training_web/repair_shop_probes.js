/* Real scene meshes: hovering is visual only; contact needs a deliberate click. */
(function(root){
 'use strict';
 const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],unit=a=>{const n=Math.hypot(...a);return n>1e-9?mul(a,1/n):[1,0,0];};
 const normalizeTurn=v=>Number.isFinite(v)?((v%360)+360)%360:0;
 function rotate(v,yaw){const cx=Math.cos(-.65),sx=Math.sin(-.65),cz=Math.cos(-.6),sz=Math.sin(-.6),a=cz*v[0]-sz*v[1],b=sz*v[0]+cz*v[1],c=cx*b-sx*v[2],d=sx*b+cx*v[2];return [Math.cos(yaw)*a+Math.sin(yaw)*d,c,-Math.sin(yaw)*a+Math.cos(yaw)*d];}
 function direction(point,color,turn=0,scale=1){const yaw=(color==='black'?Math.PI:0)+normalizeTurn(turn)*Math.PI/180;return {yaw,rear:add(point,mul(rotate([.48,1.7,.32],yaw),scale)),axis:unit(rotate([.28,1.05,.18],yaw))};}
 function cablePath(rear,axis,side,steps=40){
  const anchor=[side*5.3,.45,3.4],length=Math.max(.8,Math.min(1.8,Math.hypot(...sub(anchor,rear))*.22)),p1=add(rear,mul(axis,length)),p2=[side*4.7,Math.max(1.8,rear[1]+1),2.7];
  return Array.from({length:steps+1},(_,i)=>{const t=i/steps,u=1-t;return rear.map((x,k)=>u*u*u*x+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t*t*t*anchor[k]);});
 }
 function fillTube(points,positions,normals,sides=8,radius=.026){
  let previous=null;
  for(let i=0;i<points.length;i++){
   const tangent=unit(sub(points[Math.min(i+1,points.length-1)],points[Math.max(0,i-1)]));let normal=previous&&sub(previous,mul(tangent,dot(previous,tangent)));
   if(!normal||Math.hypot(...normal)<1e-7)normal=cross(tangent,Math.abs(tangent[1])<.95?[0,1,0]:[1,0,0]);normal=unit(normal);const binormal=unit(cross(tangent,normal));previous=normal;
   for(let j=0;j<sides;j++){const theta=j/sides*Math.PI*2,n=add(mul(normal,Math.cos(theta)),mul(binormal,Math.sin(theta))),p=add(points[i],mul(n,radius)),offset=(i*sides+j)*3;positions.set(p,offset);normals.set(n,offset);}
  }
 }
 function nearest(points,pointer,radius=24){
  if(!pointer||![pointer.x,pointer.y,radius].every(Number.isFinite)||radius<0)return null;
  let best=null,distance=radius*radius;
  for(const [id,p] of Object.entries(points)){if(!p||![p.x,p.y].every(Number.isFinite)||p.visible===false)continue;const d=(p.x-pointer.x)**2+(p.y-pointer.y)**2;if(d<=distance){best=id;distance=d;}}
  return best;
 }
 function create(T,pcb,product,h){
  const contacts=root.RepairShopMeter.contacts(product),nodes={},heldNodes={},placed={},steps=40,sides=8;let directions={black:0,red:0},held={visible:false,color:null,target:null,valid:false,tip:null,turn:0};
  function model(hex,side,overlay,color){
   const g=new T.Group();pcb.add(g);g.visible=false;
   h.rod([0,0,0],[.12,.4,.08],.018,0xd9e1e0,g);
   h.rod([.12,.4,.08],[.2,.65,.14],.048,hex,g);
   h.rod([.2,.65,.14],[.48,1.7,.32],.105,hex,g);
   h.rod([.17,.54,.12],[.22,.7,.15],.17,hex,g);
   for(let i=0;i<5;i++){const t=.83+i*.13;h.rod([.2+(t-.65)*.267,t,.14+(t-.65)*.171],[.2+(t-.63)*.267,t+.02,.14+(t-.63)*.171],.116,hex===0xc74332?0x6e2822:0x4a5555,g);}
   const geometry=new T.BufferGeometry(),positions=new Float32Array((steps+1)*sides*3),normals=new Float32Array(positions.length),indices=[];
   for(let i=0;i<steps;i++)for(let j=0;j<sides;j++){const a=i*sides+j,b=(i+1)*sides+j,c=i*sides+(j+1)%sides,d=(i+1)*sides+(j+1)%sides;indices.push(a,c,b,c,d,b);}
   geometry.setAttribute('position',new T.BufferAttribute(positions,3));geometry.setAttribute('normal',new T.BufferAttribute(normals,3));geometry.setIndex(indices);
   const wire=h.mesh(geometry,new T.MeshStandardMaterial({color:hex,roughness:.85,metalness:.02}),[0,0,0]);wire.visible=false;wire.frustumCulled=false;wire.raycast=()=>{};
   if(overlay){g.traverse(o=>{if(o.isMesh){o.renderOrder=200;o.material.depthTest=false;o.material.depthWrite=false;o.castShadow=false;o.receiveShadow=false;}});wire.renderOrder=190;wire.material.depthTest=false;wire.material.depthWrite=false;wire.castShadow=false;}
   return {g,wire,positions,normals,side,color,data:null};
  }
  for(const [color,hex,side] of [['black',0x252a2b,-1],['red',0xc74332,1]]){
   nodes[color]=model(hex,side,false,color);heldNodes[color]=model(hex,side,true,color);
  }
  const marker=h.mesh(new T.TorusGeometry(.23,.028,12,36),new T.MeshBasicMaterial({color:0x7ee6b0,depthTest:false,depthWrite:false}),[0,.14,0]);marker.rotation.x=-Math.PI/2;marker.visible=false;marker.renderOrder=180;marker.castShadow=false;
  function pose(n,point,scale){const turn=directions[n.color],d=direction(point,n.color,turn,scale),points=cablePath(d.rear,d.axis,n.side,steps);n.g.position.set(...point);n.g.rotation.set(-.65,d.yaw,-.6,'YXZ');n.g.scale.setScalar(scale);fillTube(points,n.positions,n.normals,sides);n.wire.geometry.attributes.position.needsUpdate=true;n.wire.geometry.attributes.normal.needsUpdate=true;n.data={...d,turn,tip:[...point],points};}
  function update(leads,visible,turns={}){
   directions={black:normalizeTurn(turns.black),red:normalizeTurn(turns.red)};
   for(const [color,n] of Object.entries(nodes)){const contact=contacts.find(c=>c.id===leads?.[color]);n.g.visible=Boolean(visible&&contact);n.wire.visible=n.g.visible;placed[color]=n.g.visible?contact.id:null;
    if(n.g.visible)pose(n,[contact.point[0],.1,contact.point[1]],.55);
   }
  }
  function showHeld(color,point,target,valid){
   const visible=Boolean(heldNodes[color]&&point?.every(Number.isFinite));for(const [id,n] of Object.entries(heldNodes)){n.g.visible=visible&&id===color;n.wire.visible=n.g.visible;if(n.g.visible)pose(n,point,1);}
   marker.visible=visible&&Boolean(target);if(marker.visible){marker.position.set(...point);marker.material.color.setHex(valid?0x7ee6b0:0xff785e);}
   held={visible,color:visible?color:null,target:visible?target:null,valid:visible&&Boolean(target)&&valid,tip:visible?[...point]:null,turn:visible?directions[color]:0};
  }
  function wireSnapshot(n){if(!n?.wire.visible||!n.data)return null;const center=i=>{const p=[0,0,0];for(let j=0;j<sides;j++)for(let k=0;k<3;k++)p[k]+=n.positions[(i*sides+j)*3+k]/sides;return p;};return {...n.data,tip:[...n.data.tip],rear:[...n.data.rear],axis:[...n.data.axis],points:n.data.points.map(p=>[...p]),geometryId:n.wire.geometry.id,samples:steps,start:center(0),afterStart:center(1),end:center(steps)};}
  return {update,showHeld,snapshot:()=>({...placed}),heldSnapshot:()=>({...held,tip:held.tip&&[...held.tip]}),cableSnapshot:()=>({black:wireSnapshot(nodes.black),red:wireSnapshot(nodes.red),held:wireSnapshot(Object.values(heldNodes).find(n=>n.wire.visible))})};
 }
 root.RepairShopProbes=Object.freeze({create,nearest,normalizeTurn,direction,cablePath,fillTube,VERSION:3});if(typeof module!=='undefined'&&module.exports)module.exports=root.RepairShopProbes;
})(typeof globalThis!=='undefined'?globalThis:this);
