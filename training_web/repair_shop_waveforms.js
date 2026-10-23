/* Exact traces of the declared rail networks; no decorative/random wave data. */
(function(root){
 'use strict';
 const P=typeof module!=='undefined'&&module.exports?require('./repair_shop_physics.js'):root.RepairShopPhysics;
 const dynamic=p=>['speaker','router'].includes(p.id);
 const modes=p=>dynamic(p)?['ripple','step','startup']:['steady'];
 const valid=(p,o)=>o&&modes(p).includes(o.mode)&&['specified','light'].includes(o.load);
 function propagate(q,x,load,t){
  if(!q.l){const target=q.vs-q.rs*load,vc=target+(x[0]-target)*Math.exp(-t/((q.rs+q.esr)*q.c));return [vc];}
  const a=-(q.rs+q.esr)/q.l,b=-1/q.l,c=1/q.c,d=Math.sqrt(a*a+4*b*c),r1=(a+d)/2,r2=(a-d)/2,u=Math.exp(r1*t),v=Math.exp(r2*t),s=(u-v)/d,z=[x[0]-load,x[1]-(q.vs-q.rs*load)];
  return [load+((a-r2)*s+v)*z[0]+b*s*z[1],q.vs-q.rs*load+c*s*z[0]+(-r2*s+v)*z[1]];
 }
 const rail=(q,x,i)=>q.l?x[1]+q.esr*(x[0]-i):(q.esr*q.vs+q.rs*x[0]-q.rs*q.esr*i)/(q.rs+q.esr);
 function capture(product,fault,candidate,options={mode:dynamic(product)?'ripple':'steady',load:'specified'}){
  if(!valid(product,options))throw new RangeError('Unsupported scope setting');
  const r=P.solve(product,fault,candidate),p=P.parameters(product,fault,candidate),points=[],conditions=[],{mode,load}=options;
  if(!dynamic(product)){
   const v=r.volts[0];if(!Number.isFinite(v))return {supported:false,reason:'这个节点的电位没有唯一确定值，不绘制假的0V。'};
   for(let n=0;n<=256;n++)points.push({t:n/256*.02,v});
   return {supported:true,mode,load,points,duration:.02,sampleRate:12800,min:v,max:v,channel:product.model.ports[0]+' 对GND',conditions:['仅表示已建模的直流稳态。'],limits:'本机没有启动/开关动态模型，不把平线解释为没有高频噪声或所有功能正常。'};
  }
  const speaker=product.id==='speaker',factor=load==='light'?.5:1,q={vs:speaker?5:3.3,rs:speaker?4:1.35+p.L1.dcr,c:p.C1.value*1e-6,esr:p.C1.esr,l:speaker?0:p.L1.value*1e-6,low:.02*factor,high:(speaker?.1:.3)*factor,frequency:speaker?1000:2000,duty:speaker?.5:.1};
  const alive=!p.F1.open&&(speaker||!p.L1.open),z=q.l?P.rlcPulse(q):P.pulse(q),tau=q.l?-1/z.eigenvalues[0]:(q.rs+q.esr)*q.c,T=1/q.frequency,th=q.duty*T;
  const duration=mode==='ripple'?4*T:6*tau;
  const add=(t,x,i)=>points.push({t,v:alive?rail(q,x,i):0});
  for(let n=0;n<=512;n++){
   const t=n/512*duration;
   if(mode==='ripple'){
    const phase=(t%T),high=phase<th,x=q.l?(high?z.x0:z.x1):[high?z.v0:z.v1];add(t,propagate(q,x,high?q.high:q.low,high?phase:phase-th),high?q.high:q.low);
   }else if(mode==='startup'){add(t,propagate(q,q.l?[0,0]:[0],0,t),0);}
   else{const x=q.l?[q.low,q.vs-q.rs*q.low]:[q.vs-q.rs*q.low];add(t,propagate(q,x,q.high,t),q.high);}
  }
  // Include both sides of each load edge; ESR can change terminal voltage
  // instantly while capacitor internal voltage / inductor current stay continuous.
  if(mode==='ripple')for(let k=0;k<4;k++){
   const a=q.l?z.x0:[z.v0],b=q.l?z.x1:[z.v1];add(k*T,a,q.low);add(k*T,a,q.high);add(k*T+th,b,q.high);add(k*T+th,b,q.low);
  }
  if(mode==='step'){const x=q.l?[q.low,q.vs-q.rs*q.low]:[q.vs-q.rs*q.low];points.unshift({t:0,v:alive?rail(q,x,q.low):0});}
  points.sort((a,b)=>a.t-b.t);
  conditions.push((q.l?'RLC':'RC')+'输出等效网络；'+(alive?'供电路径接通':'路径断开，取已放电状态'));
  conditions.push('曲线按理想源直接激励的独立网络计算；输入模块、控制环路与输入负载不参与实验，不据此宣称整机瞬态或功率验收通过。');
  conditions.push(mode==='startup'?'无负载上电实验：理想电容内部初始0V'+(q.l?'，电感初始0A':'')+'；端电压含ESR压降，不是整机启动时序。':mode==='step'?'从低负载稳态跳到高负载并保持。':'指定周期脉冲负载的周期稳态。');
  if(mode!=='startup')conditions.push('负载 '+(q.low*1000)+'↔'+(q.high*1000)+' mA'+(mode==='ripple'?'，'+q.frequency+' Hz，占空比'+(q.duty*100)+'%':''));
  const values=points.map(x=>x.v);if(!values.every(Number.isFinite))throw new RangeError('Nonfinite scope trace');
  return {supported:true,mode,load,points,duration,sampleRate:512/duration,min:Math.min(...values),max:Math.max(...values),channel:(speaker?'Rs后电源轨':'L1后输出轨')+' 对GND',conditions,limits:'模型计算曲线，不是实物采样。未模拟开关控制环路、仪器带宽、噪声、温升或软件；实验负载不改变工单验收条件。'};
 }
 const api=Object.freeze({VERSION:1,dynamic,modes,valid,propagate,rail,capture});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopWaveforms=api;
})(typeof globalThis!=='undefined'?globalThis:this);
