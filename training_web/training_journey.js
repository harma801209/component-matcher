/* Move existing modules intact into one learning order; no new course data/store. */
(function(){
 'use strict';
 const app=document.getElementById('training-app'),make=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
 const steps=[
  ['recognize','认识器件','先认识用途和外观，再按需要查看内部材料。'],
  ['circuit','看懂电路作用','看器件接在哪里，再观察电路或信号发生了什么变化。'],
  ['game','动手闯关','在3D电路上试一试；可重复观察，不扣分。'],
  ['specs','参数与选型','理解用途后再读参数、试条件，练习客户需求。'],
  ['review','检查理解','用小测验确认理解；答错先看解释，再试一次。']
 ];
 const path=make('nav',null,'lesson-path');path.id='lesson-path';path.setAttribute('aria-label','学习步骤快捷定位');
 const caption=make('p','建议按顺序学习；也可以直接跳到需要的步骤。','lesson-path-caption');path.append(caption);
 const buttons=make('div',null,'lesson-path-buttons');path.append(buttons);app.querySelector('.subtype-picker').after(path);
 const stageNodes=new Map();
 for(const [i,[key,title,description]] of steps.entries()){
  const b=make('button',(i+1)+' · '+title);b.type='button';b.dataset.learningTarget=key;b.setAttribute('aria-controls','lesson-'+key);b.addEventListener('click',()=>go(key));buttons.append(b);
  const section=make('section',null,'learning-stage');section.id='lesson-'+key;section.dataset.learningStage=key;section.setAttribute('aria-labelledby','lesson-'+key+'-title');
  const head=make('div',null,'learning-stage-head'),text=make('div'),heading=make('h2',String(i+1).padStart(2,'0')+' / '+title);heading.id='lesson-'+key+'-title';heading.tabIndex=-1;text.append(heading,make('p',description));
  const back=make('button','学习目录');back.type='button';back.dataset.learningTop='true';back.addEventListener('click',()=>{path.scrollIntoView({block:'start',behavior:'auto'});buttons.querySelector('[aria-current="step"]')?.focus({preventScroll:true});});head.append(text,back);section.append(head);stageNodes.set(key,section);app.append(section);
 }
 const workspace=app.querySelector('.workspace'),model=app.querySelector('.model-card'),knowledge=app.querySelector('.knowledge-card'),quiz=document.getElementById('panel-quiz'),quizTab=document.getElementById('tab-quiz');
 const overview=make('aside',null,'lesson-overview'),name=make('h3'),purpose=make('p'),useLabel=make('h4','常见应用'),use=make('p');overview.append(name,purpose,useLabel,use,make('p','先转动模型看看外观；想了解组成材料，再切换“内部材料结构”。','lesson-overview-tip'));
 knowledge.remove();workspace.append(overview);stageNodes.get('recognize').append(workspace);
 model.querySelector('.eyebrow').textContent='外观与内部结构';
 stageNodes.get('circuit').append(document.getElementById('subtype-application'),document.getElementById('circuit-card'));
 stageNodes.get('game').append(document.getElementById('games-card'));
 stageNodes.get('specs').append(knowledge,app.querySelector('.practice-card'),app.querySelector('.takeaways'));
 app.querySelector('.practice-card .eyebrow').textContent='型号与选型练习';
 const review=make('section',null,'quiz-card'),quizTabs=make('div',null,'tabs');quizTabs.setAttribute('role','tablist');quizTabs.setAttribute('aria-label','小测验');quizTabs.append(quizTab);review.append(quizTabs,quiz);quiz.hidden=false;quizTab.tabIndex=0;quizTab.setAttribute('aria-selected','true');stageNodes.get('review').append(review);
 const references=app.querySelector('.references'),more=make('details',null,'lesson-reference-more');more.id='lesson-reference-more';more.append(make('summary','需要查具体型号时：展开原厂资料'),references);app.append(more);
 function active(key){for(const b of buttons.children)b.setAttribute('aria-current',b.dataset.learningTarget===key?'step':'false');}
 function go(key){if(!stageNodes.has(key))return false;if(key==='game')document.getElementById('games-card').open=true;if(key==='review')quizTab.click();active(key);const section=stageNodes.get(key);section.scrollIntoView({block:'start',behavior:'auto'});section.querySelector('h2').focus({preventScroll:true});return true;}
 function sync(){const d=window.TrainingCatalogUI.current(),guide=d.baseline?d.family:d.id,B=window.TrainingBeginner;stageNodes.get('recognize').dataset.subtype=d.id;name.textContent=d.title;const summary=B.supported(guide)?B.lesson(guide).purpose:null;purpose.textContent=summary?summary.slice(summary.indexOf('：')+1):d.summary+'。';use.textContent=d.use+'。';const info=document.querySelector('#panel-spec .info');if(info)info.textContent='点击“电气性能”试参数；需要对照模型，可返回第1步查看外观或内部结构。';active('recognize');}
 window.addEventListener('training-subtype-change',sync);sync();app.dataset.learningJourney='ordered';
 window.TrainingJourney=Object.freeze({steps:steps.map(([key,title])=>({key,title})),go});
})();
