/* The same assembled product throughout the chapter; scene uses actual contacts. */
(function(){
 'use strict';const T=window.TrainingThree,P=window.TrainingGamePackages;
 function create(canvas,onPick){
  const renderer=new T.WebGLRenderer({canvas,antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.toneMapping=T.ACESFilmicToneMapping;
  const scene=new T.Scene(),world=new T.Group(),parts=new T.Group(),flows=new T.Group(),camera=new T.PerspectiveCamera(35,1,.1,80);scene.add(world);world.add(parts,flows);
  scene.add(new T.HemisphereLight(0xffffff,0x355566,1.8));const sun=new T.DirectionalLight(0xffffff,2.4);sun.position.set(-4,8,5);scene.add(sun);
  const lampLight=new T.PointLight(0xffc766,0,7);lampLight.position.set(2.7,1.5,-.1);world.add(lampLight);
  const pcbMap=new T.Texture();pcbMap.colorSpace=T.SRGBColorSpace;const pcbImage=new Image();pcbImage.onload=()=>{if(live){pcbMap.image=pcbImage;pcbMap.needsUpdate=true;canvas.dataset.textureLoaded='true';draw(0);}};pcbImage.src=window.TrainingPlaygroundAssets.pcb;
  const v=p=>new T.Vector3(...p),Y=.08;let live=true,key='',yaw=.15,elevation=.86,distance=13,phase=0,flowKind='',markers=[],glowing=[],maps=[],contacts=[],currentState=null,halo=null;
  function mesh(g,m,p,group=parts){const n=new T.Mesh(g,m);n.position.set(...p);group.add(n);return n;}
  function mat(c,extra={}){return new T.MeshStandardMaterial({color:c,roughness:.42,metalness:.12,...extra});}
  function box(p,size,c,group=parts){return mesh(new T.BoxGeometry(...size),mat(c),p,group);}
  function rod(a,b,r,c,group=parts,basic=false){const d=v(b).sub(v(a));if(d.length()<1e-8)return;const n=mesh(new T.CylinderGeometry(r,r,d.length(),10),basic?new T.MeshBasicMaterial({color:c}):mat(c),v(a).add(v(b)).multiplyScalar(.5).toArray(),group);n.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return n;}
  function wire(points,color=0xb9daca){for(let i=1;i<points.length;i++)rod(points[i-1],points[i],.028,color);}
  function text(label,p,w=.8,h=.24,group=parts,rotation){const c=document.createElement('canvas');c.width=512;c.height=128;const ctx=c.getContext('2d');ctx.font='600 82px Segoe UI';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#ffffff';ctx.fillText(label,256,64,490);const map=new T.CanvasTexture(c);map.colorSpace=T.SRGBColorSpace;maps.push(map);const m=mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map,transparent:true,depthWrite:false,side:T.DoubleSide}),p,group);m.rotation.set(...(rotation||[-Math.PI/2,0,0]));return m;}
  function purge(group){const geometries=new Set(),materials=new Set();group.traverse(n=>{if(n.geometry)geometries.add(n.geometry);if(n.material)materials.add(n.material);});group.clear();geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());}
  function pack(id,center,scale=1,angle=0,params={}){
   const data=P.build(id,params),group=new T.Group();group.position.set(center[0],.10,center[1]);group.scale.setScalar(scale);group.rotation.y=angle;parts.add(group);
   for(const q of data.items){let n;if(q.type==='box'){n=box(q.p,q.size,q.c,group);if(q.rotation)n.rotation.set(...q.rotation);}else if(q.type==='rod')n=rod(q.a,q.b,q.r,q.c,group);else n=text(q.text,q.p,q.w,q.h,group,q.rotation);if(n)n.userData.packagePart=q.part;}
   const pins=data.layout.pins.map(pin=>({...pin,point:v(pin.point).multiplyScalar(scale).applyAxisAngle(new T.Vector3(0,1,0),angle).add(new T.Vector3(center[0],.10,center[1])).toArray()}));
   for(const p of pins)box([p.point[0],.0825,p.point[2]],[p.pad[0]*scale+.10,.035,p.pad[2]*scale+.10],0xbca665);
   contacts.push({id,pins,seating:P.inspectContacts(group,T.Vector3,.10,data.layout.throughHole)});return pins;
  }
  function hotspot(name,p,size){const n=box(p,size,0x9bc4ed);n.material.transparent=true;n.material.opacity=.25;n.userData.pick=name;return n;}
  let supplyPath=[],capPath=[];
  function rebuild(s){
   purge(parts);maps.forEach(m=>m.dispose());maps=[];contacts=[];glowing=[];
   mesh(new T.BoxGeometry(8,.13,4.8),mat(0x9cafa1,{map:pcbMap}),[0,-.02,0]);for(const [x,z] of [[-3.7,-2.1],[3.7,-2.1],[-3.7,2.1],[3.7,2.1]]){const n=mesh(new T.TorusGeometry(.14,.04,8,20),mat(0xd6c89a),[x,Y,z]);n.rotation.x=-Math.PI/2;}
   box([-3,.31,0],[1,.45,1.4],s.power?0x243e56:0x687789);text(!s.power?'断电':s.reverse?'−5 V':'5 V',[-3,.545,0]);rod([-3.5,.2,-.4],[-4.8,.2,-.4],.065,0xe65150);rod([-3.5,.2,.5],[-4.8,.2,.5],.065,0x344657);
   const start=[-3,Y,-.72],a=[-2.35,Y,-1.2],k=[-1.25,Y,-1.2],rail=[-1,Y,-1.2];wire([start,[-3,Y,-1.2],a]);
   if(s.diode!=='none'){
    const pins=pack('dio-schottky',[-1.8,-1.2],.72,s.diode==='backward'?Math.PI:0),sorted=[...pins].sort((x,y)=>x.point[0]-y.point[0]);wire([a,sorted[0].point]);wire([sorted[1].point,k]);
   }else wire([a,k]);wire([k,rail]);text(s.index>=2?'D1 · A / K':'预留保护位置',[-1.8,.11,-1.8],1.25,.22);
   let rLeft=[-.4,Y,-1.2],rRight=[.65,Y,-1.2];
   if(s.resistance!==null){const pins=pack('res-thick',[.1,-1.2],.70,0,{marking:s.resistance===100?'101':s.resistance===330?'331':'102'});rLeft=pins[0].point;rRight=pins[1].point;}
   hotspot('resistance',[.1,.073,-1.2],[1.35,.015,.8]);text('R1',[.1,.11,-1.8],.6,.22);wire([rail,rLeft]);
   const ledPins=pack('dio-led',[2.65,-.05],.65),ledA=ledPins.find(p=>p.role==='A').point,ledK=ledPins.find(p=>p.role==='K').point;
   wire([rRight,[ledA[0],Y,-1.2],ledA]);
   const shade=mat(0xffe4ad,{transparent:true,opacity:.86,emissive:0xffaa35,emissiveIntensity:0});glowing.push(shade);
   mesh(new T.CylinderGeometry(.44,.66,.8,32,1,true),shade,[2.65,1.15,-.05]);mesh(new T.SphereGeometry(.44,24,12,0,Math.PI*2,0,Math.PI/2),shade,[2.65,1.55,-.05]);
   halo=mesh(new T.SphereGeometry(.92,24,16),new T.MeshBasicMaterial({color:0xffbf62,transparent:true,opacity:0,depthWrite:false}),[2.65,1.15,-.05]);
   rod([2.65,.75,-.05],[2.65,.47,-.05],.045,0xa9b6b9);text('小夜灯',[2.65,.11,-.85],1,.23);
   let loadReturn=[ledK,[3.15,Y,.5],[3.15,Y,1.95]];
   if(s.index===4){
    hotspot('mos',[2,.073,1.3],[1.25,.015,1.25]);
    if(s.mos){const pins=pack('mos-n',[2,1.3],.72),drain=pins.find(p=>p.role==='D').point,source=pins.find(p=>p.role==='S').point,gate=pins.find(p=>p.role==='G').point;loadReturn=[ledK,[3.15,Y,.5],[drain[0],Y,.5],drain,[2,.60,1.3],source,[source[0],Y,1.95]];wire([ledK,[3.15,Y,.5],[drain[0],Y,.5],drain]);wire([source,[source[0],Y,1.95]]);wire([gate,[.95,Y,gate[2]]],0x66c79f);for(const p of pins)text(p.role,[p.point[0],.11,p.point[2]+(p.role==='D'?-.19:.19)],.18,.19);}
    else{wire([ledK,[3.15,Y,.5],[2,Y,.5],[2,Y,.88]]);wire([[2.35,Y,1.73],[2.35,Y,1.95]]);}
    box([.75,.23,1.65],[.65,.28,.6],s.gate?0x2fa4de:0x536678);hotspot('button',[.75,.39,1.65],[.65,.04,.6]);text('按钮 · 控制',[.55,.11,2.13],1.25,.22);
   }else wire(loadReturn);
   wire([[3.15,Y,1.95],[-3,Y,1.95],[-3,Y,.72]]);if(s.index===4&&s.mos)wire([loadReturn[loadReturn.length-1],[3.15,Y,1.95]]);
   const cp=[-.8,Y,-1.2],cn=[-.8,Y,1.95];let positive=cp,negative=cn;
   if(s.capacitance>0){const pins=pack('cap-aluminum',[-.8,.55],.52,-Math.PI/2);positive=pins.find(p=>p.role==='+').point;negative=pins.find(p=>p.role==='−').point;wire([cp,positive]);wire([negative,cn]);text('C1 · '+Math.round(s.capacitance*1e6)+' µF',[-.8,.11,1.43],1.65,.24);}
   if(s.index===3)hotspot('capacitance',[-.8,.073,.55],[1.1,.015,1.1]);if(s.index===2)hotspot('diode',[-1.8,.073,-1.2],[1.4,.015,.85]);
   const rPath=[rLeft,[.1,.35,-1.2],rRight,[ledA[0],Y,-1.2],ledA,[2.65,.6,-.05],...loadReturn];
   supplyPath=[start,[-3,Y,-1.2],a,[-1.8,.35,-1.2],k,rail,...rPath,[-3,Y,1.95],[-3,Y,.72]];
   capPath=[positive,cp,...rPath,[-.8,Y,1.95],negative];canvas.dataset.contacts=JSON.stringify(contacts);canvas.dataset.product='nightlight';
  }
  function sample(points,u){const lengths=points.slice(1).map((p,i)=>v(p).distanceTo(v(points[i]))),total=lengths.reduce((a,b)=>a+b,0);let left=u*total;for(let i=0;i<lengths.length;i++){if(left<=lengths[i]||i===lengths.length-1)return {point:v(points[i]).lerp(v(points[i+1]),left/Math.max(lengths[i],1e-8)),direction:v(points[i+1]).sub(v(points[i])).normalize()};left-=lengths[i];}return {point:v(points[0]),direction:new T.Vector3(1,0,0)};}
  function update(s,r){currentState=s;const next=[s.index,s.resistance,s.diode,s.capacitance,s.mos,s.gate,s.reverse,s.power].join('|');if(next!==key){key=next;rebuild(s);}
   glowing.forEach(m=>{m.emissiveIntensity=r.brightness*3.5;m.color.setHex(0x81796b).lerp(new T.Color(0xffdca0),r.brightness);});lampLight.intensity=r.brightness*3;if(halo)halo.material.opacity=r.brightness*.15;
   const kind=r.current>1e-9&&!r.unknown?r.source:'off';if(kind!==flowKind){flowKind=kind;phase=0;purge(flows);markers=[];if(kind!=='off')for(let i=0;i<7;i++){const n=mesh(new T.CylinderGeometry(0,.075,.22,8),new T.MeshBasicMaterial({color:kind==='capacitor'?0xed9c24:0x46b7ff}),[0,0,0],flows);markers.push(n);}}
   canvas.dataset.current=String(r.current);canvas.dataset.brightness=String(r.brightness);canvas.dataset.flowSource=kind;draw(0);
  }
  function draw(dt){if(!live)return;phase+=dt*.26;const path=flowKind==='capacitor'?capPath:supplyPath;markers.forEach((m,i)=>{const age=phase-i*.12;m.visible=age>=0;if(m.visible){const p=sample(path,age%1);m.position.copy(p.point);m.position.y+=.10;m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),p.direction);}});camera.position.set(Math.sin(yaw)*Math.cos(elevation)*distance,Math.sin(elevation)*distance,Math.cos(yaw)*Math.cos(elevation)*distance);camera.lookAt(0,.45,0);renderer.render(scene,camera);canvas.dataset.phase=String(phase);canvas.dataset.frames=String(Number(canvas.dataset.frames||0)+1);}
  function resize(){const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;camera.aspect=r.width/r.height;camera.updateProjectionMatrix();distance=11*Math.max(1,1.6/camera.aspect);renderer.setSize(r.width,r.height,false);draw(0);}
  const observer=new ResizeObserver(resize);observer.observe(canvas);const raycaster=new T.Raycaster();let down=null,moved=false;
  const begin=e=>{canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);down={x:e.clientX,y:e.clientY};moved=false;};
  const move=e=>{if(!down)return;const dx=e.clientX-down.x,dy=e.clientY-down.y;if(Math.abs(dx)+Math.abs(dy)>2)moved=true;yaw+=dx*.006;elevation=Math.max(.35,Math.min(1.2,elevation+dy*.004));down={x:e.clientX,y:e.clientY};draw(0);};
  const end=e=>{if(down&&!moved){const r=canvas.getBoundingClientRect();raycaster.setFromCamera(new T.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(parts.children,true).find(i=>i.object.userData.pick);if(hit)onPick(hit.object.userData.pick);}down=null;};
  const keyboard=e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','0','Enter',' '].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft')yaw-=.12;if(e.key==='ArrowRight')yaw+=.12;if(e.key==='ArrowUp')elevation=Math.min(1.2,elevation+.08);if(e.key==='ArrowDown')elevation=Math.max(.35,elevation-.08);if(e.key==='0'){yaw=.15;elevation=.86;}if(e.key==='Enter'||e.key===' ')onPick(currentState.index===4?'button':['resistance','resistance','diode','capacitance'][currentState.index]);draw(0);}};
  canvas.addEventListener('pointerdown',begin);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',()=>{down=null;});canvas.addEventListener('keydown',keyboard);
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();live=false;canvas.dispatchEvent(new CustomEvent('nightlight-context-lost'));});canvas.addEventListener('webglcontextrestored',()=>{live=true;draw(0);});
  return {update,draw,resize,snapshot:()=>({contacts,phase,flowKind,renderer:'WebGL'}),dispose:()=>{live=false;observer.disconnect();purge(parts);purge(flows);maps.forEach(m=>m.dispose());pcbMap.dispose();renderer.dispose();}};
 }
 window.TrainingNightlightScene=Object.freeze({create});
})();
