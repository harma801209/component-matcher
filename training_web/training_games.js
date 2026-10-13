(function(){
 'use strict';
 const G=window.TrainingGamesMath,$=id=>document.getElementById(id),node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 let course=window.TrainingLesson.current().course,mode='circuit';
 const sessions=Object.fromEntries(G.courses.map(c=>[c,{params:{...G.lesson(c).defaults},memory:G.deck(c),done:new Set()}]));
 const current=()=>sessions[course];
 function feedback(text,tone=''){$('game-feedback').textContent=text;$('game-feedback').className='game-feedback '+tone;}
 function progress(){const s=current();$('game-progress').textContent='本次已完成 '+s.done.size+' / 2';$('game-summary-title').textContent='边玩边学 · '+G.lesson(course).name+'小游戏';}
 function flow(path,cls=''){return '<path class="game-flow '+cls+'" d="'+path+'"/>';}
 function drawing(p,r){
  const reversed=course==='diode'&&$('game-reverse')?.getAttribute('aria-pressed')==='true';
  const v=r.values,wire='<path class="game-wire" d="M70 190V130H450V250H70V190"/>',battery='<circle cx="70" cy="190" r="27" class="game-device"/><text x="70" y="186" text-anchor="middle">'+(reversed?'−':'+')+'</text><text x="70" y="207" text-anchor="middle">'+(reversed?'+':'−')+'</text>';
  let body='',paths='',title='';
  if(course==='resistor'){
   title='5 V → 电阻 → LED → 电源负端';
   body='<rect x="205" y="112" width="85" height="36" rx="5" class="game-device"/><text x="248" y="102" text-anchor="middle">'+p.r+' Ω</text><circle cx="450" cy="190" r="25" fill="#ffcf40" fill-opacity="'+Math.min(1,v.i/.012)+'" stroke="#b28512"/><text x="450" y="196" text-anchor="middle">LED</text><text x="290" y="280" text-anchor="middle">同一回路：电阻和LED的电流相同</text>';
   paths=flow('M70 190V130H450V250H70V190');
  }else if(course==='capacitor'){
   const x=p.near?340:180;title='电源与电容并联给芯片补电';
   body='<path class="game-wire" d="M'+x+' 130V250"/><rect x="420" y="165" width="60" height="52" rx="5" class="game-device"/><text x="450" y="187" text-anchor="middle">芯片</text><text x="450" y="205" text-anchor="middle">IC</text><rect x="'+(x-25)+'" y="176" width="50" height="28" fill="#f4f8fe"/><path class="game-symbol" d="M'+(x-22)+' 183h44M'+(x-22)+' 198h44"/><text x="'+x+'" y="162" text-anchor="middle">'+p.c+' µF</text><text x="300" y="280" text-anchor="middle">橙色补电同样经过芯片并回到电容</text>';
   paths=flow('M70 190V130H450V250H70V190')+flow('M'+x+' 183V130H450V250H'+x+'V198','energy');
  }else if(course==='inductor'){
   title='电感两端3 V，观察20 µs内电流变化';
   body='<rect x="195" y="111" width="115" height="38" rx="5" class="game-device"/><path class="game-symbol" d="M205 135c0-24 20-24 20 0c0-24 20-24 20 0c0-24 20-24 20 0c0-24 20-24 20 0h15"/><text x="250" y="102" text-anchor="middle">'+p.l+' µH</text><text x="360" y="190">'+v.peak.toFixed(2)+' A*</text><text x="285" y="280" text-anchor="middle">*未饱和线性估算；不是超Isat后的真实波形</text>';
   paths=flow('M70 190V130H450V250H70V190');
  }else{
   const reverse=reversed,conducting=reverse?!p.forward:p.forward;
   title=reverse?'接反电源 · 看反向电流是否被挡住':'正常供电 · 看方向和负载电压';
   body='<rect x="410" y="165" width="80" height="50" rx="5" class="game-device"/><text x="450" y="195" text-anchor="middle">33 Ω</text><g'+(!p.forward?' transform="translate(500 0) scale(-1 1)"':'')+'><path class="game-symbol" d="M230 112l35 18-35 18Z M265 108v44"/></g><text x="217" y="100">'+(p.forward?'A':'K')+'</text><text x="270" y="100">'+(p.forward?'K':'A')+'</text><text x="300" y="280" text-anchor="middle">'+(reverse?(conducting?'接反仍导通：方向错误':'接反被阻断（忽略漏电，未超耐压）'):'负载得到 '+v.output.toFixed(2)+' V')+'</text>';
   if(conducting)paths=flow(reverse?'M70 190V250H450V130H70V190':'M70 190V130H450V250H70V190');
  }
  const arrow=paths?'<path d="'+(reversed?'M380 123L367 130L380 137Z':'M367 123L380 130L367 137Z')+'" fill="#246edf" aria-hidden="true"/>':'';
  const capArrow=course==='capacitor'?'<path d="M404 123L417 130L404 137Z" fill="#d17814" aria-hidden="true"/>':'';
  return '<svg viewBox="0 0 560 305" role="img" aria-label="'+title+'"><title>'+title+'</title><text x="280" y="35" text-anchor="middle">'+title+'</text>'+wire+battery+body+paths+arrow+capArrow+'</svg>';
 }
 function updateCircuit(){
  const s=current(),d=G.lesson(course),r=G.evaluate(course,s.params);
  $('game-board').innerHTML=drawing(s.params,r);
  $('game-metrics').replaceChildren(...r.metrics.map(([label,value])=>{const n=node('div');n.append(node('small',label),node('strong',value));return n;}));
  $('game-hints').replaceChildren(...r.issues.map(text=>node('p',text)));
  if(!r.issues.length)$('game-hints').append(node('p','参数已满足本关目标，点击“试运行”验证。'));
  $('game-why').textContent=r.why;
 }
 function renderCircuit(){
  const out=$('game-body'),d=G.lesson(course);out.replaceChildren();
  const intro=node('div',undefined,'game-intro');intro.append(node('h3',d.title),node('p',d.goal),node('small',d.conditions));
  const layout=node('div',undefined,'game-layout'),left=node('div'),right=node('div');
  const board=node('div',undefined,'game-board');board.id='game-board';left.append(board,node('p',course==='capacitor'?'蓝色：电源供电；橙色：电容补电。箭头为约定电流方向，动画不代表速度。':'蓝色：电流路径。箭头为约定电流方向，动画不代表速度。','circuit-caption'));
  if(course==='diode'){const reverse=node('button','试接反电源');reverse.id='game-reverse';reverse.type='button';reverse.setAttribute('aria-pressed','false');reverse.addEventListener('click',()=>{const on=reverse.getAttribute('aria-pressed')!=='true';reverse.setAttribute('aria-pressed',String(on));reverse.textContent=on?'恢复正常电源':'试接反电源';updateCircuit();feedback(on?'正在观察接反电源。':'已恢复正常供电。');});left.append(reverse);}
  const controls=node('div',undefined,'game-controls');for(const field of d.fields){const label=node('label',field.label),select=node('select');select.id='game-param-'+field.id;select.dataset.gameParam=field.id;for(const [value,text] of field.options){const option=node('option',text);option.value=String(value);select.append(option);}select.value=String(current().params[field.id]);select.addEventListener('change',()=>{current().params[field.id]=field.options.find(o=>String(o[0])===select.value)[0];updateCircuit();feedback('已更换参数，观察电路再试运行。');});label.htmlFor=select.id;label.append(select);controls.append(label);}
  const metrics=node('div',undefined,'game-metrics');metrics.id='game-metrics';const hints=node('div',undefined,'game-hints');hints.id='game-hints';
  const run=node('button','试运行','primary');run.type='button';run.id='game-run';run.addEventListener('click',()=>{const r=G.evaluate(course,current().params);if(r.passed){current().done.add('circuit');progress();feedback('闯关成功！'+r.why,'correct');}else feedback('还差一点：'+r.issues.join(' '),'incorrect');});
  right.append(controls,metrics,hints,run);layout.append(left,right);
  const why=node('div',undefined,'game-takeaway');why.append(node('strong','为什么会这样？'));const text=node('p');text.id='game-why';why.append(text);
  const notes=node('details',undefined,'lesson-more'),summary=node('summary','真实选型还要看什么？'),a=node('a',d.source[0]+' ↗');a.href=d.source[1];a.target='_blank';a.rel='noopener noreferrer';notes.append(summary,node('p',d.note),a);
  out.append(intro,layout,why,notes);updateCircuit();
 }
 function renderCards(focusId){
  const out=$('game-body'),s=current(),d=G.lesson(course);out.replaceChildren();const intro=node('div',undefined,'game-intro');intro.append(node('h3',d.name+' · 知识翻牌配对'),node('p','每次翻两张，找到对应的参数、单位或作用。配对成功会解释原因；不计时，可以慢慢试。'));
  const count=node('p','已配对 '+s.memory.matched.length/2+' / 4 · 已尝试 '+s.memory.turns+' 次','game-card-count'),grid=node('div',undefined,'game-deck');grid.setAttribute('aria-label','知识配对卡牌');
  for(const [i,card] of s.memory.cards.entries()){
   const matched=s.memory.matched.includes(card.id),visible=matched||s.memory.selected.includes(card.id),b=node('button',visible?card.text:String(i+1),'game-flip-card');b.type='button';b.dataset.gameCard=String(card.id);b.dataset.revealed=String(visible);b.disabled=matched;b.setAttribute('aria-label',matched?'已配对：'+card.text:visible?card.text:'翻开第'+(i+1)+'张卡牌');b.setAttribute('aria-pressed',String(visible));
   b.addEventListener('click',()=>{const r=G.flip(s.memory,card.id);s.memory=r.state;if(s.memory.matched.length===8){s.done.add('memory');progress();feedback('全部配对完成！'+r.explain,'correct');}else feedback((r.outcome==='match'?'配对成功！':'')+r.explain,r.outcome==='miss'?'incorrect':r.outcome==='match'?'correct':'');renderCards(card.id);});grid.append(b);
  }
  out.append(intro,count,grid);if(focusId!==undefined){const target=grid.querySelector('[data-game-card="'+focusId+'"]');if(!target.disabled)target.focus({preventScroll:true});else grid.querySelector('button:not(:disabled)')?.focus({preventScroll:true});}
 }
 function render(){progress();document.querySelectorAll('[data-game-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.gameMode===mode)));if(mode==='circuit')renderCircuit();else renderCards();feedback('选择参数试运行，或翻牌配对。');}
 document.querySelectorAll('[data-game-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.gameMode;render();}));
 $('game-restart').addEventListener('click',()=>{if(mode==='circuit')current().params={...G.lesson(course).defaults};else current().memory=G.deck(course);render();feedback('已重新开始本游戏。');});
 window.addEventListener('training-course-change',e=>{if(G.courses.includes(e.detail.course)){course=e.detail.course;render();}});
 render();
})();
