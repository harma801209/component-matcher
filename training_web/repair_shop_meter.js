/* Ideal, signed DC instruments on declared teaching ports, not arbitrary OEM pins. */
(function(root){
 'use strict';
 const node=typeof module!=='undefined'&&module.exports;
 const P=node?require('./repair_shop_physics.js'):root.RepairShopPhysics,B=node?require('./repair_shop_board.js'):root.RepairShopBoard;
 function contacts(product){const p=B.get(product.id);return [...p.ports.map((x,i)=>({...x,index:i,label:x.id+' · '+product.model.ports[i]})),{id:'GND',part:null,index:-1,net:'GND',point:p.pins['TP_GND.1'].point,label:'GND · 电源公共地'}];}
 const valid=x=>x&&typeof x==='object'&&!Array.isArray(x);
 function voltage(job,a,leads){
  if(!valid(leads)||leads.jack!=='v')return {error:'测电压时红表笔必须接VΩ插孔，黑表笔接COM；不能使用mA插孔跨接电源。'};
  const ports=contacts(job.product),red=ports.find(p=>p.id===leads.red),black=ports.find(p=>p.id===leads.black);
  if(!red||!black)return {error:'请亲自放置红、黑两支表笔：点选表笔，再点击3D测试点或下方接点按钮。'};
  const candidate=a.installed?job.candidates.find(c=>c.stockId===a.installed):null,result=P.solve(job.product,job.fault,candidate),normal=P.solve(job.product);
  const diff=r=>{if(red.net===black.net)return 0;const v=x=>x.index<0?0:r.volts[x.index],x=v(red),y=v(black);return x===null||y===null||!Number.isFinite(x)||!Number.isFinite(y)?null:x-y;};
  const numeric=diff(result),reference=diff(normal),canonical=black.id==='GND'&&red.part,id=canonical?red.part:'pair';
  return {mode:'voltage',id,label:'红 '+red.id+' − 黑 '+black.id+' / 直流（周期平均）',value:P.voltage(numeric),normal:P.voltage(reference),numeric,reference,proof:false,unsupported:numeric===null,modelVersion:P.VERSION,connection:{red:red.id,black:black.id,jack:'v'},sampleKey:canonical?null:'voltage:pair:'+red.id+'>'+black.id,note:'理想无限输入阻抗电压表。浮空节点不强行赋值；不代表真实仪表加载后的电压。'};
 }
 function seriesError(leads){
  if(!valid(leads)||leads.jack!=='ma')return '串联测电流需要将红表笔接mA插孔，黑表笔接COM。';
  if(![['SRC','LOAD'],['LOAD','SRC']].some(([r,b])=>leads.red===r&&leads.black===b))return '电流表只能接入断开的供电支路SRC—LOAD，不能接TP或GND，也不能跨接电源。';
  return '';
 }
 function inputCurrent(job,result){
  if(job.product.id==='speaker')return result.metrics.mean===0?0:.02*.5+.1*.5;
  if(job.product.id==='router')return result.metrics.input/100;
  return result.metrics.current;
 }
 function current(job,a){
  const leads=a.currentSetup;if(seriesError(leads))return {error:'先断电、放电，再把电流表串入SRC—LOAD供电夹具。'};
  const candidate=a.installed?job.candidates.find(c=>c.stockId===a.installed):null,sign=leads.red==='SRC'?1:-1,numeric=sign*inputCurrent(job,P.solve(job.product,job.fault,candidate)),reference=sign*inputCurrent(job,P.solve(job.product));
  if(!Number.isFinite(numeric)||Math.abs(numeric)>.2)return {error:'超出本关200mA夹具范围，不生成推测读数。'};
  const format=x=>(x*1000).toFixed(3)+' mA';
  return {mode:'current',id:'supply',label:'SRC—LOAD供电支路 / 直流或周期平均',value:format(numeric),normal:format(reference),numeric,reference,proof:false,modelVersion:P.VERSION,connection:{...leads},note:'理想零负担串联电流表；电机测供电总电流，路由器测输入100Ω等效负载，LDO忽略静态电流。不把输出电流冒充输入电流。'};
 }
 const api=Object.freeze({VERSION:1,contacts,voltage,seriesError,inputCurrent,current});if(node)module.exports=api;else root.RepairShopMeter=api;
})(typeof globalThis!=='undefined'?globalThis:this);
