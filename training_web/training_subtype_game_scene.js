/* Live 3D boards: seven connection types, real component meshes and moving signals. */
(function(){
 'use strict';const T=window.TrainingThree,M=window.TrainingSubtypeGameMath,C=window.TrainingCatalog,P=window.TrainingGamePackages;
 function create(canvas,id,onPick){
  const d=M.profile(id),chapter=C.lesson(id),renderer=new T.WebGLRenderer({canvas,alpha:true,antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,.1,70),world=new T.Group();scene.add(world);
  scene.add(new T.HemisphereLight(0xe9f3ff,0x41604f,3));const sun=new T.DirectionalLight(0xffffff,3);sun.position.set(-3,8,5);scene.add(sun);
  const room=new T.RoomEnvironment(),pm=new T.PMREMGenerator(renderer),env=pm.fromScene(room,.04);scene.environment=env.texture;room.dispose();pm.dispose();
  const solid=new T.Group(),moving=new T.Group();world.add(solid,moving);
  let key='',textures=[],markers=[],hot=null,indicator=null,fieldRing=null,lightMaterials=[],waves=[],result=null,params=null,running=false,clockPhase=0,azimuth=.35,elevation=.8,distance=12,alive=true,disposed=false,installed=null,loadPins=null,connections=[];
  // Loading must not depend on electricity or a camera drag to repaint.
  const pcbFallback=document.createElement('canvas');pcbFallback.width=pcbFallback.height=1;const pcbContext=pcbFallback.getContext('2d');pcbContext.fillStyle='#26a34b';pcbContext.fillRect(0,0,1,1);
  const map=new T.Texture(pcbFallback);map.colorSpace=T.SRGBColorSpace;map.needsUpdate=true;canvas.dataset.textureLoaded='false';
  // Reallocate GPU storage when replacing the 1px fallback with the full image.
  const image=new Image();image.onload=()=>{if(disposed)return;map.dispose();map.image=image;map.needsUpdate=true;canvas.dataset.textureLoaded='true';draw(0);};image.src=window.TrainingPlaygroundAssets.pcb;
  const ledLight=new T.PointLight(0x409aff,0,3);world.add(ledLight);
  const V=p=>new T.Vector3(...p),color=rgb=>new T.Color().setRGB(rgb[0]/255,rgb[1]/255,rgb[2]/255,T.SRGBColorSpace);
  const mat=(c,extra={})=>new T.MeshStandardMaterial({color:c,roughness:.42,metalness:.15,...extra});
  function add(g,m,p,group=solid){const o=new T.Mesh(g,m);o.position.set(...p);group.add(o);return o;}
  const box=(p,s,c,group=solid,extra={})=>add(new T.BoxGeometry(...s),mat(c,extra),p,group);
  function rod(a,b,r,c,group=solid){const delta=V(b).sub(V(a)),o=add(new T.CylinderGeometry(r,r,delta.length(),r>.1?24:8),mat(c),V(a).add(V(b)).multiplyScalar(.5).toArray(),group);o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());return o;}
  function wire(points,c=0x8cbbb0){for(let i=1;i<points.length;i++)if(V(points[i-1]).distanceTo(V(points[i]))>1e-8)rod(points[i-1],points[i],.028,c);}
  function label(text,p,w=1.2,h=.27,c='#f5fbff',rotation=null,group=solid){
   const img=document.createElement('canvas');img.width=640;img.height=120;const ctx=img.getContext('2d');ctx.font='600 78px Microsoft YaHei,Segoe UI,sans-serif';const measured=ctx.measureText(text).width;ctx.font='600 '+Math.min(78,78*580/Math.max(1,measured))+'px Microsoft YaHei,Segoe UI,sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=c;ctx.fillText(text,320,60);
   const texture=new T.CanvasTexture(img);texture.colorSpace=T.SRGBColorSpace;textures.push(texture);const o=add(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false,side:T.DoubleSide}),p,group);o.rotation.set(...(rotation||[-Math.PI/2,0,0]));return o;
  }
  function purge(group){const gs=new Set(),ms=new Set();group.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])ms.add(m);});group.clear();gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());}
  function component(pos){
   const model=P.build(id,params),group=new T.Group(),base=[pos[0],.045,pos[2]];group.position.set(...base);group.rotation.y=model.layout.angle;solid.add(group);
   for(const q of model.items){let mesh;
    if(q.type==='box'){mesh=box(q.p,q.size,q.c,group);if(q.rotation)mesh.rotation.set(...q.rotation);}
    else if(q.type==='rod')mesh=rod(q.a,q.b,q.r,q.c,group);
    else label(q.text,q.p,q.w,q.h,q.c,q.rotation,group);
    if(mesh){mesh.userData.packagePart=q.part;if(id==='dio-led'&&q.part==='lens'){mesh.material.emissive.setHex(0xffa92e);mesh.material.roughness=.2;lightMaterials.push(mesh.material);ledLight.position.set(base[0],1,base[2]);}}
   }
   const pins=Object.fromEntries(model.layout.pins.map(p=>[p.role,p.point.map((v,i)=>v+base[i])]));
   for(const pin of model.layout.pins){const point=pin.point.map((v,i)=>v+base[i]);
    if(model.layout.throughHole){const ring=add(new T.TorusGeometry(.085,.025,8,20),mat(0xb8a06a),[point[0],.025,point[2]]);ring.rotation.x=-Math.PI/2;}
    else box([point[0],.0275,point[2]],[pin.pad[0]+.10,.035,pin.pad[2]+.10],0xb4a278,solid,{metalness:.7});
    if(model.layout.pins.length>2){const side=pin.point[2]>=0?1:-1;label(pin.number+' '+pin.role,[point[0],.095,base[2]+side*(model.layout.size[2]/2+.31)],.51,.18,'#eef4f6');}
   }
   if(id==='cap-tantalum')canvas.dataset.positiveSide=params.forward?'left':'right';
   canvas.dataset.package=model.layout.title;canvas.dataset.pinCount=String(model.layout.pins.length);canvas.dataset.pinMap=JSON.stringify(pins);canvas.dataset.packageBaseY=String(base[1]);canvas.dataset.padTopY='0.045';canvas.dataset.packageAngle=String(model.layout.angle);
   canvas.dataset.pinContacts=JSON.stringify(model.layout.pins.map(p=>({...p,point:p.point.map((v,i)=>v+base[i])})));
   canvas.dataset.cathodeSide=pins.K?(pins.K[0]<base[0]?'left':'right'):'';canvas.dataset.pinOne=JSON.stringify(model.layout.pins[0].point.map((v,i)=>v+base[i]));
   if(id==='ind-common'&&!params.installed)group.traverse(o=>{if(o.material&&/ferrite|base/.test(o.userData.packagePart||'')){o.material.transparent=true;o.material.opacity=.18;o.material.depthWrite=false;}});
   if(id==='dio-tvs'&&!params.clamp)group.traverse(o=>{if(o.material){o.material.transparent=true;o.material.opacity=.18;o.material.depthWrite=false;}});
   label(chapter.title,[base[0],.10,base[2]+model.layout.size[2]/2+.63],1.7,.25);
   const socket=box([base[0],.003,base[2]],[model.layout.size[0]+.30,.015,model.layout.size[2]+.20],0x276ded,solid,{emissive:0x1555e8,emissiveIntensity:.2});socket.userData.subtypeSocket=true;
   const halo=add(new T.TorusGeometry(.83,.055,8,44),new T.MeshBasicMaterial({color:0xef7a35,transparent:true,opacity:0}),[pos[0],.045,pos[2]]);halo.rotation.x=-Math.PI/2;hot=halo;
   const seating=P.inspectContacts(group,T.Vector3,.045,!!model.layout.throughHole);canvas.dataset.seating=JSON.stringify(seating);canvas.dataset.seatingGap=String(Math.max(0,...seating.map(p=>p.gap)));
   installed={pins,layout:model.layout,base,seating};return installed;
  }
  function chip(pos,name='负载 / IC'){
   box(pos,[1.05,.35,.95],0x253a50);for(const x of [-.62,.62])for(let i=0;i<4;i++)box([pos[0]+x,.08,pos[2]-.3+i*.2],[.27,.07,.085],0xb6c5cf);
   label(name,[pos[0],pos[1]+.185,pos[2]],.96,.28);indicator=box([pos[0]+.33,pos[1]+.20,pos[2]-.3],[.12,.06,.12],0x315a45,solid,{emissive:0x36e883,emissiveIntensity:0});
   return {vcc:[pos[0]-.62,.08,pos[2]-.3],gnd:[pos[0]+.62,.08,pos[2]+.3],clk:[pos[0]-.62,.08,pos[2]+.1],line2:[pos[0]-.62,.08,pos[2]+.3],inside:[pos[0],pos[1]+.32,pos[2]]};
  }
  function makeWave(){
   const positions=new Float32Array(81*3);for(const c of [d.topology==='clock'?0xe6b23f:0x258bff,d.topology==='clock'?0x42e8a4:0xf39934]){
    const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(positions.slice(),3));const line=new T.Line(g,new T.LineBasicMaterial({color:c}));solid.add(line);waves.push(line);
   }
   label(d.topology==='clock'?'时钟慢放 / 频差放大':id==='ind-layered'?'理想RL交流慢放':'交流半周慢放',[.1,.06,2.12],2.5,.24);
  }
  const top=-1.35,bottom=1.65,y=.065,left=-2.8,right=2.8;
  let loop=[],railLoop=[],positiveLead=[],negativeLead=[],clockPower=[],clockSignal=[],baseFlow=[],commonPaths=[],safetyLead=[];
  const N=(x,z)=>[x,y,z],insidePart=()=>[installed.base[0],installed.layout.size[1]+.12,installed.base[2]];
  function lead(role,tail,c=0x8cbbb0){const pin=installed.pins[role];if(!pin)throw new Error('Missing pin '+role);const path=[pin,N(pin[0],pin[2]),...tail];wire(path,c);connections.push({role,pin:[...pin],traceStart:[...path[0]],tail});return path;}
  function powerRails(){wire([N(left,top),N(loadPins.vcc[0],top),loadPins.vcc]);wire([loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.65)]);railLoop=[N(left,top),N(loadPins.vcc[0],top),loadPins.vcc,loadPins.inside,loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.65)];}
  function rebuild(p){
   key=JSON.stringify(p);params=p;purge(solid);purge(moving);textures.forEach(t=>t.dispose());textures=[];markers=[];waves=[];connections=[];hot=null;indicator=null;fieldRing=null;lightMaterials=[];canvas.dataset.partConnected=String(id!=='ind-common'||p.installed);
   box([0,-.09,0],[8,.16,5],0x8ca795,solid,{map,roughness:.58});for(const x of [-3.6,3.6])for(const z of [-2.1,2.1]){const ring=add(new T.TorusGeometry(.16,.04,8,24),mat(0xccb764),[x,.016,z]);ring.rotation.x=-Math.PI/2;}
   box([-3,.22,.04],[.96,.42,1.5],0x253b50);label(d.topology==='safety'?'虚拟 L / N':id==='dio-rectifier'?'5 V峰值 AC':chapter.family==='crystal'?'VDD / GND':chapter.family==='mos'?'12 V示例':id==='dio-zener'?p.input+' V':'电源',[-3,.44,.04],.85,.34);
   wire([[left,y,top],[left,y,-.68]]);wire([[left,y,.65],[left,y,bottom]]);
   if(d.topology==='parallel'){
    component([0,0,.15]);loadPins=chip([right,.28,.32]);powerRails();
    // Capacitors connect by board side, so reversing the physical part remains an error.
    const ordered=Object.entries(installed.pins).sort((a,b)=>a[1][0]-b[1][0]),diode=chapter.family==='diode',positive=diode?'K':ordered[0][0],negative=diode?'A':ordered[1][0];
    positiveLead=lead(positive,[N(installed.pins[positive][0],top)]);negativeLead=lead(negative,[N(installed.pins[negative][0],bottom)]);
    if(diode){box([-1.5,.2,top],[.5,.22,.35],0xd5bd85);label(id==='dio-zener'?p.series+' Ω':'Rs=2 Ω',[-1.5,.33,top],.72,.21);label('K 接输入 · A 接GND',[0,.09,-.6],1.9,.22);}
   }else if(d.topology==='clock'){
    component([0,0,top]);loadPins=chip([right,.28,.20],'CLK输入');powerRails();
    if(id==='xtal-passive'){
     box([-1.75,.32,top],[.8,.35,.6],0x304863);label(p.amplifier?'振荡放大器':'未接放大器',[-1.75,.51,top],.76,.26);
     lead('X1',[N(-1.12,top+.43),[-1.35,.18,top+.10]],0xb8a253);lead('X2',[N(.96,top-.43),N(.96,top-.75),N(-1.75,top-.75),[-1.75,.18,top-.30]],0xb8a253);
     // Case pads 2/4 are ground, not additional resonator/supply terminals.
     for(const pin of installed.layout.pins.filter(q=>q.role==='外壳')){const point=pin.point.map((v,i)=>v+installed.base[i]);wire([point,N(point[0],point[2]),N(point[0],bottom)]);}
     clockPower=[N(left,top),[-2.15,.18,top],[-1.75,.38,top],[-1.75,.18,top+.30],N(-1.75,bottom),N(left,bottom),N(left,.6)];wire([N(left,top),[-2.15,.18,top]]);wire([[-1.75,.18,top+.30],N(-1.75,bottom)]);
     clockSignal=[[-1.35,.18,top+.10],N(1.38,top+.43),N(1.38,loadPins.clk[2]),loadPins.clk];wire(clockSignal,0x57cfa1);label('X1/X2 接振荡反馈',[.1,.09,-.30],1.8,.23);
    }else{
     const power=lead('VDD',[N(installed.pins.VDD[0],top-.77),N(left,top-.77),N(left,top)],0x57a4e7),ground=lead('GND',[N(installed.pins.GND[0],bottom),N(left,bottom)],0x57a4e7);
     clockPower=[...power].reverse().concat([insidePart(),...ground]);clockSignal=lead('OUT',[N(1.45,installed.pins.OUT[2]),N(1.45,loadPins.clk[2]),loadPins.clk],0x57cfa1);
     const control=installed.layout.pins[0].role;
     if(control==='ST'||control==='VC'){box([-1,.10,.4],[.35,.07,.35],0x416688);lead(control,[N(-1.0,top+.43),[-1,.10,.4]],control==='VC'?0xb994ef:p.oe?0xb6d384:0x7c979a);label(control==='VC'?'VC 微调控制':'ST 启停控制',[-1.0,.09,.79],1.05,.23);}
     else if(control==='GND/NC')lead(control,[N(-1.05,top+.43),N(-1.05,bottom)],0x6a99aa);
    }
    label('OUT ≠ 供电',[1.9,.09,-.8],1.4,.24);makeWave();
   }else if(d.topology==='switch-high'||d.topology==='switch-low'){
    const high=d.topology==='switch-high',device=high?[0,0,top]:[right,0,.2];component(device);loadPins=chip(high?[right,.28,.2]:[0,.28,top],'受控负载');
    const mos=chapter.family==='mos',dual=id==='mos-dual',digital=id==='bjt-digital',control=mos?(dual?'G1':'G'):digital?'IN':'B',out=mos?(dual?'D1':'D'):digital?'OUT':'C',reference=mos?(dual?'D2':'S'):digital?'GND':'E';
    const inputRole=high?reference:out,outputRole=high?out:reference,a=installed.pins[inputRole],b=installed.pins[outputRole];
    const inTail=high?[N(-1.15,a[2]),N(left,a[2]),N(left,top)]:[N(a[0],top),N(loadPins.gnd[0],top),loadPins.gnd];
    const input=lead(inputRole,inTail),output=lead(outputRole,high?[N(1.2,b[2]),N(1.2,top),N(loadPins.vcc[0],top),loadPins.vcc]:[N(b[0],bottom),N(left,bottom),N(left,.6)]);
    if(high)wire([loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.6)]);else wire([N(left,top),N(loadPins.vcc[0],top),loadPins.vcc]);
    const ctrl=[-1.25,y,.75];box([ctrl[0],.2,ctrl[2]],[.8,.22,.6],0x416688);
    const ctrlPath=lead(control,[N(installed.pins[control][0],1.18),N(ctrl[0],1.18),[ctrl[0],.2,ctrl[2]]],mos?0xb994ef:0xf4ab53);wire([[ctrl[0],y,1.1],N(ctrl[0],bottom)],0x89a69d);
    if(dual){lead('G2',[N(installed.pins.G2[0],-.85),N(-1.6,-.85),[-1.6,.2,.75]],p.gates==='both'?0xb994ef:0x8b939a);wire([installed.pins.S1,[device[0],y,device[2]],installed.pins.S2],0x8cbbb0);connections.push({role:'S1/S2',pin:installed.pins.S1,traceStart:installed.pins.S1,tail:[installed.pins.S2]});}
    const deviceFlow=dual?[a,[device[0]-.32,.65,device[2]],installed.pins.S1,[device[0],y,device[2]],installed.pins.S2,[device[0]+.32,.65,device[2]],b]:[a,insidePart(),b];
    loop=high?[...input].reverse().concat(deviceFlow.slice(1),output.slice(1),[loadPins.inside,loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.6)]):[N(left,top),N(loadPins.vcc[0],top),loadPins.vcc,loadPins.inside,loadPins.gnd,...[...input].reverse().slice(1),...deviceFlow.slice(1),...output.slice(1)];
    baseFlow=high?[b,insidePart(),...ctrlPath,N(ctrl[0],bottom)]:[...ctrlPath].reverse().concat([insidePart(),b,...output.slice(1)]);
    const beginnerMOS=['mos-n','mos-p'].includes(id);
    label(beginnerMOS?'G控制端：相对于S':chapter.family==='mos'?'G：相对S的驱动':'B：正确极性基流',[ctrl[0],.36,ctrl[2]],beginnerMOS?1.5:1.2,.23);
    label(beginnerMOS?(high?'供电侧：S接电源':'返回侧：S接返回端'):(high?'高边：S/E接电源':'低边：S/E接返回端'),[device[0],.07,device[2]-.7],2,.22);
    if(beginnerMOS){label('S参考端',high?[-.95,.12,top+.28]:[right,.12,1.05],.8,.22);label('D负载端',high?[.95,.12,top+.28]:[right,.12,-.65],.8,.22);}
    if(id==='mos-dual'||id==='bjt-darlington')label(id==='mos-dual'?'背靠背双N示例':'两级BJT示例',[0,.06,-.55],1.8,.23);
   }else if(d.topology==='common'){
    component([0,0,-.4]);loadPins=chip([right,.28,-.15],'双线端口');commonPaths=[];
    for(const [n,a,b,z,target] of [[1,'L1入','L1出',top,loadPins.vcc],[2,'L2入','L2出',.65,loadPins.line2]]){const input=lead(a,[N(left,installed.pins[a][2]),N(left,z)]),output=lead(b,[N(target[0],installed.pins[b][2]),target]);commonPaths.push([...input].reverse().concat([[0,1.55,-.4+(n===1?-.21:.21)],...output]));}
    wire([N(left,bottom),N(right,bottom)],0x6a948b);
    label('独立线1',[1.6,.06,top+.3],.9,.23);label('独立线2',[1.6,.06,.98],.9,.23);label('参考回路 / 模式示意',[.1,.06,2.04],2.6,.23);
    fieldRing=add(new T.TorusGeometry(.76,.07,10,46),new T.MeshBasicMaterial({color:0xb57ae8,transparent:true,opacity:.12}),[0,.65,-.4]);fieldRing.rotation.x=-Math.PI/2;
   }else if(d.topology==='safety'){
    component([0,0,.05]);loadPins=chip([right,.28,-.05],'虚拟设备');wire([N(left,top),N(loadPins.vcc[0],top),loadPins.vcc]);wire([N(left,.75),N(loadPins.gnd[0],.75),loadPins.gnd]);wire([N(left,bottom),N(right,bottom)],0xbab177);box([right,.025,bottom],[.25,.03,.25],0xbab177);label('PE示意端',[right,.07,bottom+.34],.95,.21);
    safetyLead=lead('1',[N(installed.pins['1'][0],top),N(left,top)],0x86caaa);lead('2',[N(installed.pins['2'][0],p.position==='line'?.75:bottom)],0x86caaa);
    label('L',[-2.15,.06,top],.25,.23);label('N',[-2.15,.06,.75],.25,.23);label('PE等位置',[-2.1,.06,bottom],1,.23);label(p.category+'类位置示例',[.1,1.5,.05],1.3,.25,'#f0dd6e');
   }else{
    component([0,0,top]);loadPins=chip([right,.28,.28],id==='res-sense'?'测量负载':id==='dio-led'?'光输出':'负载 / IC');
    const pins=Object.entries(installed.pins).sort((a,b)=>a[1][0]-b[1][0]),input=lead(pins[0][0],[N(left,top)]),output=lead(pins[1][0],[N(loadPins.vcc[0],top),loadPins.vcc]);wire([loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.65)]);
    loop=[...input].reverse().concat([insidePart(),...output,loadPins.inside,loadPins.gnd,N(loadPins.gnd[0],bottom),N(left,bottom),N(left,.65)]);
    if(id==='res-sense'||id==='res-thin'){
     box([0,.18,.8],[1.3,.28,.65],0x466386);label('高阻测量输入',[0,.34,.8],1.2,.24);for(const [i,pin] of pins.entries())wire([pin[1],N(pin[1][0],.4),[i?.55:-.55,.08,.5]],0x77ddbc);
    }
    if(id==='dio-led'){box([-1.55,.18,top],[.6,.18,.35],0x344355);label(p.resistance+' Ω',[-1.55,.29,top],.58,.20);label(p.forward?'A → K':'K → A',[0,.07,top+.9],1,.25);}
    if(id==='dio-rectifier'){label(p.forward?'正半周':'负半周',[0,.07,top+.85],1,.25);makeWave();}
    if(id==='ind-layered')makeWave();
    if(id==='res-sulfur'){label(p.design==='resistant'?'耐硫化声明示例':'普通声明示例',[0,.07,top+.8],1.8,.23);}
   }
   canvas.dataset.model=id;canvas.dataset.topology=d.topology;canvas.dataset.meshes=String(solid.children.length);
   canvas.dataset.connections=JSON.stringify(connections);canvas.dataset.contactError=String(Math.max(0,...connections.map(c=>V(c.pin).distanceTo(V(c.traceStart)))));
  }
  function pathMarker(points,c,kind,count=5){
   for(let i=0;i<count;i++){const mesh=add(new T.CylinderGeometry(0,.09,.25,8),new T.MeshBasicMaterial({color:c}),[0,0,0],moving);markers.push({mesh,points:points.map(p=>V([p[0],p[1]+.12,p[2]])),kind,index:i,count});}
  }
  function rebuildFlows(p,r,on){
   purge(moving);markers=[];if(!on)return;
   const v=r.visual;
   if(d.topology==='clock'){
    if(v.powered!==false)pathMarker(clockPower,0x258bff,'power',4);
    if(v.clock){pathMarker(clockSignal,0x43e8a4,'clock',5);}
   }else if(d.topology==='common'){
    pathMarker(commonPaths[0],0x258bff,'current',5);pathMarker(v.common?commonPaths[1]:[...commonPaths[1]].reverse(),0xf3a43b,'current',5);
    if(v.common)pathMarker([[right,y,bottom],[left,y,bottom]],0x729cba,'current',4);
   }else if(d.topology==='safety'){
    // Mark the leads only; no conduction path through an insulating capacitor body.
    pathMarker([...safetyLead].reverse(),0x43c19a,'position',3);
   }else if(d.topology==='parallel'){
    if(v.known&&(v.current>0||['ripple','charge','discharge'].includes(v.flow)))pathMarker(railLoop,0x258bff,'current',5);
    if(v.flow==='discharge'&&v.known&&v.active)pathMarker(positiveLead.concat([N(loadPins.vcc[0],top),loadPins.vcc,loadPins.inside,loadPins.gnd,N(loadPins.gnd[0],bottom),...[...negativeLead].reverse()]),0xf6a231,'storage',6);
    else if(v.flow==='ripple'||v.flow==='charge'){
     pathMarker([N(left,top),...[...positiveLead].reverse()],0xf6a231,'ripple',3);pathMarker(negativeLead.concat([N(left,bottom),N(left,.55)]),0xf6a231,'ripple',3);
    }else if(v.shunt>0)pathMarker([...positiveLead].reverse().concat([insidePart(),...negativeLead,N(left,bottom),N(left,.55)]),0xf6a231,'shunt',5);
   }else if(d.topology.startsWith('switch')){
    if(v.active&&v.known)pathMarker(loop,0x258bff,'current',7);
    if(v.flow==='base'&&v.base>0)pathMarker(baseFlow,0xf6a231,'base',4);
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
  function sample(points,u){const lengths=points.slice(1).map((p,i)=>p.distanceTo(points[i])),total=lengths.reduce((a,b)=>a+b,0);let remaining=u*total;for(let i=0;i<lengths.length;i++){if(lengths[i]<=1e-8)continue;if(remaining<=lengths[i]||i===lengths.length-1)return {point:points[i].clone().lerp(points[i+1],remaining/lengths[i]),direction:points[i+1].clone().sub(points[i]).normalize()};remaining-=lengths[i];}return {point:points.at(-1).clone(),direction:new T.Vector3(1,0,0)};}
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
  return {update,draw,resize,hit,focusPoint,restore:()=>{azimuth=.35;elevation=.8;draw(0);},snapshot:()=>({id,renderer:'WebGL',topology:d.topology,markers:markers.length,signalMarkers:markers.filter(m=>m.kind==='clock').length,phase:clockPhase,package:installed?.layout.title,contacts:JSON.parse(canvas.dataset.pinContacts||'[]'),seating:installed?.seating,connections,contactError:Number(canvas.dataset.contactError||0)}),dispose:()=>{disposed=true;image.onload=null;observer.disconnect();purge(solid);purge(moving);textures.forEach(t=>t.dispose());map.dispose();env.dispose();renderer.dispose();renderer.forceContextLoss();}};
 }
 window.TrainingSubtypeGameScene=Object.freeze({create});
})();
