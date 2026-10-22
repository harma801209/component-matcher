/* Three bounded discovery exercises. Existing circuit solver, separate progress,
 * no paid-job events, currency, certification or claimed photometric model. */
(function(root){
 'use strict';
 const load=name=>typeof module!=='undefined'&&module.exports?require('./'+name+'.js'):null;
 const D=load('repair_shop_data')||root.RepairShopData,P=load('repair_shop_physics')||root.RepairShopPhysics,E=load('repair_shop_engine')||root.RepairShopEngine;
 const KEY='fruition.repair-shop.first-steps.v1',clone=x=>JSON.parse(JSON.stringify(x));
 function blank(episode=0){return {version:1,episode,done:false,fixture:false,power:false,discharged:false,ohms:220,selected:null,observed:null,inspected:{},diagnosed:false,installed:null,tested:false,prediction:null,comparisons:{},helpUsed:false,attempts:0,records:[],events:[]};}
 const create=()=>blank();
 function product(s){const p=clone(D.products.find(p=>p.id==='lamp'));p.name=s.episode===2?'书桌提示灯':'USB小夜灯';p.parts.find(p=>p.id==='R1').value=s.episode===1?s.ohms:s.episode===2?180:220;return p;}
 const fault=s=>s.episode===1?null:{component:'R1',reason:s.episode===2?'drift':'open',enabled:true};
 function stock(s){const p=product(s).parts.find(p=>p.id==='R1'),base={...p,compat:'已核对本板引脚、系列及工作条件'};
  const choices={original:{...base,id:'original'},higher:{...base,id:'higher',value:p.value*10},wrongpackage:{...base,id:'wrongpackage',pkg:'不同封装 / 焊盘'}};
  return (s.episode===2?['wrongpackage','original','higher']:['higher','wrongpackage','original']).map(id=>choices[id]);
 }
 const replacement=s=>s.installed?stock(s).find(c=>c.id===s.installed):null;
 const result=s=>P.solve(product(s),fault(s),replacement(s));
 function stage(s){
  if(s.done)return 'done';
  if(s.episode===1){if(!s.prediction)return 'predict';if(!s.comparisons['220']||!s.comparisons['440'])return 'compare';return s.tested?'celebrate':'principle';}
  if(s.tested)return 'celebrate';
  if(s.episode===2&&!s.diagnosed&&!s.installed)return 'investigate';
  if(!s.fixture)return 'fixture';if(!s.observed)return 'observe';if(!s.inspected.R1?.proof)return 'inspect';if(!s.diagnosed)return 'diagnose';if(!s.installed)return 'install';return 'test';
 }
 function apply(state,event){
  const s=clone(state),fail=message=>({state:s,ok:false,message});let ok=true,message='';
  if(!event||typeof event!=='object'||Array.isArray(event)||s.done)return fail('这段练习已经完成，或操作无效。');
  if(s.events.length>=300)return fail('本轮尝试较多，可以重新练习；自由维修的存档不会受到影响。');
  const p=product(s),part=id=>p.parts.find(p=>p.id===id);let clean;
  if(event.type==='fixture'){
   if(s.power||s.fixture)return fail('先断电，或夹具已经接好。');s.fixture=true;clean={type:'fixture'};message='教学夹具已接好。电压与电流接法已由师傅预接；这不是任意接线都能通用的仪表。';
  }else if(event.type==='power'){
   if(typeof event.on!=='boolean'||event.on===s.power)return fail('电源已经处于这个状态。');
   if(event.on&&!s.fixture)return fail('先接好教学夹具，再开启练习电源。');
   s.power=event.on;s.discharged=false;clean={type:'power',on:event.on};message=s.power?'电源已开。先观察灯，再亲自记录读数。':'电源已关。检测或换件前还要确认放电。';
  }else if(event.type==='discharge'){
   if(s.power)return fail('先关闭电源，再确认无电并放电。');s.discharged=true;clean={type:'discharge'};message='已模拟确认无电并放电。';
  }else if(event.type==='select'){
   if(!part(event.id))return fail('请选择板上已有的位号。');s.selected=event.id;clean={type:'select',id:event.id};message='已选择 '+event.id+'。选择位置不是诊断，也没有自动测量。';
  }else if(event.type==='observe'){
   if(!s.fixture||!s.power)return fail('先接夹具并开启电源，才能记录通电结果。');
   if(s.episode===1&&!s.prediction)return fail('先留下你的预测，再做实验。猜错不会扣金币。');
   const r=result(s),reading={current:r.metrics.current,volts:[...r.volts],resistorPower:r.metrics.resistorPower,summary:r.summary};
   if(s.episode===1)s.comparisons[String(s.ohms)]=reading;else s.observed=reading;
   clean={type:'observe'};message='已记录：'+r.summary;
  }else if(event.type==='inspect'){
   if(!s.fixture||s.power||!s.discharged)return fail('接好夹具，先关闭电源、确认无电并放电，再隔离检查。');
   if(!part(event.id))return fail('先选择一个器件。');
   const r=P.isolated(part(event.id),P.parameters(p,fault(s),replacement(s))[event.id]);s.inspected[event.id]={...r};s.selected=event.id;
   clean={type:'inspect',id:event.id};message=event.id+'：'+r.value+'。这是本夹具的隔离结果，不是在路读数。';
  }else if(event.type==='diagnose'){
   if(s.episode===1||s.diagnosed||!part(event.id)||!['open','drift'].includes(event.reason))return fail('请选择本题可用的诊断。');
   if(!s.observed||!s.inspected.R1?.proof)return fail('现在证据不够：先记录通电结果，再断电隔离检查。');
   const expected=s.episode===2?'drift':'open';clean={type:'diagnose',id:event.id,reason:event.reason};
   if(event.id==='R1'&&event.reason===expected){s.diagnosed=true;message='证据对上了：'+(expected==='open'?'R1隔离后开路，串联回路没有电流。':'R1实测高于手册值；在这个相同电源与LED的串联回路里，电流减小。');}
   else{s.attempts++;ok=false;message='这个判断还没有对应的证据。通电记录只能告诉你回路表现；请把所选器件的隔离读数与手册值逐项比较。';}
  }else if(event.type==='install'){
   if(s.episode===1||!s.diagnosed||s.installed)return fail('先凭测量确认故障；已更换的器件不用重复更换。');
   if(s.power||!s.discharged)return fail('更换前先断电、确认无电并放电。');
   const c=stock(s).find(p=>p.id===event.id);if(!c)return fail('请选择一枚教学备件。');
   const mismatch=E.compatible(part('R1'),c);clean={type:'install',id:event.id};
   if(mismatch){s.attempts++;ok=false;message=mismatch+' 本次未更换、不扣金币。对照手册 '+D.spec(part('R1'))+'，不是越大越好。';}
   else{s.installed=event.id;message='已在断电夹具中替换R1。教学备件不扣金币；还要通电复测，不能把装好当作修好。';}
  }else if(event.type==='test'){
   if(s.episode===1||!s.installed||!s.power||!s.fixture||s.tested)return fail('更换完成后，接好夹具并通电，再复测。');
   const r=P.verify(p,fault(s),replacement(s));if(!r.pass)return fail('计算验收未通过：'+r.checks.filter(x=>!x.pass).map(x=>x.label).join('；'));
   s.tested=true;clean={type:'test'};message='复测通过：'+r.summary+' 只验证本关声明的低压等效电路。';
  }else if(event.type==='predict'){
   if(s.episode!==1||s.prediction||!['lower','same','higher'].includes(event.answer))return fail('先选择一个尚未提交的预测。');
   s.prediction=event.answer;clean={type:'predict',answer:event.answer};message='你的首次预测已记下。现在实验，不提前揭晓答案；猜错不扣金币。';
  }else if(event.type==='resistor'){
   if(s.episode!==1||!s.prediction||![220,440].includes(event.value)||s.power||!s.discharged)return fail('先预测，并断电放电后才能调整实验电阻。');
   s.ohms=event.value;clean={type:'resistor',value:event.value};message='已将实验R1设为 '+event.value+' Ω。再通电记录。实验调参不是原机维修替代推荐。';
  }else if(event.type==='principle'){
   if(s.episode!==1||!s.comparisons['220']||!s.comparisons['440']||s.tested||!['series','power','supply'].includes(event.answer))return fail('先亲自记录两组实验结果，再解释差别。');
   clean={type:'principle',answer:event.answer};
   if(event.answer==='series'){s.tested=true;message='解释成立：这两次电源和LED相同，串联电阻增大，电流减小。LED压降也会变化，电流不能机械地按阻值倍数精确减半。';}
   else{s.attempts++;ok=false;message='对照两行记录：电源与LED没有更换，变化的是串联阻值。额定功率是允许损耗的上限，不是让电流变大的旋钮。';}
  }else if(event.type==='help'){
   s.helpUsed=true;clean={type:'help'};message='提示：先比较通电电流与正常参考，再断电、放电并隔离检查。只凭“灯不亮/电流小”不能确定哪一颗坏了。';
  }else if(event.type==='next'){
   if(!s.tested)return fail('先完成本章的测量、解释或维修复测，再继续。');
   const record={episode:s.episode,helpUsed:s.helpUsed,attempts:s.attempts,result:s.episode===2?(s.helpUsed?'completed-with-help':s.attempts?'completed-after-revision':'completed-unaided'):'guided',independent:s.episode===2&&!s.helpUsed&&s.attempts===0};
   if(s.episode===1){record.firstPrediction=s.prediction;record.firstPredictionCorrect=s.prediction==='lower';record.comparisons=clone(s.comparisons);}
   const records=[...s.records,record],events=s.events;
   Object.assign(s,blank(Math.min(2,s.episode+1)),{records,events,done:records.length===3});clean={type:'next'};message=s.done?'三章练习已完成。报告只记录你的实际操作，不代表已经掌握全部元器件。':'下一位客人来了。';
  }else return fail('无效练习操作。');
  s.events.push(clean);return {state:s,ok,message};
 }
 function restore(raw){
  if(!raw||raw.version!==1||!Array.isArray(raw.events)||raw.events.length>300)return create();let s=create();
  for(const e of raw.events){const r=apply(s,e);if(r.state.events.length!==s.events.length+1)return create();s=r.state;}return s;
 }
 const api=Object.freeze({VERSION:1,KEY,create,apply,restore,product,fault,stock,result,stage});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopFirstSteps=api;
})(typeof globalThis!=='undefined'?globalThis:this);
