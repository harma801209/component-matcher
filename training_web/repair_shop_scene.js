/* Real, on-demand WebGL scene. Visual picking never changes circuit parameters.
 * Enlarged package illustrations, not OEM CAD or a PCB routing netlist.
 */
(function(root){
 'use strict';
 const layouts={lamp:[[-2.5,-.75],[-.1,-.75],[2.5,.75]],fan:[[-2.5,-1],[.2,.8],[2.6,-.8]],speaker:[[-2.5,-1],[-.1,.8],[2.55,.7]],clock:[[2.5,.65],[0,-1],[-2.5,.65]],sensor:[[-2.5,-.8],[0,.8],[2.5,-.8]],router:[[-2.5,-1],[.1,-.8],[2.5,.8]]};
 function create(canvas,product,onPick,cameraState){
  const T=root.TrainingThree,P=root.TrainingGamePackages;if(!T||!P)throw new Error('3D runtime unavailable');
  const renderer=new T.WebGLRenderer({canvas,alpha:true,antialias:true});renderer.setPixelRatio(Math.min(root.devicePixelRatio||1,2));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
  const scene=new T.Scene(),world=new T.Group(),camera=new T.PerspectiveCamera(38,1,.1,70);scene.add(world);
  scene.add(new T.HemisphereLight(0xfff8e8,0x658477,2.5));const sun=new T.DirectionalLight(0xffffff,3);sun.position.set(-3,8,5);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-6;sun.shadow.camera.right=6;sun.shadow.camera.top=5;sun.shadow.camera.bottom=-5;sun.shadow.normalBias=.025;scene.add(sun);
  let disposed=false,lost=false,yaw=cameraState?.yaw??-.28,elevation=cameraState?.elevation??.92,zoom=cameraState?.zoom??1,selected=null,frames=0,dragged=false,travel=0,gesture=null;
  const nodes={},textures=[],materials=new Set(),geometries=new Set(),pointers=new Map(),positions=layouts[product.id];
  const material=(color,extra={})=>{const m=new T.MeshStandardMaterial({color,roughness:.45,metalness:.12,...extra});materials.add(m);return m;};
  function mesh(g,m,p,group=world){geometries.add(g);materials.add(m);const n=new T.Mesh(g,m);n.position.set(...p);n.castShadow=true;n.receiveShadow=true;group.add(n);return n;}
  const box=(p,size,color,group=world)=>mesh(new T.BoxGeometry(...size),material(color),p,group);
  const vec=p=>new T.Vector3(...p);
  function rod(a,b,r,color,group=world){const d=vec(b).sub(vec(a)),n=mesh(new T.CylinderGeometry(r,r,d.length(),12),material(color,{metalness:.5,roughness:.3}),vec(a).add(vec(b)).multiplyScalar(.5).toArray(),group);n.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return n;}
  function print(text,p,w=1.2,h=.25,group=world,color='#f4f5d6'){
   const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d');ctx.font='bold 76px Segoe UI, sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=color;ctx.fillText(text,256,64,495);
   const map=new T.CanvasTexture(c);map.colorSpace=T.SRGBColorSpace;textures.push(map);const m=new T.MeshBasicMaterial({map,transparent:true,depthWrite:false,side:T.DoubleSide});const n=mesh(new T.PlaneGeometry(w,h),m,p,group);n.rotation.x=-Math.PI/2;n.castShadow=false;n.receiveShadow=false;return n;
  }
  // A green fallback renders immediately; texture completion explicitly redraws.
  const fallback=document.createElement('canvas');fallback.width=fallback.height=2;const ctx=fallback.getContext('2d');ctx.fillStyle='#27994f';ctx.fillRect(0,0,2,2);
  const pcbMap=new T.Texture(fallback);pcbMap.colorSpace=T.SRGBColorSpace;pcbMap.needsUpdate=true;textures.push(pcbMap);
  const image=new Image();image.onload=()=>{if(disposed)return;pcbMap.dispose();pcbMap.image=image;pcbMap.needsUpdate=true;canvas.dataset.textureLoaded='true';draw();};image.src=root.TrainingPlaygroundAssets?.pcb||'';
  const shape=new T.Shape();shape.moveTo(-4,-2.5);shape.lineTo(4,-2.5);shape.lineTo(4,2.5);shape.lineTo(-4,2.5);shape.lineTo(-4,-2.5);
  for(const [x,z] of [[-3.65,-2.15],[3.65,-2.15],[-3.65,2.15],[3.65,2.15]]){const hole=new T.Path();hole.absarc(x,z,.13,0,Math.PI*2,true);shape.holes.push(hole);const ring=mesh(new T.TorusGeometry(.18,.045,10,24),material(0xd5bd72,{metalness:.6}),[x,.015,-z]);ring.rotation.x=-Math.PI/2;}
  const board=mesh(new T.ExtrudeGeometry(shape,{depth:.12,bevelEnabled:false}),material(0xffffff,{map:pcbMap,roughness:.72,metalness:.02}),[0,-.12,0]);board.rotation.x=-Math.PI/2;
  const ground=mesh(new T.PlaneGeometry(25,25),new T.ShadowMaterial({opacity:.16}),[0,-.35,0]);ground.rotation.x=-Math.PI/2;ground.castShadow=false;
  print('FRUITION · REPAIR LAB',[0,.025,-2.14],3.5,.24);print(product.name+' · 位置示意',[0,.025,2.12],3.5,.22);
  // Peripheral connectors are visual only, not undeclared electrical branches.
  box([-3.85,.15,.1],[.45,.3,.95],0xb4bfc1);box([-4.08,.15,.1],[.02,.14,.58],0x26363a);
  const silver=0xc6cfd0,pads=(x,z)=>box([x,.02,z],[.35,.04,.38],0xd1b77a);
  function custom(part,g){
   if(part.type==='fuse'){
    box([0,.24,0],[1.15,.38,.5],0xe4e4cd,g);for(const x of [-.62,.62]){box([x,.12,0],[.23,.24,.54],silver,g);pads(g.position.x+x,g.position.z);}print('0.5A',[0,.439,0],.8,.2,g,'#49534d');
   }else if(part.type==='diode'&&part.led){
    // Through-hole, domed red LED, not the unrelated SMD MiniLED geometry.
    const lens=material(0xb72e24,{roughness:.22,transparent:true,opacity:.88,emissive:0xd93b16,emissiveIntensity:0});nodes[part.id].lens=lens;
    mesh(new T.CylinderGeometry(.36,.36,.6,28),lens,[0,.65,0],g);mesh(new T.SphereGeometry(.36,28,18,0,Math.PI*2,0,Math.PI/2),lens,[0,.95,0],g);mesh(new T.CylinderGeometry(.42,.42,.1,28),material(0x9f3027),[0,.31,0],g);
    for(const x of [-.2,.2]){rod([x,-.16,0],[x,.46,0],.035,silver,g);pads(g.position.x+x,g.position.z);}print('A    K',[0,.03,.63],.9,.2,g);
   }else if(part.type==='diode'){
    box([0,.3,0],[1.05,.5,.55],0x333b3e,g);for(const x of [-.61,.61]){box([x,.07,0],[.3,.14,.32],silver,g);pads(g.position.x+x,g.position.z);}box([.28,.557,0],[.14,.012,.55],0xdddfcb,g);print('K',[.55,.035,.5],.3,.2,g);
   }else if(part.type==='ldo'){
    box([0,.34,0],[1.15,.5,.68],0x303b40,g);for(const [i,x,z] of [[1,-.42,.57],[2,0,.57],[3,.42,.57],[4,.42,-.57],[5,-.42,-.57]]){rod([x,.045,z],[x,.26,Math.sign(z)*.3],.045,silver,g);pads(g.position.x+x,g.position.z+z);print(String(i),[x,.035,z*1.55],.18,.18,g);}print('3V3',[0,.597,0],.78,.2,g);
   }else if(part.type==='crystal'){
    rod([-.65,.42,0],[.65,.42,0],.25,0xc2c7c4,g);for(const z of [-.13,.13]){rod([.65,.42,z],[1,.03,z],.03,silver,g);pads(g.position.x+1,g.position.z+z);}
   }
  }
  product.parts.forEach((part,i)=>{
   const [x,z]=positions[i],group=new T.Group();group.position.set(x,.04,z);world.add(group);nodes[part.id]={group,center:[x,.55,z]};
   const packageId={resistor:'res-thick',capacitor:'cap-aluminum',ceramic:'cap-mlcc',mos:'mos-n',inductor:'ind-molded'}[part.type];
   if(packageId){const data=P.build(packageId,{marking:part.type==='resistor'?(part.value===220?'221':part.value===4700?'472':'103'):undefined});
    for(const q of data.items){let n;if(q.type==='box'){n=box(q.p,q.size,q.c,group);if(q.rotation)n.rotation.set(...q.rotation);}else if(q.type==='rod')n=rod(q.a,q.b,q.r,q.c,group);else n=print(q.text,q.p,q.w,q.h,group,q.c);if(n&&q.rotation)n.rotation.set(...q.rotation);}
    for(const pin of data.layout.pins)pads(x+pin.point[0],z+pin.point[2]);
   }else custom(part,group);
   group.traverse(n=>{if(n.isMesh)n.userData.pick=part.id;});
   print(part.id,[x,.03,z+1.03],.6,.29);print(part.pkg,[x,.03,z+1.36],1.4,.18);
   const ring=mesh(new T.TorusGeometry(.86,.025,8,48),new T.MeshBasicMaterial({color:0xe6bd61}),[x,.07,z]);ring.rotation.x=-Math.PI/2;ring.visible=false;nodes[part.id].ring=ring;
  });
  function draw(){if(disposed||lost)return;const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;camera.aspect=r.width/r.height;camera.updateProjectionMatrix();const distance=11.2*Math.max(1,1.25/camera.aspect)*zoom;camera.position.set(Math.sin(yaw)*Math.cos(elevation)*distance,Math.sin(elevation)*distance,Math.cos(yaw)*Math.cos(elevation)*distance);camera.lookAt(0,.2,0);renderer.render(scene,camera);canvas.dataset.frames=String(++frames);canvas.dataset.renderer='WebGL';canvas.dataset.yaw=String(yaw);canvas.dataset.zoom=String(zoom);}
  function resize(){const r=canvas.getBoundingClientRect();if(disposed||!r.width||!r.height)return;renderer.setSize(r.width,r.height,false);draw();}
  function update(id,state){selected=id;for(const [key,n] of Object.entries(nodes))n.ring.visible=key===id;const lens=Object.values(nodes).find(n=>n.lens)?.lens;if(lens)lens.emissiveIntensity=state.power?Math.min(1.8,Math.max(0,state.current||0)*85):0;draw();}
  const reset=()=>{yaw=-.28;elevation=.92;zoom=1;draw();};
  const ray=new T.Raycaster();
  function pick(x,y){const r=canvas.getBoundingClientRect();ray.setFromCamera(new T.Vector2((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1),camera);const hit=ray.intersectObjects(world.children,true).find(h=>h.object.userData.pick);if(hit)onPick(hit.object.userData.pick);}
  const down=e=>{canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===1){dragged=false;travel=0;}else dragged=true;gesture=null;};
  const move=e=>{const prior=pointers.get(e.pointerId);if(!prior)return;const dx=e.clientX-prior.x,dy=e.clientY-prior.y;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===2){const a=[...pointers.values()],d=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);if(gesture&&d>1)zoom=Math.max(.68,Math.min(1.8,zoom*gesture/d));gesture=d;dragged=true;}else{travel+=Math.hypot(dx,dy);if(travel>5)dragged=true;yaw+=dx*.007;elevation=Math.max(.28,Math.min(1.4,elevation+dy*.005));}draw();};
  const up=e=>{if(pointers.has(e.pointerId)&&!dragged&&pointers.size===1)pick(e.clientX,e.clientY);pointers.delete(e.pointerId);gesture=null;};
  const cancel=e=>{pointers.delete(e.pointerId);gesture=null;};
  const wheel=e=>{e.preventDefault();zoom=Math.max(.68,Math.min(1.8,zoom*Math.exp(e.deltaY*.001)));draw();};
  const key=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(e.key))return;e.preventDefault();if(e.key==='0')return reset();if(e.key==='ArrowLeft')yaw-=.13;if(e.key==='ArrowRight')yaw+=.13;if(e.key==='ArrowUp')elevation=Math.min(1.4,elevation+.1);if(e.key==='ArrowDown')elevation=Math.max(.28,elevation-.1);if(['+','='].includes(e.key))zoom=Math.max(.68,zoom*.9);if(e.key==='-')zoom=Math.min(1.8,zoom/ .9);draw();};
  const lostContext=e=>{e.preventDefault();lost=true;canvas.dataset.contextLost='true';},restored=()=>{lost=false;canvas.dataset.contextLost='false';draw();};
  for(const [type,fn] of [['pointerdown',down],['pointermove',move],['pointerup',up],['pointercancel',cancel],['keydown',key],['webglcontextlost',lostContext],['webglcontextrestored',restored]])canvas.addEventListener(type,fn);
  canvas.addEventListener('wheel',wheel,{passive:false});const observer=new ResizeObserver(resize);observer.observe(canvas);
  function snapshot(){const r=canvas.getBoundingClientRect();return {renderer:'WebGL',frames,disposed,lost,yaw,elevation,zoom,selected,product:product.id,meshCount:geometries.size,projections:Object.fromEntries(Object.entries(nodes).map(([id,n])=>{const v=vec(n.center).project(camera);return [id,{x:(v.x+1)/2*r.width,y:(1-v.y)/2*r.height}];}))};}
  return {update,resize,reset,snapshot,dispose:()=>{if(disposed)return;disposed=true;image.onload=null;observer.disconnect();for(const [type,fn] of [['pointerdown',down],['pointermove',move],['pointerup',up],['pointercancel',cancel],['keydown',key],['webglcontextlost',lostContext],['webglcontextrestored',restored],['wheel',wheel]])canvas.removeEventListener(type,fn);geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());renderer.dispose();renderer.forceContextLoss();}};
 }
 const api=Object.freeze({create,layout:id=>layouts[id].map(p=>[...p])});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopScene=api;
})(typeof globalThis!=='undefined'?globalThis:this);
