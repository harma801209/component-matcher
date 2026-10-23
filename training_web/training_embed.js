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
 let immersive=false,undo=[];
 const owner=frame.ownerDocument?.defaultView;
 function change(node,key,value){if(!node?.style)return;const old=node.style.getPropertyValue?.(key)||'',priority=node.style.getPropertyPriority?.(key)||'';undo.push(()=>{if(old)node.style.setProperty(key,old,priority);else node.style.removeProperty?.(key);});node.style.setProperty(key,value,'important');}
 function setImmersive(value){
  value=Boolean(value);if(value===immersive)return;immersive=value;
  if(value){
   const target=container||frame;for(const [key,val] of Object.entries({position:'fixed',inset:'0',width:'100vw',height:'100dvh','z-index':'2147483000',margin:'0',padding:'0',transform:'none'}))change(target,key,val);
   change(frame,'width','100%');change(frame,'height',(owner?.innerHeight||window.innerHeight)+'px');change(frame,'max-height','none');change(frame.ownerDocument?.body,'overflow','hidden');
  }else{for(const f of undo.reverse())f();undo=[];resize();}
  frame.dataset.trainingImmersive=String(immersive);
 }
 function resize(){
  pending=false;
  if(immersive){frame.style.setProperty('height',(owner?.visualViewport?.height||owner?.innerHeight||window.innerHeight)+'px','important');return;}
  // Root scrollHeight includes the iframe viewport and cannot shrink reliably.
  const height=Math.ceil(app.getBoundingClientRect().height)+12;
  if(!Number.isFinite(height)||height<=12)return;
  if(frame.style.height!==height+'px'){
   frame.style.setProperty('height',height+'px','important');
   frame.dataset.trainingHeight=String(height);
  }
 }
 function schedule(){if(!pending){pending=true;requestAnimationFrame(resize);}}
 // Scene actions may change an entire work phase before the observer's next
 // frame. Let that trusted UI settle its own iframe height before scrolling.
 window.TrainingEmbedLayout=Object.freeze({flush:resize,setImmersive});
 owner?.addEventListener('resize',schedule);
 window.addEventListener('pagehide',()=>setImmersive(false));
 if(typeof ResizeObserver!=='undefined')new ResizeObserver(schedule).observe(app);
 else new MutationObserver(schedule).observe(app,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['open','hidden']});
 window.addEventListener('resize',schedule);
 window.addEventListener('load',schedule);
 document.addEventListener('toggle',schedule,true);
 document.addEventListener('load',schedule,true);
 if(document.fonts)document.fonts.ready.then(schedule);
 schedule();
})();
