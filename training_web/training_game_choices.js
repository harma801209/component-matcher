/* Explicit learner choices are ephemeral, not inferred from example values. */
(function(root){
 'use strict';
 function create(){
  const values=new Map();
  return Object.freeze({
   select(key,value){values.set(key,value);},
   has(key,value){return values.has(key)&&values.get(key)===value;},
   missing(keys){return keys.filter(key=>!values.has(key));},
   clear(){values.clear();},
   snapshot(){return Object.fromEntries(values);}
  });
 }
 const api=Object.freeze({create});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingGameChoices=api;
})(typeof globalThis==='undefined'?this:globalThis);
