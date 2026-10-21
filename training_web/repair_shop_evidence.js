/* Read-only feedback from observed records; no diagnosis or economy actions. */
(function(root){
 'use strict';
 const node=typeof module!=='undefined'&&module.exports;
 const D=node?require('./repair_shop_data.js'):root.RepairShopData;
 const E=node?require('./repair_shop_engine.js'):root.RepairShopEngine;
 const recorded=(a,mode,id,after=false)=>(a.measurements||[]).find(m=>m.key===mode+':'+id+':'+after)||null;
 function describe(m){
  if(!m)return {tone:'unknown',label:'尚未检测',proof:false,text:'先选择位号和工具，记录一次测量。'};
  if(m.mode==='component')return m.proof?
   {tone:'abnormal',label:'隔离异常',proof:true,text:'断电隔离后的读数偏离本关正常参考。再结合通电线索判断失效类型，不能只凭外观。'}:
   {tone:'reference',label:'符合隔离参考',proof:false,text:'这次隔离检测符合本关参考。它不代替整机测试，也不代表所有可能参数都已检查。'};
  if(m.mode==='voltage')return {tone:m.value===m.normal?'reference':'clue',label:m.value===m.normal?'电压符合参考':'电压偏离参考',proof:false,text:'这里比较的是测试点对GND的电压。节点电压异常可能来自上游或负载，不能直接认定这个器件坏了。'};
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
  const old=recorded(a,'component',required.id);
  const rows=[{kind:'component',id:required.id,label:required.id+' · 隔离元件复测',before:old?.value||null,after:D.healthy(required),pass:true}];
  for(let i=0;i<job.product.parts.length;i++){
   const p=job.product.parts[i],m=recorded(a,'voltage',p.id);
   rows.push({kind:'voltage',id:p.id,label:p.id+' 测试点 / 对GND',before:m?.value||null,after:job.product.normal[i].toFixed(2)+' V',pass:true});
  }
  const wave=(a.measurements||[]).find(m=>m.mode==='scope'&&m.key.endsWith(':false'));
  rows.push({kind:'function',id:'system',label:'功能与负载测试',before:wave?.value||null,after:job.product.behavior,pass:true});
  return {rows,component:required.id,partSpec:D.spec(candidate),cost:candidate.price,fee:job.fee,net:job.fee-candidate.price};
 }
 const api=Object.freeze({describe,part,checklist,report});
 if(node)module.exports=api;else root.RepairShopEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this);
