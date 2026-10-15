/* Screen-space callouts outside the projected model, with 44px hit targets. */
(function(root){
 'use strict';
 const radius=22,gap=8;
 function layout(anchors,bounds,width,height){
  if(!anchors.length)return [];
  const minY=72,maxY=height-56,rows=Math.floor((maxY-minY)/48)+1;
  if(rows<1||anchors.length>rows*2)throw new RangeError('Insufficient model label space');
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),slots=[];
  const left=clamp(bounds.left-radius-gap,radius+2,width-radius-2),right=clamp(bounds.right+radius+gap,radius+2,width-radius-2);
  for(const x of [left,right])for(let i=0;i<rows;i++)slots.push({x,y:rows===1?(minY+maxY)/2:minY+i*(maxY-minY)/(rows-1)});
  return anchors.map(anchor=>{
   let best=0,cost=Infinity;
   slots.forEach((s,i)=>{const d=(s.x-anchor.point[0])**2+(s.y-anchor.point[1])**2;if(d<cost){cost=d;best=i;}});
   const position=slots.splice(best,1)[0];return {id:anchor.id,...position,point:anchor.point.slice(0,2)};
  });
 }
 const api=Object.freeze({layout,radius,gap});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingModelLabels=api;
})(typeof globalThis==='undefined'?this:globalThis);
