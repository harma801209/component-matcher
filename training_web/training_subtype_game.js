/* One local workbench per subtype; observe the model rather than submit an answer. */
(function(){
 'use strict';const M=window.TrainingSubtypeGameMath,C=window.TrainingCatalog,sessions={};let active=null;
 const B=window.TrainingBeginner;
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 function mount(host,id){
  const d=M.profile(id),chapter=C.lesson(id);sessions[id]??={challenge:window.TrainingGameProgress.restoreSubtype(id),free:M.create(id),mode:'challenge'};
  const session=sessions[id];let mode=session.mode,s=session[mode],view=null,disposed=false,visible=false,playing=!matchMedia('(prefers-reduced-motion:reduce)').matches,speed=1,last=0,paint=0,frame=0,failed=false,lastStatus='',drag=null;
  const motion=matchMedia('(prefers-reduced-motion:reduce)'),beginner=B.supported(id);let hintDepth=0;
  const root=node('div',undefined,'playground subtype-game');root.id='subgame-root';root.dataset.subtypeGame=id;if(beginner)root.classList.add('play-beginner');host.replaceChildren(root);
  const heading=node('div',undefined,'play-heading'),title=node('div');title.append(node('h3',d.title),node('p','改一个条件，启动观察，看电路与读数一起变化。'));heading.append(title);root.append(heading);
  const modeBar=node('div',undefined,'play-mode-bar');modeBar.setAttribute('role','group');modeBar.setAttribute('aria-label','选择闯关或自由实验');
  for(const [key,text] of [['challenge','闯关挑战'],['free','自由实验']]){const b=node('button',text);b.type='button';b.dataset.subgameMode=key;b.addEventListener('click',()=>{if(mode===key)return;session[mode]=s;mode=key;session.mode=key;s=session[key];hintDepth=0;hint.hidden=true;help.setAttribute('aria-expanded','false');refresh();});modeBar.append(b);}root.append(modeBar);
  const workbench=node('section',undefined,'play-workbench');workbench.setAttribute('aria-label',chapter.title+'3D游戏操作台');root.append(workbench);
  const mission=node('section',undefined,'play-mission'),head=node('div',undefined,'play-mission-head'),missionTitle=node('h4'),count=node('span'),nav=node('div',undefined,'play-level-nav subgame-level-nav');mission.id='subgame-mission';head.append(missionTitle,count);mission.append(head,nav);workbench.append(mission);
  for(const [i,l] of d.missions.entries()){const b=node('button',(i+1)+' · '+l.title);b.type='button';b.dataset.subgameLevel=String(i);b.addEventListener('click',()=>visit(i));nav.append(b);}
  const stage=node('div',undefined,'play-stage'),viewport=node('div',undefined,'play-viewport'),canvas=node('canvas');canvas.id='subgame-canvas';canvas.tabIndex=0;canvas.setAttribute('aria-label',chapter.title+'3D电路；拖动或方向键旋转，'+(beginner?'Enter切换当前可调条件':'Enter切换第一个条件')+'，0复位视角');viewport.append(canvas,node('span','3D互动 · 题设示例','play-badge'));
  const legend=node('p',undefined,'play-labels');legend.textContent=beginner?'紫色：控制端G · 蓝色：负载主回路 · 黄圈：该驱动下参数待确认':d.topology==='clock'?'蓝色供电 · 绿色时钟信号（不是供电电流） · 黄色参考/反馈':d.topology==='common'?'蓝/橙：两独立线方向 · 紫色：理想磁通趋势':d.topology==='safety'?'虚拟连接板 · 只看应用位置，不作带电接线指导':id==='res-thin'?'蓝色：主回路 · 红圈：升温提示（不是实测温度）':'蓝色：主回路 · 橙色：补电/分流/基流 · 红圈：损耗趋势 · 黄圈：条件待核';viewport.append(legend);
  const hud=node('div',undefined,'play-hud'),hudLabel=node('small'),hudValue=node('strong');hud.append(hudLabel,hudValue);viewport.append(hud,node('p','拖动旋转 · 点击条件或拖到电路板','play-view-hint'));
  const power=node('button','停止观察','play-secondary');power.id='subgame-power';power.type='button';power.addEventListener('click',()=>{if(s.started)s=M.stop(s);else{s=M.start(s);startPlayback();}session[mode]=s;refresh(true);});
  const story=node('aside',undefined,'play-story play-console'),storyTitle=node('h4','本关目标'),goal=node('p',undefined,'play-goal'),feedback=node('p',undefined,'play-outcome'),metrics=node('div',undefined,'subgame-metrics'),reason=node('p'),why=node('details',undefined,'play-why');story.setAttribute('aria-label','游戏操作与结果');feedback.id='subgame-feedback';feedback.setAttribute('aria-live','polite');goal.id='subgame-goal';metrics.id='subgame-metrics';why.append(node('summary','为什么会这样？'),reason);story.append(storyTitle,goal);stage.append(viewport,story);workbench.append(stage);
  const fields=node('div',undefined,'subgame-fields');story.append(fields);
  for(const f of d.fields){
   const group=node('fieldset',undefined,'subgame-field');group.dataset.beginnerField=f.key;group.append(node('legend',beginner?B.fieldLabel(id,f.key):f.label));const choices=node('div',undefined,'subgame-choices');
   for(const [i,[value,label]] of f.options.entries()){
    const b=node('button',beginner?B.optionLabel(id,f.key,value,label):label,'subgame-choice');b.type='button';b.dataset.subgameField=f.key;b.dataset.subgameOption=String(i);b.draggable=true;b.setAttribute('aria-describedby','subgame-instruction');b.addEventListener('click',()=>choose(f.key,value));
    b.addEventListener('dragstart',e=>{drag={key:f.key,value};e.dataTransfer.setData('text/plain',f.key+':'+i);e.dataTransfer.effectAllowed='copy';viewport.classList.add('drop-ready');});b.addEventListener('dragend',()=>{drag=null;viewport.classList.remove('drop-ready');});
    let pointer=null,moved=false;b.addEventListener('pointerdown',e=>{if(e.pointerType!=='mouse'){pointer={id:e.pointerId,x:e.clientX,y:e.clientY};moved=false;b.setPointerCapture(e.pointerId);}});
    b.addEventListener('pointermove',e=>{if(pointer&&Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y)>12){moved=true;viewport.classList.add('drop-ready');}});
    b.addEventListener('pointerup',e=>{if(pointer&&moved){const box=viewport.getBoundingClientRect();if(e.clientX>=box.left&&e.clientX<=box.right&&e.clientY>=box.top&&e.clientY<=box.bottom){choose(f.key,value);e.preventDefault();}}pointer=null;viewport.classList.remove('drop-ready');});b.addEventListener('pointercancel',()=>{pointer=null;viewport.classList.remove('drop-ready');});choices.append(b);
   }group.append(choices);fields.append(group);
  }
  viewport.addEventListener('dragover',e=>{if(drag){e.preventDefault();e.dataTransfer.dropEffect='copy';}});viewport.addEventListener('drop',e=>{e.preventDefault();if(drag)choose(drag.key,drag.value);drag=null;viewport.classList.remove('drop-ready');});
  const row=node('div',undefined,'play-action-row'),instruction=node('p',undefined,'play-instruction'),action=node('button','开始观察','play-primary'),next=node('button','下一关','play-primary'),help=node('button','提示'),hint=node('p',undefined,'play-mission-hint');instruction.id='subgame-instruction';instruction.setAttribute('aria-live','polite');action.type=next.type=help.type='button';action.id='subgame-action';next.id='subgame-next';help.id='subgame-help';hint.id='subgame-hint';hint.hidden=true;help.setAttribute('aria-expanded','false');help.setAttribute('aria-controls',hint.id);row.append(action,next,help);story.append(instruction,row,hint);
  help.addEventListener('click',()=>{if(beginner){hintDepth=(hintDepth+1)%3;hint.hidden=hintDepth===0;}else hint.hidden=!hint.hidden;help.setAttribute('aria-expanded',String(!hint.hidden));if(beginner)refresh();});
  action.addEventListener('click',()=>{if(!s.started)power.click();else if(s.observed>=1.2){s=M.start(s);startPlayback();session[mode]=s;refresh(true);}else{playing=false;updatePause();s=M.observe(s,.6);session[mode]=s;refresh(true);}});
  next.addEventListener('click',()=>{if(!s.cleared.includes(s.index))return;if(s.index===2){if(window.TrainingGameEntry.continueLearning(id))return;s=M.create(id);session.challenge=s;refresh();}else visit(s.index+1);});
  const controls=node('div',undefined,'play-controls'),pause=node('button'),slow=node('button','慢放 1×'),reset=node('button');pause.type=slow.type=reset.type='button';pause.id='subgame-pause';slow.id='subgame-speed';reset.id='subgame-reset';pause.className=reset.className='play-icon';
  const retry=node('button','再练一遍');retry.type='button';retry.id='subgame-retry-chapter';retry.hidden=true;retry.addEventListener('click',()=>{s=M.create(id);session.challenge=s;refresh();});controls.append(retry);
  reset.setAttribute('aria-label','恢复当前关卡与视角');reset.title='恢复当前关卡与视角';reset.innerHTML=window.TrainingPlaygroundAssets.icons['arrow-path'];
  pause.addEventListener('click',()=>{playing=!playing;last=0;updatePause();refresh();});slow.addEventListener('click',()=>{speed=speed===1?.35:1;slow.textContent=speed===1?'慢放 1×':'慢放 0.35×';});reset.addEventListener('click',()=>{s=M.visit(s,s.index);session[mode]=s;hintDepth=0;view?.restore();hint.hidden=true;help.setAttribute('aria-expanded','false');refresh();});controls.append(pause,slow,reset,power);story.append(controls,node('h5','观察结果','play-result-title'),feedback,metrics,why);
  const status=node('p',undefined,'play-live sr-only');status.id='subgame-status';status.setAttribute('aria-live','polite');story.append(status);
  const assumptions=node('details',undefined,'play-assumptions');assumptions.append(node('summary','本次实验条件与资料'),node('p',d.note),node('p','端子位置参照本例封装资料；板上是教学连接，不是可生产布板。动画慢放，数值由题设计算，不是参照料号的额定保证。'));for(const [label,url] of chapter.sources){const a=node('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';assumptions.append(a);}root.append(assumptions);
  const learning=beginner?B.create(id,viewport,story,trial=>{for(const [key,value] of Object.entries(trial))if(key!=='trigger')s=M.change(s,key,value);if(trial.trigger){s=M.start(s);startPlayback();}session[mode]=s;refresh(true);}):null;
  const packageExample=window.TrainingGamePackages.profile(id);viewport.querySelector('.play-badge').textContent='封装示例：'+packageExample.title.split(' · ')[0];
  assumptions.append(node('p','本例端子：'+packageExample.pins.map(p=>p.number+' '+p.role).join(' · ')+'。封装相同也要按具体料号确认引脚。'));
  const packageLink=node('a','查看本例封装资料 ↗');packageLink.href=packageExample.source;packageLink.target='_blank';packageLink.rel='noopener noreferrer';assumptions.append(packageLink);
  function updatePause(){pause.setAttribute('aria-label',playing?'暂停动画':'继续动画');pause.setAttribute('aria-pressed',String(!playing));pause.title=playing?'暂停动画':'继续动画';pause.innerHTML=window.TrainingPlaygroundAssets.icons[playing?'pause':'play'];}
  // Respect reduced-motion on mount; a deliberate start plays this lesson only.
  function startPlayback(){playing=true;last=0;updatePause();}
  function choose(key,value){if(beginner&&mode==='challenge'&&!B.fields(id,s.index).includes(key))return;s=M.change(s,key,value);session[mode]=s;hintDepth=0;hint.hidden=true;help.setAttribute('aria-expanded','false');refresh(true);}
  function cycle(){const f=beginner&&mode==='challenge'?d.fields.find(f=>B.fields(id,s.index).includes(f.key)):d.fields[0],i=f.options.findIndex(o=>o[0]===s.params[f.key]);choose(f.key,f.options[(i+1)%f.options.length][0]);}
  function visit(i){const next=M.visit(s,i);if(next===s)return;s=next;session[mode]=s;hintDepth=0;hint.hidden=true;help.setAttribute('aria-expanded','false');view?.restore();refresh();mission.scrollIntoView({block:'start'});}
  function refresh(announce=false){
   if(disposed)return;const l=M.level(id,s.index),done=mode==='challenge'&&s.cleared.includes(s.index),r=M.evaluate(id,s.params,Math.min(1,s.observed));if(mode==='challenge')window.TrainingGameProgress.recordSubtype(s);
   root.dataset.mode=mode;root.dataset.level=String(s.index);root.dataset.cleared=String(s.cleared.length);root.dataset.started=String(s.started);root.dataset.playing=String(playing);mission.hidden=mode==='free';
   for(const b of modeBar.children)b.setAttribute('aria-pressed',String(b.dataset.subgameMode===mode));missionTitle.textContent='第 '+(s.index+1)+' / 3 关 · '+l.title;count.textContent='已通过 '+s.cleared.length+' / 3';
   for(const b of nav.children){const i=Number(b.dataset.subgameLevel);b.disabled=i>Math.min(s.cleared.length,2);b.setAttribute('aria-current',i===s.index?'step':'false');b.dataset.done=String(s.cleared.includes(i));}
   goal.textContent=mode==='challenge'?l.goal:'选择条件，观察电路如何变化；这里没有通关限制。';goal.hidden=done;storyTitle.textContent=done?(beginner?'本关观察完成':'你刚刚学会了'):mode==='free'?'自由实验':'本关目标';
   const text=done?l.learned:!s.started?'尚未开始，以下是当前条件的试算结果。':s.observed<1?'观察进行中，注意电路与读数的变化。':mode==='free'?r.story:beginner?'还未达到本关目标。'+B.explain(id,s.params,r,0,true).change+' '+l.hint:'这次还未达到目标。试着改一个条件，再重新观察。';if(feedback.textContent!==text)feedback.textContent=text;feedback.dataset.done=String(done);
   metrics.replaceChildren(...r.metrics.map(([label,value])=>{const card=node('div');card.append(node('small',label+(s.started?'':' · 条件试算')),node('strong',value));return card;}));reason.textContent=r.story;
   hudLabel.textContent=s.started?r.metrics[0][0]:'观察状态';hudValue.textContent=s.started?r.metrics[0][1]:'未开始';
   power.hidden=!s.started;power.setAttribute('aria-pressed',String(s.started));
   next.hidden=!done;next.disabled=!done;next.textContent=s.index===2?window.TrainingGameProgress.nextLabel(id)||'全部通关 · 再玩一次':'下一关';retry.hidden=mode!=='challenge'||s.index!==2||s.cleared.length!==3||!window.TrainingGameProgress.nextLabel(id);action.hidden=done;action.textContent=s.started?(s.observed>=1.2?'重新观察':'继续观察一步'):'开始观察';help.hidden=mode==='free'||done;if(help.hidden)hint.hidden=true;hint.textContent=beginner&&hintDepth===1?B.hint(id,s.index)+' 再点一次“提示”看操作建议。':l.hint;
   const paused=s.started&&!playing?'动画已暂停，点 ▶ 继续动画；也可逐步观察。 ':'';instruction.textContent=paused+(done?'完成了！可以继续下一关。':!s.started?'选好条件，点“开始观察”。改变条件后需重新开始。':'看动画，或点“继续观察一步”手动推进。');
   for(const b of fields.querySelectorAll('button')){const f=d.fields.find(f=>f.key===b.dataset.subgameField);b.setAttribute('aria-pressed',String(s.params[f.key]===f.options[Number(b.dataset.subgameOption)][0]));}
   if(beginner)for(const group of fields.children)group.hidden=mode==='challenge'&&!B.fields(id,s.index).includes(group.dataset.beginnerField);
   if(view){view.update(s.params,r,s.started);view.draw(0);}learning?.update({params:s.params,result:r,started:s.started,index:s.index,mode,done},view);if(failed){status.textContent='浏览器当前无法显示3D，仍可改条件、观察计算结果和闯关。';}else if(announce&&lastStatus!==text){lastStatus=text;status.textContent=text;}
  }
  try{view=window.TrainingSubtypeGameScene.create(canvas,id,cycle);}catch(_){failed=true;canvas.hidden=true;viewport.append(node('p','3D不可用，请启用图形加速；条件卡片与计算结果仍然可用。','play-fallback'));}
  canvas.addEventListener('subgame-context-lost',()=>{failed=true;playing=false;updatePause();refresh();});canvas.addEventListener('subgame-context-restored',()=>{failed=false;status.textContent='3D已恢复，可点击继续动画。';refresh();});
  const motionChanged=()=>{if(motion.matches){playing=false;updatePause();refresh();}};motion.addEventListener('change',motionChanged);
  const layout=window.TrainingPlaygroundLayout.mount(root);updatePause();refresh();view?.resize();const observer=new IntersectionObserver(es=>{visible=es[0].isIntersecting;last=0;});observer.observe(viewport);
  function loop(now){if(disposed)return;const dt=last?Math.min(.06,(now-last)/1000):0;last=now;if(visible&&!document.hidden&&root.closest('details')?.open&&!root.closest('[data-game-pane]')?.hidden){const advance=playing?dt*speed:0;if(s.started&&advance){s=M.observe(s,advance);session[mode]=s;}if(now-paint>90){refresh();paint=now;}view?.draw(id==='cap-tantalum'&&s.observed>=1.2?0:advance);}frame=requestAnimationFrame(loop);}
  frame=requestAnimationFrame(loop);
  const api={id,snapshot:()=>({id,mode,progress:{...s,params:{...s.params},cleared:[...s.cleared]},result:M.evaluate(id,s.params,Math.min(1,s.observed)),playing,speed,scene:view?.snapshot()}),dispose:()=>{session[mode]=s;disposed=true;cancelAnimationFrame(frame);observer.disconnect();motion.removeEventListener('change',motionChanged);layout.dispose();view?.dispose();if(active===api)active=null;}};active=api;return api;
 }
 window.TrainingSubtypeGame=Object.freeze({mount,current:()=>active});
})();
