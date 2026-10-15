/* Actual interactive WebGL meshes, not a pre-rendered board or loop video. */
(function(){
 'use strict';const T=window.TrainingThree,P=window.TrainingGamePackages;
 function create(canvas,textureSource,onPick){
  const renderer=new T.WebGLRenderer({canvas,alpha:true,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,.1,80),world=new T.Group();scene.add(world);scene.add(new T.HemisphereLight(0xdcefff,0x355648,2.1));
  const room=new T.RoomEnvironment(),pmrem=new T.PMREMGenerator(renderer),environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;room.dispose();pmrem.dispose();
  const sun=new T.DirectionalLight(0xffffff,3.5);sun.position.set(-4,10,6);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-8;sun.shadow.camera.right=8;sun.shadow.camera.top=8;sun.shadow.camera.bottom=-8;sun.shadow.normalBias=.03;scene.add(sun);
  const ground=new T.Mesh(new T.PlaneGeometry(200,200),new T.ShadowMaterial({opacity:.13}));ground.rotation.x=-Math.PI/2;ground.position.y=-.37;ground.receiveShadow=true;scene.add(ground);
  let course='resistor',key='',parts=new T.Group(),flows=new T.Group(),ledMaterials=[],labelTextures=[],phase=0,alive=true,disposed=false,azimuth=.35,elevation=.8,distance=13.4,lastResult=null,heatRing=null,selected=null,consumer=null,connections=[];
  world.add(parts,flows);const glow=new T.PointLight(0xffbd3e,0,3);world.add(glow);
  // A valid green texel avoids a black first frame while the image decodes.
  const pcbFallback=document.createElement('canvas');pcbFallback.width=pcbFallback.height=1;const pcbContext=pcbFallback.getContext('2d');pcbContext.fillStyle='#26a34b';pcbContext.fillRect(0,0,1,1);
  const pcbMap=new T.Texture(pcbFallback);pcbMap.colorSpace=T.SRGBColorSpace;pcbMap.needsUpdate=true;canvas.dataset.textureLoaded='false';
  // Reallocate GPU storage when replacing the 1px fallback with the full image.
  const image=new Image();image.onload=()=>{if(disposed)return;pcbMap.dispose();pcbMap.image=image;pcbMap.needsUpdate=true;canvas.dataset.textureLoaded='true';draw(0);};image.src=textureSource;
  const v=p=>new T.Vector3(...p),silver=0xbcbdb3;
  function material(color,extra={}){return new T.MeshStandardMaterial({color,roughness:.36,metalness:.12,...extra});}
  function mesh(geometry,mat,pos,group=parts){const m=new T.Mesh(geometry,mat);m.position.set(...pos);m.castShadow=true;m.receiveShadow=true;group.add(m);return m;}
  function box(pos,size,color,group=parts,extra={}){return mesh(new T.BoxGeometry(...size),material(color,extra),pos,group);}
  function rod(a,b,r,color,group=parts){const d=v(b).sub(v(a)),m=mesh(new T.CylinderGeometry(r,r,d.length(),12),material(color,{metalness:.35}),v(a).add(v(b)).multiplyScalar(.5).toArray(),group);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return m;}
  function print(text,pos,w=1.2,h=.36,color='#ffffff',group=parts){const c=document.createElement('canvas');c.width=512;c.height=192;const ctx=c.getContext('2d');ctx.font='600 155px "Segoe UI","Microsoft YaHei",sans-serif';const measured=ctx.measureText(text).width;ctx.font='600 '+Math.min(155,155*448/measured)+'px "Segoe UI","Microsoft YaHei",sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=color;ctx.fillText(text,256,96);const map=new T.CanvasTexture(c);map.colorSpace=T.SRGBColorSpace;labelTextures.push(map);const m=mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map,transparent:true,depthWrite:false,side:T.DoubleSide}),pos,group);m.rotation.x=-Math.PI/2;return m;}
  function wire(points,color=0x8faeb1){for(let i=1;i<points.length;i++)if(v(points[i-1]).distanceTo(v(points[i]))>1e-8)rod(points[i-1],points[i],.038,color);}
  function purge(group){const geometries=new Set(),materials=new Set();group.traverse(m=>{if(m.geometry)geometries.add(m.geometry);if(m.material)for(const x of Array.isArray(m.material)?m.material:[m.material])materials.add(x);});group.clear();geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());}
  function board(){const s=new T.Shape(),r=.28,x=-4,z=-2.5,w=8,h=5;s.moveTo(x+r,z);s.lineTo(x+w-r,z);s.quadraticCurveTo(x+w,z,x+w,z+r);s.lineTo(x+w,z+h-r);s.quadraticCurveTo(x+w,z+h,x+w-r,z+h);s.lineTo(x+r,z+h);s.quadraticCurveTo(x,z+h,x,z+h-r);s.lineTo(x,z+r);s.quadraticCurveTo(x,z,x+r,z);
   for(const [px,pz] of [[-3.6,-2.1],[3.6,-2.1],[-3.6,2.1],[3.6,2.1]]){const hole=new T.Path();hole.absarc(px,pz,.14,0,Math.PI*2,true);s.holes.push(hole);const ring=mesh(new T.TorusGeometry(.185,.045,8,24),material(0xc7ad60,{metalness:.65}),[px,.04,-pz]);ring.rotation.x=-Math.PI/2;}
   const b=mesh(new T.ExtrudeGeometry(s,{depth:.13,bevelEnabled:true,bevelThickness:.035,bevelSize:.025,bevelSegments:2,steps:1}),material(0x85978c,{map:pcbMap,roughness:.55,metalness:.2}),[0,-.10,0]);b.rotation.x=-Math.PI/2;
  }
  const top=-1.25,bottom=1.6,left=-2.8,right=2.6,Y=.08;
  const mainPath=()=>[[left,Y,top],selected.left,[0,.76,top],selected.right,[consumer.input[0],Y,top],consumer.input,consumer.inside,consumer.output,[consumer.output[0],Y,bottom],[left,Y,bottom],[left,Y,.7]];
  function source(p){box([-3,.23,.03],[1.15,.45,1.55],0x25394b);box([-3,.48,.03],[.88,.055,1.25],0x142533);print(course==='capacitor'?'3.3 V':course==='inductor'?'驱动':p.reverse?'−5 V':'5 V',[-3,.515,.06],.9,.38);print(p.reverse?'−':'+',[left,.10,top-.38],.24,.24);print(p.reverse?'+':'−',[left,.10,1.96],.24,.24);rod([-3.55,.13,-.5],[-5.1,.15,-.5],.095,0xd74042);rod([-3.55,.13,.7],[-5.1,.15,.7],.095,0x263a4c);wire([[left,Y,top],[left,Y,-.7]]);wire([[left,Y,.7],[left,Y,bottom],[right,Y,bottom]]);}
  function packageMesh(id,p,center,scale=1,angle=0){
   const data=P.build(id,p),group=new T.Group();group.position.set(center[0],.10,center[2]);group.scale.setScalar(scale);group.rotation.y=angle+data.layout.angle;parts.add(group);
   for(const q of data.items){let m;
    if(q.type==='box'){m=box(q.p,q.size,q.c,group);if(q.rotation)m.rotation.set(...q.rotation);}
    else if(q.type==='rod')m=rod(q.a,q.b,q.r,q.c,group);
    else{m=print(q.text,q.p,q.w,q.h,q.c,group);if(q.rotation)m.rotation.set(...q.rotation);}
    if(m)m.userData.packagePart=q.part;
   }
   group.updateMatrixWorld(true);const contacts=data.layout.pins.map(pin=>({...pin,point:v(pin.point).multiplyScalar(scale).applyAxisAngle(new T.Vector3(0,1,0),angle).add(new T.Vector3(center[0],.10,center[2])).toArray()}));
   for(const pin of contacts)box([pin.point[0],.0825,pin.point[2]],[pin.pad[0]*scale+.12,.035,pin.pad[2]*scale+.12],0xbba679,parts,{metalness:.65});
   selected={layout:data.layout,contacts,group,left:[...contacts].sort((a,b)=>a.point[0]-b.point[0])[0].point,right:[...contacts].sort((a,b)=>b.point[0]-a.point[0])[0].point};
   canvas.dataset.package=data.layout.title;canvas.dataset.pinCount=String(contacts.length);canvas.dataset.pinContacts=JSON.stringify(contacts);canvas.dataset.packageBaseY='0.10';canvas.dataset.padTopY='0.10';canvas.dataset.packageAngle=String(data.layout.angle+angle);
   selected.seating=P.inspectContacts(group,T.Vector3,.10);canvas.dataset.seating=JSON.stringify(selected.seating);canvas.dataset.seatingGap=String(Math.max(0,...selected.seating.map(p=>p.gap)));
   const k=contacts.find(pin=>pin.role==='K');canvas.dataset.cathodeSide=k?(k.point[0]<center[0]?'left':'right'):'';return selected;
  }
  function connect(pin,target){wire([pin,...target]);connections.push({pin,traceStart:pin,target});}
  function resistor(value,pos=[0,0,top]){packageMesh('res-thick',{marking:value===100?'101':value===330?'331':'102'},pos);print('R1',[pos[0],.09,pos[2]+.64],.6,.25);heatRing=mesh(new T.TorusGeometry(.87,.045,8,40),new T.MeshBasicMaterial({color:0xf29923,transparent:true,opacity:0}),[pos[0],.085,pos[2]]);heatRing.rotation.x=-Math.PI/2;}
  function led(){for(const x of [right-.15,right+.15]){rod([x,.10,.35],[x,.41,.35],.035,silver);box([x,.0825,.35],[.18,.035,.18],0xbba679);}
   const mat=material(0xf69a08,{transparent:true,opacity:.82,roughness:.18,emissive:0xff9b00,emissiveIntensity:.1});ledMaterials.push(mat);
   const shape=new T.Shape();for(let i=0;i<=32;i++){const a=i/32*Math.PI*2,x=Math.min(.35*Math.cos(a),.27),z=.35*Math.sin(a);if(i===0)shape.moveTo(x,z);else shape.lineTo(x,z);}shape.closePath();const flange=mesh(new T.ExtrudeGeometry(shape,{depth:.09,bevelEnabled:false}),mat,[right,.325,.35]);flange.rotation.x=-Math.PI/2;
   mesh(new T.CylinderGeometry(.29,.30,.45,32),mat,[right,.61,.35]);mesh(new T.SphereGeometry(.29,32,20,0,Math.PI*2,0,Math.PI/2),mat,[right,.835,.35]);print('A',[right-.15,.09,.70],.15,.18);print('K',[right+.15,.09,.70],.15,.18);print('LED',[right,.09,.99],.7,.3);glow.position.set(right,1.05,.35);
   consumer={input:[right-.15,.135,.35],output:[right+.15,.135,.35],inside:[right,.95,.35]};
  }
  function chip(label='芯片 IC'){box([right,.39,.28],[1.3,.46,1.2],0x25394b);for(const x of [right-.78,right+.78])for(let i=0;i<4;i++){box([x,.14,-.1+i*.26],[.35,.08,.09],silver);box([x,.0825,-.1+i*.26],[.38,.035,.16],0xbba679);}print(label,[right,.63,.25],1.05,.32);consumer={input:[right-.78,.14,-.1],output:[right+.78,.14,.68],inside:[right,.65,.28]};}
  function capacitor(p){const x=p.near?.4:-1.5;packageMesh('cap-mlcc',{},[x,0,.4],.6,Math.PI/2);selected.positive=[...selected.contacts].sort((a,b)=>a.point[2]-b.point[2])[0].point;selected.negative=[...selected.contacts].sort((a,b)=>b.point[2]-a.point[2])[0].point;connect(selected.positive,[[x,Y,top]]);connect(selected.negative,[[x,Y,bottom]]);print('C1',[x,.09,1.15],.6,.24);print(p.value+' µF',[x,.09,-.35],.9,.3);}
  function inductor(p){packageMesh('ind-wound',{},[0,0,top]);print('L1',[0,.09,top+.68],.5,.25);print(p.value+' µH',[0,.09,top-.65],1,.3);}
  function diode(p){packageMesh('dio-switch',{forward:!!p.value},[0,0,top]);print(p.value?'A    K':'K    A',[0,.09,top+.52],1.3,.28);}
  function rebuild(c,p){course=c;purge(parts);labelTextures.forEach(t=>t.dispose());labelTextures=[];ledMaterials=[];connections=[];heatRing=null;board();source(p);
   if(c==='capacitor'){chip();capacitor(p);connect(consumer.input,[[consumer.input[0],Y,top],[left,Y,top]]);connect(consumer.output,[[consumer.output[0],Y,bottom],[left,Y,bottom]]);}
   else{if(c==='resistor')resistor(p.value);else if(c==='inductor')inductor(p);else diode(p);if(c==='resistor')led();else chip(c==='diode'?'负载 1 kΩ':'负载');connect(selected.left,[[left,Y,top]]);connect(selected.right,[[consumer.input[0],Y,top],consumer.input]);connect(consumer.output,[[consumer.output[0],Y,bottom],[left,Y,bottom]]);}
   // Interactive socket is a scene object, not a picture of a circuit.
   const slot=box(c==='capacitor'?[p.near?.4:-1.5,.068,.4]:[0,.068,top],c==='capacitor'?[1.2,.005,1.1]:[2.15,.005,1.1],0x297bfc,parts,{emissive:0x1555e8,emissiveIntensity:.25});slot.userData.playgroundSocket=true;canvas.dataset.model=c;canvas.dataset.choice=String(p.value);canvas.dataset.meshes=String(parts.children.length);canvas.dataset.contactError='0';canvas.dataset.connections=JSON.stringify(connections);
  }
  function sample(points,u){const lengths=points.slice(1).map((p,i)=>v(p).distanceTo(v(points[i]))),total=lengths.reduce((a,b)=>a+b,0);let remaining=u*total;for(let i=0;i<lengths.length;i++){if(lengths[i]<1e-8)continue;if(remaining<=lengths[i]||i===lengths.length-1){return {point:v(points[i]).lerp(v(points[i+1]),remaining/lengths[i]),direction:v(points[i+1]).sub(v(points[i])).normalize()};}remaining-=lengths[i];}return {point:v(points[0]),direction:new T.Vector3(1,0,0)};}
  const markers=[];let flowKey='',focusTarget=[0,1.1,top];
  function flowSets(r,p){
   if(!p.power)return [];
   if(course!=='capacitor'){if(Math.abs(r.current)<1e-12||r.unknown)return [];const points=mainPath();return [{points:r.current<0?points.reverse():points,color:0x258bff,count:Math.max(4,Math.min(12,Math.round(Math.abs(r.current)*(course==='inductor'?3:800))))}];}
   const x=p.near?.4:-1.5,sets=[{points:[[left,Y,top],[consumer.input[0],Y,top],consumer.input,consumer.inside,consumer.output,[consumer.output[0],Y,bottom],[left,Y,bottom],[left,Y,.7]],color:0x258bff,count:6}];
   if(r.storage<0)sets.push({points:[selected.positive,[x,Y,top],[consumer.input[0],Y,top],consumer.input,consumer.inside,consumer.output,[consumer.output[0],Y,bottom],[x,Y,bottom],selected.negative],color:0xf29923,count:8});
   if(r.storage>0){sets.push({points:[[left,Y,top],[x,Y,top],selected.positive],color:0xf29923,count:3});sets.push({points:[selected.negative,[x,Y,bottom],[left,Y,bottom],[left,Y,.7]],color:0xf29923,count:3});}return sets;
  }
  function update(c,p,r){const k=c+'|'+p.value+'|'+p.near+'|'+p.reverse;if(key!==k){key=k;rebuild(c,p);}lastResult=r;focusTarget=c==='capacitor'?[p.near?.4:-1.5,1.1,.4]:[0,1.1,top];
   if(heatRing)heatRing.material.opacity=r.power>0?Math.min(.65,.18+r.power*6):0;canvas.dataset.heatPower=String(r.power);
   for(const mat of ledMaterials){mat.emissiveIntensity=.8*r.brightness;mat.color.setHex(0x62400d).lerp(new T.Color(0xffb326),r.brightness);}glow.intensity=c==='resistor'?2.4*r.brightness:0;canvas.dataset.brightness=String(r.brightness);canvas.dataset.current=String(r.current);canvas.dataset.source=String(r.source);canvas.dataset.load=String(r.load);canvas.dataset.storage=String(r.storage);canvas.dataset.marking=c==='resistor'?(p.value===100?'101':p.value===330?'331':'102'):'';
   const sets=flowSets(r,p),fk=JSON.stringify(sets);if(flowKey!==fk){flowKey=fk;purge(flows);markers.length=0;for(const set of sets){const offset=course==='capacitor'?(set.color===0x258bff?-.055:.055):0;set.points=set.points.map(point=>[point[0],point[1]+.11,point[2]+offset]);for(let i=1;i<set.points.length;i++){const a=v(set.points[i-1]),b=v(set.points[i]),d=b.clone().sub(a),guide=mesh(new T.CylinderGeometry(.017,.017,d.length(),6),new T.MeshBasicMaterial({color:set.color,transparent:true,opacity:.42}),a.add(b).multiplyScalar(.5).toArray(),flows);guide.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());guide.castShadow=false;guide.receiveShadow=false;}for(let i=0;i<set.count;i++){const marker=mesh(new T.CylinderGeometry(0,.095,.29,8),new T.MeshBasicMaterial({color:set.color}),[0,0,0],flows);marker.castShadow=false;marker.receiveShadow=false;markers.push({mesh:marker,set,index:i});}}}
   canvas.dataset.flowCount=String(markers.length);canvas.dataset.energyThroughLoad=String(c==='capacitor'&&r.storage<0&&markers.some(m=>m.set.color===0xf29923));
  }
  function cameraPosition(){camera.position.set(Math.sin(azimuth)*Math.cos(elevation)*distance,Math.sin(elevation)*distance,Math.cos(azimuth)*Math.cos(elevation)*distance);camera.lookAt(0,.05,0);}
  function draw(dt){if(!alive||disposed)return;phase+=dt*.15;for(const m of markers){const s=sample(m.set.points,(phase+m.index/m.set.count)%1);m.mesh.position.copy(s.point);m.mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),s.direction);}cameraPosition();renderer.render(scene,camera);canvas.dataset.frames=String(Number(canvas.dataset.frames||0)+1);canvas.dataset.flowPhase=String(phase);canvas.dataset.yaw=String(azimuth);}
  function resize(){const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;camera.aspect=rect.width/rect.height;distance=11.3*Math.max(1,1.7/camera.aspect);camera.updateProjectionMatrix();renderer.setSize(rect.width,rect.height,false);draw(0);}
  const observer=new ResizeObserver(resize);observer.observe(canvas);
  const raycaster=new T.Raycaster(),pointer=new T.Vector2();function hit(x,y){const b=canvas.getBoundingClientRect();pointer.set((x-b.left)/b.width*2-1,-(y-b.top)/b.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(parts.children,true).some(i=>i.object.userData.playgroundSocket);}
  let down=null,moved=false;canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);down={x:e.clientX,y:e.clientY};moved=false;});canvas.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-down.x,dy=e.clientY-down.y;if(Math.abs(dx)+Math.abs(dy)>2)moved=true;azimuth+=dx*.006;elevation=Math.max(.35,Math.min(1.25,elevation+dy*.005));down={x:e.clientX,y:e.clientY};draw(0);});canvas.addEventListener('pointerup',e=>{if(down&&!moved&&hit(e.clientX,e.clientY))onPick();down=null;});canvas.addEventListener('pointercancel',()=>{down=null;});
  canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','0','Enter',' '].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft')azimuth-=.12;if(e.key==='ArrowRight')azimuth+=.12;if(e.key==='ArrowUp')elevation=Math.min(1.25,elevation+.1);if(e.key==='ArrowDown')elevation=Math.max(.35,elevation-.1);if(e.key==='0'){azimuth=.35;elevation=.8;}if(e.key==='Enter'||e.key===' ')onPick();draw(0);}});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();alive=false;canvas.dispatchEvent(new CustomEvent('playground-context-lost'));});canvas.addEventListener('webglcontextrestored',()=>{alive=true;draw(0);});
  function focusPoint(){const point=v(focusTarget).project(camera);return {x:(point.x+1)/2,y:(1-point.y)/2};}
  return {update,draw,resize,hit,focusPoint,restore:()=>{azimuth=.35;elevation=.8;draw(0);},snapshot:()=>({course,current:lastResult?.current,markers:markers.length,renderer:'WebGL',phase,package:selected?.layout.title,contacts:selected?.contacts,seating:selected?.seating,connections,contactError:0}),dispose:()=>{disposed=true;alive=false;image.onload=null;observer.disconnect();purge(parts);purge(flows);labelTextures.forEach(t=>t.dispose());pcbMap.dispose();environment.dispose();renderer.dispose();}};
 }
 let previewRenderer=null;
 function thumbnail(course,value,canvas){
  if(!previewRenderer){previewRenderer=new T.WebGLRenderer({alpha:true,antialias:true});previewRenderer.setSize(170,95,false);previewRenderer.toneMapping=T.ACESFilmicToneMapping;previewRenderer.toneMappingExposure=1.3;}
  const s=new T.Scene(),c=new T.PerspectiveCamera(30,170/95,.1,20);c.position.set(1.2,1.5,2.1);c.lookAt(0,0,0);s.add(new T.HemisphereLight(0xffffff,0x889bb0,3));const light=new T.DirectionalLight(0xffffff,3);light.position.set(-2,4,3);s.add(light);
  const mat=color=>new T.MeshStandardMaterial({color,roughness:.3,metalness:.2}),add=(g,m,pos)=>{const mesh=new T.Mesh(g,m);mesh.position.set(...pos);s.add(mesh);return mesh;};
  const maps=[],id={resistor:'res-thick',capacitor:'cap-mlcc',inductor:'ind-wound',diode:'dio-switch'}[course],model=P.build(id,{forward:!!value,marking:value===100?'101':value===330?'331':'102'}),group=new T.Group();group.position.y=-model.layout.size[1]/2;group.rotation.y=model.layout.angle;s.add(group);
  for(const q of model.items){let geometry,material,mesh;
   if(q.type==='box'){geometry=new T.BoxGeometry(...q.size);material=mat(q.c);mesh=new T.Mesh(geometry,material);mesh.position.set(...q.p);if(q.rotation)mesh.rotation.set(...q.rotation);}
   else if(q.type==='rod'){const a=new T.Vector3(...q.a),b=new T.Vector3(...q.b),delta=b.clone().sub(a);mesh=new T.Mesh(new T.CylinderGeometry(q.r,q.r,delta.length(),10),mat(q.c));mesh.position.copy(a.add(b).multiplyScalar(.5));mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());}
   else{const image=document.createElement('canvas');image.width=256;image.height=96;const ctx=image.getContext('2d');ctx.font='600 62px Segoe UI';ctx.fillStyle=q.c;ctx.textAlign='center';ctx.fillText(q.text,128,69);const map=new T.CanvasTexture(image);map.colorSpace=T.SRGBColorSpace;maps.push(map);mesh=new T.Mesh(new T.PlaneGeometry(q.w,q.h),new T.MeshBasicMaterial({map,transparent:true}));mesh.position.set(...q.p);mesh.rotation.set(...(q.rotation||[-Math.PI/2,0,0]));}
   group.add(mesh);
  }
  previewRenderer.render(s,c);canvas.getContext('2d').drawImage(previewRenderer.domElement,0,0,170,95);s.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});maps.forEach(t=>t.dispose());
 }
 window.TrainingPlaygroundScene=Object.freeze({create,thumbnail});
})();
