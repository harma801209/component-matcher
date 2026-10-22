/* Pure, replayable repair state machine. No real rewards or business data. */
(function(root){
 'use strict';
 const D=typeof module!=='undefined'&&module.exports?require('./repair_shop_data.js'):root.RepairShopData;
 const P=typeof module!=='undefined'&&module.exports?require('./repair_shop_physics.js'):root.RepairShopPhysics;
 const M=typeof module!=='undefined'&&module.exports?require('./repair_shop_mechanics.js'):root.RepairShopMechanics;
 const Meter=typeof module!=='undefined'&&module.exports?require('./repair_shop_meter.js'):root.RepairShopMeter;
 const Learning=typeof module!=='undefined'&&module.exports?require('./repair_shop_learning.js'):root.RepairShopLearning;
 const clone=x=>JSON.parse(JSON.stringify(x)),int=(x,max=10000000)=>Number.isSafeInteger(x)&&x>=0&&x<=max;
 const KEY='fruition.repair-shop.v1';
 const productName=name=>name==='USB阅读台灯'?'USB小夜灯':name;
 function offer(seed){
  if(!int(seed,4294967295))throw new RangeError('Invalid job seed');
  const x=(Math.imul(seed,1664525)+1013904223)>>>0,product=D.products[x%D.products.length],fault=product.faults[Math.floor(x/D.products.length)%product.faults.length];
  return {seed,id:'R-'+seed.toString(36).toUpperCase(),product,fault,fee:95+(x%4)*15,candidates:D.candidates(product.parts.find(p=>p.id===fault.component),seed)};
 }
 function create(){return {version:1,coins:150,points:0,completed:0,owned:[],theme:'sand',active:null,history:[],revision:0};}
 function active(seed,entry='closed'){return {seed,power:false,discharged:false,mechanics:M.create(entry),currentSetup:null,review:null,finalTested:false,measurements:[],diagnosed:false,installed:null,tested:false,delivered:false,mistakes:0,hinted:false,events:[]};}
 function compatible(required,candidate){
  if(!candidate||required.type!==candidate.type||required.pkg!==candidate.pkg)return '器件类别、封装或焊盘不兼容。';
  const p=required,c=candidate;
  if(c.compat!=='已核对本板引脚、系列及工作条件')return '该备件尚未确认本板电路兼容性。';
  for(const key of ['voltage','tolerance','power','drive','cl','isat','current','dcr','esr'])if(p[key]!==undefined&&!Number.isFinite(c[key]))return '备件关键参数缺失，不能确认兼容。';
  if(c.value!==p.value)return '标称值不符合本关维修手册，不能只看外观相似。';
  if(c.voltage<p.voltage)return '额定耐压低于维修手册要求。';
  if(c.tolerance>p.tolerance)return '精度低于维修手册要求。';
  if(c.power<p.power)return '额定功率不足。';
  if(c.pin!==p.pin)return '引脚定义或极性标识与本板不兼容。';
  if(c.curve!==p.curve)return '保险丝额定电流相同，但快慢断特性不匹配。';
  if(c.drive!==p.drive)return '本板只有4.5V驱动，不能换成仅在10V下保证导通性能的MOS。';
  if(c.cl!==p.cl)return '晶体频率相同，但负载电容CL要求不同。';
  if(c.isat<p.isat||c.current<p.current||c.dcr>p.dcr)return '电流、饱和电流或直流电阻不满足手册。';
  if(c.esr>p.esr)return 'ESR超出本关电路的兼容范围。';
  return '';
 }
 function measurement(a,mode,id){
  const job=offer(a.seed),p=job.product.parts.find(p=>p.id===id),index=job.product.parts.indexOf(p),candidate=a.installed?job.candidates.find(c=>c.stockId===a.installed):null;
  if(!p)return {error:'先在电路板上选择要测量的器件。'};
  if(!M.onTable(a.mechanics))return {error:'先完成拆螺丝、取下外壳与支架、断开连接线，并把电路板放到检修垫，不能隔着外壳检测。'};
  if(!job.fault.enabled)return {error:'这张旧工单的晶体动态模型暂未开放，请撤销换单；未交付备件会退款，旧成绩保留。'};
  const result=P.solve(job.product,job.fault,candidate);
  if(mode==='voltage'){
   if(!a.power)return {error:'电压测量需要先开启模拟限流电源。'};
   return {mode,id,label:id+' 对应 '+job.product.model.ports[index]+' / 对GND',value:P.voltage(result.volts[index]),normal:P.voltage(job.product.normal[index]),proof:false,modelVersion:P.VERSION};
  }
  if(mode==='scope'){
   if(!a.power)return {error:'观察运行波形前，先开启模拟限流电源。'};
   return {mode,id,label:'规定条件下的计算测试口',value:result.summary,normal:job.product.behavior,proof:false,modelVersion:P.VERSION};
  }
  if(mode==='component'){
   if(a.power||!a.discharged)return {error:'先断电并放电。游戏会自动模拟隔离元件，避免在路测量误判。'};
   const isolated=P.isolated(p,P.parameters(job.product,job.fault,candidate)[id]);
   return {mode,id,label:id+' / 隔离元件检测',value:isolated.value,normal:D.healthy(p),proof:!a.installed&&isolated.proof,unsupported:isolated.pass===null,modelVersion:P.VERSION};
  }
  if(mode==='visual')return {mode,id,label:id+' / 放大观察',value:p.name+'；外观未见明显破损，不能仅凭外观排除故障。',normal:'按维修手册核对位号、封装与标识。',proof:false};
  return {error:'请选择可用的工具。'};
 }
 function apply(state,event,record=true){
  const s=clone(state),a=s.active;let message='',ok=false,reading=null;
  const fail=text=>({state:s,ok:false,message:text});
  if(!event||typeof event!=='object'||Array.isArray(event))return fail('无效操作。');
  if(event.type==='accept'){
   if(a&&!a.delivered)return fail('请先完成当前工单，或确认撤销。');
   if(!int(event.seed,4294967295))return fail('无效工单。');
   if(!offer(event.seed).fault.enabled)return fail('晶振停振关已暂停，等待完整振荡器模型验证后再开放。');
   if(a?.seed===event.seed||s.history.some(h=>h.id===offer(event.seed).id))return fail('这张工单已交付，不能重复领取报酬。');
   s.active=active(event.seed);ok=true;message='工单已接收。先看成品与客人描述，断电放电后拆螺丝、取壳并取出电路板，再开始检测。';
  }else if(event.type==='redeem'){
   const r=D.rewards.find(r=>r.id===event.id);if(!r)return fail('没有这个奖励。');
   if(s.owned.includes(r.id))return fail('这个奖励已经兑换，不会重复扣款。');
   if(s.points<r.points||s.coins<r.cost+50)return fail('积分或金币还不足；兑换后需保留50金币作为维修周转金。');
   s.coins-=r.cost;s.owned.push(r.id);if(r.id==='mint')s.theme='mint';ok=true;message='已兑换：'+r.title+'。学习积分为累计成绩，不会扣除。';
  }else if(event.type==='abandon'){
   if(!a||a.delivered)return fail('当前没有可撤销工单。');
   if(a.installed)s.coins+=offer(a.seed).candidates.find(p=>p.stockId===a.installed).price;
   s.active=null;ok=true;message='已撤销本单；如有未交付备件，已退回备件架并返还采购金币。';
  }else{
   if(!a)return fail('先选择一位客人的工单。');
   if(a.delivered&&event.type!=='review')return fail('本工单已交付，不会再次结算。');
   if(record&&a.events.length>=300)return fail('本工单记录已满。请撤销工单后重新接单，已购备件会返还。');
   const job=offer(a.seed),required=job.product.parts.find(p=>p.id===job.fault.component);
   if(!job.fault.enabled)return fail('旧晶振工单暂停：请撤销换单，未交付备件退回；已获得成绩保留。');
   if(event.type==='mechanical'){
    if(a.currentSetup)return fail('先断电放电并恢复普通供电连接，取下串联电流夹具，再拆装产品。');
    if(a.power||!a.discharged)return fail('拆装前必须关闭电源、确认无电并放电。');
    const r=M.apply(a.mechanics,event,a.tested);if(r.error)return fail(r.error);a.mechanics=r.state;a.finalTested=false;ok=true;message=r.message;
   }else if(event.type==='power'){
    if(!a.power&&!M.closed(a.mechanics)&&!M.onTable(a.mechanics))return fail('结构正在拆装，不能通电。取出的电路板可在检修垫上接限流测试电源。');
    a.power=!a.power;a.discharged=false;ok=true;message=a.power?'模拟限流电源已开启，可测电压、观察测试波形。':'已断电；做元件检测或更换前还需放电。';
   }else if(event.type==='discharge'){
    if(a.power)return fail('先关闭模拟电源，再放电。');
    a.discharged=true;ok=true;message='已模拟确认无电并放电。元件检测会自动隔离目标元件。';
   }else if(event.type==='meterSeries'){
    if(a.power||!a.discharged)return fail('改接电流表前必须关闭电源、确认无电并放电。');
    if(!M.onTable(a.mechanics))return fail('先把电路板放到检修垫，再连接串联供电夹具。');
    if(event.leads===null){a.currentSetup=null;ok=true;message='已取下电流表并恢复普通供电连接。';}
    else{const error=Meter.seriesError(event.leads);if(error)return fail(error);a.currentSetup={red:event.leads.red,black:event.leads.black,jack:'ma'};ok=true;message='已在断开的SRC—LOAD主供电支路串入理想电流表。现在可以通电读数；改接前仍须断电放电。';}
   }else if(event.type==='measure'||event.type==='probeMeasure'){
    let result;
    if(event.type==='measure')result=measurement(a,event.mode,event.id); // Replay pre-probe saves unchanged.
    else{
     if(!M.onTable(a.mechanics))return fail('先将电路板取到检修垫。');
     if(event.mode==='voltage')result=a.power?Meter.voltage(job,a,event.leads):{error:'电压测量需要先开启模拟限流电源。'};
     else if(event.mode==='current')result=a.power?Meter.current(job,a):{error:'先在断电状态串入电流表，再开启模拟电源读数。'};
     else if(event.mode==='component')result=event.leads?.fixture===event.id?measurement(a,event.mode,event.id):{error:'先断电放电，选择目标，再亲自点击“隔离并接入测试夹具”。'};
     else if(event.mode==='scope')result=event.leads?.scope===true?measurement(a,event.mode,event.id):{error:'先接入本板的缓冲运行诊断口；这不是普通万用表的单元件测量。'};
     else result=measurement(a,event.mode,event.id);
    }
    if(result.error)return fail(result.error);
    if(event.type==='probeMeasure'&&['component','scope'].includes(event.mode))result.connection=event.mode==='component'?{fixture:event.id}:{scope:true};
    const key=(result.sampleKey||result.mode+':'+result.id)+':'+Boolean(a.installed),old=a.measurements.findIndex(m=>m.key===key);
    const item={...result,key};if(old<0)a.measurements.push(item);else a.measurements[old]=item;reading=item;
    ok=true;message='已记录：'+result.label+' — '+result.value;
   }else if(event.type==='diagnose'){
    if(a.diagnosed)return fail('诊断已确认，下一步核对备件规格。');
    if(!job.product.parts.some(p=>p.id===event.id)||!D.reasons.some(r=>r[0]===event.reason))return fail('请亲自选择故障位号和失效类型，不预选答案。');
    const evidence=a.measurements.some(m=>m.proof&&m.id===event.id),live=a.measurements.some(m=>['voltage','scope'].includes(m.mode));
    if(!evidence||!live)return fail('证据还不足：需要一项通电电压/波形观察，以及对目标器件的断电隔离检测。');
    if(event.id!==job.fault.component||event.reason!==job.fault.reason){a.mistakes=Math.min(a.mistakes+1,20);message='诊断与证据还对不上。比较隔离实测值、正常参考和失效类型，再判断。';}
    else{a.diagnosed=true;ok=true;message='诊断已确认。现在按维修手册选择兼容备件，断电放电后才能更换。';}
   }else if(event.type==='install'){
    if(!M.onTable(a.mechanics))return fail('先把电路板取到检修垫上，再更换器件。');
    if(!a.diagnosed)return fail('先用测量证据确认诊断，不能盲目换件。');
    if(a.installed)return fail('备件已装好，不会重复采购。');
    if(a.power||!a.discharged)return fail('更换前必须关闭电源并放电。');
    const candidate=job.candidates.find(p=>p.stockId===event.stockId);if(!candidate)return fail('请亲自选择一个备件。');
    const mismatch=compatible(required,candidate);
    if(mismatch){a.mistakes=Math.min(a.mistakes+1,20);message=mismatch+' 本次没有扣金币。';}
    else if(required.polar&&event.orientation!=='correct'){a.mistakes=Math.min(a.mistakes+1,20);message='请核对极性，选择与本板A/K或正负极标记一致的方向。本次没有扣金币。';}
    else if(s.coins<candidate.price)return fail('金币不足，不能采购。');
    else{s.coins-=candidate.price;a.installed=candidate.stockId;a.tested=false;ok=true;message='已采购并更换 '+required.id+'，扣除 '+candidate.price+' 金币。现在通电进行功能与负载复测。';}
   }else if(event.type==='test'){
    if(a.currentSetup)return fail('板级验收前，请先断电放电并恢复普通供电连接，避免把串联夹具留在产品上。');
    if(!M.onTable(a.mechanics))return fail('板级测试需要电路板位于检修垫上。');
    if(!a.installed)return fail('尚未完成维修，不能通过验收。');
    if(!a.power)return fail('先通电，再进行功能和负载测试。');
    if(a.tested)return fail('板级测试已经通过，请断电放电后重新装配，再做成品复测。');
    const candidate=job.candidates.find(c=>c.stockId===a.installed),result=P.verify(job.product,job.fault,candidate);
    if(!result.pass)return fail('验收未通过：'+result.checks.filter(c=>!c.pass).map(c=>c.label+'，计算为'+c.actual).join('；'));
    a.tested=true;ok=true;message='本关已建模项目验收通过（不包含未建模功能）：'+result.summary;
   }else if(event.type==='testAssembly'){
    if(!a.tested||!a.installed||!M.assembled(a.mechanics))return fail('先通过板级验收，再接回连接线、装回支架和外壳，并装齐全部螺丝。');
    if(!a.power)return fail('先通电，再复测装配后的成品。');
    const result=P.verify(job.product,job.fault,job.candidates.find(c=>c.stockId===a.installed));if(!result.pass)return fail('装配后的已建模电路项目未通过，不能交付。');
    a.finalTested=true;ok=true;message='接线与装配步骤完整，本关已建模电路复测通过。未建模功能仍不视为已验证。';
   }else if(event.type==='deliver'){
    if(!a.tested||!a.installed)return fail('先完成维修并通过功能与负载复测。');
    if(!a.finalTested||!M.assembled(a.mechanics))return fail('还没有完成重新装配和成品复测，暂不能交付。');
    const points=Math.max(35,100-a.mistakes*8);
    s.coins+=job.fee;s.points+=points;s.completed+=1;a.delivered=true;a.power=false;
    s.history.unshift({id:job.id,product:job.product.name,component:job.fault.component,points,fee:job.fee});s.history=s.history.slice(0,30);
    ok=true;message='交付成功！+'+job.fee+' 金币 · +'+points+' 学习积分。';
   }else if(event.type==='review'){
    if(!a.tested||!a.installed)return fail('先完成维修和板级验收，再做换情境复盘。');
    const q=Learning.quiz(job),answer=q.options.find(o=>o.id===event.answer);if(!answer)return fail('请亲自选择一个复盘答案。');
    a.review={answer:answer.id,correct:answer.correct,attempts:Math.min(300,(a.review?.attempts||0)+1)};ok=true;message=answer.correct?'换情境判断正确。'+q.explanation:'这个判断还需要调整。'+q.explanation;
   }else if(event.type==='hint'){
    a.hinted=true;ok=true;message='师傅提示已展开，不扣积分。先看排查思路，需要时再展开本单的详细定位与维修讲解。';
   }else return fail('无效操作。');
   if(record&&a.events.length<300)a.events.push(clone(event));
  }
  // The local economy deliberately guarantees that a new job remains affordable.
  s.revision=Math.min(10000000,s.revision+1);
  return {state:s,ok,message,reading};
 }
 function restore(raw){
  const base=create();
  if(!raw||raw.version!==1||!int(raw.coins)||!int(raw.points)||!int(raw.completed,100000)||!int(raw.revision)||!Array.isArray(raw.owned))return base;
  base.coins=raw.coins;base.points=raw.points;base.completed=raw.completed;base.revision=raw.revision;
  base.owned=D.rewards.filter(r=>raw.owned.includes(r.id)).map(r=>r.id);base.theme=base.owned.includes('mint')?'mint':'sand';
  if(Array.isArray(raw.history))base.history=raw.history.slice(0,30).filter(h=>h&&typeof h.id==='string'&&h.id.length<24&&D.products.some(p=>p.name===productName(h.product))&&int(h.points,100)&&int(h.fee,200)&&typeof h.component==='string'&&h.component.length<4).map(h=>({id:h.id,product:productName(h.product),component:h.component,points:h.points,fee:h.fee}));
  const a=raw.active;
  if(a&&int(a.seed,4294967295)&&Array.isArray(a.events)&&a.events.length<=300){
   if(!offer(a.seed).fault.enabled){
    // Retire an unsupported legacy job without resetting economy/history or
    // repeatedly issuing a refund on reload. Abandon is the sole refund action.
    if(base.history.some(h=>h.id===offer(a.seed).id))return base;
    base.active=active(a.seed);base.active.paused=true;
    const c=offer(a.seed).candidates.find(c=>c.stockId===a.installed);
    if(c&&a.events.some(e=>e?.type==='install'&&e.stockId===c.stockId)){base.active.installed=c.stockId;base.active.events=a.events;}
    return base;
   }
   // Rebuild progress from permitted actions rather than trusting completion flags.
   const legacy=!a.mechanics||a.mechanics.entry==='legacy-open',replay=create();replay.coins=100000;replay.active=active(a.seed,legacy?'legacy-open':'closed');let rebuilt=replay;
   for(const event of a.events){if(!['power','discharge','measure','probeMeasure','meterSeries','review','diagnose','install','test','testAssembly','mechanical','deliver','hint'].includes(event?.type))return base;rebuilt=apply(rebuilt,event).state;}
   if(legacy&&base.history.some(h=>h.id===offer(a.seed).id)){rebuilt.active.delivered=true;rebuilt.active.legacyCompleted=true;rebuilt.active.power=false;}
   base.active=rebuilt.active;
  }
  return base;
 }
 function nextSeeds(seed){const out=[];for(let i=0;out.length<3;i++){const n=(Math.imul((seed+i)>>>0,1103515245)+12345)>>>0;if(offer(n).fault.enabled)out.push(n);}return out;}
 const api=Object.freeze({KEY,offer,create,apply,restore,compatible,measurement,nextSeeds});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopEngine=api;
})(typeof globalThis!=='undefined'?globalThis:this);
