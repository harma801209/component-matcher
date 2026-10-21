/* Explicit teaching PCB contacts and two-layer routing. No hidden fault/economy data.
 * Functional blocks are declared equivalents, not an invented OEM pinout or PCB.
 */
(function(root){
 'use strict';
 const layouts={lamp:[[-2.5,-.75],[-.1,-.75],[2.5,.75]],fan:[[-2.5,-1],[.2,.8],[2.6,-.8]],speaker:[[-2.5,-1],[-.1,.8],[2.55,.7]],clock:[[2.5,.65],[0,-1],[-2.5,.65]],sensor:[[-2.5,-.8],[0,.8],[2.5,-.8]],router:[[-2.5,-1],[.1,-.8],[2.5,.8]]};
 const ids={lamp:['F1','R1','D1'],fan:['F1','Q1','D1'],speaker:['F1','C1','R1'],clock:['X1','R1','C1'],sensor:['U1','C1','R1'],router:['F1','L1','C1']};
 const STEP=.1,NX=77,NZ=45,cache=new Map(),clone=x=>JSON.parse(JSON.stringify(x));
 const cell=p=>[Math.round((p[0]+3.8)/STEP),Math.round((p[1]+2.2)/STEP),0],world=c=>[Number((-3.8+c[0]*STEP).toFixed(4)),Number((-2.2+c[1]*STEP).toFixed(4))];
 function contacts(id){
  if(!layouts[id])throw new RangeError('Unknown repair PCB');
  const p={id,components:[],pins:{},nets:[],ports:[],routes:[],vias:[]};
  function comp(name,point,label,pins,main=false,size=[.9,.55]){p.components.push({id:name,point,label,main,size});for(const [role,x,z] of pins)p.pins[name+'.'+role]={point:[point[0]+x,point[1]+z],label:role,net:null};}
  const pair=(roles=['1','2'],x=.72)=>[[roles[0],-x,0],[roles[1],x,0]];
  ids[id].forEach((name,i)=>{
   let pins=pair();
   if(name==='F1')pins=pair(['1','2'],.62);
   if(name==='D1')pins=pair(['A','K'],id==='lamp'?.2:.61);
   if(name==='Q1')pins=[['G',-.475,.59],['S',.475,.59],['D',0,-.59]];
   if(name==='U1')pins=[['IN',-.42,.57],['GND',0,.57],['EN',.42,.57],['NC',.42,-.57],['OUT',-.42,-.57]];
   if(name==='X1')pins=[['OSC1',1,-.13],['OSC2',1,.13]];
   if(name==='C1'&&['speaker','router'].includes(id))pins=pair(['+','-'],.29);
   comp(name,layouts[id][i],name,pins,true);
  });
  if(id==='sensor')for(const [role,number] of [['IN',1],['GND',2],['EN',3],['NC',4],['OUT',5]])p.pins['U1.'+role].label=number+' '+role;
  if(id==='fan')for(const [role,number] of [['G',1],['S',2],['D',3]])p.pins['Q1.'+role].label=number+role;
  comp('J_PWR',[-2.9,1.55],id==='clock'?'3.3V / GND':'5V / GND',pair(['VIN','GND'],.35),false,[1.15,.5]);
  function net(name,label,kind,members){for(const ref of members){if(!p.pins[ref]||p.pins[ref].net)throw new Error('Invalid/duplicate pad '+ref);p.pins[ref].net=name;}p.nets.push({id:name,label,kind,members});}
  if(id==='lamp'){
   net('VIN','5V输入','power',['J_PWR.VIN','F1.1']);net('VCC','保险丝后 / R1前','power',['F1.2','R1.1']);net('LED_A','LED阳极','signal',['R1.2','D1.A']);net('GND','电源负极 / GND','ground',['D1.K','J_PWR.GND']);
  }else if(id==='fan'){
   comp('M1',[0,-1.25],'电机等效',pair(['+','-'],.5),false,[1.1,.6]);comp('J_GATE',[2.7,1.45],'4.5V栅极驱动',pair(['OUT','GND'],.35),false,[1.2,.5]);
   net('VIN','5V限流输入','power',['J_PWR.VIN','F1.1']);net('VCC','电机正端 / D1阴极','power',['F1.2','M1.+','D1.K']);net('MOTOR_LOW','电机负端 / Q1漏极','signal',['M1.-','Q1.D','D1.A']);net('GATE','栅极4.5V','signal',['J_GATE.OUT','Q1.G']);net('GND','电源负极 / Q1源极','ground',['Q1.S','J_PWR.GND','J_GATE.GND']);
  }else if(id==='speaker'){
   comp('RS',[-.55,-1.2],'等效Rs 3.8Ω',pair(['1','2'],.35));
   comp('U_AMP',[1.35,-1.2],'理想放大级',[['VCC',-.4,-.5],['GND',.4,-.5],['IN+',-.4,.5],['IN-',.4,.5],['OUT',.65,0]],false,[1,.65]);
   comp('RF',[3,-1.1],'Rf 90kΩ',pair(['1','2'],.35));comp('LOAD',[1.2,1.55],'规定脉冲负载',pair(['+','-'],.35),false,[1,.5]);
   comp('VREF',[2.8,1.65],'Vref=VCC/2',[['VCC',-.35,-.25],['GND',.35,-.25],['OUT',-.35,.25]],false,[1.1,.45]);
   comp('SIGNAL',[.2,-.2],'Vref+100mVrms',[['OUT',-.3,0],['GND',.3,0]],false,[1.1,.35]);
   net('VIN','5V输入','power',['J_PWR.VIN','F1.1']);net('POST_FUSE','F1后 / Rs前','power',['F1.2','RS.1']);net('VCC','4Ω总源阻抗后电源轨','power',['RS.2','C1.+','U_AMP.VCC','VREF.VCC','LOAD.+']);
   net('OUT','放大器输出 / 反馈上端','signal',['U_AMP.OUT','RF.1']);net('INV','反相端 / 反馈节点','signal',['RF.2','U_AMP.IN-','R1.1']);net('VREF','缓冲参考电压','signal',['R1.2','VREF.OUT']);net('SIGNAL','非反相输入检验信号','signal',['SIGNAL.OUT','U_AMP.IN+']);
   net('GND','供电与检验负载回路','ground',['J_PWR.GND','C1.-','U_AMP.GND','LOAD.-','VREF.GND','SIGNAL.GND']);
  }else if(id==='clock'){
   comp('RLOAD',[.4,.1],'1kΩ等效负载',pair(['1','2'],.35));
   comp('U_CTRL',[.15,1.6],'控制块 / 高阻RESET',[['VCC',-.55,-.3],['GND',.55,-.3],['RESET',-.55,.25],['OSC1',.55,0],['OSC2',.55,.3]],false,[1.1,.5]);
   net('VCC','3.3V限流电源轨','power',['J_PWR.VIN','C1.1','R1.1','U_CTRL.VCC','RLOAD.1']);net('RESET','高阻复位上拉节点','signal',['R1.2','U_CTRL.RESET']);net('GND','电源负极 / GND','ground',['C1.2','RLOAD.2','U_CTRL.GND','J_PWR.GND']);
   net('OSC1','晶体支路：未建模','unmodeled',['X1.OSC1','U_CTRL.OSC1']);net('OSC2','晶体支路：未建模','unmodeled',['X1.OSC2','U_CTRL.OSC2']);
  }else if(id==='sensor'){
   comp('RLOAD',[1.8,1.25],'100Ω检验负载',pair(['1','2'],.35));comp('BUS',[2.7,1.85],'总线输入∞Ω',[['IN',-.35,0],['GND',.35,0]],false,[1.1,.4]);
   net('VIN','5V输入 / EN固定使能','power',['J_PWR.VIN','U1.IN','U1.EN']);net('VOUT','稳压输出电源轨','power',['U1.OUT','C1.1','R1.1','RLOAD.1']);net('BUS','高阻总线上拉节点','signal',['R1.2','BUS.IN']);net('GND','电源负极 / GND','ground',['J_PWR.GND','U1.GND','C1.2','RLOAD.2','BUS.GND']);
  }else{
   comp('MODULE',[-1.15,.45],'输入100Ω / 3.3V等效',[['IN',-.55,-.2],['GND',.55,-.2],['OUT',-.55,.2]],false,[1.2,.6]);comp('RS',[-.5,-1.85],'等效Rs 1.35Ω',pair(['1','2'],.35));comp('LOAD',[1.15,1.55],'规定脉冲负载',pair(['+','-'],.35),false,[1.1,.5]);
   net('VIN','5V输入','power',['J_PWR.VIN','F1.1']);net('MODULE_IN','模块输入 / VIN','power',['F1.2','MODULE.IN']);net('SOURCE','3.3V输出等效源','power',['MODULE.OUT','RS.1']);net('PRE_L','1.35Ω后 / L1前','power',['RS.2','L1.1']);net('VOUT','电感后 / 输出电源轨','power',['L1.2','C1.+','LOAD.+']);net('GND','输出及输入公共地','ground',['C1.-','LOAD.-','MODULE.GND','J_PWR.GND']);
  }
  const portNets={lamp:['VCC','VCC','LED_A'],fan:['VCC','MOTOR_LOW','VCC'],speaker:['VCC','VCC','VREF'],clock:['VCC','RESET','VCC'],sensor:['VOUT','VOUT','BUS'],router:['MODULE_IN','VOUT','VOUT']}[id];
  for(let i=0;i<3;i++){const point=[[-3.15,-1.85],[id==='router'?1.4:0,-2],[3.15,.2]][i],name='TP'+(i+1),ref=name+'.1',n=p.nets.find(n=>n.id===portNets[i]);p.pins[ref]={point,label:name,net:n.id};n.members.push(ref);p.ports.push({id:name,ref,net:n.id,part:ids[id][i],point});}
  p.pins['TP_GND.1']={point:[-3.45,0],label:'GND',net:'GND'};p.nets.find(n=>n.id==='GND').members.push('TP_GND.1');
  for(const pin of Object.values(p.pins))pin.cell=cell(pin.point);
  return p;
 }
 function route(p){
  const key=(x,z,l)=>l*NX*NZ+z*NX+x,decode=k=>[k%NX,Math.floor(k/NX)%NZ,Math.floor(k/(NX*NZ))],reserved=new Map(),used=new Map();
  for(const pin of Object.values(p.pins)){const [x,z]=pin.cell;for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++)for(let l=0;l<2;l++){const k=key(x+dx,z+dz,l),owner=pin.net||'NC';if(!reserved.has(k))reserved.set(k,new Set());reserved.get(k).add(owner);}}
  const blocked=(x,z,l,net)=>{if(x<0||z<0||x>=NX||z>=NZ)return true;const r=reserved.get(key(x,z,l));if(r&&[...r].some(n=>n!==net))return true;
   const [wx,wz]=world([x,z,l]);if([[-3.65,-2.15],[3.65,-2.15],[-3.65,2.15],[3.65,2.15]].some(([a,b])=>Math.hypot(wx-a,wz-b)<.23))return true;
   for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++){const owner=used.get(key(x+dx,z+dz,l));if(owner&&owner!==net)return true;}return false;};
  const heap=[];function push(item){heap.push(item);let i=heap.length-1;while(i){const parent=(i-1)>>1;if(heap[parent][0]<=item[0])break;heap[i]=heap[parent];i=parent;}heap[i]=item;}
  function pop(){const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1][0]<heap[c][0])c++;if(heap[c][0]>=last[0])break;heap[i]=heap[c];i=c;}heap[i]=last;}return first;}
  function path(start,end,net){if(blocked(...start,net)||blocked(...end,net))throw new Error('Pad keepout conflict '+p.id+':'+net);heap.length=0;const startKey=key(...start),endKey=key(...end),cost=new Map([[startKey,0]]),previous=new Map(),done=new Set();push([0,startKey]);
   while(heap.length){const [,k]=pop();if(done.has(k))continue;done.add(k);if(k===endKey){const out=[];for(let at=k;at!==undefined;at=previous.get(at))out.push(decode(at));return out.reverse();}const [x,z,l]=decode(k);
    for(const [xx,zz,ll] of [[x+1,z,l],[x-1,z,l],[x,z+1,l],[x,z-1,l],[x,z,1-l]]){if(blocked(xx,zz,ll,net))continue;const next=key(xx,zz,ll),value=cost.get(k)+(ll!==l?12:ll===0?1:1.08);if(value>=(cost.get(next)??Infinity))continue;cost.set(next,value);previous.set(next,k);push([value+Math.abs(xx-end[0])+Math.abs(zz-end[1])+(ll===end[2]?0:8),next]);}
   }throw new Error('Unroutable teaching net '+p.id+':'+net);
  }
  const nets=[...p.nets].sort((a,b)=>b.members.length-a.members.length);
  for(const n of nets){const anchor=p.pins[n.members[0]].cell;for(const ref of n.members.slice(1)){const cells=path(p.pins[ref].cell,anchor,n.id);p.routes.push({net:n.id,from:ref,to:n.members[0],cells});for(let i=0;i<cells.length;i++){const c=cells[i];used.set(key(...c),n.id);if(i&&c[2]!==cells[i-1][2]&&!p.vias.some(v=>v.net===n.id&&v.cell[0]===c[0]&&v.cell[1]===c[1]))p.vias.push({net:n.id,cell:[c[0],c[1]],point:world(c)});}}}
  return p;
 }
 function get(id){if(!cache.has(id))cache.set(id,route(contacts(id)));return clone(cache.get(id));}
 const api=Object.freeze({get,world,layout:id=>layouts[id].map(p=>[...p]),VERSION:1});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopBoard=api;
})(typeof globalThis!=='undefined'?globalThis:this);
