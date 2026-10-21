/* Six generic finished products and retained desk parts. No electrical mutations. */
(function(root){
 'use strict';
 function create(T,world,pcb,product,h){
  const {mesh,box,rod,print,material}=h,M=root.RepairShopMechanics,base=new T.Group(),cover=new T.Group(),brace=new T.Group(),screws={};world.add(base,cover,brace);
  const origin=[-3.5,-.32,0],parks={cover:[-3.5,-.27,-4.8],brace:[3.1,-.26,-4.4],board:[2.5,-.25,1.8]},colors={lamp:0xd2a35c,fan:0x7aa499,speaker:0x354e57,clock:0xac7956,sensor:0xe3e5d9,router:0xdce1d6},color=colors[product.id];base.position.set(...origin);
  const bodyPick=(group,id)=>group.traverse(n=>{if(n.isMesh)n.userData.pick=id;});
  box([0,-.53,-.6],[18,.35,13],0xb98a58,world);print('维修区',[-3.5,-.344,3.8],2,.45,world,'#735539');print('防静电检修垫',[2.5,-.339,4.2],2.8,.35,world,'#405f54');box([2.5,-.34,1.6],[6.6,.025,4.8],0x577d71,world);
  const tray=new T.Group();world.add(tray);tray.position.set(6.2,-.29,-1.3);box([0,.03,0],[1.9,.08,2.1],0xcbd0b7,tray);for(const x of [-.95,.95])box([x,.13,0],[.06,.2,2.1],0x919d80,tray);for(const z of [-1.05,1.05])box([0,.13,z],[1.9,.2,.06],0x919d80,tray);print('螺丝盘',[6.2,-.335,.2],1.5,.32,world,'#735539');
  box([0,.18,0],[6.4,.32,4.2],color,base);for(const x of [-3.12,3.12])box([x,1,0],[.15,1.5,4.2],color,base);for(const z of [-2.02,2.02])box([0,1,z],[6.4,1.5,.15],color,base);
  for(const [x,z] of [[-2.7,-1.55],[2.7,-1.55],[-2.7,1.55],[2.7,1.55]]){mesh(new T.CylinderGeometry(.12,.12,.14,12),material(0x313d39),[x,-.01,z],base);mesh(new T.CylinderGeometry(.14,.14,1.55,12),material(0xaab5a3),[x,.95,z],base);}
  box([0,.08,0],[6.45,.16,4.25],color,cover);for(const x of [-2.2,-1.65,-1.1,-.55,0,.55,1.1,1.65,2.2])box([x,.167,.9],[.26,.014,.6],0x586a60,cover);print('FRUITION',[0,.169,-.65],2.4,.3,cover,'#f1f0de');
  box([0,.1,0],[5.8,.18,.38],0xa5b1b2,brace);for(const x of [-2.75,2.75])box([x,-.02,0],[.35,.3,.7],0xc2cbca,brace);print('固定支架',[0,.2,0],1.5,.25,brace,'#2a4343');
  let lamp=null,fan=null;
  if(product.id==='lamp'){
   rod([-.6,1.2,-2.05],[.3,4.1,-2.05],.12,0x4b605c,base);rod([.3,4.1,-2.05],[1.5,4.8,-1.5],.12,0x4b605c,base);
   mesh(new T.CylinderGeometry(.65,1.1,1.2,28,1,true),material(0xd5a049),[1.5,4.5,-1.5],base);lamp=material(0xffe5b1,{emissive:0xffc056,emissiveIntensity:0});mesh(new T.CylinderGeometry(.95,.95,.08,28),lamp,[1.5,3.94,-1.5],base);
  }else if(product.id==='fan'){
   rod([0,.8,-2.1],[0,3.6,-2.1],.18,0x527c73,base);const rim=mesh(new T.TorusGeometry(1.75,.13,12,48),material(0x40635c),[0,4.6,-2.1],base);fan=new T.Group();fan.position.set(0,4.6,-1.9);base.add(fan);
   for(let i=0;i<4;i++){const blade=new T.Group();blade.rotation.z=i*Math.PI/2;fan.add(blade);const b=box([.63,.24,0],[1.35,.54,.14],0x74a491,blade);b.rotation.z=.3;}
   mesh(new T.SphereGeometry(.28,16,12),material(0xc8bb83),[0,0,.04],fan);
   for(let i=0;i<8;i++){const a=i*Math.PI/4;rod([Math.cos(a)*1.65,4.6+Math.sin(a)*1.65,-1.66],[Math.cos(a+Math.PI)*1.65,4.6+Math.sin(a+Math.PI)*1.65,-1.66],.018,0xb8c7ba,base);}
  }else if(product.id==='speaker'){
   for(const x of [-1.55,1.55]){const cone=mesh(new T.CylinderGeometry(1,1,.18,28),material(0x1f343d),[x,1.22,2.13],base);cone.rotation.x=Math.PI/2;const dust=mesh(new T.SphereGeometry(.5,20,12),material(0x59746f),[x,1.22,2.24],base);dust.scale.z=.23;}
   rod([-1.8,1.9,-2.08],[-1.8,2.8,-2.08],.11,0x3e5559,base);rod([-1.8,2.8,-2.08],[1.8,2.8,-2.08],.11,0x3e5559,base);rod([1.8,2.8,-2.08],[1.8,1.9,-2.08],.11,0x3e5559,base);
  }else if(product.id==='clock'||product.id==='sensor'){
   box([0,1.45,2.12],[5.2,1.2,.15],product.id==='clock'?0xcbd6b5:0x91b09c,base);const screen=print(product.id==='clock'?'08:24':'24°C  56%',[0,1.45,2.21],4.5,.75,base,'#28483e');screen.rotation.set(0,0,0);for(const x of [-1.5,0,1.5])mesh(new T.SphereGeometry(.13,12,8),material(0x798c79),[x,.52,2.18],base);
  }else{
   for(const x of [-2.4,2.4]){rod([x,1.35,-2.05],[x*1.15,4.2,-2.6],.11,0x506a61,base);}
   for(const x of [-1.5,-.5,.5,1.5])box([x,.9,2.1],[.6,.42,.15],0x354e4e,base);
  }
  const connector=new T.Group();base.add(connector);connector.position.set(2.4,1.65,-1.4);box([0,0,0],[.55,.3,.35],0xe3cf9a,connector);print('J1',[0,.18,.05],.4,.18,connector,'#354c42');bodyPick(connector,'@connector');
  const cable=rod([1.6,1.6,-1.4],[2.3,1.6,-1.4],.055,0xc19b55,base),looseLead=new T.Group();base.add(looseLead);rod([1.6,1.6,-1.4],[2.8,.8,-1.45],.055,0xc19b55,looseLead);rod([2.8,.8,-1.45],[3.5,.55,-1.45],.055,0xc19b55,looseLead);
  bodyPick(cover,'@cover');bodyPick(brace,'@brace');
  const corners=[[-2.7,-1.55],[2.7,-1.55],[-2.7,1.55],[2.7,1.55]];
  M.SCREWS.forEach((id,i)=>{const g=new T.Group();world.add(g);mesh(new T.CylinderGeometry(.14,.14,.07,16),material(0xc6cdcd,{metalness:.65}),[0,.02,0],g);rod([0,-.32,0],[0,0,0],.055,0xa8b4b8,g);box([0,.059,0],[.2,.008,.035],0x45595b,g);box([0,.06,0],[.035,.008,.2],0x45595b,g);bodyPick(g,'@screw:'+id);screws[id]=g;});
  const driver=new T.Group();world.add(driver);driver.position.set(-6.4,-.13,3.4);rod([0,0,0],[1.2,0,0],.17,0xd2a24f,driver);rod([1.2,0,0],[2.4,0,0],.05,0xc2cbcc,driver);bodyPick(driver,'@driver');print('十字螺丝刀',[-5.1,-.335,4.2],2,.3,world,'#735539');
  const moved=new Map();let signature='',current=M.create(),motion=false,rpm=0,power=false;
  function target(group,p,rotation=0,turns=0){const start=group.position.clone(),end=new T.Vector3(...p);if(start.distanceTo(end)<1e-5&&Math.abs(group.rotation.z-rotation)<1e-5)return;const immediate=!signature||root.matchMedia?.('(prefers-reduced-motion: reduce)').matches;if(immediate){group.position.copy(end);group.rotation.z=rotation;return;}moved.set(group,{start,end,t:0,from:group.rotation.z,to:rotation,turns});motion=true;}
  function update(m,state){
   current=m||M.create();power=Boolean(state.power&&M.closed(current));rpm=Math.max(0,state.rpm||0);if(lamp)lamp.emissiveIntensity=power?Math.min(2,(state.current||0)*110):0;
   const key=JSON.stringify(current);if(key===signature)return;
   pcb.scale.setScalar(.65);const onTable=M.onTable(current);target(pcb,onTable?parks.board:[origin[0],origin[1]+.35,origin[2]]);pcb.visible=current.cover||onTable;
   target(cover,current.cover?parks.cover:[origin[0],origin[1]+1.95,origin[2]]);target(brace,current.brace?parks.brace:[origin[0],origin[1]+1.7,origin[2]]);target(connector,current.unplugged?[3.55,.55,-1.45]:[2.4,1.65,-1.4]);cable.visible=!current.unplugged;looseLead.visible=current.unplugged;
   M.SCREWS.forEach((id,i)=>{const loose=current.loose.includes(id),[x,z]=corners[i];target(screws[id],loose?[5.72+(i%2)*.75,-.13,-1.8+Math.floor(i/2)*.8]:[origin[0]+x,origin[1]+2.12,z],loose?Math.PI/2:0,loose?4:-4);});signature=key;
  }
  function advance(dt){for(const [g,a] of moved){a.t=Math.min(1,a.t+dt/.7);const t=a.t*a.t*tE(a.t);g.position.lerpVectors(a.start,a.end,t);g.position.y+=Math.sin(Math.PI*t)*1.1;g.rotation.z=a.from+(a.to-a.from)*t;g.rotation.y=a.turns*2*Math.PI*t;if(a.t===1){g.rotation.y=0;moved.delete(g);}}motion=moved.size>0;if(fan&&power&&!root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)fan.rotation.z-=rpm*Math.PI/30*dt;}
  const tE=t=>3-2*t;
  function projections(camera,width,height){const map={};const out=(id,p)=>{const v=p.clone().project(camera);map[id]={x:(v.x+1)*width/2,y:(1-v.y)*height/2};};for(const [id,g] of Object.entries(screws))out('@screw:'+id,g.position);out('@cover',cover.position.clone().add(new T.Vector3(0,.2,0)));out('@brace',brace.position.clone());out('@connector',connector.getWorldPosition(new T.Vector3()));out('@driver',driver.position.clone().add(new T.Vector3(.6,0,0)));return map;}
  return {update,advance,needsFrame:()=>motion||Boolean(fan&&power&&rpm>0&&!root.matchMedia?.('(prefers-reduced-motion: reduce)').matches),boardVisible:()=>pcb.visible,boardCenter:()=>pcb.position.clone().add(new T.Vector3(0,.5,0)),projections,snapshot:()=>({mechanics:JSON.parse(JSON.stringify(current)),boardOnTable:M.onTable(current),boardVisible:pcb.visible,removedOnDesk:{cover:current.cover,brace:current.brace,board:M.onTable(current),screws:current.loose.length},moving:motion,product:product.id})};
 }
 root.RepairShopEnclosure=Object.freeze({create});
})(typeof globalThis!=='undefined'?globalThis:this);
