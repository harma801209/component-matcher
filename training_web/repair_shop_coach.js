/* Read-only teaching plans: never perform measurements, select answers or spend coins. */
(function(root){
 'use strict';
 const D=typeof module!=='undefined'&&module.exports?require('./repair_shop_data.js'):root.RepairShopData;
 const plans={
  lamp:{order:['F1','R1','D1'],where:'F1供电路径、R1限流电阻、D1发光二极管。',why:'完全不亮可能是回路某处开路；变暗则要比较供电、电流和R1阻值。不能只凭“灯不亮”就认定LED坏了。'},
  fan:{order:['F1','Q1','D1'],where:'F1保险丝、Q1电机开关、D1续流保护支路。',why:'电机不转，既可能没有供电，也可能开关没有导通；若电源进入限流，还要怀疑短路。要同时看供电和控制条件。'},
  speaker:{order:['F1','C1','R1'],where:'F1供电路径、C1电源滤波、R1反馈支路。',why:'全无反应先查供电；低音或大负载才重启，重点看电源纹波和C1的ESR；供电稳定但音量异常，再看反馈参数。'},
  clock:{order:['C1','R1','X1'],where:'C1供电去耦、R1复位上拉、X1时钟回路。',why:'电源被拉低、芯片一直复位、时钟停振，都可能让电子钟不运行。先确认供电，再区分复位与时钟，不能只看屏幕就换晶体。'},
  sensor:{order:['U1','C1','R1'],where:'U1稳压器、C1去耦电容、R1通信总线上拉。',why:'稳压输出低，可能是U1本身异常，也可能是C1短路拖低电源；电源正常却通信失败时，还要检查R1上拉。'},
  router:{order:['F1','L1','C1'],where:'F1输入保护、L1能量传输路径、C1输出滤波。',why:'无法启动先确认供电有没有传到输出；待机正常、传数据才重启，要观察负载时的纹波，不能只测一次静态电压。'}
 };
 const words={
  resistor:'电阻用Ω表示阻值。隔离后比较实测与标称值；功率额定值不是阻值，也不能用更大阻值代替更高功率。',
  capacitor:'µF是容量，ESR是等效串联电阻。容量接近标称仍可能ESR过高；电源纹波和负载表现也是线索。',
  ceramic:'MLCC也可能短路。断电、放电并隔离后，持续低阻才是本关的异常线索；不要把接表瞬间的充电过程当成短路。',
  fuse:'保险丝正常时应导通。OL表示超出本档量程；在本关隔离导通检测中支持开路。真实维修还要查清过流原因，不能只换保险丝。',
  diode:'A是阳极，K是阴极。用本关支持该器件的二极管测试夹具比较正反向读数；OL的含义还取决于档位和测试能力。',
  mos:'VGS是栅极相对源极的电压。本关用专用夹具在4.5V驱动下检查D/S导通，不能只拿阈值电压判断能否带动电机。',
  ldo:'LDO是稳压器。要区分输入/使能不正常、稳压器失效和输出负载短路；本关隔离夹具会分别检查这些条件。',
  inductor:'µH是电感量，DCR是绕组直流电阻。断线会显示不导通；换件还需核对饱和电流、温升电流与封装。',
  crystal:'kHz是频率，CL是负载电容要求。停振不一定是晶体坏；本关用缓冲测试口和专用晶体分析夹具排查，不是普通万用表直接判断晶体好坏。'
 };
 const reasonName=value=>D.reasons.find(r=>r[0]===value)?.[1]||value;
 const explain={open:'在本关给定档位和量程下，隔离后OL/不导通表示这条元件路径断开；并非看到任何档位的OL都能判断损坏。',drift:'元件仍有读数，但与标称参数明显不一致，超过手册允许范围，会改变限流或反馈条件。',short:'隔离后仍持续低阻，或二极管正反向都接近零，说明本关器件形成了不应有的导通路径。',esr:'容量接近标称并不代表正常；ESR比手册值高很多，再结合负载纹波异常，支持滤波电容老化。',drive:'本关输入/驱动条件已经正常，专用隔离测试却不能得到要求的导通或稳压结果，才支持控制器件异常。',clock:'运行测试口没有时钟，且专用晶体夹具的ESR也超限；两条线索结合，才支持本关晶体异常。'};
 const record=(a,mode,id)=>a.measurements.find(m=>m.mode===mode&&(!id||m.id===id)&&!m.key.endsWith(':true'));
 function step(job,a,c={}){
  const plan=plans[job.product.id],entry=plan.order[0],part=id=>job.product.parts.find(p=>p.id===id),s=(id,title,body,target,group)=>({id,title,body,target,group});
  const choose=(id,why)=>s('target-'+id,'选择 '+id+' · '+part(id).name,why+' 点板下方的“'+id+' · '+part(id).name+'”。只选中，不会自动测量。','target-'+id,'选择测量目标');
  const power=on=>s(on?'power-on':'power-off',on?'开启模拟电源':'先关闭模拟电源',on?'电压和运行波形要在模拟电源开启后观察。点击“开启模拟电源”。':'接下来检测或更换元件，必须先关闭电源。不要带电测阻值、容量或拆换器件。','power',on?'通电观察':'断电检测');
  if(a.delivered)return s('complete','这单已经修好了','回看“诊断复盘”，再接下一位客人。新产品也沿用“供电 → 运行线索 → 断电隔离 → 换件 → 测试”的顺序。','next-customer','复盘与迁移');
  if(a.tested)return s('deliver','把修好的产品交给客人','功能、供电和负载复测已通过。点击“交付并领取报酬”，本单只结算一次。','deliver','交付结算');
  if(a.installed){if(!a.power)return power(true);return s('test','运行功能与负载测试','装好不代表修好。点击测试，核对：'+job.product.behavior,'test','维修后验证');}
  if(a.diagnosed){
   const required=part(job.fault.component);
   if(a.power)return power(false);
   if(!a.discharged)return s('discharge','断电后还要放电','点击“断电后放电”，游戏会模拟确认无电并释放残余电荷，再允许换件。','discharge','安全换件');
   if(!c.stock)return s('stock','按规格挑一枚兼容备件','原件要求：'+D.spec(required)+'。比较四个备件，不是选最贵的；要同时满足参数、封装和引脚兼容要求。','stock-list','核对备件');
   if(c.partError)return s('stock-mismatch','这枚备件还不合适',c.partError+' 回到备件抽屉重新比较；此时不会扣金币。','stock-list','核对备件');
   if(required.polar&&c.orientation!=='correct')return s('orientation','确认安装方向','对照手册的 '+required.pin+'，亲自选择“与本板A/K或正负极标记一致”。同参数装反也不能修好。','id:repair-orientation','核对极性');
   return s('install','采购并更换故障器件','备件规格已匹配，电源已关且已放电。点击“采购并更换”；成功安装才扣采购金币。','install','执行维修');
  }
  const live=a.measurements.find(m=>['voltage','scope'].includes(m.mode));
  if(!live){
   if(c.selected!==entry)return choose(entry,'先读客人的原始症状。本关从供电相关器件开始排查，避免一上来就盲目换件。');
   if(!a.power)return power(true);
   if(c.mode!=='voltage')return s('voltage-mode','选“直流电压”工具','比较该测试点对GND的电压。正常参考为 '+job.product.normal[job.product.parts.indexOf(part(entry))].toFixed(2)+' V。','mode-voltage','通电观察');
   return s('voltage-read','记录一次供电电压','点击“记录一次测量”。读数会与正常参考一起留在诊断笔记，不需要自己记住。','measure','通电观察');
  }
  if(!record(a,'scope')){
   if(!c.selected)return choose(entry,'已经有一次电压观察，再选择目标，以便观察本产品的诊断测试口。');
   if(!a.power)return power(true);
   if(c.mode!=='scope')return s('scope-mode','再观察运行线索','静态电压不一定暴露故障。选择“诊断测试波形”，查看电流、纹波、驱动或时钟信息。','mode-scope','观察工作状态');
   return s('scope-read','记录本单的运行表现','点击“记录一次测量”。正常应为：'+job.product.behavior,'measure','观察工作状态');
  }
  if(a.power)return power(false);
  if(!a.discharged)return s('discharge','确认无电并模拟放电','点击“断电后放电”。之后“隔离元件检测”会自动模拟拆离测试，避免其他并联支路干扰读数。','discharge','断电检测');
  const proof=a.measurements.find(m=>m.proof);
  if(proof){
   const why='你测到 '+proof.id+'：'+proof.value+'；正常参考：'+proof.normal+'。这是异常证据，不是只靠外观猜的。';
   if(c.diagnosis!==proof.id)return s('diagnosis-id','把证据对应到故障位号',why+' 在“故障位号”选择 '+proof.id+'，不要误选旁边的正常器件。','id:repair-diagnosis','依据证据判断');
   if(c.reason!==job.fault.reason)return s('diagnosis-reason','判断它是怎样失效的',why+' '+explain[job.fault.reason]+' 因此在“失效类型”中亲自选择“'+reasonName(job.fault.reason)+'”。','id:repair-reason','依据证据判断');
   return s('diagnosis-submit','提交你的诊断','位号与失效类型已经选好。点击“提交诊断”，通过后才能购买和更换备件。','diagnose','依据证据判断');
  }
  const next=plan.order.find(id=>!record(a,'component',id))||entry;
  const last=[...a.measurements].reverse().find(m=>m.mode==='component');
  if(c.selected!==next)return choose(next,(last?last.id+' 的隔离读数符合本关正常参考，继续排查下一处。':'现在沿维修手册的顺序检查器件。')+' 这不是直接认定 '+next+' 已损坏。');
  if(c.mode!=='component')return s('component-mode','选择“隔离元件检测”',words[part(next).type]+' 本关正常参考：'+D.healthy(part(next))+'。','mode-component','检查器件本身');
  return s('component-read','测量 '+next+' 并比较正常值','点击“记录一次测量”。正常应为 '+D.healthy(part(next))+'；若不同，结合通电线索判断，别立即盲目换件。','measure','检查器件本身');
 }
 function overview(job,a){
  const p=plans[job.product.id],proof=a.measurements.find(m=>m.proof),measured=a.measurements.filter(m=>m.mode==='component');
  return [
   {title:'可能坏在哪里',text:'先排查 '+p.where+' 未测量前，它们都是候选，不是已经确认的坏件。'},
   {title:'为什么这样怀疑',text:'客人的症状是“'+job.fault.symptom+'”。'+p.why},
   {title:'如何检测出来',text:'先开启模拟电源测电压、记录诊断测试波形；再关闭电源、放电，按 '+p.order.join(' → ')+' 的顺序用“隔离元件检测”比较实测与正常参考。'+(proof?'目前已有 '+proof.id+' 的异常记录：'+proof.value+'。':measured.length?'已做 '+measured.length+' 项隔离检测，继续比较，不要只凭外观。':'当前还没有隔离检测证据。')},
   {title:'如何维修和验收',text:'确认异常位号及失效类型后，按维修手册核对备件参数、封装、引脚和极性。断电放电后更换，再通电执行功能与负载复测，通过后才交付。'}
  ];
 }
 function detail(job,a){
  const p=job.product.parts.find(p=>p.id===job.fault.component),proof=a.measurements.find(m=>m.proof);
  return [
   {title:'重点定位',text:(proof?'你的检测已经支持 ':'详细定位提示：本单优先核对 ')+p.id+' · '+p.name+'，失效类型为“'+reasonName(job.fault.reason)+'”。'+(proof?'':'这属于关键线索，仍需亲自测量、提交诊断，不能跳过证据。')},
   {title:'本关的原因',text:job.fault.why},
   {title:'具体怎样测',text:'通电选择“诊断测试波形”，本单异常表现为：'+job.fault.wave+' 然后关闭电源、放电，选 '+p.id+'，用“隔离元件检测”记录：本关异常为 '+job.fault.bad+'，正常为 '+D.healthy(p)+'。'+words[p.type]},
   {title:'具体怎样修',text:'诊断确认后，更换 '+p.id+'；要求 '+D.spec(p)+'。'+(p.polar?'安装方向按 '+p.pin+'，不能接反。':'')+' 备件必须是本板兼容系列；断电放电后采购更换，最后通电复测：'+job.product.behavior+' 真实设备不能只凭这些简化数据下结论。'}
  ];
 }
 const api=Object.freeze({step,overview,detail,words:Object.freeze(words)});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopCoach=api;
})(typeof globalThis!=='undefined'?globalThis:this);
