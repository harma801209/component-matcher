(function(root){
  'use strict';
  const positive=(v,name)=>{if(!Number.isFinite(v)||v<=0)throw new RangeError(name+'必须是有限正数');return v;};
  const finite=(v,name)=>{if(!Number.isFinite(v))throw new RangeError(name+'必须是有限数值');return v;};
  function resistor(p){const r=positive(p.r,'阻值'),v=finite(p.v,'电压'),rating=positive(p.rating,'课堂额定功率');return {current:v/r,power:v*v/r,ratio:v*v/r/rating,voltageLimit:Math.sqrt(rating*r)};}
  function capacitor(p){const c=positive(p.c,'容量'),f=positive(p.f,'频率'),v=finite(p.v,'电压');return {reactance:1/(2*Math.PI*f*c),charge:c*v,energy:.5*c*v*v};}
  function inductor(p){const l=positive(p.l,'电感量'),f=positive(p.f,'频率'),i=finite(p.i,'电流'),dcr=positive(p.dcr,'直流电阻');return {reactance:2*Math.PI*f*l,energy:.5*l*i*i,copperLoss:i*i*dcr,saturated:Math.abs(i)>positive(p.isat,'课堂Isat')};}
  function diode(p){const v=finite(p.v,'电压'),is=positive(p.is,'饱和电流参数'),n=positive(p.n,'理想因子'),vt=positive(p.vt,'热电压');const exponent=v/(n*vt);if(exponent>100)throw new RangeError('超出课堂模型范围');const current=is*Math.expm1(exponent);return {current,power:v*current,forward:v>0};}
  function format(v,unit){if(!Number.isFinite(v))return '—';if(v===0)return '0 '+unit;const scales=[[1e9,'G'],[1e6,'M'],[1e3,'k'],[1,''],[1e-3,'m'],[1e-6,'µ'],[1e-9,'n'],[1e-12,'p']];const [scale,prefix]=scales.find(([s])=>Math.abs(v)>=s)||[1e-12,'p'];return Number((v/scale).toPrecision(3))+' '+prefix+unit;}
  const api={resistor,capacitor,inductor,diode,format};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingMath=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this);
