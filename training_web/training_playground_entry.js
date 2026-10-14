/* One game module: learn components first, then unlock product circuits. */
(function(){
 'use strict';
 const M=window.TrainingPlaygroundMath,P=window.TrainingGameProgress,C=window.TrainingCatalog,names={resistor:'厚膜电阻',capacitor:'MLCC',inductor:'绕线电感',diode:'开关二极管'},$=id=>document.getElementById(id);
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
 let course=window.TrainingLesson.current().course,subtype=null,activePlayground=null,stage='lessons';
 const path=node('div',null,'game-learning-path'),tabs=node('div',null,'game-path-tabs'),lessons=node('button','1 · 器件学习关卡'),projects=node('button','2 · 综合电路'),guide=node('details',null,'game-prerequisites'),summary=node('summary'),list=node('ul'),storage=node('p',null,'game-progress-note');
 lessons.id='game-lessons';projects.id='game-projects';lessons.type=projects.type='button';tabs.setAttribute('role','group');tabs.setAttribute('aria-label','学习闯关阶段');lessons.setAttribute('aria-controls','game-body');projects.setAttribute('aria-controls','nightlight-pane');tabs.append(lessons,projects);guide.id='game-prerequisites';guide.append(summary,list);path.append(tabs,guide,storage);$('game-progression').append(path);
 for(const id of P.requirements){const d=C.lesson(id),item=node('li'),title=node('strong',d.title),count=node('span'),go=node('button','去学习');go.type='button';go.dataset.gamePrerequisite=id;go.setAttribute('aria-label','学习'+d.title+'的关卡');go.addEventListener('click',()=>{showLessons();window.TrainingCatalogUI.choose(id);$('games-card').open=true;guide.open=false;focusLesson();});item.dataset.prerequisite=id;item.append(title,count,go);list.append(item);}
 function focusLesson(){const mission=$('game-body').querySelector('.play-mission'),head=mission?.querySelector('h4');mission?.scrollIntoView({block:'start'});if(head){head.tabIndex=-1;head.focus({preventScroll:true});}}
 function update(){
  const unlocked=P.eligible('nightlight');projects.disabled=!unlocked;projects.textContent='2 · 综合电路'+(unlocked?'':'（待解锁）');projects.title=unlocked?'组装小夜灯':'完成厚膜电阻、肖特基二极管、铝电解电容和N沟道MOS的关卡后解锁';
  lessons.setAttribute('aria-pressed',String(stage==='lessons'));projects.setAttribute('aria-pressed',String(stage==='project'));
  let finished=0;for(const item of list.children){const id=item.dataset.prerequisite,n=P.get(id).cleared,done=n===P.total(id);if(done)finished++;item.querySelector('span').textContent=done?'已通关':n+' / '+P.total(id)+' 关';item.dataset.done=String(done);item.querySelector('button').textContent=done?'复习':'去学习';}
  if(unlocked&&guide.dataset.unlocked!=='true')guide.open=false;summary.textContent=unlocked?'已解锁小夜灯 · 查看已学器件':'解锁小夜灯：已通过 '+finished+' / 4 个所需器件';guide.dataset.unlocked=String(unlocked);
  storage.textContent=P.storageOK()?'先学器件，再挑战综合电路。通关记录保存在当前浏览器，重玩不会取消解锁。':'当前浏览器无法保存记录；本次仍可学习并解锁，刷新后需重新完成器件关卡。';
  $('game-body').hidden=stage!=='lessons';$('nightlight-pane').hidden=stage!=='project';$('games-card').dataset.gameStage=stage;
  if(stage==='project'){$('game-summary-title').textContent='学习闯关 · 综合电路：小夜灯';const n=window.TrainingNightlight?.current()?.snapshot().state.cleared||0;$('game-summary-count').textContent='5步产品制作 · 已完成'+n+'步';}
 }
 function showLessons(){stage='lessons';update();const d=subtype?C.lesson(subtype):null;$('game-summary-title').textContent='学习闯关 · '+(d?d.title:names[course]);$('game-summary-count').textContent=(d&&!d.baseline?'3':'4')+' 关挑战 · 可自由实验';return true;}
 function showProject(){if(!P.eligible('nightlight')){guide.open=true;update();return false;}stage='project';update();$('games-card').open=true;const result=window.TrainingNightlight?.open();if(!result){showLessons();return false;}update();$('nightlight-body').scrollIntoView({block:'start'});$('nightlight-body').querySelector('h3')?.focus({preventScroll:true});return true;}
 function continueLearning(id){if(!P.nextLabel(id))return false;if(P.eligible('nightlight'))return showProject();const next=P.requirements.find(id=>P.get(id).cleared<P.total(id));showLessons();window.TrainingCatalogUI.choose(next);guide.open=false;focusLesson();return true;}
 function render(){activePlayground?.dispose();const d=subtype?C.lesson(subtype):null;activePlayground=d&&!d.baseline?window.TrainingSubtypeGame.mount($('game-body'),subtype):window.TrainingPlayground.mount($('game-body'),course);showLessons();}
 lessons.addEventListener('click',showLessons);projects.addEventListener('click',showProject);
 window.addEventListener('training-game-progress-change',update);window.addEventListener('training-nightlight-progress',update);
 window.addEventListener('training-course-change',e=>{if(M.courses.includes(e.detail?.course)){course=e.detail.course;if(!subtype)render();}});
 window.addEventListener('training-subtype-change',e=>{const d=C.lesson(e.detail.id);subtype=d.id;if(d.baseline)course=d.family;render();});
 window.TrainingGameEntry=Object.freeze({current:()=>activePlayground,showLessons,showProject,continueLearning,stage:()=>stage});render();
})();
