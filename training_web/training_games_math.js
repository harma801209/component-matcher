/* Small, explicit teaching challenges. Values are examples, not catalog ratings. */
(function(root){
 'use strict';
 const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
 const courses=freeze({
  resistor:{name:'贴片电阻',title:'点亮LED，不让它过流',goal:'把LED电流调到8～12 mA，并让电阻功耗不超过题设允许功率的80%。',
   conditions:'5 V电源，LED正向压降按2 V估算。80%是这关的余量要求，不是所有产品的通用规定。',
   fields:[{id:'r',label:'选择阻值',options:[[100,'100 Ω'],[150,'150 Ω'],[220,'220 Ω'],[330,'330 Ω'],[470,'470 Ω'],[1000,'1 kΩ']]},{id:'rating',label:'该工作条件下允许的功率',options:[[.02,'0.02 W'],[.063,'0.063 W'],[.125,'0.125 W']]}],defaults:{r:100,rating:.02},
   note:'串联回路中，流入与流出电阻的电流相同；电阻产生压降并把一部分电能转成热。实际还要核对LED曲线、脉冲、温度降额和电压限制。',
   source:['Vishay · 电阻规格与降额','https://www.vishay.com/docs/20035/dcrcwe3.pdf'],
   pairs:[['101','100 Ω','三位码：10×10¹＝100 Ω。'],['102','1 kΩ','三位码：10×10²＝1000 Ω。'],['R10','0.1 Ω','本关采用R作小数点：R10＝0.10 Ω＝100 mΩ。'],['5 mΩ','0.005 Ω','小写m是毫；不要和大写M（兆）混淆。']]},
  capacitor:{name:'陶瓷电容',title:'给芯片送一口“应急电”',goal:'电流突然增加时，50 µs内让芯片电压保持不低于3.2 V，并把电容放在电源脚旁。',
   conditions:'初始3.3 V；电容承担新增的20 mA、持续50 µs。选项给的是工作点有效容量，不是标称容量。',
   fields:[{id:'c',label:'工作点有效容量',options:[[.1,'0.1 µF'],[1,'1 µF'],[4.7,'4.7 µF'],[10,'10 µF'],[22,'22 µF']]},{id:'near',label:'放在哪里',options:[[false,'远离芯片'],[true,'芯片电源脚旁']]}],defaults:{c:1,near:false},
   note:'ΔV＝ΔI×Δt/C。本关忽略ESR、ESL及电源响应；远近只做布局判断，不虚构距离对应的电压。实际X7R/X5R有效容量还要查偏压、温度和误差。',
   source:['Murata · 工作电压与有效容量','https://www.murata.com/en-us/support/faqs/capacitor/ceramiccapacitor/char/0005'],
   pairs:[['104（本关三位容量码）','10×10⁴ pF','10×10⁴ pF＝100 nF＝0.1 µF；先确认厂家采用此编码。'],['100 nF','0.1 µF','1 µF＝1000 nF，单位换算后才可以比较容量。'],['内电极','相邻层交替连接两端','相邻内电极之间隔着陶瓷介质，不能直接短接。'],['工作点有效容量','要结合偏压与温度核对','标称10 µF不代表任何工作条件下都保持10 µF。']]},
  inductor:{name:'电感',title:'拦住突然上升的电流',goal:'20 µs内电流增加不超过0.3 A，并让估算峰值低于所选Isat。',
   conditions:'初始电流1 A；这20 µs内电感两端恒定3 V。用未饱和的线性模型估算，Isat选项采用相同跌落判据。',
   fields:[{id:'l',label:'未饱和电感量',options:[[10,'10 µH'],[22,'22 µH'],[47,'47 µH'],[100,'100 µH'],[220,'220 µH']]},{id:'isat',label:'饱和电流Isat（题设值）',options:[[1,'1 A'],[1.5,'1.5 A'],[3,'3 A']]}],defaults:{l:22,isat:1},
   note:'ΔI＝V×Δt/L。触及Isat后，不能继续用固定L预测波形；Isat不是烧毁电流。真实选型还须分别核对Irms、DCR、频率与热条件。',
   source:['Coilcraft · Isat与Irms的区别','https://www.coilcraft.com/en-us/resources/application-notes/current-and-temperature-ratings/'],
   pairs:[['Isat','规定电感跌落时的电流','Isat关注磁芯饱和导致的电感下降，判据因系列而异。'],['Irms','规定温升条件下的电流','Irms关注温升，不能直接拿Isat替代。'],['DCR','绕组直流电阻','直流铜损可用I²×DCR估算，未包括全部交流与磁芯损耗。'],['10 µH','0.00001 H','µ是百万分之一；单位相同后才能比较电感量。']]},
  diode:{name:'二极管',title:'让电源接反时不伤负载',goal:'正常接电源时，负载电压至少3.0 V；接反时要阻断反向供电。',
   conditions:'3.3 V电源、33 Ω负载。正向压降0.3/0.7 V是题设近似值，不是二极管固定导通门槛。反向测试假定未超耐压、忽略漏电。',
   fields:[{id:'forward',label:'二极管安装方向',options:[[false,'K接电源，A接负载'],[true,'A接电源，K接负载']]},{id:'vf',label:'本工作点正向压降Vf',options:[[.7,'0.7 V（题设）'],[.3,'0.3 V（题设）']]}],defaults:{forward:false,vf:.7},
   note:'正向约定电流由A流向K。串联防接反会带来压降和功耗；真实器件要核对相同电流/温度下的Vf、反向耐压、漏电和电流限制。',
   source:['Vishay · 极性及电气测试条件','https://www.vishay.com/docs/81857/1n4148.pdf'],
   pairs:[['A','阳极','正向偏置时，阳极A电位高于阴极K。'],['K','阴极','本课轴向封装的环标为K；其他封装按规格书确认。'],['Vf','指定电流与温度下的正向压降','不能把不同测试电流下的Vf直接比较。'],['反向耐压','允许反向工作电压的限制','反向不等于任何电压都安全，还会有漏电并可能击穿。']]}
 });
 function lesson(course){if(!Object.hasOwn(courses,course))throw new RangeError('Unknown course');return courses[course];}
 function evaluate(course,p){
  const d=lesson(course);for(const f of d.fields)if(!p||!f.options.some(o=>o[0]===p[f.id]))throw new RangeError('Invalid game parameter');
  let metrics,issues=[],why,values;
  if(course==='resistor'){
   const i=3/p.r,power=i*i*p.r;values={i,power,ratio:power/p.rating};
   metrics=[['LED电流',(i*1000).toFixed(2)+' mA'],['电阻功耗',(power*1000).toFixed(2)+' mW'],['允许功率占比',(power/p.rating*100).toFixed(1)+'%']];
   if(i<.008-1e-12)issues.push('电流偏小，LED亮度目标未达到；试着减小阻值。');
   if(i>.012+1e-12)issues.push('电流过大；增大阻值可以限流。');
   if(power>p.rating*.8+1e-12)issues.push('功率余量不足；在合适阻值下再选足够的允许功率。');
   why='同样的5 V电源，电阻越大，回路电流越小。流过LED和电阻的是同一股电流，电阻不会把电流“吃掉”。';
  }else if(course==='capacitor'){
   const droop=.02*50e-6/(p.c*1e-6),v=3.3-droop;values={droop,v,near:p.near};
   metrics=[['短时压降',v>0?droop.toFixed(3)+' V':'储备耗尽，不能外推'],['50 µs末电压',v>0?v.toFixed(3)+' V':'储备不足'],['电容提供的新增电流','20 mA（题设）']];
   if(v<3.2-1e-12)issues.push('补电储备不足；有效容量越大，同样时间内压降越小。');
   if(!p.near)issues.push('请把电容放在芯片电源脚旁，减短补电回路。');
   why='芯片突然多要电流时，电容放出储能补一部分；随后电源需要给它回充。它不是无限的电池，容量太小会很快掉压。';
  }else if(course==='inductor'){
   const delta=3*20e-6/(p.l*1e-6),peak=1+delta,safe=peak<p.isat;values={delta,peak,safe};
   metrics=[['线性估算电流增量',delta.toFixed(3)+' A'],['线性估算峰值',peak.toFixed(3)+' A'],['Isat检查',safe?'低于题设Isat':'超出线性模型范围']];
   if(delta>.3+1e-12)issues.push('电流上升太快；增大未饱和电感量可减缓上升。');
   if(!safe)issues.push('估算已触及Isat；需要核对更高的Isat，不能继续相信这条线性波形。');
   why='绕组建立磁场，电流变化会产生反对突变的电压；同样施加电压和时间，L越大，电流增加越慢。';
  }else{
   const output=p.forward?3.3-p.vf:0,i=output/33,reverseBlocked=p.forward;values={output,i,reverseBlocked};
   metrics=[['正常供电时负载电压',output.toFixed(2)+' V'],['正常供电时负载电流',(i*1000).toFixed(1)+' mA'],['接反电源时',reverseBlocked?'反向供电被阻断':'反向电流会通过']];
   if(!p.forward)issues.push('方向反了：正常电源被挡住，接反时反而能导通；请翻转A/K方向。');
   if(p.forward&&output<3-1e-12)issues.push('正向压降占掉太多电压；在相同工作点比较更低的Vf。');
   why='方向决定放行还是阻挡；正向工作仍有压降，所以负载拿到的电压比电源低。真实反向电流不严格为零。';
  }
  return {metrics,issues,why,values,passed:issues.length===0};
 }
 function deck(course,random=Math.random){
  const d=lesson(course),cards=d.pairs.flatMap((p,pair)=>[0,1].map(side=>({id:pair*2+side,pair,text:p[side]})));
  for(let i=cards.length-1;i>0;i--){const n=random();if(!Number.isFinite(n)||n<0||n>=1)throw new RangeError('Invalid shuffle');const j=Math.floor(n*(i+1));[cards[i],cards[j]]=[cards[j],cards[i]];}
  return {course,cards,selected:[],matched:[],turns:0};
 }
 function flip(state,id){
  const d=lesson(state.course),card=state.cards.find(c=>c.id===id);if(!card)throw new RangeError('Invalid card');
  if(state.matched.includes(id)||state.selected.length===1&&state.selected[0]===id)return {state,outcome:'unchanged',explain:''};
  const selected=state.selected.length===2?[]:[...state.selected];selected.push(id);
  const next={...state,selected,matched:[...state.matched]},result={state:next,outcome:'first',explain:'再翻一张，找到它的对应知识。'};
  if(selected.length===2){next.turns++;const a=state.cards.find(c=>c.id===selected[0]);if(a.pair===card.pair){next.matched.push(...selected);result.outcome='match';result.explain=d.pairs[card.pair][2];}else{result.outcome='miss';result.explain='这两张不是一对。记住它们，点下一张继续尝试。';}}
  return result;
 }
 const api=Object.freeze({lesson,evaluate,deck,flip,courses:Object.freeze(Object.keys(courses))});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingGamesMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);
