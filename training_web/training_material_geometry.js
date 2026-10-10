/* Procedural cutaway volumes; visual thicknesses are enlarged for learning. */
(function(root){
 'use strict';
 const data=typeof module!=='undefined'&&module.exports?require('./training_material_data.js'):root.TrainingMaterialData;
 function build(course,e,primitives){
  const lesson=data.lesson(course);
  if(!Number.isFinite(e)||e<0||e>1)throw new RangeError('Invalid explosion');
  const {box,tube}=primitives,f=[],points={};
  const block=(id,p,size,color)=>box(f,p,size,color,id);
  const anchor=(id,p)=>{points[id]=p;};
  if(course==='resistor'){
   block('substrate',[0,-.2,-.2],[2.6,.5,.9],[222,230,235]);anchor('substrate',[0,-.3,.25]);
   block('film',[0,.14+e*.5,-.2],[2.45,.09,.9],[77,81,92]);anchor('film',[0,.17+e*.5,.25]);
   block('cover',[0,.43+e*1.0,-.2],[2.48,.12,.9],[147,188,217]);anchor('cover',[0,.49+e*1.0,.25]);
   for(const s of [-1,1]){
    block('electrode',[s*(1.34+e*.12),-.12,-.2],[.12,.65,.9],[187,157,100]);
    block('nickel',[s*(1.46+e*.3),-.12,-.2],[.12,.65,.9],[130,156,185]);
    block('finish',[s*(1.58+e*.48),-.12,-.2],[.12,.65,.9],[200,212,224]);
   }
   anchor('electrode',[-1.34-e*.12,.08,.25]);anchor('nickel',[-1.46-e*.3,-.17,.25]);anchor('finish',[1.58+e*.48,-.17,.25]);
  }else if(course==='capacitor'){
   const step=.16+e*.10;
   for(let i=0;i<7;i++)block('dielectric',[0,(i-3)*step,-.15],[2.6,.13,.9],[231,208,153]);
   for(let i=0;i<6;i++)block('internal',[i%2?.075:-.075,(i-2.5)*step,-.15],[2.65,.025,.85],[133,151,176]);
   for(const s of [-1,1]){
    block('base',[s*(1.44+e*.12),0,-.15],[.14,1.18+e*.6,.9],[179,119,67]);
    block('barrier',[s*(1.58+e*.3),0,-.15],[.14,1.18+e*.6,.9],[139,163,191]);
    block('tin',[s*(1.72+e*.48),0,-.15],[.14,1.18+e*.6,.9],[204,215,227]);
   }
   anchor('dielectric',[.5,step*3,.3]);anchor('internal',[-.3,step*2.5,.275]);anchor('base',[-1.44-e*.12,.2,.3]);anchor('barrier',[-1.58-e*.3,-.15,.3]);anchor('tin',[1.72+e*.48,0,.3]);
  }else if(course==='inductor'){
   block('core',[0,-.7,-.15],[2.7,.3,1.35],[82,101,120]);
   tube(f,[0,-.55,-.15],[0,.65,-.15],.38,[106,129,149],'core',20);
   // Keep rear shielding separate; the front is removed to reveal the winding.
   block('core',[0,0,-.85],[2.7,1.3,.18],[82,101,120]);
   const turns=Array.from({length:65},(_,i)=>[Math.cos(i/64*Math.PI*8)*(.7+e*.15),-.48+i/64*1.03,Math.sin(i/64*Math.PI*8)*(.7+e*.15)-.15]);
   for(let i=0;i<turns.length-1;i++)tube(f,turns[i],turns[i+1],.075,[186,121,62],'copper',6,false);
   // Enlarged isolated sample exposes copper under the enamel cut face.
   tube(f,[1.23+e*.35,-.2,.1],[1.23+e*.35,.38,.1],.17,[226,196,90],'insulation',18);
   tube(f,[1.23+e*.35,.39,.1],[1.23+e*.35,.5,.1],.105,[186,121,62],'copper',18);
   for(const s of [-1,1])block('terminal',[s*1.08,-.95,0],[.55,.12,1.25],[191,205,219]);
   anchor('core',[0,.65,.15]);anchor('copper',[0,-.48+4/64*1.03,.55+e*.15]);anchor('insulation',[1.23+e*.35,.18,.25]);anchor('terminal',[-1.08,-.95,.5]);
  }else{
   // Adjacent doped regions stay in one chip even in the exploded view.
   block('p',[-.46,0,.05],[.8,.5,.65],[218,150,116]);
   block('junction',[0,0,.05],[.12,.5,.65],[229,218,193]);
   block('n',[.46,0,.05],[.8,.5,.65],[108,165,218]);
   const lift=.25+e*.8;
   for(let i=0;i<18;i++){
    const a=Math.PI+i/18*Math.PI,c=Math.PI+(i+1)/18*Math.PI;
    const p=(x,t)=>[x,lift+.65*Math.cos(t),-.05+.65*Math.sin(t)];
    f.push({id:'glass',color:[192,152,102],p:[p(-1.15,a),p(1.15,a),p(1.15,c),p(-1.15,c)]});
   }
   for(const s of [-1,1])tube(f,[s*.86,0,.05],[s*2.05,0,.05],.065,[177,196,214],'lead',12);
   anchor('p',[-.46,.2,.375]);anchor('junction',[0,.2,.375]);anchor('n',[.46,.2,.375]);anchor('glass',[0,lift+.65,-.05]);anchor('lead',[1.72,0,.05]);
  }
  const shorts={resistor:['Al₂O₃','RuO₂＋玻璃相','保护玻璃','导电金属（Ag示例）','Ni','Sn示例'],capacitor:['BaTiO₃基陶瓷','Ni','Cu','Ni','Sn'],inductor:['铁氧体','Cu','聚合物绝缘漆','导电金属'],diode:['Si＋受主杂质','同一硅中的结区','Si＋施主杂质','密封玻璃','导电金属']};
  return {faces:f,anchors:lesson.layers.map((p,i)=>({id:p.id,point:points[p.id],name:p.name,material:shorts[course][i]}))};
 }
 const api=Object.freeze({build});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingMaterialGeometry=api;
})(typeof window==='undefined'?globalThis:window);
