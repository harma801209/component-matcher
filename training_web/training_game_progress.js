/* Browser-local learning achievements. No member or business data access. */
(function(root){
 'use strict';const node=typeof module!=='undefined'&&module.exports;
 const C=node?require('./training_catalog.js'):root.TrainingCatalog,L=node?require('./training_playground_levels.js'):root.TrainingPlaygroundLevels,S=node?require('./training_subtype_game_math.js'):root.TrainingSubtypeGameMath;
 const key='fruition.training.lessons.v1',requirements=Object.freeze(['res-thick','dio-schottky','cap-aluminum','mos-n']);
 const projects=Object.freeze({nightlight:Object.freeze({title:'小夜灯',requires:requirements})});
 const known=Object.fromEntries(C.lessons.map(d=>[d.id,d])),baseline=Object.fromEntries(C.lessons.filter(d=>d.baseline).map(d=>[d.family,d.id]));
 const total=id=>{if(!Object.hasOwn(known,id))throw new RangeError('Unknown learning chapter');return known[id].baseline?4:3;};
 function validEntry(id,e){
  if(!Object.hasOwn(known,id)||!e||!Number.isInteger(e.cleared)||e.cleared<1||e.cleared>total(id)||!e.review)return null;
  const d=known[id],r=e.review,index=e.cleared-1,cleared=Array.from({length:e.cleared},(_,i)=>i);
  try{
   if(d.baseline){const p={value:r.params.value,power:r.params.power,reverse:r.params.reverse,near:r.params.near},state={course:d.family,index,cleared,started:r.started,interacted:r.interacted};if(!L.judge(state,p,r.phase).passed)return null;return {cleared:e.cleared,review:{params:p,phase:r.phase,started:r.started,interacted:r.interacted}};}
   const params=Object.fromEntries(S.profile(id).fields.map(f=>[f.key,r.params[f.key]])),state={id,index,cleared,params,started:r.started,observed:r.observed};if(!S.judge(state).passed)return null;return {cleared:e.cleared,review:{params,started:r.started,observed:r.observed}};
  }catch(_){return null;}
 }
 function validate(raw){const lessons={};if(raw?.version===1&&raw.lessons&&typeof raw.lessons==='object'&&!Array.isArray(raw.lessons))for(const id of Object.keys(raw.lessons)){const e=validEntry(id,raw.lessons[id]);if(e)lessons[id]=e;}return {version:1,lessons};}
 function eligible(records,project='nightlight'){return Object.hasOwn(projects,project)&&projects[project].requires.every(id=>(records.lessons[id]?.cleared||0)===total(id));}
 function createStore(storage,onChange=()=>{}){
  let state={version:1,lessons:{}},storageOK=true;const clone=x=>JSON.parse(JSON.stringify(x));
  try{const text=storage.getItem(key);try{state=validate(JSON.parse(text||'null'));}catch(_){}}catch(_){storageOK=false;}
  function merge(raw){const incoming=validate(raw);for(const [id,e] of Object.entries(incoming.lessons))if(e.cleared>(state.lessons[id]?.cleared||0))state.lessons[id]=e;}
  function save(id,entry){const e=validEntry(id,entry);if(!e||e.cleared<=(state.lessons[id]?.cleared||0))return false;state.lessons[id]=e;
   try{const text=storage.getItem(key);let incoming=null;try{incoming=JSON.parse(text||'null');}catch(_){}merge(incoming);storage.setItem(key,JSON.stringify(state));storageOK=true;}catch(_){storageOK=false;}
   onChange();return true;
  }
  function recordBaseline(course,progress,params,phase,mode='challenge'){const id=baseline[course];if(mode!=='challenge'||!id||progress.index!==progress.cleared.length-1)return false;return save(id,{cleared:progress.cleared.length,review:{params,phase,started:progress.started,interacted:progress.interacted}});}
  function recordSubtype(progress,mode='challenge'){if(mode!=='challenge'||progress.index!==progress.cleared.length-1)return false;return save(progress.id,{cleared:progress.cleared.length,review:{params:progress.params,started:progress.started,observed:progress.observed}});}
  function restoreBaseline(course){const id=baseline[course],e=state.lessons[id],count=e?.cleared||0,index=Math.min(count,3),progress={...L.create(course),index,cleared:Array.from({length:count},(_,i)=>i)};
   if(count===4){Object.assign(progress,{started:e.review.started,interacted:e.review.interacted});return {progress,params:{...e.review.params},elapsed:course==='capacitor'?e.review.phase*3:course==='inductor'?e.review.phase:0};}
   return {progress,params:{...L.level(course,index).setup},elapsed:0};
  }
  function restoreSubtype(id){const initial=S.create(id),e=state.lessons[id],count=e?.cleared||0,index=Math.min(count,2);return {...initial,index,cleared:Array.from({length:count},(_,i)=>i),params:count===3?{...e.review.params}:{...S.level(id,index).setup},started:count===3?e.review.started:false,observed:count===3?e.review.observed:0};}
  function nextLabel(id){if(!requirements.includes(id)||(state.lessons[id]?.cleared||0)!==total(id))return null;if(eligible(state))return '挑战综合电路 · 小夜灯';const next=requirements.find(id=>(state.lessons[id]?.cleared||0)<total(id));return '继续学 · '+known[next].title;}
  return Object.freeze({recordBaseline,recordSubtype,restoreBaseline,restoreSubtype,total,nextLabel,get:id=>clone(state.lessons[id]||{cleared:0}),snapshot:()=>clone(state),eligible:project=>eligible(state,project),storageOK:()=>storageOK,merge:raw=>{merge(raw);onChange();}});
 }
 const pure=Object.freeze({key,requirements,projects,total,validEntry,validate,eligible,createStore});
 if(node){module.exports=pure;return;}
 let storage;try{storage=root.localStorage;}catch(_){storage={getItem(){throw new Error('Storage unavailable');},setItem(){throw new Error('Storage unavailable');}};}
 const changed=()=>root.dispatchEvent(new CustomEvent('training-game-progress-change'));
 root.TrainingGameProgress=Object.freeze({...pure,...createStore(storage,changed)});
 root.addEventListener('storage',e=>{if(e.key===key&&e.newValue){try{root.TrainingGameProgress.merge(JSON.parse(e.newValue));}catch(_){}}});
})(typeof globalThis!=='undefined'?globalThis:this);
