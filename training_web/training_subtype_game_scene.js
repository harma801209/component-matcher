/* Live 3D boards: seven connection types, real component meshes and moving signals. */
(function(){
 'use strict';const T=window.TrainingThree,M=window.TrainingSubtypeGameMath,C=window.TrainingCatalog;
 function create(canvas,id,onPick){
  const d=M.profile(id),chapter=C.lesson(id),renderer=new T.WebGLRenderer({canvas,alpha:true,antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,.1,70),world=new T.Group();scene.add(world);
  scene.add(new T.HemisphereLight(0xe9f3ff,0x41604f,3));const sun=new T.DirectionalLight(0xffffff,3);sun.position.set(-3,8,5);scene.add(sun);
  const room=new T.RoomEnvironment(),pm=new T.PMREMGenerator(renderer),env=pm.fromScene(room,.04);scene.environment=env.texture;room.dispose();pm.dispose();
  const map=new T.Texture();map.colorSpace=T.SRGBColorSpace;const image=new Image();image.onload=()=>{map.image=image;map.needsUpdate=true;};image.src=window.TrainingPlaygroundAssets.pcb;
  const solid=new T.Group(),moving=new T.Group();world.add(solid,moving);
  let key='',textures=[],markers=[],hot=null,indicator=null,fieldRing=null,lightMaterials=[],waves=[],result=null,params=null,running=false,clockPhase=0,azimuth=.35,elevation=.8,distance=12,alive=true,disposed=false;
  const ledLight=new T.PointLight(0x409aff,0,3);world.add(ledLight);
  const V=p=>new T.Vector3(...p),color=rgb=>new T.Color().setRGB(rgb[0]/255,rgb[1]/255,rgb[2]/255,T.SRGBColorSpace);
  const mat=(c,extra={})=>new T.MeshStandardMaterial({color:c,roughness:.42,metalness:.15,...extra});
  function add(g,m,p,group=solid){const o=new T.Mesh(g,m);o.position.set(...p);group.add(o);return o;}
  const box=(p,s,c,group=solid,extra={})=>add(new T.BoxGeometry(...s),mat(c,extra),p,group);
  function rod(a,b,r,c,group=solid){const delta=V(b).sub(V(a)),o=add(new T.CylinderGeometry(r,r,delta.length(),8),mat(c),V(a).add(V(b)).multiplyScalar(.5).toArray(),group);o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());return o;}
  function wire(points,c=0x8cbbb0){for(let i=1;i<points.length;i++)rod(points[i-1],points[i],.028,c);}
  function label(text,p,w=1.2,h=.27,c='#f5fbff'){
   const img=document.createElement('canvas');img.width=640;img.height=120;const ctx=img.getContext('2d');ctx.font='600 78px Microsoft YaHei,Segoe UI,sans-serif';const measured=ctx.measureText(text).width;ctx.font='600 '+Math.min(78,78*580/Math.max(1,measured))+'px Microsoft YaHei,Segoe UI,sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=c;ctx.fillText(text,320,60);
   const texture=new T.CanvasTexture(img);texture.colorSpace=T.SRGBColorSpace;textures.push(texture);const o=add(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,side:T.DoubleSide}),p);o.rotation.x=-Math.PI/2;return o;
  }
  function purge(group){const gs=new Set(),ms=new Set();group.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])ms.add(m);});group.clear();gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());}
  function component(pos){
   const group=new T.Group();group.position.set(...pos);group.scale.setScalar(.52);solid.add(group);
   window.TrainingCatalogGeometry.build(id,'exterior',0,{
    box(f,p,s,c,part){const mesh=box(p,s,color(c),group);if(id==='dio-led'&&part==='case')mesh.material.color.setHex(0x335465);f.push({});},tube(f,a,b,r,c){rod(a,b,r,color(c),group);f.push({});}
   });
   if(id==='cap-tantalum'){const sign=params.forward?-1:1;box([pos[0]+sign*.53,pos[1]+.338,pos[2]-.026],[.12,.009,.73],0x5b3c1b);label('+',[pos[0]+sign*.36,pos[1]+.345,pos[2]-.026],.25,.25,'#5b3c1b');canvas.dataset.positiveSide=params.forward?'left':'right';}
   if(id==='ind-common'&&!params.installed)group.traverse(o=>{if(o.material){o.material.transparent=true;o.material.opacity=.22;o.material.depthWrite=false;}});
   if(['res-thin','res-sulfur'].includes(id))label(id==='res-thin'?'1001':'102',[pos[0],pos[1]+.316,pos[2]-.026],.7,.23);
   if(id==='dio-led'){const lens=mat(0x12305b,{emissive:0x348fff,emissiveIntensity:0,transparent:true,opacity:.92,roughness:.18});add(new T.SphereGeometry(.30,24,14,0,Math.PI*2,0,Math.PI/2),lens,[pos[0],pos[1]+.33,pos[2]]);lightMaterials.push(lens);ledLight.position.set(pos[0],pos[1]+.7,pos[2]);}
   label(chapter.title,[pos[0],.10,pos[2]+.88],1.7,.25);
   const socket=box([pos[0],.025,pos[2]],[1.8,.045,1.35],0x276ded,solid,{emissive:0x1555e8,emissiveIntensity:.2});socket.userData.subtypeSocket=true;
   const halo=add(new T.TorusGeometry(.83,.055,8,44),new T.MeshBasicMaterial({color:0xef7a35,transparent:true,opacity:0}),[pos[0],.045,pos[2]]);halo.rotation.x=-Math.PI/2;hot=halo;
  }
  function chip(pos,name='负载 / IC'){
   box(pos,[1.05,.35,.95],0x253a50);for(const x of [-.62,.62])for(let i=0;i<4;i++)box([pos[0]+x,.08,pos[2]-.3+i*.2],[.27,.07,.085],0xb6c5cf);
   label(name,[pos[0],pos[1]+.185,pos[2]],.96,.28);indicator=box([pos[0]+.33,pos[1]+.20,pos[2]-.3],[.12,.06,.12],0x315a45,solid,{emissive:0x36e883,emissiveIntensity:0});
  }
  function makeWave(){
   const positions=new Float32Array(81*3);for(const c of [d.topology==='clock'?0xe6b23f:0x258bff,d.topology==='clock'?0x42e8a4:0xf39934]){
    const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(positions.slice(),3));const line=new T.Line(g,new T.LineBasicMaterial({color:c}));solid.add(line);waves.push(line);
   }
   label(d.topology==='clock'?'时钟慢放 / 频差放大':id==='ind-layered'?'理想RL交流慢放':'交流半周慢放',[.1,.06,2.12],2.5,.24);
  }
  const top=-1.35,bottom=1.65,y=.11,left=-2.8,right=2.8;
  const loop=[[left,y,top],[-.75,.46,top+.3],[.75,.46,top+.3],[right,y,top],[right,y,.45],[right,y,bottom],[left,y,bottom],[left,y,.55]];
  const railLoop=[[left,y,top],[right,y,top],[right,y,.45],[right,y,bottom],[left,y,bottom],[left,y,.55]];
  function rebuild(p){
   key=JSON.stringify(p);params=p;purge(solid);purge(moving);textures.forEach(t=>t.dispose());textures=[];markers=[];waves=[];hot=null;indicator=null;fieldRing=null;lightMaterials=[];canvas.dataset.partConnected=String(id!=='ind-common'||p.installed);
   box([0,-.09,0],[8,.16,5],0x8ca795,solid,{map,roughness:.58});for(const x of [-3.6,3.6])for(const z of [-2.1,2.1]){const ring=add(new T.TorusGeometry(.16,.04,8,24),mat(0xccb764),[x,.016,z]);ring.rotation.x=-Math.PI/2;}
   box([-3,.22,.04],[.96,.42,1.5],0x253b50);label(d.topology==='safety'?'虚拟 L / N':id==='dio-rectifier'?'5 V峰值 AC':chapter.family==='crystal'?'VDD / GND':chapter.family==='mos'?'12 V示例':id==='dio-zener'?p.input+' V':'电源',[-3,.44,.04],.85,.34);
   wire([[left,y,top],[left,y,-.68]]);wire([[left,y,.65],[left,y,bottom]]);
   if(d.topology==='parallel'){
    component([0,chapter.kind==='aluminum'?1.0:.78,.15]);chip([right,.28,.32]);wire(railLoop);
    // Two separate terminal leads; storage current never drawn through the dielectric.
    wire([[-.5,.38,.45],[-.5,y,top]]);wire([[.5,.38,.45],[.5,y,bottom]]);
    if(chapter.family==='diode'){box([-1.5,.2,top],[.5,.22,.35],0xd5bd85);label(id==='dio-zener'?p.series+' Ω':'Rs=2 Ω',[-1.5,.33,top],.72,.21);label('A→GND / K→输入',[0,.06,-.6],1.9,.22);}
   }else if(d.topology==='clock'){
    component([0,.78,top]);chip([right,.28,.20],'CLK输入');
    wire([[left,y,top],[-.8,y,top]],0x57a4e7);wire([[0,y,top+.4],[0,y,bottom],[left,y,bottom]],0x57a4e7);
    wire([[.8,y,top],[right,y,top],[right,y,.2]],0x57cfa1);wire([[right,y,.65],[right,y,bottom],[left,y,bottom]],0x6a99aa);
    if(id==='xtal-passive'){
     box([-1.75,.32,top],[.8,.35,.6],0x304863);label(p.amplifier?'振荡放大器':'未接放大器',[-1.75,.51,top],.76,.26);
     wire([[.8,y,top],[1.2,y,-.55],[-1.75,y,-.55],[-1.75,y,top+.32]],0xb8a253);label('晶体反馈支路',[.1,.06,-.42],1.8,.24);
     wire([[-1.3,y,top],[right,y,top],[right,y,.2]],0x57cfa1);
    }
    label('OUT ≠ 供电',[1.9,.06,-.8],1.4,.24);makeWave();
   }else if(d.topology==='switch-high'||d.topology==='switch-low'){
    const high=d.topology==='switch-high',device=high?[0,.78,top]:[right,.78,.2];component(device);chip(high?[right,.28,.2]:[0,.28,top],'受控负载');
    wire([[left,y,top],[-.75,y,top],[.75,y,top],[right,y,top],[right,y,bottom],[left,y,bottom],[left,y,.6]]);
    const ctrl=[-1.25,y,.75],target=[device[0]-.8,.4,device[2]+.2];box([ctrl[0],.2,ctrl[2]],[.8,.22,.6],0x416688);
    wire([ctrl,[ctrl[0],y,.3],target],chapter.family==='mos'?0xb994ef:0xf4ab53);wire([[ctrl[0],y,1.1],[ctrl[0],y,bottom]],0x89a69d);
    const beginnerMOS=['mos-n','mos-p'].includes(id);
    label(beginnerMOS?'G控制端：相对于S':chapter.family==='mos'?'G：相对S的驱动':'B：正确极性基流',[ctrl[0],.36,ctrl[2]],beginnerMOS?1.5:1.2,.23);
    label(beginnerMOS?(high?'供电侧：S接电源':'返回侧：S接返回端'):(high?'高边：S/E接电源':'低边：S/E接返回端'),[device[0],.07,device[2]-.7],2,.22);
    if(beginnerMOS){label('S参考端',high?[-.95,.12,top+.28]:[right,.12,1.05],.8,.22);label('D负载端',high?[.95,.12,top+.28]:[right,.12,-.65],.8,.22);}
    if(id==='mos-dual'||id==='bjt-darlington')label(id==='mos-dual'?'背靠背双N示例':'两级BJT示例',[0,.06,-.55],1.8,.23);
   }else if(d.topology==='common'){
    component([0,.82,-.4]);chip([right,.28,-.15],'双线端口');wire([[left,y,top],[right,y,top]]);wire([[left,y,.65],[right,y,.65]]);wire([[left,y,bottom],[right,y,bottom]],0x6a948b);
    label('独立线1',[1.6,.06,top+.3],.9,.23);label('独立线2',[1.6,.06,.98],.9,.23);label('参考回路 / 模式示意',[.1,.06,2.04],2.6,.23);
    fieldRing=add(new T.TorusGeometry(.76,.07,10,46),new T.MeshBasicMaterial({color:0xb57ae8,transparent:true,opacity:.12}),[0,.65,-.4]);fieldRing.rotation.x=-Math.PI/2;
   }else if(d.topology==='safety'){
    component([0,.78,.05]);chip([right,.28,-.05],'虚拟设备');wire([[left,y,top],[right,y,top]]);wire([[left,y,.75],[right,y,.75]]);wire([[left,y,bottom],[right,y,bottom]],0xbab177);
    wire([[-.5,.38,.25],[-.5,y,top]],0x86caaa);wire([[.5,.38,.25],[.5,y,p.position==='line'?.75:bottom]],0x86caaa);
    label('L',[-2.15,.06,top],.25,.23);label('N',[-2.15,.06,.75],.25,.23);label('PE等位置',[-2.1,.06,bottom],1,.23);label(p.category+'类位置示例',[.1,1.5,.05],1.3,.25,'#f0dd6e');
   }else{
    component([0,.78,top]);chip([right,.28,.28],id==='res-sense'?'测量负载':id==='dio-led'?'光输出':'负载 / IC');wire(loop);
    if(id==='res-sense')label('R'+String(p.resistance).padStart(3,'0'),[0,.847,top],.72,.22,'#4f4536');
    if(id==='res-sense'||id==='res-thin'){
     box([0,.18,.8],[1.3,.28,.65],0x466386);label('高阻测量输入',[0,.34,.8],1.2,.24);wire([[-.55,y,-.65],[-.55,y,.6]],0x77ddbc);wire([[.55,y,-.65],[.55,y,.6]],0x77ddbc);
    }
    if(id==='dio-led'){box([-1.55,.18,top],[.6,.18,.35],0x344355);label(p.resistance+' Ω',[-1.55,.29,top],.58,.20);label(p.forward?'A → K':'K → A',[0,.07,top+.9],1,.25);}
    if(id==='dio-rectifier'){label(p.forward?'正半周':'负半周',[0,.07,top+.85],1,.25);makeWave();}
    if(id==='ind-layered')makeWave();
    if(id==='res-sulfur'){label(p.design==='resistant'?'耐硫化声明示例':'普通声明示例',[0,.07,top+.8],1.8,.23);}
   }
   canvas.dataset.model=id;canvas.dataset.topology=d.topology;canvas.dataset.meshes=String(solid.children.length);
  }
  function pathMarker(points,c,kind,count=5){
   for(let i=0;i<count;i++){const mesh=add(new T.CylinderGeometry(0,.09,.25,8),new T.MeshBasicMaterial({color:c}),[0,0,0],moving);markers.push({mesh,points:points.map(p=>V([p[0],p[1]+.12,p[2]])),kind,index:i,count});}
  }
  function rebuildFlows(p,r,on){
   purge(moving);markers=[];if(!on)return;
   const v=r.visual;
   if(d.topology==='clock'){
    if(v.powered!==false)pathMarker([[left,y,top],[-.8,y,top],[0,y,top+.4],[0,y,bottom],[left,y,bottom],[left,y,.6]],0x258bff,'power',4);
    if(v.clock){pathMarker([[id==='xtal-passive'?-1.3:.8,y,top],[right,y,top],[right,y,.2]],0x43e8a4,'clock',5);}
   }else if(d.topology==='common'){
    pathMarker([[left,y,top],[right,y,top]],0x258bff,'current',5);pathMarker(v.common?[[left,y,.65],[right,y,.65]]:[[right,y,.65],[left,y,.65]],0xf3a43b,'current',5);
    if(v.common)pathMarker([[right,y,bottom],[left,y,bottom]],0x729cba,'current',4);
   }else if(d.topology==='safety'){
    // Mark the leads only; no conduction path through an insulating capacitor body.
    pathMarker([[left,y,top],[-.5,y,top],[-.5,.25,.25]],0x43c19a,'position',3);
   }else if(d.topology==='parallel'){
    if(v.known&&(v.current>0||['ripple','charge','discharge'].includes(v.flow)))pathMarker(railLoop,0x258bff,'current',5);
    if(v.flow==='discharge'&&v.known&&v.active)pathMarker([[-.5,.38,.45],[-.5,y,top],[right,y,top],[right,y,.45],[right,y,bottom],[.5,y,bottom],[.5,.38,.45]],0xf6a231,'storage',6);
    else if(v.flow==='ripple'||v.flow==='charge'){
     pathMarker([[left,y,top],[-.5,y,top],[-.5,.38,.45]],0xf6a231,'ripple',3);pathMarker([[.5,.38,.45],[.5,y,bottom],[left,y,bottom],[left,y,.55]],0xf6a231,'ripple',3);
    }else if(v.shunt>0)pathMarker([[-.5,y,top],[-.5,.38,.45],[.5,.38,.45],[.5,y,bottom],[left,y,bottom],[left,y,.55]],0xf6a231,'shunt',5);
   }else if(d.topology.startsWith('switch')){
    if(v.active&&v.known)pathMarker([[left,y,top],[-.75,y,top],[.75,y,top],[right,y,top],[right,y,bottom],[left,y,bottom],[left,y,.6]],0x258bff,'current',7);
    if(v.flow==='base'&&v.base>0){const high=d.topology==='switch-high';pathMarker(high?[[0,.4,top],[-.8,.35,top+.2],[-1.25,y,.3],[-1.25,y,bottom]]:[[-1.25,y,.75],[-1.25,y,.3],[right-.8,.4,.4],[right,y,bottom],[-1.25,y,bottom]],0xf6a231,'base',4);}
   }else if(v.known&&v.active){pathMarker(v.current<0?[...loop].reverse():loop,0x258bff,v.flow==='rectify'?'rectify':v.flow==='ac'?'ac':'current',6);}
   canvas.dataset.flowCount=String(markers.length);canvas.dataset.signalCount=String(markers.filter(m=>m.kind==='clock').length);canvas.dataset.storageThroughLoad=String(v.flow==='discharge'&&markers.some(m=>m.kind==='storage'));
  }
  let flowKey='';
  function update(p,r,on){
   if(key!==JSON.stringify(p)){rebuild(p);flowKey='';}result=r;params=p;running=on;
   const fk=JSON.stringify([p,r.visual.flow,r.visual.active,r.visual.known,r.visual.clock,r.visual.shunt,r.visual.powered,on]);if(fk!==flowKey){flowKey=fk;rebuildFlows(p,r,on);}
   const v=r.visual;if(indicator){indicator.material.emissiveIntensity=on&&v.active?v.brightness*1.8:0;indicator.material.color.setHex(v.warning?0xe3a443:0x315a45);}
   for(const material of lightMaterials)material.emissiveIntensity=on?v.brightness*3:0;ledLight.intensity=id==='dio-led'&&on?v.brightness*8:0;
   if(hot){hot.material.color.setHex(v.warning?0xffcb4d:0xef6335);hot.material.opacity=on?Math.max(v.warning?.65:0,Math.min(.8,v.heat*.7)):0;}
   if(fieldRing)fieldRing.material.opacity=on&&v.installed&&v.flux?.65:0;
   canvas.dataset.current=String(on&&v.known?(v.current||0):0);canvas.dataset.known=String(v.known);canvas.dataset.brightness=String(on&&v.active?v.brightness:0);canvas.dataset.heat=String(on?v.heat:0);canvas.dataset.running=String(on);
  }
  function sample(points,u){const lengths=points.slice(1).map((p,i)=>p.distanceTo(points[i])),total=lengths.reduce((a,b)=>a+b,0);let remaining=u*total;for(let i=0;i<lengths.length;i++){if(remaining<=lengths[i]||i===lengths.length-1)return {point:points[i].clone().lerp(points[i+1],remaining/lengths[i]),direction:points[i+1].clone().sub(points[i]).normalize()};remaining-=lengths[i];}}
  function draw(dt){
   if(!alive||disposed)return;clockPhase+=dt;
   const v=result?.visual||{};
   for(const m of markers){const rate=m.kind==='clock'?1+(v.offset||0)/1300*.2:1,at=(clockPhase*.28*rate+m.index/m.count)%1,currentPhase=clockPhase*Math.PI*2-(m.kind==='ac'?Math.atan2(result.values.reactance,100):0),reversed=['ripple','ac'].includes(m.kind)&&Math.sin(currentPhase)<0,s=sample(m.points,reversed?1-at:at);if(reversed)s.direction.negate();m.mesh.position.copy(s.point);m.mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),s.direction);
    const ac=Math.sin(clockPhase*Math.PI*2);m.mesh.visible=m.kind!=='rectify'||(params?.forward?ac>.14:ac<-.14);
    if(id==='dio-tvs'&&v.pulse)m.mesh.visible=clockPhase%3<.75;
   }
   if(waves.length){for(const [j,wave] of waves.entries()){const attr=wave.geometry.attributes.position;for(let i=0;i<81;i++){
     const x=(i/80-.5)*3.8,phase=i/80*Math.PI*4-clockPhase*Math.PI*2;
     let value;if(d.topology==='clock'){const speed=j?1+(v.offset||0)/1300*.2:1;value=running&&(!j||v.clock)?(Math.sin(i/80*Math.PI*4-clockPhase*Math.PI*2*speed)>0?.55:0):0;}
     else if(id==='ind-layered')value=!running?0:j?result.values.gain*Math.sin(phase-Math.atan2(result.values.reactance,100))*.5:Math.sin(phase)*.5;
     else{const input=5*Math.sin(phase);value=!running?0:j?(params.forward?Math.max(0,input-.7):Math.min(0,input+.7))/10:input/10;}
     attr.setXYZ(i,x,.09+(j?.012:0),1.42-value*.55);
    }attr.needsUpdate=true;}}
   camera.position.set(Math.sin(azimuth)*Math.cos(elevation)*distance,Math.sin(elevation)*distance,Math.cos(azimuth)*Math.cos(elevation)*distance);camera.lookAt(0,.1,0);renderer.render(scene,camera);
   canvas.dataset.frames=String(Number(canvas.dataset.frames||0)+1);canvas.dataset.flowPhase=String(clockPhase);canvas.dataset.yaw=String(azimuth);
  }
  function resize(){const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;camera.aspect=rect.width/rect.height;distance=12.7*Math.max(1,1.65/camera.aspect);camera.updateProjectionMatrix();renderer.setSize(rect.width,rect.height,false);draw(0);}
  const observer=new ResizeObserver(resize);observer.observe(canvas);
  const ray=new T.Raycaster(),pointer=new T.Vector2();function hit(x,y){const b=canvas.getBoundingClientRect();pointer.set((x-b.left)/b.width*2-1,-(y-b.top)/b.height*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(solid.children,true).some(o=>o.object.userData.subtypeSocket);}
  let down=null,moved=false;
  canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);down={x:e.clientX,y:e.clientY};moved=false;});
  canvas.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-down.x,dy=e.clientY-down.y;if(Math.abs(dx)+Math.abs(dy)>2)moved=true;azimuth+=dx*.006;elevation=Math.max(.35,Math.min(1.2,elevation+dy*.005));down={x:e.clientX,y:e.clientY};draw(0);});
  canvas.addEventListener('pointerup',e=>{if(down&&!moved&&hit(e.clientX,e.clientY))onPick();down=null;});canvas.addEventListener('pointercancel',()=>{down=null;});
  canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','0','Enter',' '].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')azimuth-=.12;if(e.key==='ArrowRight')azimuth+=.12;if(e.key==='ArrowUp')elevation=Math.min(1.2,elevation+.1);if(e.key==='ArrowDown')elevation=Math.max(.35,elevation-.1);if(e.key==='0'){azimuth=.35;elevation=.8;}if(e.key==='Enter'||e.key===' ')onPick();draw(0);});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();alive=false;canvas.dispatchEvent(new CustomEvent('subgame-context-lost'));});canvas.addEventListener('webglcontextrestored',()=>{alive=true;canvas.dispatchEvent(new CustomEvent('subgame-context-restored'));draw(0);});
  function focusPoint(){const point=V(d.topology==='switch-high'?[0,1.5,top]:[right,1.5,.2]).project(camera);return {x:(point.x+1)/2,y:(1-point.y)/2};}
  return {update,draw,resize,hit,focusPoint,restore:()=>{azimuth=.35;elevation=.8;draw(0);},snapshot:()=>({id,renderer:'WebGL',topology:d.topology,markers:markers.length,signalMarkers:markers.filter(m=>m.kind==='clock').length,phase:clockPhase}),dispose:()=>{disposed=true;observer.disconnect();purge(solid);purge(moving);textures.forEach(t=>t.dispose());map.dispose();env.dispose();renderer.dispose();renderer.forceContextLoss();}};
 }
 window.TrainingSubtypeGameScene=Object.freeze({create});
})();
