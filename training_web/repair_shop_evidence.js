/* Read-only feedback from observed records; no diagnosis or economy actions. */
(function(root){
 'use strict';
 const node=typeof module!=='undefined'&&module.exports;
 const D=node?require('./repair_shop_data.js'):root.RepairShopData;
 const E=node?require('./repair_shop_engine.js'):root.RepairShopEngine;
 const P=node?require('./repair_shop_physics.js'):root.RepairShopPhysics;
 const Hands=node?require('./repair_shop_hands.js'):root.RepairShopHands;
 const recorded=(a,mode,id,after=false)=>(a.measurements||[]).find(m=>m.key===mode+':'+id+':'+after)||null;
 function describe(m){
  if(!m)return {tone:'unknown',label:'尚未检测',proof:false,text:'先选择位号和工具，记录一次测量。'};
  if(m.unsupported)return {tone:'unknown',label:m.mode==='voltage'?'节点电位无法确定':'该项未建模',proof:false,text:m.mode==='voltage'?'浮空或未确定的节点不强行设成0V。理想仪表不含漏电和加载效应，这条记录不能证明某个元件损坏。':'没有可验证的动态模型，不能据此判定元件好坏；不参与本关验收。'};
  if(m.mode==='component')return m.proof?
   {tone:'abnormal',label:'隔离异常',proof:true,text:'断电隔离后的读数偏离本关正常参考。再结合通电线索判断失效类型，不能只凭外观。'}:
   {tone:'reference',label:'符合隔离参考',proof:false,text:'这次隔离检测符合本关参考。它不代替整机测试，也不代表所有可能参数都已检查。'};
  if(m.mode==='voltage')return {tone:m.value===m.normal?'reference':'clue',label:m.value===m.normal?'电压符合参考':'电压偏离参考',proof:false,text:(m.connection?'接点：红 '+m.connection.red+' − 黑 '+m.connection.black+'。':'这里比较的是测试点对GND的电压。')+' 节点电压异常可能来自上游或负载，不能直接认定这个器件坏了。'+(m.note||'')};
  if(m.mode==='current')return {tone:m.value===m.normal?'reference':'clue',label:'供电支路电流已记录',proof:false,text:'这是SRC—LOAD支路的直流或周期平均电流，不是任意元件的电流，也不单独证明故障。'+(m.note||'')};
  if(m.mode==='scope')return {tone:'clue',label:'运行线索已记录',proof:false,text:'这是整机诊断测试口的表现，不是所选元件的单独检测。请结合断电隔离读数定位原因。'};
  return {tone:'neutral',label:'外观记录',proof:false,text:'没有明显破损不能排除内部故障，还需要电气检测。'};
 }
 function part(job,a,id){
  const unknown={id,tone:'unknown',label:'尚未检测'};
  if(!a||!job.product.parts.some(p=>p.id===id))return unknown;
  if(a.diagnosed&&a.installed&&job.fault.component===id)return {id,tone:a.tested?'repaired':'pending',label:a.tested?'已修复 · 已验收':'已更换 · 待验收'};
  const isolated=recorded(a,'component',id);
  if(isolated){const f=describe(isolated);return {id,tone:f.tone,label:f.label};}
  const voltage=recorded(a,'voltage',id);
  if(voltage)return {id,tone:'clue',label:'电压已记录'};
  // A whole-device waveform is not component-specific evidence.
  return unknown;
 }
 function checklist(a,id){
  const records=a.measurements||[];
  return [
   {label:'通电观察',done:records.some(m=>['voltage','scope'].includes(m.mode)&&m.key.endsWith(':false')),text:'维修前的电压或运行测试口记录'},
   {label:id?id+' 隔离检测':'目标隔离检测',done:Boolean(id&&recorded(a,'component',id)),text:id?'确认所选位号的断电隔离读数':'先选择测量目标；测过不等于已判定故障'},
   {label:'诊断确认',done:Boolean(a.diagnosed),text:'亲自选择故障位号与失效类型'}
  ];
 }
 function report(job,a){
  if(!a?.tested||!a.diagnosed||!a.installed)return null;
  const required=job.product.parts.find(p=>p.id===job.fault.component);
  const candidate=job.candidates.find(p=>p.stockId===a.installed);
  if(!candidate||E.compatible(required,candidate))return null;
  const result=P.verify(job.product,job.fault,candidate);if(!result.pass)return null;
  const old=recorded(a,'component',required.id);
  const rows=[{kind:'component',id:required.id,label:required.id+' · 隔离元件复测',before:old?.value||null,after:result.part.value,pass:result.part.pass}];
  for(let i=0;i<job.product.parts.length;i++){
   const p=job.product.parts[i],m=recorded(a,'voltage',p.id);
   const actual=result.volts[i],reference=job.product.normal[i];
   rows.push({kind:'voltage',id:p.id,label:p.id+' · '+job.product.model.ports[i],before:m?.value||null,after:P.voltage(actual),pass:actual!==null&&Number.isFinite(actual)&&Math.abs(actual-reference)<=Math.max(1e-9,Math.abs(reference)*.05)});
  }
  const wave=(a.measurements||[]).find(m=>m.mode==='scope'&&m.key.endsWith(':false'));
  rows.push({kind:'function',id:'system',label:'已建模项目验收',before:wave?.value||null,after:result.summary,pass:result.pass});
  const observed=(a.measurements||[]).filter(m=>['voltage','current','scope'].includes(m.mode)&&m.key.endsWith(':false'));
  const reasoning=[
   {title:'客人描述',text:job.fault.symptom},
   {title:'实际测量线索',text:observed.length?observed.map(m=>m.label+'：'+m.value+'（正常参考 '+m.normal+'）').join('；'):'未记录通电测量，不补造历史读数。'},
   {title:'隔离检测证据',text:old?required.id+'：'+old.value+'；正常参考 '+old.normal+'。这是断电隔离后的元件检测，不是在路测量。':'未记录隔离读数，不补造历史读数。'},
   {title:'为什么这样判断',text:required.id+' · '+(D.reasons.find(r=>r[0]===job.fault.reason)?.[1]||job.fault.reason)+'。'+job.fault.why+' 此解释适用于本关等效电路，不能仅凭相同症状推断其他产品。'},
   {title:'为什么选这个备件',text:'原件要求：'+D.spec(required)+'；实际换件：'+D.spec(candidate)+'。已核对本板参数、封装、引脚、极性和兼容条件；不是按价格决定。'},
   {title:'如何确认修复',text:result.summary+'。验收范围：'+job.product.model.limits+'；板级通过后仍须重新装配和成品复测才可交付。'}
  ];
  const feedback={lamp:'这盏小灯又能用了，谢谢你！',fan:'它又转起来了，谢谢你找到问题。',speaker:'这次规定负载测试稳定了，谢谢。',clock:'供电和复位检查好了，谢谢；走时还需要另行检查。',sensor:'电源和上拉检查正常了，谢谢。',router:'供电负载测试通过了，网络功能还需继续检查。'};
  const service=Hands.STEPS.map(step=>({title:step.title,done:Boolean(a.rework&&a.events.some(e=>e.type==='repairStep'&&e.op===step.op))}));
  return {rows,reasoning,service,customer:{name:job.product.customer,delivered:Boolean(a.delivered),text:a.delivered?feedback[job.product.id]:a.finalTested?'已完成装配与成品复测，等待交付。':'板级测试已通过，先装回结构件并完成成品复测。'},checks:result.checks,modelVersion:P.VERSION,component:required.id,partSpec:D.spec(candidate),cost:candidate.price,fee:job.fee,net:job.fee-candidate.price};
 }
 const api=Object.freeze({describe,part,checklist,report});
 if(node)module.exports=api;else root.RepairShopEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this);
