/* Product task chapter. Progress is browser-local, separate from member records. */
(function(){
 'use strict';const M=window.TrainingNightlightMath,F=window.TrainingGameFeedback;
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
 const card=document.getElementById('games-card'),pane=document.getElementById('nightlight-pane');let mounted=null;
 function mount(root){
  let saved=null,storageOK=true;try{saved=JSON.parse(localStorage.getItem(M.key)||'null');}catch(_){storageOK=false;}
  let s={...M.restore(saved),power:false,running:false,elapsed:0},view=null,playing=false,visible=true,disposed=false,last=0,frame=0,notice='',hintOpen=false,comparison=null,reviewing=s.cleared>s.index;
  const motion=matchMedia('(prefers-reduced-motion:reduce)'),picks=window.TrainingGameChoices.create();root.replaceChildren();root.className='nightlight';
  const head=node('div',null,'nightlight-head'),title=node('h3'),count=node('span'),map=node('nav',null,'nightlight-map');map.setAttribute('aria-label','小夜灯制作步骤');head.append(title,count);root.append(head,map);
  for(const [i,c] of M.chapters.entries()){const b=node('button',String(i+1)+' · '+c.title);b.type='button';b.dataset.nightlightLevel=String(i);b.setAttribute('aria-label',String(i+1)+' · '+c.title);b.addEventListener('click',()=>dispatch('visit',i));map.append(b);}
  const stage=node('div',null,'nightlight-stage'),viewport=node('div',null,'nightlight-viewport'),canvas=node('canvas');canvas.id='nightlight-canvas';canvas.tabIndex=0;canvas.setAttribute('aria-label','3D小夜灯；拖动或方向键旋转，0复位，点击亮起位置安装器件，也可使用右侧按钮');viewport.append(canvas);
  const hud=node('div',null,'nightlight-hud'),current=node('strong'),hudLabel=node('small'),viewHint=node('small','拖动转动 · 点击亮起位置','nightlight-view-hint');hud.append(hudLabel,current);viewport.append(hud,viewHint);
  const console=node('div',null,'nightlight-console'),customer=node('p','本关目标','nightlight-customer'),goal=node('h4'),instruction=node('p',null,'nightlight-instruction'),options=node('fieldset',null,'nightlight-options'),legend=node('legend'),choices=node('div',null,'nightlight-choices');options.append(legend,choices);
  const status=node('p',null,'nightlight-status');status.id='nightlight-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const row=node('div',null,'nightlight-actions'),power=node('button','打开电源','nightlight-primary'),experiment=node('button',null,'nightlight-secondary'),primary=node('button',null,'nightlight-primary'),hint=node('button','提示'),hintText=node('p',null,'nightlight-hint');power.id='nightlight-power';power.type='button';experiment.id='nightlight-experiment';experiment.type='button';primary.id='nightlight-action';primary.type='button';hint.type='button';hint.setAttribute('aria-expanded','false');hint.setAttribute('aria-controls','nightlight-hint');hintText.id='nightlight-hint';hintText.hidden=true;row.append(power,experiment,primary,hint);
  const detail=node('details',null,'nightlight-detail'),why=node('p'),condition=node('p');detail.append(node('summary','刚才发生了什么？'),why,condition);
  const trophy=node('section',null,'nightlight-trophy'),trophyTitle=node('h4','第一件作品完成：柔光小夜灯'),trophyText=node('p','你做成了柔光、接反保护、短时备用供电和按钮控制。可以按按钮继续试，也可以去练其他器件。'),practice=node('button','继续器件专项练习');practice.type='button';practice.id='nightlight-practice';trophy.append(trophyTitle,trophyText,practice);trophy.hidden=true;
  console.append(customer,goal,instruction,options,status,row,hintText);const takeawayView=F.mountTakeaway(console),comparisonView=F.mount(console);console.append(detail,trophy);stage.append(viewport,console);root.append(stage);
  const collection=node('ul',null,'nightlight-collection');collection.setAttribute('aria-label','已完成的产品功能');root.append(collection);
  const footer=node('div',null,'nightlight-footer'),storage=node('small'),restart=node('button','重新制作');restart.type='button';restart.id='nightlight-restart';footer.append(storage,restart);root.append(footer);
  function persist(){try{localStorage.setItem(M.key,JSON.stringify(M.record(s)));storageOK=true;}catch(_){storageOK=false;}}
  function choiceReady(){const field=['resistance','resistance','diode','capacitance','mos'][s.index];return s.index===4&&s.cleared===5||picks.has(field,s[field]);}
  function dispatch(type,value){
   if(['resistance','diode','capacitance','mos'].includes(type)&&s[type]===(type==='mos'?true:value)){const chosen=type==='mos'?true:value;if(!picks.has(type,chosen)){picks.select(type,chosen);render();}return;}
   if(['primary','experiment'].includes(type)&&!s.power&&!(type==='primary'&&s.cleared>s.index&&s.index<4))return;
   if(type==='primary'&&s.cleared>s.index&&s.index<4){type='next';}
   if(type==='experiment')type='primary';
   if((type==='power'&&!s.power||type==='primary')&&!choiceReady())return;
   const before=JSON.stringify(M.record(s)),beforeState={...s};s=M.action(s,type,value);notice='';if(['resistance','diode','capacitance','mos'].includes(type))comparison=F.nightlight(beforeState,s)||comparison;
   if(['resistance','diode','capacitance','mos'].includes(type))picks.select(type,type==='mos'?true:value);
   if(['visit','next','reset'].includes(type)){picks.clear();comparison=null;s={...s,power:false,running:false,elapsed:0};reviewing=s.cleared>s.index;hintOpen=false;detail.open=false;}playing=s.power||s.running;last=0;
   if(before!==JSON.stringify(M.record(s))||type!=='tick')persist();render();
   if(type==='next'||type==='visit'){title.focus({preventScroll:true});root.scrollIntoView({block:'start',behavior:'auto'});}
  }
  primary.addEventListener('click',()=>dispatch('primary'));
  experiment.addEventListener('click',()=>dispatch('experiment'));
  power.addEventListener('click',()=>dispatch('power'));
  hint.addEventListener('click',()=>{hintOpen=!hintOpen;render();});
  restart.addEventListener('click',()=>{if(!window.confirm('重新制作会清除这台浏览器的小夜灯章节进度，其他培训记录不受影响。继续吗？'))return;picks.clear();comparison=null;reviewing=false;s=M.setup(0);playing=false;hintOpen=false;persist();render();});
  practice.textContent='返回器件关卡';practice.addEventListener('click',()=>{window.TrainingGameEntry.showLessons();card.scrollIntoView({block:'start'});document.getElementById('game-lessons').focus({preventScroll:true});});
  function pick(name){if(name==='button')return dispatch('primary');const values=name==='resistance'?M.resistors:name==='capacitance'?M.capacitors:name==='diode'?['none','forward','backward']:[];if(name==='mos')return dispatch('mos');if(values.length)dispatch(name,values[(values.indexOf(s[name])+1)%values.length]);}
  viewport.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('application/x-fruition-nightlight'))e.preventDefault();});viewport.addEventListener('drop',e=>{e.preventDefault();try{const d=JSON.parse(e.dataTransfer.getData('application/x-fruition-nightlight'));if(d.index!==s.index)return;dispatch(d.field,d.value);}catch(_){notice='请选择本关提供的器件。';render();}});
  let optionKey='';
  function choice(field,value,label){const b=node('button',label);b.type='button';b.dataset.nightlightField=field;b.dataset.nightlightValue=String(value);b.draggable=true;b.addEventListener('click',()=>dispatch(field,value));b.addEventListener('dragstart',e=>e.dataTransfer.setData('application/x-fruition-nightlight',JSON.stringify({index:s.index,field,value})));choices.append(b);return b;}
  function render(){
   const r=M.result(s),c=M.chapters[s.index],done=s.cleared>s.index,finished=s.cleared===5&&s.index===4;
   title.textContent=finished?'你的第一盏小夜灯，做好了':'第 '+(s.index+1)+' / 5 步 · '+c.title;title.tabIndex=-1;count.textContent='已做成 '+s.cleared+' / 5';
   for(const b of map.children){const i=Number(b.dataset.nightlightLevel);b.disabled=i>Math.min(s.cleared,4);b.setAttribute('aria-current',String(i===s.index?'step':'false'));b.dataset.done=String(i<s.cleared);}
   goal.textContent=c.goal;takeawayView.render(done?c.learned:null);
   if(optionKey!==String(s.index)){optionKey=String(s.index);choices.replaceChildren();if(s.index<=1){legend.textContent='点击或拖入一个电阻';for(const v of M.resistors){const b=choice('resistance',v,v===1000?'1 kΩ':v+' Ω'),thumb=node('canvas');thumb.width=170;thumb.height=95;b.prepend(thumb);try{window.TrainingPlaygroundScene.thumbnail('resistor',v,thumb);}catch(_){thumb.remove();}}}else if(s.index===2){legend.textContent='选择保护二极管的接法';choice('diode','none','暂不安装');choice('diode','forward','A → K');choice('diode','backward','K → A');}else if(s.index===3){legend.textContent='选择有效容量';for(const v of M.capacitors)choice('capacitance',v,Math.round(v*1e6).toLocaleString('en-US')+' µF');}else{legend.textContent='装上灯的电子开关';choice('mos',true,'安装N沟道MOS');}}
   options.hidden=finished;for(const b of choices.children){const field=b.dataset.nightlightField,value=field==='mos'?true:field==='diode'?b.dataset.nightlightValue:Number(b.dataset.nightlightValue);b.setAttribute('aria-pressed',String(picks.has(field,value)));}
   let text='',label='';
   if(s.index===0){text=s.resistance===null?'先点一个电阻装到电路板上。':'电阻已装好，现在打开电源。';label='打开电源';}
   if(s.index===1){text='试换一个电阻，看灯光和电流有没有达到要求。';label='检查灯光';}
   if(s.index===2){text=s.reverse?(s.tested?'接反测试成功：灯不接受反向供电。现在恢复正常。':'这个接法没有正确挡住反向供电，换一种接法再试。'):'选好方向后，测试一次接反。';label=s.reverse?'恢复正常供电':'测试电源接反';}
   if(s.index===3){text=s.power?'电容已按本例充满。断开外部电源，看橙色储能电流给灯补电。':s.elapsed<2?'正在断电观察；橙色电流来自电容，灯会慢慢变暗。':'2秒的结果已定格；真实放电继续时，灯还会变暗。';label=s.power?'断电观察2秒':s.running?'观察下一刻':'恢复供电再试';}
   if(s.index===4){text=!s.mos?'先安装MOS管，再用按钮控制灯。':!s.sawOn?'按按钮让灯亮起来。':!s.sawOff?'再按一次，让灯灭。':'再按一次，让灯重新亮起。';label=s.gate?'按按钮关灯':'按按钮亮灯';}
   if(done&&!finished){text='这项功能已做成。下一步会为同一盏灯加上新功能。';label='继续制作';}
   if(finished)text='蓝色是供电，按钮改变MOS的控制状态；灯的电能仍来自电源。';
   if(!s.power&&!s.running&&!done)text=s.index===3?'先打开电源储能，再关闭电源看补电。':'选好器件，点“打开电源”。';const reviewPrompt=done&&!s.power&&!s.running&&(reviewing||finished);instruction.textContent=reviewPrompt?(s.index===4?'先打开电源，再用按钮开关灯。':s.index===3?'选电容、打开电源储能，再关闭电源看补电。':'选好器件，打开电源再观察。'):done?'':text;instruction.hidden=done&&!reviewPrompt;primary.textContent=label;primary.disabled=!(done&&s.index<4)&&(!s.power||s.index===4&&!s.mos);experiment.hidden=!done||s.index!==2;experiment.disabled=!s.power;experiment.textContent=s.reverse?'恢复正常供电':'测试电源接反';comparisonView.render(comparison,s.power||s.running||s.elapsed>0);
   power.textContent=s.power?'关闭电源':'打开电源';power.className=s.power?'nightlight-secondary':'nightlight-primary';power.setAttribute('aria-pressed',String(s.power));power.disabled=!s.power&&!choiceReady();root.dataset.choiceReady=String(choiceReady());if(!choiceReady()){instruction.textContent='请先点选本关的器件或条件，再打开电源。';instruction.hidden=false;}
   primary.setAttribute('aria-label',done&&!finished?'继续制作：'+M.chapters[s.index+1].title:label);primary.title=primary.getAttribute('aria-label');primary.hidden=!done&&![2,4].includes(s.index);hint.hidden=done&&!reviewing;hintText.hidden=!hintOpen||hint.hidden;hintText.textContent=c.hint;hint.setAttribute('aria-expanded',String(hintOpen));
   const message=s.index===3&&!s.power?'已观察 '+s.elapsed.toFixed(1)+' / 2.0 秒 · '+(r.current*1000).toFixed(1)+' mA':s.acted&&!done?'当前回路 '+(r.current*1000).toFixed(1)+' mA':'';
   const nextStatus=notice||(r.unknown?'当前接法会让负载受到反向供电，未预测电流；请修正保护方向。':message);if(status.textContent!==nextStatus)status.textContent=nextStatus;status.hidden=!notice&&!r.unknown;
   hudLabel.textContent=s.index===3&&!s.power?'电容补电 · '+s.elapsed.toFixed(1)+'秒':'回路电流';current.textContent=r.unknown?'接法待修正':(r.current*1000).toFixed(1)+' mA';
   why.textContent=c.learned+' 本例电阻损耗为 '+(r.resistorPower*1000).toFixed(1)+' mW；灯光仅表示相对变化，不是实测光度。';
   condition.textContent=s.index===3?'本例5 V电源、二极管固定压降0.3 V、LED固定压降2 V、330 Ω负载；按有效容量和理想RC放电比较2秒结果，未模拟充电时长、ESR与实际LED曲线。':s.index===4?'本例已经假设核对了MOS在VGS=3.3 V时的导通电阻2 Ω；0 V时忽略漏电。不用阈值电压代替导通条件，不代表任意型号都能这样使用。':'这是5 V低压虚拟产品；LED固定压降2 V，保护二极管固定压降0.3 V。真实选型要查电流、功率、耐压、温度与测试条件。';
   trophy.hidden=!finished;restart.hidden=!finished;collection.replaceChildren();for(let i=0;i<s.cleared;i++)collection.append(node('li',M.chapters[i].title));
   storage.textContent=storageOK?'进度保存在当前浏览器，不与会员账号同步。':'当前浏览器无法保存进度；本次仍可完成，刷新后需重新制作。';
   root.dataset.level=String(s.index);root.dataset.cleared=String(s.cleared);root.dataset.playing=String(playing);view?.update(s,r);summaryCount();
  }
  function summaryCount(){window.dispatchEvent(new CustomEvent('training-nightlight-progress'));}
  try{view=window.TrainingNightlightScene.create(canvas,pick);}catch(_){canvas.hidden=true;viewport.append(node('p','当前浏览器无法显示3D；仍可用下面的器件和按钮制作，实时结果会显示在操作区。','nightlight-fallback'));}
  const lost=()=>{notice='3D显示暂时中断；仍可用按钮观察数值。';render();};canvas.addEventListener('nightlight-context-lost',lost);
  const restored=()=>{notice='3D已恢复。';render();};canvas.addEventListener('webglcontextrestored',restored);
  const motionChanged=()=>{if(motion.matches&&s.power)dispatch('power');};motion.addEventListener('change',motionChanged);
  const observer=new IntersectionObserver(es=>{visible=es[0].isIntersecting;last=0;});observer.observe(viewport);
  function loop(now){if(disposed)return;const dt=last?Math.min(.06,(now-last)/1000):0;last=now;if(visible&&card.open&&!pane.hidden&&!document.hidden&&playing){if(s.running){s=M.action(s,'tick',dt);if(!s.running){playing=false;persist();}render();}view?.draw(dt);}frame=requestAnimationFrame(loop);}
  render();view?.resize();frame=requestAnimationFrame(loop);
  return {snapshot:()=>({state:{...s},selection:picks.snapshot(),result:M.result(s),playing,storageOK,comparison:comparison?JSON.parse(JSON.stringify(comparison)):null,scene:view?.snapshot()}),dispose:()=>{disposed=true;cancelAnimationFrame(frame);observer.disconnect();motion.removeEventListener('change',motionChanged);view?.dispose();}};
 }
 window.TrainingNightlight=Object.freeze({current:()=>mounted,open:()=>{if(!window.TrainingGameProgress.eligible('nightlight'))return null;if(!mounted)mounted=mount(document.getElementById('nightlight-body'));return mounted;}});
})();
