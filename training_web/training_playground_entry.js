/* One entrance: the existing sequential challenges and their free mode. */
(function(){
 'use strict';
 const M=window.TrainingPlaygroundMath,names={resistor:'厚膜电阻',capacitor:'MLCC',inductor:'绕线电感',diode:'开关二极管'};
 let course=window.TrainingLesson.current().course,activePlayground=null;
 function render(){
  activePlayground?.dispose();
  document.getElementById('game-summary-title').textContent='边玩边学 · '+names[course]+'闯关';
  activePlayground=window.TrainingPlayground.mount(document.getElementById('game-body'),course);
 }
 window.addEventListener('training-course-change',e=>{
  if(M.courses.includes(e.detail?.course)){course=e.detail.course;render();}
 });
 render();
})();
