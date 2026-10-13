/* One local workbench per subtype; observe the model rather than submit an answer. */
(function(){
 'use strict';const M=window.TrainingSubtypeGameMath,C=window.TrainingCatalog,sessions={};let active=null;
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 function mount(host,id){
  const d=M.profile(id),chapter=C.lesson(id);sessions[id]??={challenge:M.create(id),free:M.create(id),mode:'challenge'};
  const session=sessions[id];let mode=session.mode,s=session[mode],view=null,disposed=false,visible=false,playing=!matchMedia('(prefers-reduced-motion:reduce)').matches,speed=1,last=0,paint=0,frame=0,failed=false,lastStatus='',drag=null;
  const motion=matchMedia('(prefers-reduced-motion:reduce)');
  const root=node('div',undefined,'playground subtype-game');root.id='subgame-root';root.dataset.subtypeGame=id;host.replaceChildren(root);
  const heading=node('div',undefined,'play-heading'),title=node('div');title.append(node('h3',d.title),node('p','改一个条件，启动观察，看电路与读数一起变化。'));heading.append(title);root.append(heading);
  const modeBar=node('div',undefined,'play-mode-bar');modeBar.setAttribute('role','group');modeBar.setAttribute('aria-label','选择闯关或自由实验');
  for(const [key,text] of [['challenge','闯关挑战'],['free','自由实验']]){const b=node('button',text);b.type='button';b.dataset.subgameMode=key;b.addEventListener('click',()=>{if(mode===key)return;session[mode]=s;mode=key;session.mode=key;s=session[key];hint.hidden=true;refresh();});modeBar.append(b);}root.append(modeBar);
  const workbench=node('section',undefined,'play-workbench');workbench.setAttribute('aria-label',chapter.title+'3D游戏操作台');root.append(workbench);
  const mission=node('section',undefined,'play-mission'),head=node('div',undefined,'play-mission-head'),missionTitle=node('h4'),count=node('span'),nav=node('div',undefined,'play-level-nav subgame-level-nav');mission.id='subgame-mission';head.append(missionTitle,count);mission.append(head,nav);workbench.append(mission);
  for(const [i,l] of d.missions.entries()){const b=node('button',(i+1)+' · '+l.title);b.type='button';b.dataset.subgameLevel=String(i);b.addEventListener('click',()=>visit(i));nav.append(b);}
  const stage=node('div',undefined,'play-stage'),viewport=node('div',undefined,'play-viewport'),canvas=node('canvas');canvas.id='subgame-canvas';canvas.tabIndex=0;canvas.setAttribute('aria-label',chapter.title+'3D电路；拖动或方向键旋转，Enter切换第一个条件，0复位视角');viewport.append(canvas,node('span','3D互动 · 题设示例','play-badge'));
  const legend=node('p',undefined,'play-labels');legend.textContent=d.topology==='clock'?'蓝色供电 · 绿色时钟信号（不是供电电流） · 黄色参考/反馈':d.topology==='common'?'蓝/橙：两独立线方向 · 紫色：理想磁通趋势':d.topology==='safety'?'虚拟连接板 · 只看应用位置，不作带电接线指导':id==='res-thin'?'蓝色：主回路 · 红圈：升温提示（不是实测温度）':'蓝色：主回路 · 橙色：补电/分流/基流 · 红圈：损耗趋势 · 黄圈：条件待核';viewport.append(legend);
  const hud=node('div',undefined,'play-hud'),hudLabel=node('small'),hudValue=node('strong');hud.append(hudLabel,hudValue);viewport.append(hud,node('p','拖动旋转 · 点击条件或拖到电路板','play-view-hint'));
  const power=node('button','打开电源 / 开始观察','play-board-power');power.id='subgame-power';power.type='button';power.addEventListener('click',()=>{s=s.started?M.stop(s):M.start(s);session[mode]=s;refresh(true);});viewport.append(power);
  const story=node('aside',undefined,'play-story'),storyTitle=node('h4','这关怎么玩'),goal=node('p',undefined,'play-goal'),feedback=node('p',undefined,'play-outcome'),metrics=node('div',undefined,'subgame-metrics'),reason=node('p'),why=node('details',undefined,'play-why');feedback.id='subgame-feedback';feedback.setAttribute('aria-live','polite');goal.id='subgame-goal';metrics.id='subgame-metrics';why.append(node('summary','为什么会这样？'),reason);story.append(storyTitle,goal,feedback,metrics,why);stage.append(viewport,story);workbench.append(stage);
  const fields=node('div',undefined,'subgame-fields');workbench.append(fields);
  for(const f of d.fields){
   const group=node('fieldset',undefined,'subgame-field');group.append(node('legend',f.label));const choices=node('div',undefined,'subgame-choices');
   for(const [i,[value,label]] of f.options.entries()){
    const b=node('button',label,'subgame-choice');b.type='button';b.dataset.subgameField=f.key;b.dataset.subgameOption=String(i);b.draggable=true;b.setAttribute('aria-describedby','subgame-instruction');b.addEventListener('click',()=>choose(f.key,value));
    b.addEventListener('dragstart',e=>{drag={key:f.key,value};e.dataTransfer.setData('text/plain',f.key+':'+i);e.dataTransfer.effectAllowed='copy';viewport.classList.add('drop-ready');});b.addEventListener('dragend',()=>{drag=null;viewport.classList.remove('drop-ready');});
    let pointer=null,moved=false;b.addEventListener('pointerdown',e=>{if(e.pointerType!=='mouse'){pointer={id:e.pointerId,x:e.clientX,y:e.clientY};moved=false;b.setPointerCapture(e.pointerId);}});
    b.addEventListener('pointermove',e=>{if(pointer&&Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y)>12){moved=true;viewport.classList.add('drop-ready');}});
    b.addEventListener('pointerup',e=>{if(pointer&&moved){const box=viewport.getBoundingClientRect();if(e.clientX>=box.left&&e.clientX<=box.right&&e.clientY>=box.top&&e.clientY<=box.bottom){choose(f.key,value);e.preventDefault();}}pointer=null;viewport.classList.remove('drop-ready');});b.addEventListener('pointercancel',()=>{pointer=null;viewport.classList.remove('drop-ready');});choices.append(b);
   }group.append(choices);fields.append(group);
  }
  viewport.addEventListener('dragover',e=>{if(drag){e.preventDefault();e.dataTransfer.dropEffect='copy';}});viewport.addEventListener('drop',e=>{e.preventDefault();if(drag)choose(drag.key,drag.value);drag=null;viewport.classList.remove('drop-ready');});
  const row=node('div',undefined,'play-action-row'),instruction=node('p',undefined,'play-instruction'),action=node('button','打开电源 / 开始观察','play-primary'),next=node('button','下一关','play-primary'),help=node('button','给我一点提示'),hint=node('p',undefined,'play-mission-hint');instruction.id='subgame-instruction';instruction.setAttribute('aria-live','polite');action.type=next.type=help.type='button';action.id='subgame-action';next.id='subgame-next';help.id='subgame-help';hint.hidden=true;help.setAttribute('aria-expanded','false');row.append(instruction,action,next,help,hint);workbench.append(row);
  help.addEventListener('click',()=>{hint.hidden=!hint.hidden;help.setAttribute('aria-expanded',String(!hint.hidden));});
  action.addEventListener('click',()=>{if(!s.started)power.click();else if(s.observed>=1.2){s=M.start(s);session[mode]=s;refresh(true);}else{playing=false;updatePause();s=M.observe(s,.6);session[mode]=s;refresh(true);}});
  next.addEventListener('click',()=>{if(!s.cleared.includes(s.index))return;if(s.index===2){s=M.create(id);session.challenge=s;refresh();}else visit(s.index+1);});
  const controls=node('div',undefined,'play-controls'),pause=node('button'),slow=node('button','慢放 1×'),reset=node('button');pause.type=slow.type=reset.type='button';pause.id='subgame-pause';slow.id='subgame-speed';reset.id='subgame-reset';pause.className=reset.className='play-icon';
  reset.setAttribute('aria-label','恢复当前关卡与视角');reset.title='恢复当前关卡与视角';reset.innerHTML=window.TrainingPlaygroundAssets.icons['arrow-path'];
  pause.addEventListener('click',()=>{playing=!playing;last=0;updatePause();});slow.addEventListener('click',()=>{speed=speed===1?.35:1;slow.textContent=speed===1?'慢放 1×':'慢放 0.35×';});reset.addEventListener('click',()=>{s=M.visit(s,s.index);session[mode]=s;view?.restore();hint.hidden=true;refresh();});controls.append(pause,slow,reset);workbench.append(controls);
  const status=node('p',undefined,'play-live');status.id='subgame-status';status.setAttribute('aria-live','polite');workbench.append(status);
  const assumptions=node('details',undefined,'play-assumptions');assumptions.append(node('summary','本次实验条件与资料'),node('p',d.note),node('p','模型为教学功能连接，不是厂商针脚或可生产布板。动画慢放；数字由题设计算，不能替代真实规格。'));for(const [label,url] of chapter.sources){const a=node('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';assumptions.append(a);}root.append(assumptions);
  function updatePause(){pause.setAttribute('aria-label',playing?'暂停动画':'继续动画');pause.setAttribute('aria-pressed',String(!playing));pause.title=playing?'暂停动画':'继续动画';pause.innerHTML=window.TrainingPlaygroundAssets.icons[playing?'pause':'play'];}
  function choose(key,value){s=M.change(s,key,value);session[mode]=s;hint.hidden=true;refresh(true);}
  function cycle(){const f=d.fields[0],i=f.options.findIndex(o=>o[0]===s.params[f.key]);choose(f.key,f.options[(i+1)%f.options.length][0]);}
  function visit(i){const next=M.visit(s,i);if(next===s)return;s=next;session[mode]=s;hint.hidden=true;help.setAttribute('aria-expanded','false');view?.restore();refresh();mission.scrollIntoView({block:'start'});}
  function refresh(announce=false){
   if(disposed)return;const l=M.level(id,s.index),done=mode==='challenge'&&s.cleared.includes(s.index),r=M.evaluate(id,s.params,Math.min(1,s.observed));
   root.dataset.mode=mode;root.dataset.level=String(s.index);root.dataset.cleared=String(s.cleared.length);root.dataset.started=String(s.started);mission.hidden=mode==='free';
   for(const b of modeBar.children)b.setAttribute('aria-pressed',String(b.dataset.subgameMode===mode));missionTitle.textContent='第 '+(s.index+1)+' / 3 关 · '+l.title;count.textContent='已通过 '+s.cleared.length+' / 3';
   for(const b of nav.children){const i=Number(b.dataset.subgameLevel);b.disabled=i>Math.min(s.cleared.length,2);b.setAttribute('aria-current',i===s.index?'step':'false');b.dataset.done=String(s.cleared.includes(i));}
   goal.textContent=mode==='challenge'?l.goal:'直接改条件，再启动观察；这里不限制目标。';goal.hidden=done;storyTitle.textContent=done?'你刚刚学会了':mode==='free'?'自由观察':'这关怎么玩';
   const text=done?l.learned:!s.started?'条件已选好。点电路图里的蓝色按钮，或点下方同名按钮开始。':s.observed<1?'正在观察，可以看动画，也可以点“继续观察一步”。':mode==='free'?r.story:'这次还未达到目标。试着改一个条件，再重新观察。';if(feedback.textContent!==text)feedback.textContent=text;feedback.dataset.done=String(done);
   metrics.replaceChildren(...r.metrics.map(([label,value])=>{const card=node('div');card.append(node('small',label+(s.started?'':' · 条件试算')),node('strong',value));return card;}));reason.textContent=r.story;
   hudLabel.textContent=s.started?r.metrics[0][0]:'等待启动';hudValue.textContent=s.started?r.metrics[0][1]:'点蓝色按钮';
   power.textContent=s.started?'停止观察':'打开电源 / 开始观察';power.setAttribute('aria-pressed',String(s.started));
   next.hidden=!done;next.disabled=!done;next.textContent=s.index===2?'全部通关 · 再玩一次':'下一关';action.hidden=done;action.textContent=s.started?(s.observed>=1.2?'重新观察':'继续观察一步'):'打开电源 / 开始观察';help.hidden=mode==='free'||done;if(help.hidden)hint.hidden=true;hint.textContent=l.hint;
   instruction.textContent=done?'这关通过了！点击下一关继续；最后一关可以再玩一次。':!s.started?'点击条件卡片或拖入电路板，然后点“打开电源 / 开始观察”。每次改条件后会重新开始。':'观察画面与读数；暂停或不想等待时，点“继续观察一步”。未达目标可重新改条件。';
   for(const b of fields.querySelectorAll('button')){const f=d.fields.find(f=>f.key===b.dataset.subgameField);b.setAttribute('aria-pressed',String(s.params[f.key]===f.options[Number(b.dataset.subgameOption)][0]));}
   if(view){view.update(s.params,r,s.started);view.draw(0);}if(failed){status.textContent='浏览器当前无法显示3D，仍可改条件、观察计算结果和闯关。';}else if(announce&&lastStatus!==text){lastStatus=text;status.textContent=text;}
  }
  try{view=window.TrainingSubtypeGameScene.create(canvas,id,cycle);}catch(_){failed=true;canvas.hidden=true;viewport.append(node('p','3D不可用，请启用图形加速；条件卡片与计算结果仍然可用。','play-fallback'));}
  canvas.addEventListener('subgame-context-lost',()=>{failed=true;playing=false;updatePause();refresh();});canvas.addEventListener('subgame-context-restored',()=>{failed=false;status.textContent='3D已恢复，可点击继续动画。';refresh();});
  const motionChanged=()=>{if(motion.matches){playing=false;updatePause();}};motion.addEventListener('change',motionChanged);
  updatePause();refresh();view?.resize();const observer=new IntersectionObserver(es=>{visible=es[0].isIntersecting;last=0;});observer.observe(viewport);
  function loop(now){if(disposed)return;const dt=last?Math.min(.06,(now-last)/1000):0;last=now;if(visible&&!document.hidden&&root.closest('details')?.open){const advance=playing?dt*speed:0;if(s.started&&advance){s=M.observe(s,advance);session[mode]=s;}if(now-paint>90){refresh();paint=now;}view?.draw(id==='cap-tantalum'&&s.observed>=1.2?0:advance);}frame=requestAnimationFrame(loop);}
  frame=requestAnimationFrame(loop);
  const api={id,snapshot:()=>({id,mode,progress:{...s,params:{...s.params},cleared:[...s.cleared]},result:M.evaluate(id,s.params,Math.min(1,s.observed)),playing,speed,scene:view?.snapshot()}),dispose:()=>{session[mode]=s;disposed=true;cancelAnimationFrame(frame);observer.disconnect();motion.removeEventListener('change',motionChanged);view?.dispose();if(active===api)active=null;}};active=api;return api;
 }
 window.TrainingSubtypeGame=Object.freeze({mount,current:()=>active});
})();
