/* Explicit exercise values; no device recommendations or business data access. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'&&module.exports?require('./training_catalog.js'):root.TrainingCatalog;
 const labs={
  ohm:{label:'电压（阻值题设1 kΩ）',options:[[1,'1 V'],[5,'5 V'],[10,'10 V']],initial:5},
  tcr:{label:'温度变化（题设TCR=25 ppm/K、R₀=1 kΩ）',options:[[0,'0 K'],[40,'升高40 K'],[80,'升高80 K']],initial:40},
  sense:{label:'电流（题设采样电阻10 mΩ）',options:[[.5,'0.5 A'],[1,'1 A'],[2,'2 A']],initial:1},
  sulfur:{label:'使用环境',options:[[false,'一般环境，仍按系列核对'],[true,'有含硫环境要求']],initial:true},
  cap:{label:'容量（理想公式，工作电压5 V）',options:[[.1,'0.1 µF'],[1,'1 µF'],[10,'10 µF']],initial:1},
  esr:{label:'ESR（题设纹波有效值1 A）',options:[[.05,'0.05 Ω'],[.2,'0.2 Ω'],[1,'1 Ω']],initial:.2},
  safety:{label:'应用位置（只作学习示意）',options:[['across','线间'],['earth','线与保护接地等位置']],initial:'across'},
  pulse:{label:'电压变化率（题设C=0.1 µF）',options:[[10,'10 V/µs'],[50,'50 V/µs'],[100,'100 V/µs']],initial:10},
  polarity:{label:'极性检查',options:[[true,'按规格正确接入'],[false,'极性接反']],initial:true},
  inductor:{label:'电流（题设DCR=0.1 Ω）',options:[[.5,'0.5 A'],[1,'1 A'],[3,'3 A']],initial:1},
  reactance:{label:'频率（题设L=1 µH）',options:[[1e4,'10 kHz'],[1e5,'100 kHz'],[1e6,'1 MHz']],initial:1e5},
  common:{label:'比较噪声模式（按图示绕向）',options:[['differential','理想等大反向差模电流'],['common','同向共模电流']],initial:'common'},
  loadcap:{label:'外部振荡电路与负载匹配',options:[[0,'没有接入振荡电路'],[15,'接入；C1/C2各15 pF'],[20,'接入；C1/C2各20 pF']],initial:15},
  clock:{label:'供电与使能（题设输出24 MHz）',options:[['off','没有供电'],['disabled','已供电，但OE关闭'],['on','正常供电并使能']],initial:'on'},
  ppm:{label:'频偏预算（题设中心频率26 MHz）',options:[[.5,'±0.5 ppm'],[2.5,'±2.5 ppm'],[20,'±20 ppm']],initial:2.5},
  pull:{label:'课堂频率调谐位置（不是实际电压曲线）',options:[[-50,'中心频率下偏50 ppm'],[0,'中心频率'],[50,'中心频率上偏50 ppm']],initial:0},
  mos:{label:'VGS幅度与极性（题设Ron只在|VGS|=10 V给出）',options:[[0,'VGS=0'],[2.5,'|VGS|=2.5 V，只看阈值不够'],[10,'|VGS|=10 V，极性正确']],initial:2.5},
  dualmos:{label:'题设两颗串联MOS的负载电流（各20 mΩ）',options:[[1,'1 A'],[2,'2 A'],[3,'3 A']],initial:2},
  diode:{label:'输入电源方向',options:[[true,'正常方向'],[false,'接反方向']],initial:true},
  rectify:{label:'选看整流前/后（题设5 V峰值、Vf≈0.7 V）',options:[['input','交流输入'],['output','半波整流输出']],initial:'output'},
  vf:{label:'本工作点Vf（题设电流1 A）',options:[[.3,'0.3 V示例'],[.5,'0.5 V示例'],[.7,'0.7 V示例']],initial:.3},
  zener:{label:'输入电压（题设Vz=5.1 V、Rs=200 Ω、RL=1 kΩ）',options:[[3,'3 V'],[6,'6 V'],[9,'9 V'],[12,'12 V']],initial:9},
  tvs:{label:'观察题设工作点（VRWM=5 V、VC=10 V@1 A脉冲）',options:[['normal','正常3.3 V信号'],['surge','12 V脉冲、源阻抗2 Ω']],initial:'surge'},
  led:{label:'限流电阻（题设5 V电源、蓝光LED Vf≈3 V）',options:[[100,'100 Ω'],[330,'330 Ω'],[1000,'1 kΩ']],initial:330},
  bjt:{label:'提供的基流幅度（题设Ic=20 mA、强迫β=10）',options:[[0,'0 mA'],[.1,'0.1 mA'],[2,'2 mA']],initial:.1},
  darlington:{label:'负载电流（题设VCE(sat)=1.0 V）',options:[[.1,'0.1 A'],[1,'1 A'],[2,'2 A']],initial:1},
  digital:{label:'输入电压（题设R1=R2=4.7 kΩ、VBE≈0.7 V）',options:[[0,'0 V'],[1,'1 V'],[3.3,'3.3 V']],initial:3.3}
 };
 function config(id){const d=C.lesson(id),lab=labs[d.lab];if(!lab)throw new RangeError('Unknown lab');return {...lab,options:lab.options.map(o=>[...o])};}
 function evaluate(id,x){
  const d=C.lesson(id),lab=config(id);if(!lab.options.some(o=>o[0]===x))throw new RangeError('Invalid lab choice');
  let metrics=[],status='',warn=false,signal='none',series=[];const fmt=(n,u)=>Number(n.toPrecision(5))+' '+u;
  switch(d.lab){
   case 'ohm':metrics=[['电流',fmt(x,'mA')],['功耗',fmt(x*x,'mW')]];status='I=V/R，P=V²/R。本例只展示理想值，不判断额定能力。';signal='current';break;
   case 'tcr':{const drift=1000*25e-6*x;metrics=[['题设阻值',fmt(1000+drift,'Ω')],['相对变化',fmt(25e-6*x*100,'%')]];status='线性近似只展示温漂，不把25 ppm/K作为所有薄膜的指标。';break;}
   case 'sense':metrics=[['采样电压',fmt(x*10,'mV')],['电阻功耗',fmt(x*x*10,'mW')]];status='小阻值也会发热；接触/走线压降可能影响采样。';signal='current';break;
   case 'sulfur':metrics=[['环境要求',x?'耐硫化':'按普通条件核对'],['需确认资料',x?'专用试验与判据':'完整规格条件']];status='有含硫要求时，不把未声明的普通系列自动认为合格；抗硫化也不保证永久免疫。';warn=x;break;
   case 'cap':metrics=[['理想储能',fmt(.5*x*1e-6*25*1e6,'µJ')],['电荷量',fmt(x*5,'µC')]];status='本例未包含偏压、ESR与ESL，不能代替真实器件曲线。';break;
   case 'esr':metrics=[['纹波导致的ESR损耗',fmt(x,'W')],['若电流阶跃1 A，初始ESR压降',fmt(x,'V')]];status='损耗用纹波有效值计算；电流阶跃压降是另一个条件，不等于整个输出纹波。寿命还须看温度与系列条件。';break;
   case 'safety':metrics=[['常见类别',x==='across'?'X类':'Y类'],['必须确认','设备要求、等级及认证']];status='只说明应用位置。图不指导带电接线，也不凭这一项宣布可用于具体设备。';break;
   case 'pulse':metrics=[['I=C×dV/dt估算',fmt(x*.1,'A')],['下一步核对','型号脉冲/纹波允许值']];status='电流越大，越需要核对电极、端接与热条件；本例没有给出任何真实型号的承受保证。';signal='current';break;
   case 'polarity':metrics=[['极性',x?'按要求接入':'接反'],['处理',x?'继续核对降额、ESR及浪涌':'不可按正常方式使用']];status='有极性钽电容不可任意反接；不同阴极体系需按对应规格书确认。';warn=!x;break;
   case 'inductor':metrics=[['直流铜损',fmt(x*x*.1,'W')],['磁饱和检查',x>2?'超过题设Isat=2 A':'低于题设Isat=2 A']];status='题设Isat只是本例判据；Irms、交流损耗、L下降和热条件还要分别核对。';warn=x>2;signal='current';break;
   case 'reactance':metrics=[['理想感抗',fmt(2*Math.PI*x*1e-6,'Ω')],['测量频率',fmt(x/1e3,'kHz')]];status='这里用固定L理想公式，接近SRF或材料损耗明显时不能外推。';break;
   case 'common':metrics=[['理想磁通趋势',x==='common'?'叠加':'抵消'],['实际还要看','漏感、寄生与损耗']];status='按本图绕向比较；“差模抵消”只指理想平衡条件，不是完全没有差模阻抗。';signal=x;break;
   case 'loadcap':metrics=[['有效负载电容',x?fmt(x/2+2,'pF'):'未构成振荡系统'],['题设目标CL','9.5 pF']];status=x?'CL≈C1C2/(C1+C2)+Cstray，题设Cstray=2 pF。波形假设其余振荡条件已满足；CL匹配不单独保证启动，还要看ESR、驱动和放大器。':'没有外部维持振荡的电路，无源晶体不能独立持续输出时钟。';warn=x!==15;signal=x===15?'clock':'none';break;
   case 'clock':metrics=[['时钟输出',x==='on'?'24 MHz（题设）':'本例没有有效时钟'],['周期',x==='on'?fmt(1e9/24e6,'ns'):'—']];status='此为已满足供电/接口条件的示例。OE/ST功能及未使能输出状态随系列变化，不假定所有型号都相同。';signal=x==='on'?'clock':'none';break;
   case 'ppm':metrics=[['26 MHz对应频偏预算','±'+fmt(26*x,'Hz')],['ppm预算','±'+x+' ppm']];status='Δf=f₀×ppm/10⁶。只换算给定预算，不编造TCXO温度补偿曲线或把老化忽略。';signal='clock';break;
   case 'pull':metrics=[['课堂输出频率',fmt(26e6*(1+x*1e-6)/1e6,'MHz')],['设定频偏',x+' ppm']];status='仅展示给定频偏的频率换算，不把它当作实际控制电压线性曲线或通用牵引范围。';signal='clock';break;
   case 'mos':{const p=d.id==='mos-p',on=x===10;metrics=[['VGS',fmt(p?-x:x,'V')],['导通条件',on?'符合题设Ron测试条件':'不能据阈值保证低阻'],['若2 A且Ron=20 mΩ',on?'0.08 W导通损耗':'Ron未提供，暂不推算']];status='本例Ron只在正确极性|VGS|=10 V给出；不把此电压当成所有MOS的要求。栅源极限、SOA、开关损耗另查。';warn=!on;signal=on?'current':'none';break;}
   case 'dualmos':metrics=[['题设串联总电阻','40 mΩ'],['导通损耗',fmt(x*x*.04,'W')]];status='两颗串联、各20 mΩ只是题设，不表示所有双MOS都共源、串联或可以并联。';signal='current';break;
   case 'diode':metrics=[['正常供电输出',x?'4.3 V（题设）':'反向被阻断，忽略漏电']];status='本例用5 V输入、0.7 V近似Vf；实际电压与电流、温度和系列有关。';signal=x?'current':'none';break;
   case 'rectify':{const input=Array.from({length:81},(_,i)=>5*Math.sin(i/80*Math.PI*4)),output=input.map(v=>Math.max(0,v-.7));series=[input,x==='output'?output:input];metrics=[['正峰值',x==='output'?'4.3 V近似':'5 V'],['输出形态',x==='output'?'脉动，不是稳压直流':'含正负半周']];status='理想半波教学示例；实际恢复、负载及滤波会改变波形。';signal='current';break;}
   case 'vf':metrics=[['题设1 A下导通损耗',fmt(x,'W')],['工作点Vf',fmt(x,'V')]];status='P≈If×Vf；不能由这个损耗直接判断温升，漏电与反向耐压也需比较。';signal='current';break;
   case 'zener':{const v=Math.min(5.1,x*1000/1200),load=v/1000,iz=Math.max(0,(x-v)/200-load);metrics=[['理想负载电压',fmt(v,'V')],['稳压管电流',fmt(iz*1000,'mA')],['稳压管功耗',fmt(v*iz*1000,'mW')]];status=iz>0?'理想示例进入反向稳压支路；真实Vz有测试电流与动态电阻条件。':'输入/负载条件不足，本例不能保持5.1 V。';warn=iz===0;signal=iz>0?'shunt':'current';break;}
   case 'tvs':metrics=[['示例工作点',x==='normal'?'3.3 V正常信号':'VC=10 V@1 A脉冲'],['保护判断',x==='normal'?'正常保持不动作':'芯片是否能承受10 V还需核对']];status='本脉冲用12 V源与2 Ω源阻抗近似，(12−10)/2=1 A。只描述这个给定工作点，不虚构完整TVS曲线或持续稳压。';warn=x==='surge';signal=x==='surge'?'shunt':'current';break;
   case 'led':metrics=[['LED电流',fmt(2000/x,'mA')],['限流电阻功耗',fmt(4000/x,'mW')]];status='用题设蓝光LED约3 V估算；没有给出实际LED最大允许电流，不能据数值宣布安全。';signal='current';break;
   case 'bjt':metrics=[['目标集电极电流','20 mA（题设）'],['强迫β=10时基流目标','2 mA'],['本次提供',fmt(x,'mA')]];status=x>=2?'基流达到题设目标；还需按数据手册核对VCE(sat)、热与SOA。':'本例基流不足，不能用放大区hFE直接保证饱和；不凭空推算实际负载电流。';warn=x<2;signal=x>=2?'current':'none';break;
   case 'darlington':metrics=[['导通损耗（只算VCE×IC）',fmt(x,'W')],['题设饱和压降','1.0 V']];status='压降是题设值而非所有达林顿的保证；高增益不等于低发热，还要核对输入/速度与热条件。';signal='current';break;
   case 'digital':{const ib=Math.max(0,(x-.7)/4700-.7/4700);metrics=[['近似可用基流',fmt(ib*1e6,'µA')],['本例R1/R2','各4.7 kΩ']];status='以VBE≈0.7 V估算并扣除R2分流；这不是实际输入阈值或负载开关保证，需按型号输入/输出条件核对。';signal=ib>0?'current':'none';break;}
   default:throw new RangeError('Missing lab calculation');
  }
  if(!series.length)series=[Array.from({length:61},()=>0),Array.from({length:61},(_,i)=>signal==='clock'?(i%20<10?1:0):signal==='none'?0:1)];
  return {metrics,status,warn,signal,series};
 }
 const api=Object.freeze({config,evaluate});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingCatalogLabs=api;
})(typeof globalThis!=='undefined'?globalThis:this);
