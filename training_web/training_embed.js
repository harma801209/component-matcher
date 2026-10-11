/* Expand only this trusted training iframe; the host page owns vertical scroll. */
(function(){
 'use strict';
 const app=document.getElementById('training-app');
 let frame;
 try{frame=window.frameElement;}catch(_){return;}
 // Standalone lessons retain their normal page scrolling (including local QA).
 if(!frame||!app)return;
 const container=frame.closest('[data-testid="stElementContainer"]')||frame.closest('.element-container');
 frame.dataset.trainingAutoheight='true';
 frame.setAttribute('scrolling','no');
 document.documentElement.dataset.trainingEmbedded='autoheight';
 document.documentElement.style.overflowY='hidden';
 document.body.style.overflowY='hidden';
 app.style.display='flow-root';
 frame.style.display='block';
 frame.style.setProperty('min-height','0','important');
 frame.style.setProperty('max-height','none','important');
 if(container){
  container.style.setProperty('height','auto','important');
  container.style.setProperty('flex','0 0 auto','important');
  container.style.setProperty('min-height','0','important');
  container.style.setProperty('max-height','none','important');
 }
 let pending=false;
 function resize(){
  pending=false;
  // Root scrollHeight includes the iframe viewport and cannot shrink reliably.
  const height=Math.ceil(app.getBoundingClientRect().height)+12;
  if(!Number.isFinite(height)||height<=12)return;
  if(frame.style.height!==height+'px'){
   frame.style.setProperty('height',height+'px','important');
   frame.dataset.trainingHeight=String(height);
  }
 }
 function schedule(){if(!pending){pending=true;requestAnimationFrame(resize);}}
 if(typeof ResizeObserver!=='undefined')new ResizeObserver(schedule).observe(app);
 else new MutationObserver(schedule).observe(app,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['open','hidden']});
 window.addEventListener('resize',schedule);
 window.addEventListener('load',schedule);
 document.addEventListener('toggle',schedule,true);
 document.addEventListener('load',schedule,true);
 if(document.fonts)document.fonts.ready.then(schedule);
 schedule();
})();
