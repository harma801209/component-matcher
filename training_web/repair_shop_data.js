/* Inventory and failure parameters. All readings are calculated by Physics. */
(function(root){
 'use strict';
 const P=typeof module!=='undefined'&&module.exports?require('./repair_shop_physics.js'):root.RepairShopPhysics;
 const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
 const reasons=[['open','开路 / 无法导通'],['drift','参数漂移 / 超差'],['short','短路'],['esr','ESR过高'],['drive','控制 / 稳压失效'],['clock','停振']];
 function part(id,name,type,value,pkg,extra={}){return {id,name,type,value,pkg,tolerance:5,power:.125,voltage:16,price:18,...extra};}
 const R=(id,value,extra={})=>part(id,'厚膜电阻','resistor',value,'0805',extra);
 const C=(id,value,extra={})=>part(id,'铝电解电容','capacitor',value,'径向 Φ5 / 脚距2mm',{voltage:16,tolerance:20,esr:.3,polar:true,...extra});
 const F=()=>part('F1','快断保险丝','fuse',.5,'1206',{voltage:32,curve:'快断',price:12});
 const D=(id,name='肖特基二极管',extra={})=>part(id,name,'diode',1,'SOD-123',{voltage:30,pin:'A/K按图',polar:true,price:20,...extra});
 const fault=(component,reason,symptom,why,enabled=true)=>({component,reason,symptom,why,enabled});
 // Positions are stable: never reorder old seed identities or erase old scores.
 const products=[
  {id:'lamp',name:'USB小夜灯',customer:'林同学',tag:'光与电流',voltage:5,flow:'5V → F1 → R1 → D1 → GND',parts:[F(),R('R1',220),D('D1','红光LED',{voltage:5,pkg:'直插 Φ5',pin:'长脚A / 短脚K',led:true,price:16})],faults:[
   fault('R1','open','插电后灯不亮。','R1开路使串联电流为0；LED阳极经LED接地，在本理想直流模型中为0V。还需结合隔离开路证据。'),
   fault('R1','drift','能亮，但明显变暗。','R1由220Ω漂至2.2kΩ，由5=I·(R1+0.2Ω)+VLED(I)求电流，LED压降也随电流变化，不能总当成2V。'),
   fault('D1','open','灯不亮，LED阳极电压却偏高。','LED开路使电流为0，R1无压降，LED阳极升至5V。隔离夹具具备3V限压能力；普通档位的任意OL并不都表示损坏。')
  ]},
  {id:'fan',name:'桌面小风扇',customer:'周先生',tag:'开关与保护',voltage:5,flow:'F1 → 电机 → Q1 → GND；D1阴极接电机正端，阳极接Q1漏极',parts:[F(),part('Q1','逻辑电平N沟道MOS','mos',1,'SOT-23',{voltage:30,drive:4.5,pin:'1G / 2S / 3D',price:32}),D('D1')],faults:[
   fault('F1','open','启动后风扇不转。','F1开路切断供电。本单电机与保护支路正常；真实维修仍需查明过流原因，模型不预测保险丝动作时间。'),
   fault('Q1','drive','有启动指令，风扇却不转。','本故障将Q1通道变为1GΩ，4.5V驱动下仍只有极小漏电流。电机有效压差接近0；阈值电压不能代替RDS(on)驱动条件。'),
   fault('D1','short','启动后电源限流，风扇几乎不转。','D1用0.05Ω短路表示，旁路电机，150mA限流使输出电压下降；由电阻、电流和电机反电动势一起计算。')
  ]},
  {id:'speaker',name:'便携蓝牙音箱',customer:'许女士',tag:'滤波与反馈',voltage:5,flow:'5V → 4Ω总源阻抗 → 电源轨；C1并联；Rf=90kΩ接输出与反相端；R1接反相端与缓冲Vref',parts:[F(),C('C1',470),R('R1',10000,{tolerance:1})],faults:[
   fault('C1','esr','播放不稳定，怀疑供电波动。','容量460µF仍在允许范围，但ESR由0.3Ω变为6.8Ω。规定脉冲负载下由RC微分方程计算纹波，不把某个纹波值直接等同于软件重启。'),
   fault('R1','drift','声音明显变小。','本关是非反相级，Rf固定90kΩ，R1为接Vref的Rg。Rg从10kΩ漂至100kΩ，增益1+Rf/Rg由10降至1.9；不是所有反馈电阻变大都会使声音变小。'),
   fault('F1','open','插电后无法工作。','F1开路切断供电；本单下游无短路，修复后再以规定负载和放大级计算验收，不代表真实音箱全部功能已测。')
  ]},
  {id:'clock',name:'桌面电子钟',customer:'陈老师',tag:'供电与复位',voltage:3.3,flow:'3.3V限流源 → VCC → 1kΩ负载 → GND；C1跨VCC/GND；R1从VCC上拉RESET（高阻）',parts:[part('X1','音叉无源晶体','crystal',32768,'圆柱2×6mm',{cl:12.5,esr:35000,drive:.000001,price:35}),R('R1',10000),part('C1','X7R MLCC','ceramic',.1,'0603',{voltage:16,tolerance:10,price:14})],faults:[
   fault('X1','clock','晶振停振关暂时停用。','缺少完整振荡器、负载电容和驱动模型，不提供虚构起振或ESR结论。旧成绩保留。',false),
   fault('R1','open','复位状态不确定，不能可靠运行。','R1开路后RESET失去唯一偏置路径，理想高阻节点浮空。真实电压还受漏电、寄生与探针影响，不能武断指定为0.1V或一直低电平。'),
   fault('C1','short','电源轨被拉低。','隔离C1持续0.4Ω；与1kΩ负载并联后，在50mA限流下约20mV，由V=IR计算，不是任意指定的0.12V。')
  ]},
  {id:'sensor',name:'环境监测小站',customer:'叶女士',tag:'稳压与上拉',voltage:5,flow:'5V → U1稳压行为块 → 100Ω负载；C1跨输出/GND；R1从输出上拉高阻总线',parts:[part('U1','3.3V低压差稳压器','ldo',3.3,'SOT-23-5',{voltage:6,current:.3,pin:'本板A引脚定义',price:36}),part('C1','X7R MLCC','ceramic',1,'0603',{voltage:16,tolerance:10,price:15}),R('R1',4700)],faults:[
   fault('U1','drive','输入有5V，但输出偏低。','本单稳压设定值由3.3V变为1.1V。排除短路后，以100Ω标准负载隔离检验，读数包含1Ω输出电阻的压降。不是所有坏LDO都输出1.1V。'),
   fault('C1','short','输出轨被拉低。','C1用0.3Ω短路表示，并联100Ω负载后使U1进入100mA限流，约30mV来自电路计算。此时发热，模型只用于短时观察，不预测热保护。'),
   fault('R1','open','供电正常，总线空闲状态却不确定。','R1开路后没有其他上下拉，总线为浮空，不能指定为0.2V，也不能由此直接确定某个具体通信故障。')
  ]},
  {id:'router',name:'USB迷你路由器',customer:'高先生',tag:'输出滤波与导通',voltage:5,flow:'5V → F1 → 模块输入；输出等效3.3V源 → 1.35Ω → L1(10µH / DCR) → C1及脉冲负载',parts:[F(),part('L1','屏蔽功率电感','inductor',10,'4×4mm',{current:1,isat:1.5,dcr:.15,price:30}),C('C1',220,{esr:.2})],faults:[
   fault('L1','open','有输入供电，输出却没有电压。','L1绕组开路切断供电路径；正常网络同时计算电感电流和电容电压，不能让电感电流瞬间跳变。仍未模拟磁饱和与开关控制，不能据此判断磁芯性能。'),
   fault('C1','esr','负载变化时输出电源波动。','容量210µF，ESR升至4.2Ω；用规定脉冲负载和RLC模型求最低电压及纹波。电感电流连续，负载跳变由电容支路暂时补偿，ESR引起额外电压跳变；平均值正常不能证明瞬态合格。'),
   fault('F1','open','输入保护后没有电压。','F1开路使模块输入、输出失电。导通修复后仍按规定输入与脉冲负载验收，不把网络软件功能当作已经验证。')
  ]}
 ];
 function spec(p){switch(p.type){
  case 'resistor':return `${p.value>=1000?p.value/1000+' kΩ':p.value+' Ω'} · ±${p.tolerance}% · ${p.power} W · ${p.pkg}`;
  case 'capacitor':return `${p.value} µF · ${p.voltage} V · ESR≤${p.esr} Ω（1kHz） · ${p.pkg} · 有极性`;
  case 'ceramic':return `${p.value} µF · ${p.voltage} V · X7R · ±${p.tolerance}% · ${p.pkg}`;
  case 'fuse':return `${p.value} A · ${p.voltage} V · ${p.curve} · ${p.pkg}`;
  case 'mos':return `N沟道 · ${p.voltage} V · 本关Ron=0.1Ω在${p.drive}V驱动下 · ${p.pkg} · ${p.pin}`;
  case 'diode':return `${p.led?'红光LED / 本关20mA上限':'肖特基 / 1 A / 30 V'} · ${p.pkg} · ${p.pin}`;
  case 'ldo':return `${p.value} V输出 · ≥${p.current} A等级（本板限流100mA） · ${p.pkg} · ${p.pin} · 本板兼容系列`;
  case 'inductor':return `${p.value} µH · Irms≥${p.current} A · Isat≥${p.isat} A · DCR≤${p.dcr} Ω · ${p.pkg}`;
  case 'crystal':return `${p.value/1000} kHz · CL ${p.cl} pF · ${p.pkg} · 动态模型暂未开放`;
  default:throw new RangeError('Unknown component type');
 }}
 const healthy=p=>P.isolated(p).value;
 for(const product of products){const normal=P.solve(product);product.story='请按测量证据检修，保留还可以继续使用的产品。';product.normal=normal.volts;product.behavior=normal.summary;product.model=P.config[product.id];
  for(const f of product.faults){const result=P.solve(product,f),required=product.parts.find(p=>p.id===f.component);f.volts=result.volts;f.wave=result.summary;f.bad=P.isolated(required,P.parameters(product,f)[f.component]).value;}
 }
 function candidates(p,seed){
  const original={...p,sku:'原规格备件',compat:'已核对本板引脚、系列及工作条件'},better={...p,sku:'兼容系列备件',price:p.price+12,compat:'已核对本板引脚、系列及工作条件'},bad={...p,sku:'相近规格备件',price:8,compat:'已核对本板引脚、系列及工作条件'},wrong={...p,sku:'同类另一封装备件',pkg:'不同封装 / 脚位',price:9,compat:'不兼容'};
  if(p.type==='resistor'){better.tolerance=1;better.power=.25;bad.value=p.value*10;}
  else if(['capacitor','ceramic'].includes(p.type)){better.voltage=25;bad.voltage=2.5;}
  else if(p.type==='fuse'){bad.curve='慢断';better.price=p.price+5;}
  else if(p.type==='mos')bad.drive=10;
  else if(p.type==='inductor')bad.isat=.4;
  else if(p.type==='crystal')bad.cl=6;
  else if(p.type==='ldo')bad.value=5;
  else bad.pin='K/A反向引脚';
  const list=[original,bad,better,wrong];let x=seed>>>0;
  for(let i=list.length-1;i>0;i--){x=(Math.imul(x,1664525)+1013904223)>>>0;const j=x%(i+1);[list[i],list[j]]=[list[j],list[i]];}
  return list.map((p,i)=>({...p,stockId:'part-'+i}));
 }
 const rewards=[{id:'mint',title:'薄荷绿工作台',cost:80,points:80,description:'把维修台换成薄荷绿。'},{id:'sign',title:'「妙手修复」招牌',cost:180,points:180,description:'在店铺门头展示你的专属招牌。'},{id:'badge',title:'诊断达人纪念章',cost:300,points:400,description:'完成更多维修，点亮店铺纪念章。'}];
 const api=freeze({products,reasons,rewards,spec,healthy,candidates});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopData=api;
})(typeof globalThis!=='undefined'?globalThis:this);
