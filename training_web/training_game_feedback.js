/* Same-condition comparisons: reuse lesson math, never award or persist credit. */
(function(root){
 'use strict';
 const common=typeof module!=='undefined'&&module.exports,base=common?require('./training_playground_math.js'):root.TrainingPlaygroundMath,sub=common?require('./training_subtype_game_math.js'):root.TrainingSubtypeGameMath;
 const changed=(a,b,keys)=>keys.filter(k=>a[k]!==b[k]);
 const number=(n,unit,digits=1)=>n.toFixed(digits)+' '+unit;
 function pair(context,fields,a,b){return {context,fields,before:a,after:b};}
 function baseline(course,before,after){
  const keys=changed(before,after,course==='diode'?['value','reverse']:course==='capacitor'?['value','near']:['value']);if(!keys.length)return null;
  const a={...before,power:true},b={...after,power:true},phase=course==='capacitor'?2:course==='inductor'?3:0;
  const ra=base.evaluate(course,a,phase),rb=base.evaluate(course,b,phase);
  const fields=keys.map(k=>k==='near'?['电容位置',a.near?'靠近芯片':'远离芯片',b.near?'靠近芯片':'远离芯片']:k==='reverse'?['电源方向',a.reverse?'接反':'正常',b.reverse?'接反':'正常']:[{resistor:'阻值',capacitor:'有效容量',inductor:'电感量',diode:'器件方向'}[course],base.lesson(course).choices.find(o=>o[0]===a.value)[1],base.lesson(course).choices.find(o=>o[0]===b.value)[1]]);
  if(course==='resistor')return pair('相同5 V供电 · 灯光为相对示意',fields,{metrics:[['回路电流',number(ra.current*1000,'mA')]],brightness:ra.brightness},{metrics:[['回路电流',number(rb.current*1000,'mA')]],brightness:rb.brightness});
  if(course==='capacitor'){
   if(keys.length===1&&keys[0]==='near')return pair('只比较接线长度，不预测额外压降',fields,{metrics:[['补电回路',a.near?'较短':'较长']]},{metrics:[['补电回路',b.near?'较短':'较长']]});
   return pair('相同20 mA补电50 µs · 末端结果试算',fields,{metrics:[['补电末端电压',number(ra.voltage,'V',3)]]},{metrics:[['补电末端电压',number(rb.voltage,'V',3)]]});
  }
  if(course==='inductor')return pair('相同3 V、20 µs · 末端结果试算',fields,{metrics:[['末端电流',ra.unknown?'触及Isat，不再预测':number(ra.current,'A',3)]]},{metrics:[['末端电流',rb.unknown?'触及Isat，不再预测':number(rb.current,'A',3)]]});
  return pair('相同5 V电源、1 kΩ负载',fields,{metrics:[['负载电压',number(ra.voltage,'V')],['负载电流',number(ra.current*1000,'mA')]]},{metrics:[['负载电压',number(rb.voltage,'V')],['负载电流',number(rb.current*1000,'mA')]]});
 }
 function subtype(id,before,after){
  const d=sub.profile(id),keys=changed(before,after,d.fields.map(f=>f.key));if(!keys.length)return null;
  const a=sub.evaluate(id,before,1),b=sub.evaluate(id,after,1);
  return pair(id==='cap-tantalum'?'相同补电需求 · 补电末端结果试算':'相同题设与观察终点 · 结果试算',keys.map(k=>{const f=d.fields.find(f=>f.key===k);return [f.label,f.options.find(o=>o[0]===before[k])[1],f.options.find(o=>o[0]===after[k])[1]];}),{metrics:a.metrics.map(m=>[...m]),...(id==='dio-led'?{brightness:a.visual.brightness}:{})},{metrics:b.metrics.map(m=>[...m]),...(id==='dio-led'?{brightness:b.visual.brightness}:{})});
 }
 function nightlight(before,after){
  const keys=changed(before,after,['resistance','diode','capacitance','mos']);if(!keys.length||before.index!==after.index||before.resistance===null)return null;
  const m=common?require('./training_nightlight_math.js'):root.TrainingNightlightMath;
  const at=s=>after.index===3?{...s,power:false,running:true,elapsed:2}:{...s,power:true,running:false,elapsed:0};
  const a=m.result(at(before)),b=m.result(at(after));
  const label=(k,v)=>k==='resistance'?(v===1000?'1 kΩ':v+' Ω'):k==='capacitance'?Math.round(v*1e6)+' µF':k==='mos'?(v?'安装MOS':'未安装'):{none:'未安装',forward:'A → K',backward:'K → A'}[v];
  const sample=r=>({metrics:[['回路电流',r.unknown?'接法待核，不预测':number(r.current*1000,'mA')]],...(!r.unknown?{brightness:r.brightness}:{})});
  return pair(after.index===3?'相同满充条件 · 断电2秒结果试算':'相同供电与控制条件 · 灯光为相对示意',keys.map(k=>[{resistance:'阻值',diode:'二极管接法',capacitance:'有效容量',mos:'电子开关'}[k],label(k,before[k]),label(k,after[k])]),sample(a),sample(b));
 }
 const goals={resistor:['让LED亮起来。','把灯调亮到相对亮度80%以上。','做一盏柔和提示灯：回路电流8～12 mA。','灯仍要亮，回路电流不超过4 mA。']};
 function goal(course,index,fallback){return goals[course]?.[index]||fallback;}
 function mountTakeaway(host){
  const panel=document.createElement('section'),title=document.createElement('h5'),text=document.createElement('p');panel.className='play-takeaway';panel.hidden=true;panel.setAttribute('aria-label','通关知识总结');title.textContent='可以这样向客户解释';panel.append(title,text);host.append(panel);
  return {element:panel,render(learned){const value=learned||'';panel.hidden=!value;if(text.textContent!==value)text.textContent=value;}};
 }
 function mount(host){
  const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
  const panel=make('section',undefined,'play-comparison');panel.hidden=true;panel.setAttribute('aria-label','调整前后，同条件比较');host.append(panel);let last='';
  function render(data,active){
   panel.hidden=!data||!active;const key=JSON.stringify([data,active]);if(key===last)return;last=key;if(!data)return;
   panel.replaceChildren(make('h5','看看刚才的变化'),make('p',data.context,'play-comparison-context'));
   const columns=make('div',undefined,'play-comparison-columns');panel.append(columns);
   for(const [index,name] of ['调整前','调整后'].entries()){
    const item=make('section'),sample=index?data.after:data.before;item.append(make('small',name,'play-comparison-side'));
    for(const [label,a,b] of data.fields){const row=make('p',undefined,'play-comparison-field');row.append(make('small',label),make('strong',index?b:a));item.append(row);}
    for(const [label,value] of sample.metrics){const row=make('p',undefined,'play-comparison-metric');row.append(make('small',label),make('strong',value));item.append(row);}
    if(sample.brightness!==undefined){
     const level=Math.max(0,Math.min(1,sample.brightness)),row=make('p',undefined,'play-comparison-light'),lamp=make('span',undefined,'play-comparison-lamp'),meter=make('meter');lamp.setAttribute('aria-hidden','true');lamp.style.setProperty('--lamp-level',String(level));meter.min=0;meter.max=1;meter.value=level;meter.setAttribute('aria-label',name+'相对灯光，教学示意');row.append(lamp,make('small','相对灯光 '+Math.round(level*100)+'%'),meter);item.append(row);
    }columns.append(item);
   }
  }
  return {render,element:panel};
 }
 const api=Object.freeze({baseline,subtype,nightlight,goal,mountTakeaway,mount});if(common)module.exports=api;else root.TrainingGameFeedback=api;
})(typeof globalThis==='undefined'?this:globalThis);
