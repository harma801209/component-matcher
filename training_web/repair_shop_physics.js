/* Deterministic, low-voltage equivalent-circuit models. SI units internally.
 * These are declared teaching circuits, NOT OEM device simulations or SPICE.
 * Derivations, limits and independent numerical checks: docs/repair-shop-physics.md.
 */
(function(root){
 'use strict';
 const VERSION=2, fmt=(x,d=2)=>Number.isFinite(x)?Number(x.toFixed(d)).toString():'未定义';
 const voltage=x=>x===null?'浮空 · 无唯一确定电压':Number.isFinite(x)?x.toFixed(2)+' V':'该测点未建模';
 const parallel=(a,b)=>1/(1/a+1/b);
 const diodeVoltage=(i,led=true)=>{
  if(i<=0)return 0;
  const nvt=led?2*.02585:.02585,rs=led?2:.2;
  const is=(led?.02:.001)/Math.expm1(((led?2:.28)-(led?.02:.001)*rs)/nvt);
  return nvt*Math.log1p(i/is)+i*rs;
 };
 function ledLoop(vs,r,open=false){
  if(open||!Number.isFinite(r))return {i:0,vd:open?vs:0,pr:0};
  let lo=0,hi=vs/r;for(let k=0;k<90;k++){const i=(lo+hi)/2;if(i*r+diodeVoltage(i)>vs)hi=i;else lo=i;}
  const i=(lo+hi)/2;return {i,vd:diodeVoltage(i),pr:i*i*r};
 }
 // Periodic steady state of a Thevenin source Rs feeding (C + ESR) and a
 // piecewise constant current sink. Vc is the ideal capacitor voltage.
 function pulse({vs,rs,c,esr,low,high,frequency,duty}){
  if(!(rs>0&&c>0&&esr>=0&&frequency>0&&duty>0&&duty<1))throw new RangeError('Invalid RC circuit');
  const tau=(rs+esr)*c,th=duty/frequency,tl=(1-duty)/frequency;
  const A=Math.exp(-th/tau),B=Math.exp(-tl/tau),u=vs-rs*high,w=vs-rs*low;
  const v0=(B*(-Math.expm1(-th/tau))*u+(-Math.expm1(-tl/tau))*w)/(-Math.expm1(-(th+tl)/tau));
  const v1=u+(v0-u)*A,rail=(vc,i)=>(esr*vs+rs*vc-rs*esr*i)/(rs+esr);
  const samples=[rail(v0,low),rail(v0,high),rail(v1,high),rail(v1,low)];
  const intRail=(vstart,target,i,t)=>((esr*vs-rs*esr*i)*t+rs*(target*t+(vstart-target)*tau*(-Math.expm1(-t/tau))))/(rs+esr);
  const loadPower=frequency*(high*intRail(v0,u,high,th)+low*intRail(v1,w,low,tl));
  return {mean:vs-rs*(high*duty+low*(1-duty)),min:Math.min(...samples),max:Math.max(...samples),ripple:Math.max(...samples)-Math.min(...samples),samples,v0,v1,tau,loadPower};
 }
 // Two-state R-L-(ESR+C) output network. Exact real-eigenvalue propagation
 // preserves inductor current and capacitor voltage across load steps.
 function rlcPulse(q){
  const {vs,rs,c,esr,low,high,frequency,duty,l}=q;
  if(!(rs>0&&c>0&&l>0&&esr>=0&&frequency>0&&duty>0&&duty<1))throw new RangeError('Invalid RLC circuit');
  const aa=-(rs+esr)/l,bb=-1/l,cc=1/c,delta=aa*aa+4*bb*cc;
  if(!(delta>0))throw new RangeError('This RLC teaching solver requires an overdamped network');
  const diff=Math.sqrt(delta),r1=(aa+diff)/2,r2=(aa-diff)/2;
  const mv=(m,x)=>[m[0]*x[0]+m[1]*x[1],m[2]*x[0]+m[3]*x[1]],add=(x,y)=>[x[0]+y[0],x[1]+y[1]],sub=(x,y)=>[x[0]-y[0],x[1]-y[1]];
  const mat=t=>{const u=Math.exp(r1*t),v=Math.exp(r2*t),s=(u-v)/diff;return [(aa-r2)*s+v,bb*s,cc*s,-r2*s+v];};
  const th=duty/frequency,tl=(1-duty)/frequency,H=mat(th),T=mat(tl),star=i=>[i,vs-rs*i],sh=star(high),sl=star(low),bh=sub(sh,mv(H,sh)),bl=sub(sl,mv(T,sl));
  const M=[T[0]*H[0]+T[1]*H[2],T[0]*H[1]+T[1]*H[3],T[2]*H[0]+T[3]*H[2],T[2]*H[1]+T[3]*H[3]],rhs=add(mv(T,bh),bl);
  const a=1-M[0],b=-M[1],d=1-M[3],e=-M[2],det=a*d-b*e;
  const x0=[(d*rhs[0]-b*rhs[1])/det,(-e*rhs[0]+a*rhs[1])/det],x1=add(mv(H,x0),bh);
  const rail=(x,i)=>x[1]+esr*(x[0]-i),at=(x,i,t)=>add(star(i),mv(mat(t),sub(x,star(i))));
  const samples=[rail(x0,low),rail(x0,high),rail(x1,high),rail(x1,low)];
  let powerIntegral=0;
  for(const [start,i,duration,m] of [[x0,high,th,H],[x1,low,tl,T]]){
   const z=sub(start,star(i)),dz=[aa*z[0]+bb*z[1],cc*z[0]],ddz=[aa*dz[0]+bb*dz[1],cc*dz[0]],dv=esr*dz[0]+dz[1],ddv=esr*ddz[0]+ddz[1];
   const k1=(ddv-r2*dv)/diff,k2=(r1*dv-ddv)/diff,ratio=-k2/k1,t=ratio>0?Math.log(ratio)/diff:NaN;
   if(t>0&&t<duration)samples.push(rail(at(start,i,t),i));
   // Integral exp(A*t)z dt = A^-1 (exp(A*t)-I)z.
   const y=sub(mv(m,z),z),integral=[y[1]/cc,(y[0]-aa*y[1]/cc)/bb];
   powerIntegral+=i*((vs-rs*i)*duration+esr*integral[0]+integral[1]);
  }
  return {mean:vs-rs*(high*duty+low*(1-duty)),min:Math.min(...samples),max:Math.max(...samples),ripple:Math.max(...samples)-Math.min(...samples),samples,x0,x1,loadPower:powerIntegral*frequency,eigenvalues:[r1,r2]};
 }
 const config={
  lamp:{title:'串联LED直流模型',conditions:['5 V理想直流源；F1闭合电阻0.2 Ω；R1串联红光LED后回到GND。','25°C；LED采用Shockley方程加2 Ω串阻，n=2，并以20 mA时2 V校准；不是任意LED的通用压降。','验收：LED电流10–20 mA、R1损耗不超过备件额定功率。'],limits:'只计算稳态电流和功率，不预测亮度、结温或长期寿命。',ports:['F1后','R1前','LED阳极']},
  fan:{title:'永磁直流电机稳态模型',conditions:['5 V限流源，最大150 mA；F1=0.2 Ω；Q1在VGS=4.5 V时Ron=0.1 Ω。','电机Rw=10 Ω、Kt=Ke=0.05（SI）、黏性阻尼b=0.00005 N·m·s/rad；D1反并联电机。','稳态：Vmotor=I·Rw+Ke·ω；Kt·I=b·ω。短路二极管用0.05 Ω表示。验收转速600–1000 rpm且未限流。'],limits:'不模拟起动、静摩擦、关断反冲、温升和保险丝熔断时间；不能据此选择真实电机保险丝。',ports:['F1后 / 电机正端','Q1漏极','D1阴极 / 电机正端']},
  speaker:{title:'供电RC瞬态 + 非反相放大器',conditions:['5 V源经4 Ω等效源阻抗（含F1的0.2 Ω）供电；C1与负载并联；外接负载20↔100 mA、1 kHz、50%占空比。','理想非反相放大器：Rf=90 kΩ从输出接反相端，R1=10 kΩ从反相端接缓冲Vref；Vref=供电平均值/2。输入100 mVrms、100 Hz，增益1+Rf/R1。','验收：供电最低4.5 V、纹波≤80 mVpp、增益9.5–10.5，输出峰值离电源轨≥0.2 V。'],limits:'外接负载是规定的检验刺激，不模拟音乐、扬声器或软件重启；理想运放假设不适用于任意实际功放。',ports:['F1后供电平均值','C1正端平均值','缓冲Vref']},
  clock:{title:'时钟板VCC / RESET直流检查',conditions:['3.3 V限流源，最大50 mA；控制负载1 kΩ；C1并联电源；R1=10 kΩ将RESET上拉至VCC。','RESET输入理想高阻，无内部上下拉；R1开路时节点浮空，电压无唯一解。X1对应金点改测缓冲器VCC，而非晶体引脚。','验收仅限VCC为3.3 V±5%、RESET具有有效上拉；晶振停振工单暂停发放。'],limits:'不模拟晶体起振、频率、芯片计时和复位时序，不能据此宣称电子钟计时精度已合格。',ports:['缓冲器VCC（非晶体引脚）','RESET','VCC / C1正端']},
  sensor:{title:'有限流的LDO行为模型 + 上拉',conditions:['输入5 V；给定稳压块Vset=3.3 V、压差0.2 V、输出电阻1 Ω、限流100 mA；负载100 Ω，C1并联输出。','R1=4.7 kΩ将高阻总线输入上拉至输出轨；无其他上下拉。R1开路后是浮空，不是固定0.2 V。','验收：输出3.3 V±5%、总线上拉完整、未限流。隔离U1用100 Ω标准负载测输出。'],limits:'不模拟数字通信、实际LDO环路稳定性、过热关断；短路计算为短时限流观察。真实替换必须查具体LDO数据表的输出电容与ESR要求。',ports:['U1输出','C1正端','总线空闲电压']},
  router:{title:'RLC输出网络负载检验',conditions:['模块输出用3.3 V源表示，经1.35 Ω源阻抗和L1（10µH / DCR 0.15Ω）到输出；C1及ESR并联在输出与GND之间。','同时计算电感电流与电容内部电压，负载跳变时两者连续；负载20↔300 mA、2 kHz、10%高负载占空比，ESR在检验频段视为常数。输入为5V、F1=0.2Ω和100Ω等效总负载。','输入≥4.5 V时启用输出等效；输入或L1断路取放电后稳态0V。验收：输入≥4.5 V、输出最低≥3 V、纹波≤100 mVpp，输出等效源功率不超过输入功率。'],limits:'电感按线性10µH处理；不模拟降压开关、控制环路、磁饱和、热保护或网络软件。只验收所列RLC网络，不是完整路由器仿真。',ports:['F1后 / 模块输入','L1后平均电压','C1正端平均电压']}
 };
 function parameters(product,fault=null,candidate=null){
  const parts=Object.fromEntries(product.parts.map(p=>[p.id,{...p}]));
  if(fault&&!candidate){const p=parts[fault.component];
   if(fault.reason==='open')p.open=true;
   if(fault.reason==='drift')p.value*=10;
   if(fault.reason==='short')p.short=product.id==='fan'?.05:product.id==='clock'?.4:.3;
   if(fault.reason==='esr'){p.esr=product.id==='speaker'?6.8:4.2;p.value=product.id==='speaker'?460:210;}
   if(fault.reason==='drive')p.failed=true;
  }
  if(candidate){if(!fault||!parts[fault.component])throw new RangeError('No repair target');parts[fault.component]={...candidate,id:fault.component};}
  return parts;
 }
 function solve(product,fault=null,candidate=null){
  const p=parameters(product,fault,candidate),id=product.id,checks=[],metrics={};let volts=[],summary='';
  const check=(label,actual,pass)=>checks.push({label,actual,pass:Boolean(pass)});
  if(id==='lamp'){
   const z=ledLoop(5,p.R1.open?Infinity:p.R1.value+.2,p.D1.open);Object.assign(metrics,z,{supply:5,current:z.i,resistorPower:z.i*z.i*p.R1.value});
   volts=[5-.2*z.i,5-.2*z.i,z.vd];summary=`电流 ${fmt(z.i*1000,3)} mA；LED压降 ${fmt(z.vd,3)} V；R1损耗 ${fmt(metrics.resistorPower*1000,3)} mW。`;
   check('LED电流10–20 mA',fmt(z.i*1000,3)+' mA',z.i>=.01&&z.i<=.02);check('R1损耗≤备件额定功率',fmt(metrics.resistorPower*1000,3)+' mW',Number.isFinite(metrics.resistorPower)&&metrics.resistorPower<=p.R1.power);
  }else if(id==='fan'){
   const motorR=10+.05*.05/.00005,ron=p.Q1.failed||p.Q1.drive>4.5?1e9:(p.Q1.ron??.1),branch=p.D1.short?parallel(motorR,p.D1.short):motorR,total=.2+ron+branch;
   const current=p.F1.open?0:Math.min(5/total,.15),supply=p.F1.open?5:current*total,va=p.F1.open?0:supply-current*.2,vb=current*ron,vm=current*branch,im=vm/motorR,omega=.05*im/.00005,rpm=omega*60/(2*Math.PI);
   Object.assign(metrics,{current,supply,va,vb,vm,motorCurrent:im,omega,rpm,limited:!p.F1.open&&5/total>.15,pin:current*supply,loss:current*current*(.2+ron)+im*im*10+.00005*omega*omega+(p.D1.short?vm*vm/p.D1.short:0)});
   volts=[va,vb,va];summary=`电源 ${fmt(supply,3)} V / ${fmt(current*1000,3)} mA；电机 ${fmt(vm,3)} V；稳态 ${fmt(rpm,1)} rpm${metrics.limited?'；已限流':''}。`;
   check('稳态转速600–1000 rpm',fmt(rpm,1)+' rpm',rpm>=600&&rpm<=1000);check('未触发150 mA限流',fmt(current*1000,3)+' mA',!metrics.limited);
  }else if(id==='speaker'||id==='router'){
   const isSpeaker=id==='speaker',input=p.F1.open?0:5*100/100.2,alive=!p.F1.open&&(isSpeaker||!p.L1.open),q={vs:isSpeaker?5:3.3,rs:isSpeaker?4:1.35+p.L1.dcr,c:p.C1.value*1e-6,esr:p.C1.esr,low:.02,high:isSpeaker?.1:.3,frequency:isSpeaker?1000:2000,duty:isSpeaker?.5:.1,l:isSpeaker?0:p.L1.value*1e-6},z=alive?(isSpeaker?pulse(q):rlcPulse(q)):{mean:0,min:0,max:0,ripple:0};
   const gain=isSpeaker?1+90000/p.R1.value:null;
   Object.assign(metrics,z,{input});
   if(isSpeaker){metrics.gain=gain;metrics.outputRms=alive?.1*gain:0;metrics.bias=z.mean/2;volts=[z.mean,z.mean,metrics.bias];
    summary=`供电均值 ${fmt(z.mean,3)} V / 最低 ${fmt(z.min,3)} V；纹波 ${fmt(z.ripple*1000,3)} mVpp；增益 ${fmt(gain,2)}，输出 ${fmt(metrics.outputRms,3)} Vrms。`;
    check('供电最低≥4.5 V',fmt(z.min,3)+' V',z.min>=4.5);check('供电纹波≤80 mVpp',fmt(z.ripple*1000,3)+' mVpp',alive&&z.ripple<=.08);check('增益9.5–10.5',fmt(gain,3),gain>=9.5&&gain<=10.5);check('输出未削顶',fmt(metrics.outputRms,3)+' Vrms',alive&&metrics.outputRms*Math.SQRT2<=z.min/2-.2);
   }else{volts=[input,z.mean,z.mean];summary=`模块输入 ${fmt(input,3)} V；输出均值 ${fmt(z.mean,3)} V / 最低 ${fmt(z.min,3)} V；纹波 ${fmt(z.ripple*1000,3)} mVpp。`;
    // Input power is a separately specified constant-resistance load; reject
    // an output equivalent circuit requesting more energy than that supply.
    metrics.pin=input*input/100;metrics.pout=z.loadPower||0;metrics.sourcePower=alive?3.3*.048:0;
    check('模块输入≥4.5 V',fmt(input,3)+' V',input>=4.5);check('输出最低≥3 V',fmt(z.min,3)+' V',z.min>=3);check('纹波≤100 mVpp',fmt(z.ripple*1000,3)+' mVpp',alive&&z.ripple<=.1);check('输出等效源功率不超过输入功率',fmt(metrics.sourcePower,3)+' W',metrics.pout<=metrics.sourcePower&&metrics.sourcePower<=metrics.pin);
   }
  }else if(id==='clock'){
   const load=p.C1.short?parallel(1000,p.C1.short):1000,current=Math.min(3.3/load,.05),v=current*load,reset=p.R1.open?null:v;
   Object.assign(metrics,{current,supply:v,reset,limited:3.3/load>.05});volts=[v,reset,v];summary=`VCC ${fmt(v,3)} V；RESET ${voltage(reset)}。仅验收直流供电与上拉，不验收走时。`;
   check('VCC为3.3 V±5%',fmt(v,3)+' V',v>=3.135&&v<=3.465);check('RESET上拉完整',voltage(reset),reset!==null&&reset>=3.135);
  }else if(id==='sensor'){
   const load=p.C1.short?parallel(100,p.C1.short):100,target=p.U1.failed?1.1:Math.min(p.U1.value,5-.2),current=Math.min(target/(1+load),.1),v=current*load,bus=p.R1.open?null:v;
   Object.assign(metrics,{current,supply:v,bus,limited:target/(1+load)>.1,ldoPower:(5-v)*current});volts=[v,v,bus];summary=`输出 ${fmt(v,3)} V / ${fmt(current*1000,3)} mA；总线 ${voltage(bus)}；稳压块损耗 ${fmt(metrics.ldoPower*1000,3)} mW${metrics.limited?'（短时限流，非热稳态）':''}。`;
   check('输出为3.3 V±5%',fmt(v,3)+' V',v>=3.135&&v<=3.465);check('总线上拉完整',voltage(bus),bus!==null&&bus>=3.135);check('未进入限流',fmt(current*1000,3)+' mA',!metrics.limited);
  }else throw new RangeError('Unknown physical circuit');
  if(fault?.enabled===false)check('本故障尚未建模','不能验收',false);
  return {volts,summary,metrics,checks,pass:checks.length>0&&checks.every(c=>c.pass)};
 }
 function isolated(required,actual=required){
  let value='',pass=true;const p=actual;
  if(p.open){value='OL · 本夹具开路';pass=false;}
  else if(p.short){value=fmt(p.short,3)+' Ω · 持续低阻';pass=false;}
  else if(p.type==='resistor'){value=fmt(p.value>=1000?p.value/1000:p.value,4)+(p.value>=1000?' kΩ':' Ω');pass=Math.abs(p.value-required.value)<=required.value*required.tolerance/100;}
  else if(p.type==='capacitor'){value=`${fmt(p.value)} µF / ESR ${fmt(p.esr)} Ω（1 kHz夹具）`;pass=Math.abs(p.value-required.value)<=required.value*required.tolerance/100&&p.esr<=required.esr;}
  else if(p.type==='ceramic')value=`${fmt(p.value)} µF / 无持续低阻（理想绝缘模型）`;
  else if(p.type==='fuse')value='0.2 Ω · 导通（不代表熔断特性已验证）';
  else if(p.type==='diode')value=`正向 ${fmt(diodeVoltage(.001,Boolean(p.led)),3)} V / 反向 OL（1 mA / 3 V夹具）`;
  else if(p.type==='mos'){const r=p.failed||p.drive>4.5?1e9:(p.ron??.1),i=Math.min(.01,1/r);value=`VGS=4.5 V：ID ${fmt(i*1000,6)} mA / VDS ${fmt(i*r,3)} V（1 V限压）`;pass=i>=.009&&i*r<=.01;}
  else if(p.type==='ldo'){const v=(p.failed?1.1:Math.min(p.value,4.8))*100/101;value=`5 V输入 / 100 Ω负载：${fmt(v,3)} V`;pass=v>=3.135&&v<=3.465;}
  else if(p.type==='inductor')value=`${p.value} µH / DCR ${p.dcr} Ω（小信号夹具）`;
  else if(p.type==='crystal'){value='晶体动态参数未建模；不能凭普通电阻档判断';pass=null;}
  return {value,pass,proof:pass===false};
 }
 function verify(product,fault,candidate){
  if(!candidate)return {pass:false,checks:[{label:'必须存在有效备件',actual:'未安装',pass:false}]};
  const result=solve(product,fault,candidate),required=product.parts.find(p=>p.id===fault.component),part=isolated(required,candidate);
  const rating={label:'备件额定耐压不低于手册要求',actual:fmt(candidate.voltage)+' V',pass:Number.isFinite(candidate.voltage)&&candidate.voltage>=required.voltage};
  const checks=[...result.checks,rating];
  return {...result,part,checks,pass:checks.every(c=>c.pass)&&part.pass===true};
 }
 const api=Object.freeze({VERSION,config,fmt,voltage,parallel,diodeVoltage,ledLoop,pulse,rlcPulse,parameters,solve,isolated,verify});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopPhysics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
