/* Explicit classroom circuits, separate from individual-device parameter labs. */
(function(root){
 'use strict';
 function evaluate(course,step,u=0,options={}){
  if(!['resistor','capacitor','inductor','diode'].includes(course)||!Number.isInteger(step)||step<0||step>2||!Number.isFinite(u)||u<0||u>1)throw new RangeError('Invalid teaching state');
  if(course==='resistor'){
   const r=step===2?(options.r===220?220:1000):220,v=step===0?0:5,vf=2,i=v?Math.max(0,(v-vf)/r):0;
   return {r,v,vf:i?vf:0,i,p:i*i*r,brightness:i/(3/220),closed:step>0};
  }
  if(course==='capacitor'){
   const vs=3.3,rs=1,c=10e-6,tau=rs*c,low=.005,high=.1,load=step===1?high:low;
   const vLow=vs-rs*low,vHigh=vs-rs*high,highEnd=vHigh+(vLow-vHigh)*Math.exp(-5),present=options.cap!==false;
   let v=vLow;if(step===1)v=vHigh+(vLow-vHigh)*Math.exp(-5*u);if(step===2)v=vLow+(highEnd-vLow)*Math.exp(-5*u);
   if(!present)v=vs-rs*load;
   const source=step===0?load:(vs-v)/rs,icap=present&&step>0?source-load:0;
   return {vs,rs,c,tau,t:u*5*tau,v,load,source,icap,present,energy:present?.5*c*v*v:0};
  }
  if(course==='inductor'){
   const vs=5,r=10,l=.001,tau=l/r,end=vs/r*(1-Math.exp(-5));
   const i=step===0?0:step===1?vs/r*(1-Math.exp(-5*u)):end*Math.exp(-5*u);
   return {vs,r,l,tau,t:u*5*tau,i,vl:step===1?vs-r*i:step===2?-r*i:0,energy:.5*l*i*i,closed:step===1,freewheel:step===2};
  }
  const input=step===0?0:step===1?5:-5,vf=.7,r=1000,output=input>vf?input-vf:0,i=output/r;
  return {input,vf,r,output,i,conducting:i>0,reverse:input<0};
 }
 // Shared conductors carry the sum of contributions, not a second full load current.
 function currentFlows(course,r){
  if(course==='resistor'||course==='diode')return {main:r.i};
  if(course==='capacitor'){
   const discharge=Math.max(0,-r.icap);
   return {source:r.source,load:r.load-discharge,'cap-load':discharge,return:r.source,'cap-up':r.icap,'cap-down':r.icap};
  }
  return {supply:r.closed?r.i:0,freewheel:r.freewheel?r.i:0};
 }
 const api=Object.freeze({evaluate,currentFlows});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingCircuitMath=api;
})(typeof window==='undefined'?globalThis:window);
