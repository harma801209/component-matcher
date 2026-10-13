/* One entrance: the existing sequential challenges and their free mode. */
(function(){
 'use strict';
 const M=window.TrainingPlaygroundMath,names={resistor:'厚膜电阻',capacitor:'MLCC',inductor:'绕线电感',diode:'开关二极管'};
 let course=window.TrainingLesson.current().course,subtype=null,activePlayground=null;
 function render(){
  activePlayground?.dispose();
  const chapter=subtype?window.TrainingCatalog.lesson(subtype):null;
  document.getElementById('game-summary-title').textContent='边玩边学 · '+(chapter?chapter.title:names[course])+'闯关';
  document.getElementById('game-summary-count').textContent=(chapter&&!chapter.baseline?'3':'4')+' 关挑战 · 可自由实验';
  activePlayground=chapter&&!chapter.baseline?window.TrainingSubtypeGame.mount(document.getElementById('game-body'),subtype):window.TrainingPlayground.mount(document.getElementById('game-body'),course);
 }
 window.addEventListener('training-course-change',e=>{
  if(M.courses.includes(e.detail?.course)){course=e.detail.course;if(!subtype)render();}
 });
 window.addEventListener('training-subtype-change',e=>{const chapter=window.TrainingCatalog.lesson(e.detail.id);subtype=chapter.id;if(chapter.baseline)course=chapter.family;render();});
 window.TrainingGameEntry=Object.freeze({current:()=>activePlayground});render();
})();
