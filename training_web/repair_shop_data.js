/* Authored low-voltage teaching cases. Readings are scenario fixtures, not OEM data. */
(function(root){
 'use strict';
 const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
 const reasons=[['open','开路 / 无法导通'],['drift','参数漂移 / 超差'],['short','短路'],['esr','ESR过高'],['drive','控制 / 稳压失效'],['clock','停振']];
 function part(id,name,type,value,pkg,extra={}){return {id,name,type,value,pkg,tolerance:5,power:.125,voltage:16,price:18,...extra};}
 const R=(id,value,extra={})=>part(id,'厚膜电阻','resistor',value,'0805',extra);
 const C=(id,value,extra={})=>part(id,'铝电解电容','capacitor',value,'径向 Φ5 / 脚距2mm',{voltage:16,tolerance:20,esr:.3,polar:true,...extra});
 const F=()=>part('F1','快断保险丝','fuse',.5,'1206',{voltage:32,curve:'快断',price:12});
 const D=(id,name='肖特基二极管',extra={})=>part(id,name,'diode',1,'SOD-123',{voltage:30,pin:'A/K按图',polar:true,price:20,...extra});
 function fault(component,reason,symptom,bad,volts,wave,why){return {component,reason,symptom,bad,volts,wave,why};}
 const products=[
  {id:'lamp',name:'USB阅读台灯',customer:'林同学',story:'每天晚自习都靠它，想在今晚之前修好。',tag:'光与电流',voltage:5,flow:'5V → F1 → R1 → D1 → GND',behavior:'灯光稳定亮起，无明显闪烁。',parts:[F(),R('R1',220),D('D1','白光LED',{value:1,voltage:5,pkg:'直插 Φ5',pin:'长脚A / 短脚K',led:true,price:16})],normal:[5,5,2.0],faults:[
   fault('R1','open','插上电源后完全不亮。','OL · 超出量程',[5,5,0],'输出为0，无工作电流。','F1之后仍有5V，但电阻隔离检测为OL，说明供电没有在保险丝处中断；R1开路使LED支路无法形成回路。'),
   fault('R1','drift','能亮，但亮度明显低于以前。','2.20 kΩ',[5,5,2.0],'约1.36mA；正常约13.6mA。','本例LED压降约2V。R1从220Ω变成2.2kΩ，支路电流由(5−2)/220≈13.6mA降到约1.36mA，不能靠加大电源电压补救。'),
   fault('D1','open','开关打开了，灯还是不亮。','正向 OL / 反向 OL',[5,5,5],'电流为0；LED两端约5V。','供电与限流电阻都正常，LED节点却上升到5V；断电隔离后二极管档双向OL，支持LED开路，而不是阻值过大。')
  ]},
  {id:'fan',name:'桌面小风扇',customer:'周先生',story:'办公室有点闷，这台小风扇平时每天都用，麻烦帮我看看。',tag:'开关与保护',voltage:5,flow:'5V → F1 → 电机 → Q1(D/S) → GND；D1反并联电机',behavior:'电机在给定栅极驱动下稳定运转。',parts:[F(),part('Q1','逻辑电平N沟道MOS','mos',1,'SOT-23',{voltage:30,drive:4.5,pin:'1G / 2S / 3D',price:32}),D('D1')],normal:[5,.05,5],faults:[
   fault('F1','open','主板有电，但电机完全没有反应。','OL · 不导通',[0,0,0],'电机电流为0。','输入5V已确认，F1后节点为0V，隔离检测不导通。此关额外检测电机和D1均正常后，模拟一次老化开路；真实维修不能不查过流原因就换保险丝。'),
   fault('Q1','drive','有启动指令，风扇还是不转。','VGS=4.5V时D/S仍不导通',[5,5,5],'栅极驱动4.5V正常，电机电流为0。','电机正端有5V，低端却也为5V；已知驱动条件下MOS仍不能导通，电机两端没有有效压差。不能仅凭VGS(th)选替代品。'),
   fault('D1','short','启动时电源进入限流，扇叶不动。','正向0.01V / 反向0.01V',[.12,.01,.12],'限流电源输出被拉低。','续流二极管本应反向截止于正常供电，短路后形成异常旁路；隔离后双向近0V支持短路。先断电检查，再更换并进行限流测试。')
  ]},
  {id:'speaker',name:'便携蓝牙音箱',customer:'许女士',story:'希望周末露营时还能继续用，外壳不需要换。',tag:'滤波与反馈',voltage:5,flow:'5V → F1 → 功放；C1跨接电源；R1为反馈支路',behavior:'播放测试音稳定，电源纹波≤80mVpp。',parts:[F(),C('C1',470),R('R1',10000,{tolerance:1})],normal:[5,5,2.5],faults:[
   fault('C1','esr','小音量正常，低音一响就杂音、重启。','460 µF / ESR 6.8 Ω',[5,4.7,2.35],'电源纹波620 mVpp；目标≤80 mVpp。','容量接近标称不代表电容健康：本例ESR升高使负载瞬变时电源波动过大，需要同时检查ESR和负载波形。'),
   fault('R1','drift','声音明显变小，电源指示灯正常。','100 kΩ',[5,5,2.5],'电源纹波40mVpp正常；反馈增益偏离手册。','电源没有异常纹波，反馈支路电阻却从10kΩ漂移到100kΩ；本关给定反馈网络的闭环增益失配，不能把所有音量故障都归因于电容。'),
   fault('F1','open','插上电源也无法启动。','OL · 不导通',[0,0,0],'功放供电0V。','输入端正常，F1之后无电压且隔离检测开路。本例功放供电支路的短路检查正常，才进入保险丝替换。')
  ]},
  {id:'clock',name:'桌面电子钟',customer:'陈老师',story:'它一直放在讲台上用了很多年，请尽量保留原来的外壳。',tag:'时钟与信号',voltage:3.3,flow:'3.3V → 控制芯片；X1接振荡回路；R1上拉；C1去耦',behavior:'秒计数连续运行，时钟缓冲测试口32.768kHz。',parts:[part('X1','音叉无源晶体','crystal',32768,'圆柱2×6mm',{cl:12.5,esr:35000,drive:.000001,price:35}),R('R1',10000),part('C1','X7R MLCC','ceramic',.1,'0603',{voltage:16,tolerance:10,price:14})],normal:[1.65,3.3,3.3],faults:[
   fault('X1','clock','屏幕亮着，秒数不走。','等效串联电阻>1 MΩ',[1.65,3.3,3.3],'缓冲测试口0 Hz；目标32.768 kHz。','控制电源正常而时钟缓冲口没有振荡，断电后专用晶体分析仪也显示ESR严重超限。本例已排除负载电容和放大器异常，不是仅凭“不起振”就判断晶体坏。'),
   fault('R1','open','屏幕停在复位画面，按键无效。','OL · 超出量程',[0,.1,3.3],'复位输入一直保持低电平。','本例R1负责复位上拉；供电正常但复位节点偏低，隔离测量R1为OL。修复上拉路径后，芯片才能退出复位。'),
   fault('C1','short','插电后屏幕完全不亮。','0.4 Ω · 持续低阻',[0,0,.12],'限流状态，3.3V电源轨约0.12V。','C1位于电源与地之间。断电隔离后仍持续低阻，支持该MLCC短路；不能把电容刚接表时的充电瞬态当作短路。')
  ]},
  {id:'sensor',name:'环境监测小站',customer:'叶女士',story:'它平时放在书房里测温湿度，希望修好后能继续记录环境。',tag:'稳压与上拉',voltage:5,flow:'5V → U1(3.3V LDO) → 传感器；C1去耦；R1总线上拉',behavior:'3.3V供电稳定，总线空闲为高电平，能读取数据。',parts:[part('U1','3.3V低压差稳压器','ldo',3.3,'SOT-23-5',{voltage:6,current:.3,pin:'本板A引脚定义',price:36}),part('C1','X7R MLCC','ceramic',1,'0603',{voltage:16,tolerance:10,price:15}),R('R1',4700)],normal:[3.3,3.3,3.3],faults:[
   fault('U1','drive','输入有5V，传感器却一直重启。','输出负载隔离后仍只有1.1V',[1.1,1.1,1.1],'输入5V、使能有效，输出仅1.1V。','输入和使能条件正常，排除输出短路后，LDO在隔离负载的检查中仍不能稳压到3.3V。本关选择同引脚、同稳定性条件的替换件。'),
   fault('C1','short','系统启动不了，电源指示异常。','0.3 Ω · 持续低阻',[.15,.15,.15],'LDO限流，输出轨约0.15V。','本例C1隔离后持续低阻，而U1移除负载后能恢复3.3V；证据指向负载端电容短路，而非直接更换稳压器。'),
   fault('R1','open','电源正常，但总是读不到传感器。','OL · 超出量程',[3.3,3.3,.2],'总线空闲仅0.2V，目标接近3.3V。','供电正常但总线无法回到高电平；上拉电阻隔离检测开路。这里已经排除总线器件拉低故障，不能只看到低电平就认定芯片损坏。')
  ]},
  {id:'router',name:'USB迷你路由器',customer:'高先生',story:'外出经常靠它连网，这次想请你做一次完整检修。',tag:'电源与储能',voltage:5,flow:'5V → F1 → 降压开关级 → L1 → 3.3V；C1跨接输出',behavior:'负载测试不重启，3.3V输出纹波≤80mVpp。',parts:[F(),part('L1','屏蔽功率电感','inductor',10,'4×4mm',{current:1,isat:1.5,dcr:.15,price:30}),C('C1',220,{esr:.2})],normal:[5,3.3,3.3],faults:[
   fault('L1','open','输入正常，系统始终无法启动。','OL · 绕组不导通',[5,0,0],'开关级测试信号存在，输出0V。','开关级有输入和驱动，但电感绕组开路，输出无法输送能量；电感选型还要看饱和电流、温升电流和直流电阻。'),
   fault('C1','esr','待机正常，一传文件就掉线、重启。','210 µF / ESR 4.2 Ω',[5,3.15,3.15],'负载纹波480 mVpp；目标≤80 mVpp。','静态电压接近正常不能排除电源问题；负载时纹波异常，加上隔离ESR超限，支持输出滤波电容老化。'),
   fault('F1','open','插USB电源后所有指示灯都不亮。','OL · 不导通',[0,0,0],'降压级输入0V。','电源输入正常，F1后为0V，保险丝隔离检测开路；本例下游检查正常。换件后仍须做负载验证，而不是看到灯亮就交付。')
  ]}
 ];
 function spec(p){switch(p.type){
  case 'resistor':return `${p.value>=1000?p.value/1000+' kΩ':p.value+' Ω'} · ±${p.tolerance}% · ${p.power} W · ${p.pkg}`;
  case 'capacitor':return `${p.value} µF · ${p.voltage} V · ESR≤${p.esr} Ω · ${p.pkg} · 有极性`;
  case 'ceramic':return `${p.value} µF · ${p.voltage} V · X7R · ±${p.tolerance}% · ${p.pkg}`;
  case 'fuse':return `${p.value} A · ${p.voltage} V · ${p.curve} · ${p.pkg}`;
  case 'mos':return `N沟道 · ${p.voltage} V · RDS(on)在${p.drive}V下保证 · ${p.pkg} · ${p.pin}`;
  case 'diode':return `${p.led?'白光LED':'肖特基 / 1 A / 30 V'} · ${p.pkg} · ${p.pin}`;
  case 'ldo':return `${p.value} V输出 · ≥${p.current} A · ${p.pkg} · ${p.pin} · 指定稳定性兼容`;
  case 'inductor':return `${p.value} µH · Irms≥${p.current} A · Isat≥${p.isat} A · DCR≤${p.dcr} Ω · ${p.pkg}`;
  case 'crystal':return `${p.value/1000} kHz · CL ${p.cl} pF · ESR≤${p.esr/1000} kΩ · ${p.pkg}`;
  default:throw new RangeError('Unknown component type');
 }}
 function healthy(p){switch(p.type){
  case 'resistor':return p.value>=1000?p.value/1000+' kΩ':p.value+' Ω';
  case 'capacitor':return `${p.value} µF / ESR ${p.esr} Ω`;
  case 'ceramic':return `${p.value} µF / 无持续低阻`;
  case 'fuse':return '0.2 Ω · 导通';
  case 'mos':return 'VGS=4.5V时D/S能导通';
  case 'diode':return p.led?'正向2.0V / 反向OL':'正向0.28V / 反向OL';
  case 'ldo':return '隔离负载测试输出3.3V';
  case 'inductor':return `${p.value} µH / DCR ${p.dcr} Ω`;
  case 'crystal':return '等效串联电阻28 kΩ';
 }}
 function candidates(p,seed){
  const original={...p,sku:'原规格备件',compat:'已核对本板引脚、系列及工作条件'},better={...p,sku:'兼容系列备件',price:p.price+12,compat:'已核对本板引脚、系列及工作条件'},bad={...p,sku:'相近规格备件',price:8,compat:'已核对本板引脚、系列及工作条件'},wrong={...p,sku:'同类另一封装备件',pkg:'不同封装 / 脚位',price:9,compat:'不兼容'};
  if(p.type==='resistor'){better.tolerance=1;better.power=.25;bad.value=p.value*10;}
  else if(['capacitor','ceramic'].includes(p.type)){better.voltage=25;bad.voltage=2.5;}
  else if(p.type==='fuse'){bad.curve='慢断';better.price=p.price+5;}
  else if(p.type==='mos'){bad.drive=10;}
  else if(p.type==='inductor'){bad.isat=.4;}
  else if(p.type==='crystal'){bad.cl=6;}
  else if(p.type==='ldo'){bad.value=5;}
  else{bad.pin='K/A反向引脚';}
  const list=[original,bad,better,wrong];let x=seed>>>0;
  for(let i=list.length-1;i>0;i--){x=(Math.imul(x,1664525)+1013904223)>>>0;const j=x%(i+1);[list[i],list[j]]=[list[j],list[i]];}
  return list.map((p,i)=>({...p,stockId:'part-'+i}));
 }
 const rewards=[{id:'mint',title:'薄荷绿工作台',cost:80,points:80,description:'把维修台换成薄荷绿。'},{id:'sign',title:'「妙手修复」招牌',cost:180,points:180,description:'在店铺门头展示你的专属招牌。'},{id:'badge',title:'诊断达人纪念章',cost:300,points:400,description:'完成更多维修，点亮店铺纪念章。'}];
 const api=freeze({products,reasons,rewards,spec,healthy,candidates});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopData=api;
})(typeof globalThis!=='undefined'?globalThis:this);
