/* Game-only package examples. One contact map drives leads, pads and traces.
   Enlarged teaching geometry, not vendor CAD or guaranteed electrical ratings. */
(function(root){
 'use strict';
 const sources={
  sot:'https://assets.nexperia.com/documents/outline-drawing/SOT23.pdf',
  nmos:'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf',
  pmos:'https://assets.nexperia.com/documents/data-sheet/BSS84.pdf',
  dual:'https://assets.nexperia.com/documents/data-sheet/PMGD280UN.pdf',
  npn:'https://assets.nexperia.com/documents/data-sheet/PMBT2222A.pdf',
  pnp:'https://assets.nexperia.com/documents/data-sheet/PMBT2907A.pdf',
  darlington:'https://assets.nexperia.com/documents/data-sheet/BCV27.pdf',
  digital:'https://assets.nexperia.com/documents/data-sheet/PDTC114ET.pdf',
  xtal:'https://download.epsondevice.com/td/pdf/brief/FA-238_en.pdf',
  xo:'https://download.epsondevice.com/td/pdf/app/SG-210STF_en.pdf',
  tcxo:'https://abracon.com/datasheets/ILSI/I538.pdf',
  vcxo:'https://abracon.com/Support/PackageDrawing/Oscillators/ASFLV.PDF',
  diode:'https://www.vishay.com/docs/98678/ss14hm3_bia_ss14-m3ia.pdf',
  axial:'https://assets.nexperia.com/documents/data-sheet/1N4148_1N4448.pdf',
  zener:'https://assets.nexperia.com/documents/data-sheet/BZX79.pdf',
  layered:'https://www.murata.com/en-global/products/inductor',
  led:'https://www.vishay.com/docs/84215/vlmx234.pdf',
  aluminum:'https://www.chemi-con.co.jp/en/faq/detail.php?id=alEcapPolarity',
  film:'https://www.tdk-electronics.tdk.com/download/537974/76160cdb800cf40be24ef767fe5082bb/pdf-generaltechnicalinformation.pdf',
  wound:'https://www.coilcraft.com/en-us/products/rf/ferrite-core-chip-inductors/1812-%284532%29/1812ls/',
  common:'https://www.coilcraft.com/getmedia/38efcbd7-3710-40e5-9e90-1a4381ec2b36/comoee.pdf',
  molded:'https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/epl/epl3015/',
  sulfur:'https://www.vishay.com/docs/20034/rca.pdf',
  resistor:'https://www.vishay.com/en/resistors-fixed/',
  shunt:'https://www.vishay.com/en/product/30183/',
  mlcc:'https://www.murata.com/en-global/products/capacitor/ceramiccapacitor',
  tantalum:'https://www.kyocera-avx.com/docs/techinfo/Tantalum-NiobiumCapacitors/Tantalum-Capacitors-Characteristics-and-Component.pdf',
  tvs:'https://www.vishay.com/en/diodes/tvs-protection/'
 };
 const records={};
 const pin=(number,role,x,z)=>({number,role,point:[x,.04,z],pad:[.28,.035,.27]});
 function define(id,shape,title,reference,pins,size,extra={}){records[id]={id,shape,title,reference,source:sources[reference],pins,size,...extra};}
 const two=(roles=['1','2'],x=.72)=>[pin(1,roles[0],-x,0),pin(2,roles[1],x,0)];
 const sot=roles=>[pin(1,roles[0],-.475,.59),pin(2,roles[1],.475,.59),pin(3,roles[2],0,-.59)];
 const corner=roles=>[pin(1,roles[0],-.59,.43),pin(2,roles[1],.59,.43),pin(3,roles[2],.59,-.43),pin(4,roles[3],-.59,-.43)];
 define('res-thick','resistor','贴片双端电阻','resistor',two(),[1.5,.31,.65]);
 define('res-thin','resistor','贴片双端电阻','resistor',two(),[1.5,.31,.65]);
 define('res-sulfur','resistor','贴片双端电阻','sulfur',two(),[1.5,.31,.65]);
 define('res-sense','shunt','宽端接两端采样电阻','shunt',two(),[1.5,.27,.8]);
 define('cap-mlcc','mlcc','MLCC 包覆端电极','mlcc',two(),[1.5,.55,.78]);
 define('cap-aluminum','aluminum','径向引线铝电解 · 负极条','aluminum',two(['+','−'],.29),[1.16,1.75,1.16],{throughHole:true});
 define('cap-film','film','盒式径向引线薄膜电容','film',two(['1','2'],.50),[1.5,1.25,.65],{throughHole:true});
 define('cap-safety','film','盒式径向引线 · X/Y仅为类别示例','film',two(['1','2'],.50),[1.5,1.25,.65],{throughHole:true});
 define('cap-tantalum','tantalum','模压贴片钽 · 正极条','tantalum',two(['+','−']),[1.5,.68,.82],{rotatable:true});
 define('ind-wound','wound','铁氧体芯绕线贴片电感','wound',two(),[1.65,.85,1.0]);
 define('ind-layered','layered','双端叠层贴片电感','layered',two(),[1.5,.55,.8]);
 define('ind-molded','molded','一体成型 · 底部两端接','molded',two(),[1.6,.8,1.3]);
 define('ind-common','choke','双绕组磁芯 · 四端引线','common',[
  pin(1,'L1入',-.76,-.55),pin(2,'L2入',-.76,.55),pin(3,'L2出',.76,.55),pin(4,'L1出',.76,-.55)
 ],[1.9,1.4,1.5],{throughHole:true});
 define('xtal-passive','crystal','FA-238 四底焊盘外形','xtal',corner(['X1','外壳','X2','外壳']),[1.6,.4,1.2]);
 define('xtal-active','crystal','SG-210STF 四底焊盘外形','xo',corner(['ST','GND','OUT','VDD']),[1.6,.4,1.2]);
 define('xtal-tcxo','crystal','I538 四底焊盘外形','tcxo',corner(['GND/NC','GND','OUT','VDD']),[1.6,.5,1.2]);
 define('xtal-vcxo','crystal','ASFLV 四底焊盘外形','vcxo',corner(['VC','GND','OUT','VDD']),[1.6,.5,1.2]);
 for(const [id,ref,roles] of [
  ['mos-n','nmos',['G','S','D']],['mos-p','pmos',['G','S','D']],
  ['bjt-npn','npn',['B','E','C']],['bjt-pnp','pnp',['B','E','C']],
  ['bjt-darlington','darlington',['B','E','C']],['bjt-digital','digital',['IN','GND','OUT']]
 ])define(id,'sot23','SOT-23 · 两侧 2+1 引脚',ref,sot(roles),[1.45,.53,.65]);
 define('mos-dual','sot363','SOT-363 · 两侧 3+3 引脚','dual',[
  pin(1,'S1',-.50,.59),pin(2,'G1',0,.59),pin(3,'D2',.50,.59),
  pin(4,'S2',.50,-.59),pin(5,'G2',0,-.59),pin(6,'D1',-.50,-.59)
 ],[1.45,.5,.65]);
 define('dio-switch','axial','玻璃轴向 · 阴极环','axial',two(['A','K'],.87),[1.78,.47,.4],{rotatable:true});
 for(const id of ['dio-rectifier','dio-schottky'])define(id,'sma','SMA / DO-214AC · 阴极条','diode',two(['A','K']),[1.5,.62,.84],{rotatable:id==='dio-rectifier'});
 define('dio-zener','axial','轴向稳压二极管 · 阴极环','zener',two(['A','K'],.87),[1.78,.47,.4]);
 define('dio-tvs','sma','本关单向 TVS 外形 · 阴极条','tvs',two(['A','K']),[1.5,.62,.84]);
 define('dio-led','led','MiniLED · 阴极标记','led',two(['A','K'],.55),[1.15,.72,.65],{rotatable:true});
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}freeze(records);
 function profile(id){if(!records[id])throw new RangeError('Unknown game package: '+id);return records[id];}
 function layout(id,params={}){
  const d=profile(id),reversed=d.rotatable&&params.forward===false,sign=reversed?-1:1;
  return {...d,reversed,angle:reversed?Math.PI:0,pins:d.pins.map(p=>({...p,point:[p.point[0]*sign,p.point[1],p.point[2]*sign]}))};
 }
 function build(id,params={}){
  const d=profile(id),items=[],B=(part,p,size,c,rotation)=>items.push({type:'box',part,p,size,c,rotation}),R=(part,a,b,r,c)=>items.push({type:'rod',part,a,b,r,c}),P=(text,p,w,h,c='#eef4ff',rotation)=>items.push({type:'print',part:'mark',text,p,w,h,c,rotation});
  const silver=0xbac5cc,dark=0x303641,ceramic=0xc8b17e,gold=0xc0a357,copper=0xb87742;
  function feet(){for(const p of d.pins){const [x,,z]=p.point;
   if(d.throughHole)R('lead-'+p.number,[x,-.18,z],[x,.27,z],.035,silver);
   else{B('foot-'+p.number,[x,.04,z],[d.shape==='crystal'?.37:.22,.08,d.shape==='crystal'?.33:.22],silver);
    if(['sot23','sot363'].includes(d.shape)){R('lead-'+p.number,[x,.04,z],[x,.18,Math.sign(z)*.34],.034,silver);R('lead-'+p.number,[x,.18,Math.sign(z)*.34],[x,.23,Math.sign(z)*.30],.034,silver);}
   }
  }}feet();
  if(['resistor','shunt','mlcc','layered'].includes(d.shape)){
   const h=d.size[1],depth=d.size[2];B('body',[0,h/2+.06,0],[1.3,h,depth],d.shape==='mlcc'?ceramic:d.shape==='layered'?0x777a7d:dark);
   for(const x of [-.66,.66]){B('end-cap',[x,h/2+.04,0],[.25,h+.08,depth+.035],silver);}
   if(d.shape==='shunt')B('alloy',[0,.26,0],[.90,.07,depth-.06],0x96968e);
   if(d.shape==='resistor'||d.shape==='shunt')P(d.shape==='shunt'?'R'+String(params.resistance||10).padStart(3,'0'):id==='res-thin'?'1001':params.marking||'102',[0,h+.067,0],.82,.23);
  }else if(d.shape==='film'){
   B('body',[0,.74,0],[1.5,1.05,.65],0xaec3bd);P(id==='cap-safety'?'SAFETY':'FILM',[0,1.27,0],1.1,.25,'#243f44');
  }else if(d.shape==='tantalum'){
   B('body',[0,.39,0],[1.25,.58,.82],0xc8ad70);for(const x of [-.67,.67])B('end-cap',[x,.12,0],[.23,.24,.82],silver);
   B('positive-band',[-.46,.686,0],[.13,.015,.82],0x503d25);P('+',[-.28,.698,0],.18,.20,'#3f3020');
  }else if(d.shape==='aluminum'){
   R('sleeve',[0,.20,0],[0,1.62,0],.55,0x35596b);R('bottom-seal',[0,.16,0],[0,.23,0],.54,0x2d3034);R('can-top',[0,1.615,0],[0,1.68,0],.51,silver);
   R('can-rim',[0,1.58,0],[0,1.64,0],.555,silver);
   for(const a of [-.8,.8])R('vent',[-.32,1.684,a*.32],[.32,1.684,-a*.32],.014,0x6f7d86);
   const angle=.70;B('negative-stripe',[.56*Math.cos(angle),.94,.56*Math.sin(angle)],[.27,1.13,.015],0xe7e7d9,[0,Math.PI/2-angle,0]);
   for(const h of [.6,.95,1.3])P('−',[.576*Math.cos(angle),h,.576*Math.sin(angle)],.20,.21,'#22343d',[0,Math.PI/2-angle,0]);
  }else if(d.shape==='crystal'){
   B('ceramic-base',[0,.135,0],[1.6,.15,1.2],0xd2d9dc);B('metal-rim',[0,.245,0],[1.55,.075,1.15],gold);B('metal-lid',[0,.32,0],[1.47,.11,1.07],silver);
   R('pin-one',[-.54,.382,.37],[-.54,.39,.37],.045,0x263a50);P(id==='xtal-passive'?'XTAL':id==='xtal-active'?'XO':id==='xtal-tcxo'?'TCXO':'VCXO',[0,.382,0],.85,.23,'#344654');
  }else if(['sot23','sot363'].includes(d.shape)){
   B('case',[0,.34,0],[1.45,.38,.65],dark);R('pin-one',[-.48,.532,.20],[-.48,.54,.20],.035,0xd2d9dd);P(d.shape==='sot363'?'DUAL':id.startsWith('mos')?'MOS':'BJT',[.04,.535,0],.65,.20);
  }else if(d.shape==='sma'){
   B('case',[0,.35,0],[1.18,.50,.84],dark);for(const x of [-.64,.64]){B('end-lead',[x,.075,0],[.23,.15,.60],silver);R('lead', [x,.09,0],[Math.sign(x)*.51,.23,0],.045,silver);}
   B('cathode-band',[.38,.609,0],[.12,.017,.84],0xe6e7df);P('K',[.38,.627,0],.11,.16,'#273b45');
  }else if(d.shape==='axial'){
   R('case',[-.52,.26,0],[.52,.26,0],.20,0x96563e);R('cathode-ring',[.34,.26,0],[.44,.26,0],.209,0xe2ded3);
   for(const x of [-.87,.87]){R('lead',[x,.04,0],[x,.26,0],.028,silver);R('lead',[x,.26,0],[Math.sign(x)*.50,.26,0],.028,silver);}
  }else if(d.shape==='led'){
   B('base',[0,.19,0],[1.10,.30,.65],0xdde4e6);B('emitter',[0,.43,0],[.66,.30,.50],0xb39959);B('lens',[0,.61,0],[.72,.08,.54],0xcba857);
   B('cathode-mark',[.40,.348,0],[.075,.018,.64],0x264234);P('K',[.40,.37,0],.10,.16,'#152c25');
  }else if(d.shape==='molded'){
   B('core',[0,.40,0],[1.42,.64,1.22],0x484d52);for(const x of [-.70,.70])B('termination',[x,.075,0],[.23,.15,.85],silver);P('L',[0,.727,0],.26,.25,'#d5dce0');
  }else if(d.shape==='wound'){
   R('ferrite-core',[-.56,.45,0],[.56,.45,0],.18,0x4a5058);for(const x of [-.60,.60])B('core-flange',[x,.44,0],[.16,.64,.74],0x454c54);
   let first,last;for(let i=0;i<96;i++){const a=i/96*10*Math.PI,b=(i+1)/96*10*Math.PI,point=[-.50+i/96, .45+Math.cos(a)*.245,Math.sin(a)*.245],next=[-.50+(i+1)/96,.45+Math.cos(b)*.245,Math.sin(b)*.245];R('winding',point,next,.027,copper);first??=point;last=next;}
   R('coil-start',[-.72,.06,0],first,.027,copper);R('coil-end',last,[.72,.06,0],.027,copper);
  }else if(d.shape==='choke'){
   B('base',[0,.20,0],[1.9,.22,1.5],0xcbd0c4);for(const x of [-.66,.66])B('ferrite-leg',[x,.78,0],[.25,1.02,.73],0x444b52);
   for(const y of [.35,1.32])B('ferrite-return',[0,y,0],[1.58,.21,.73],0x444b52);
   B('ferrite-center',[0,.80,0],[1.2,.55,.42],0x444b52);
   for(const side of [1,2])for(let i=0;i<5;i++){const x=(side===1?-.48:.08)+i*.08,pts=[[x,.40,-.30],[x,1.20,-.30],[x,1.20,.30],[x,.40,.30],[x+.07,.40,-.30]];for(let k=1;k<pts.length;k++)R('winding-'+side,pts[k-1],pts[k],.026,side===1?copper:0xcf9654);}
   for(const p of d.pins){const x=p.number===1?-.48:p.number===4?-.09:p.number===2?.08:.47;
    R('winding-end-'+p.number,[p.point[0],.27,p.point[2]],[x,.33,p.point[2]],.026,copper);R('winding-end-'+p.number,[x,.33,p.point[2]],[x,.40,-.30],.026,copper);
   }
  }
  return {layout:layout(id,params),items};
 }
 // Inspect actual transformed GPU mesh vertices, not a self-reported zero gap.
 function inspectContacts(group,Vector,padTop,throughHole=false){
  group.updateMatrixWorld(true);const contacts=[];
  group.traverse(mesh=>{const name=mesh.userData.packagePart||'',match=name.match(throughHole?/^lead-(\d+)$/:/^foot-(\d+)$/);if(!match||!mesh.geometry)return;
   const position=mesh.geometry.attributes.position;let min=Infinity,max=-Infinity;for(let i=0;i<position.count;i++){const point=new Vector(position.getX(i),position.getY(i),position.getZ(i)).applyMatrix4(mesh.matrixWorld);min=Math.min(min,point.y);max=Math.max(max,point.y);}
   contacts.push({number:Number(match[1]),minY:min,maxY:max,gap:throughHole?Math.max(0,min-padTop,padTop-max):Math.abs(min-padTop),center:new Vector(0,0,0).applyMatrix4(mesh.matrixWorld).toArray()});
  });return contacts;
 }
 const api=Object.freeze({profile,layout,build,inspectContacts,ids:Object.freeze(Object.keys(records))});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingGamePackages=api;
})(typeof globalThis!=='undefined'?globalThis:this);
