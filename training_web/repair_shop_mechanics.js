/* Replayable mechanical steps. Generic low-voltage teaching structures, not OEM teardown instructions. */
(function(root){
 'use strict';
 const SCREWS=Object.freeze(['S1','S2','S3','S4']);
 function create(entry='closed'){const open=entry==='legacy-open';return {version:1,entry:open?'legacy-open':'closed',loose:open?[...SCREWS]:[],cover:open,brace:open,unplugged:open,board:open,returned:false};}
 const onTable=m=>Boolean(m?.board&&!m.returned);
 const assembled=m=>Boolean(m?.returned&&!m.cover&&!m.brace&&!m.unplugged&&!m.board&&m.loose.length===0);
 const closed=m=>Boolean(m&&!m.cover&&!m.brace&&!m.board&&!m.unplugged&&m.loose.length===0);
 function next(m,tested=false){
  if(m.returned){
   if(m.unplugged)return {op:'plug',title:'接回 J1 连接线',body:'按定位方向接回连接器，不能把板子装回去却忘记接线。'};
   if(m.brace)return {op:'brace-in',title:'装回固定支架',body:'从桌面取回支架，按原来的卡扣位置固定。'};
   if(m.cover)return {op:'cover-in',title:'装回外壳',body:'对齐外壳定位柱；此教学上盖没有附带电线，接线必须先完成。'};
   if(m.loose.length)return {op:'tighten',id:m.loose[0],title:'装回螺丝 '+m.loose[0],body:'拿起十字螺丝刀，从零件盘将螺丝装回原位置。每颗都要装回，不会自动补齐。'};
   return {op:'final',title:'成品通电复测',body:'结构件与连接线已复位，再接通教学电源，复核本关已建模项目。'};
  }
  if(m.loose.length<SCREWS.length){const id=SCREWS.find(id=>!m.loose.includes(id));return {op:'unscrew',id,title:'拆下螺丝 '+id,body:'拿起十字螺丝刀，逐颗拆下上盖螺丝；拆下的螺丝会留在桌面的零件盘里。'};}
  if(!m.cover)return {op:'cover-out',title:'取下外壳，放到桌面',body:'上盖螺丝已全部拆除。这套教学结构的上盖不连接电线，可抬起后放在桌面后方。'};
  if(!m.brace)return {op:'brace-out',title:'取下固定支架',body:'松开支架卡扣，取下固定结构件，放在桌面独立位置；不能越过支架直接拔板。'};
  if(!m.unplugged)return {op:'unplug',title:'断开 J1 连接线',body:'握住连接器壳体解除锁扣，不拉扯电线。主机、灯头或显示组件仍留在原底座上。'};
  if(!m.board)return {op:'board-out',title:'取出电路板，放到检修垫',body:'支架和连接线已解除，取出电路板。外壳、底座、支架和螺丝都会留在同一张维修桌上。'};
  if(tested)return {op:'board-in',title:'装回电路板',body:'板级验收通过后，关闭电源并放电，再把电路板放回底座定位柱。'};
  return {op:'service',title:'开始板级检修',body:'桌面检测使用手册声明的限流电源和等效负载。成品连接线仍断开，不能把台架检测当成整机功能认证。'};
 }
 function apply(m,event,tested=false){
  const copy=JSON.parse(JSON.stringify(m)),n=next(copy,tested),bad=text=>({error:text,state:copy});
  if(!event||event.op!==n.op||['service','final'].includes(n.op))return bad('请先完成：'+n.title+'。');
  if(['unscrew','tighten'].includes(n.op)){
   if(event.tool!=='phillips')return bad('先拿起十字螺丝刀，不能直接用手拧螺丝。');
   if(!SCREWS.includes(event.id))return bad('没有这颗外壳螺丝。');
   if(n.op==='unscrew'){if(copy.loose.includes(event.id))return bad('这颗螺丝已经在零件盘里。');copy.loose.push(event.id);}
   else{if(!copy.loose.includes(event.id))return bad('这颗螺丝已经装回。');copy.loose=copy.loose.filter(id=>id!==event.id);}
  }else if(n.op==='cover-out')copy.cover=true;
  else if(n.op==='brace-out')copy.brace=true;
  else if(n.op==='unplug')copy.unplugged=true;
  else if(n.op==='board-out')copy.board=true;
  else if(n.op==='board-in'){copy.board=false;copy.returned=true;}
  else if(n.op==='plug')copy.unplugged=false;
  else if(n.op==='brace-in')copy.brace=false;
  else if(n.op==='cover-in')copy.cover=false;
  return {state:copy,message:n.title+' · 已完成。'};
 }
 const api=Object.freeze({SCREWS,create,next,apply,onTable,assembled,closed});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopMechanics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
