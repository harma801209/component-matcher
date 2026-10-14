/* Keep text outside the rotating model; move existing nodes, never duplicate controls. */
(function(){
 'use strict';
 function mount(root){
  const console=root.querySelector('.play-console'),media=matchMedia('(max-width:760px)'),moves=[];
  const viewport=root.querySelector('.play-viewport');
  let board=root.querySelector('.play-board-column');
  if(!board){board=document.createElement('div');board.className='play-board-column';viewport.before(board);board.append(viewport);}
  const caption=document.createElement('div'),readout=document.createElement('div');
  caption.className='play-scene-caption';readout.className='play-scene-readout';
  // A screen-space pill anchored to R1 can cover its marking at any camera angle.
  // Reserve separate rows instead, keeping the full canvas available to the model.
  viewport.before(caption);viewport.after(readout);
  for(const selector of ['.play-badge','.play-device-focus','.play-labels']){const node=viewport.querySelector(selector);if(node)caption.append(node);}
  for(const selector of ['.play-view-hint','.play-hud']){const node=viewport.querySelector(selector);if(node)readout.append(node);}
  const detail=document.createElement('details'),summary=document.createElement('summary'),body=document.createElement('div');
  detail.className='play-mobile-explanation';detail.hidden=true;summary.textContent='原理与详细结果';body.className='play-mobile-explanation-body';detail.append(summary,body);console.append(detail);
  const paragraphs=[...console.children].filter(n=>n.tagName==='P'&&!n.matches('.play-goal,.play-fixed-condition,.play-instruction,.play-mission-hint,.play-live,.play-outcome'));
  const candidates=[root.querySelector('.play-beginner-intro'),root.querySelector('.play-cause'),root.querySelector('.play-result-title'),...paragraphs,root.querySelector('.subgame-metrics'),root.querySelector('.play-why')].filter(Boolean);
  for(const node of new Set(candidates)){const home=document.createComment('original game explanation position');node.before(home);moves.push({node,home});}
  for(const [i,button] of [...root.querySelectorAll('.play-level-nav button')].entries()){
   const label=document.createElement('span'),index=document.createElement('span');label.className='play-level-label';label.textContent=button.textContent;index.className='play-level-index';index.textContent=String(i+1);index.setAttribute('aria-hidden','true');button.setAttribute('aria-label',label.textContent);button.replaceChildren(label,index);
  }
  function sync(){
   const compact=media.matches,focused=document.activeElement;
   if(!compact)detail.open=false;
   for(const {node,home} of moves){if(compact)body.append(node);else home.after(node);}
   detail.hidden=!compact;root.dataset.mobileLayout=compact?'compact':'desktop';
   // Keep keyboard focus if an orientation change moves the same control.
   if(focused&&root.contains(focused)&&focused.getClientRects().length)focused.focus({preventScroll:true});
  }
  media.addEventListener('change',sync);sync();
  return {dispose(){media.removeEventListener('change',sync);}};
 }
 window.TrainingPlaygroundLayout=Object.freeze({mount});
})();
