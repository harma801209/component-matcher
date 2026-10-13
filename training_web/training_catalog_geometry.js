/* Shared canvas meshes. Cutaways illustrate typical structures, not vendor CAD. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'&&module.exports?require('./training_catalog.js'):root.TrainingCatalog;
 function build(id,mode,e,{box,tube}){
  const d=C.lesson(id);if(!['exterior','materials'].includes(mode)||!Number.isFinite(e)||e<0||e>1)throw new RangeError('Invalid subtype view');
  const f=[],points={},inside=mode==='materials',b=(id,p,s,c)=>{box(f,p,s,c,id);points[id]??=p.map((v,i)=>i===2?v+s[2]/2:v);},t=(id,p,q,r,c)=>{tube(f,p,q,r,c,id,12);points[id]??=[(p[0]+q[0])/2,(p[1]+q[1])/2,(p[2]+q[2])/2+r];};
  const metal=[174,191,209],ceramic=[216,226,234],plastic=[69,84,101],copper=[195,128,68],silicon=[104,154,195],pink=[212,145,153];
  function terminals(n=2){for(let i=0;i<n;i++){const x=n===2?(i?1.35:-1.35):(i-(n-1)/2)*.65;b('terminal',[x,-.48,.52],[.3,.13,.65],metal);}}
  function shell(id='case',color=plastic){if(inside){b(id,[0,.65+e*1.3,-.15],[2.65,.16,1.5],color);b(id,[0,.04,-.83],[2.65,1.1,.12],color);}else b(id,[0,.08,-.05],[2.65,1.1,1.65],color);}
  const kind=d.kind;
  if(kind==='filmres'){
   if(inside){b('substrate',[0,-.28,-.05],[2.5,.4,1],ceramic);b('element',[0,.0+e*.3,-.05],[2.3,.07,1],[79,87,101]);}
   b('cover',[0,.18+e*.8,-.05],[2.4,inside?.12:.8,1],d.id==='res-sulfur'?[121,166,194]:plastic);terminals();
  }else if(kind==='shunt'){
   b('element',[0,0,0],[2.25,.22,1.1],[165,150,126]);b('cover',[0,.15+e*.8,-.37],[2.2,.12,.3],plastic);terminals();
  }else if(kind==='aluminum'){
   // Front opened can; foil stack is an enlarged unrolled section of a wound core.
   if(inside){b('case',[0,.15,-.65],[1.8,2.4,.14],metal);b('case',[0,1.4+e*.7,0],[1.9,.14,1.4],metal);
    for(let i=0;i<3;i++){const z=-.3+i*.36+e*.1;b('foil',[0,.1,z],[1.25,1.8,.06],metal);b('oxide',[0,.1,z+.05],[1.25,1.8,.04],[131,191,215]);b('paper',[0,.1,z+.13],[1.25,1.8,.09],[236,211,163]);b('cathode',[0,.1,z+.21],[1.25,1.8,.05],[146,162,179]);}
   }else t('case',[0,-.9,0],[0,1.4,0],.95,metal);
   for(const x of [-.42,.42])t('terminal',[x,-1.4,0],[x,-.95,0],.08,metal);
  }else if(kind==='filmcap'){
   shell('case',d.id==='cap-safety'?[193,172,86]:[124,166,184]);terminals();
   if(inside){for(let i=0;i<6;i++){const y=-.33+i*.12+e*(i-2)*.08;b('dielectric',[0,y,0],[1.9,.085,1],[225,207,144]);b('metal',[0,y+.05,0],[1.84,.025,1],metal);}for(const x of [-1.05,1.05])b('end',[x,0,0],[.13,.8,1],copper);}
  }else if(kind==='tantalum'){
   shell('case',[201,174,94]);terminals();
   if(inside){for(let x=0;x<3;x++)for(let y=0;y<2;y++){const p=[(x-1)*.38,-.18+y*.38,0];b('anode',p,[.31,.28,.65],[145,157,177]);b('dielectric',[p[0],p[1]+.17+e*.25,.04],[.34,.045,.67],[153,196,213]);b('cathode',[p[0],p[1]+.23+e*.5,.04],[.34,.07,.67],[86,96,111]);}}
  }else if(kind==='multilayer'){
   if(inside){for(let i=0;i<5;i++){const y=-.4+i*.18+e*(i-2)*.15;b('core',[0,y,-.1],[2.3,.11,1.2],ceramic);const z=i%2?.3:-.35;for(const x of [-.8,.8])t('winding',[x,y+.07,-.4],[x,y+.07,.4],.04,metal);t('winding',[-.8,y+.07,z],[.8,y+.07,z],.04,metal);if(i<4)t('via',[.8,y+.07,z],[.8,y+.25+e*.15,z],.035,copper);}}
   else b('core',[0,0,0],[2.4,1.0,1.3],[124,152,173]);terminals();
  }else if(kind==='molded'||kind==='wound'){
   if(inside){b('core',[0,-.55,0],[2.4,.3,1.45],plastic);b('core',[0,0,-.75],[2.4,1.35,.15],plastic);
    for(let i=0;i<5;i++){const y=-.35+i*.17+e*.3;for(let j=0;j<16;j++){const a=j/16*Math.PI*2,q=(j+1)/16*Math.PI*2,p=[Math.cos(a)*.72,y,Math.sin(a)*.52];t('winding',p,[Math.cos(q)*.72,y+.01,Math.sin(q)*.52],.055,copper);}}
    if(kind==='molded'){b('insulation',[1.1,.15+e*.7,.33],[.18,.4,.32],[207,164,99]);}
   }else b('core',[0,0,0],[2.4,1.3,1.65],plastic);terminals();
   if(kind==='wound')shell();
  }else if(kind==='choke'){
   for(const x of [-.9,.9])b('core',[x,0,-.1],[.4,1.6,1.2],plastic);for(const y of [-.65,.65])b('core',[0,y,-.1],[1.8,.3,1.2],plastic);
   for(const [i,x] of [-.9,.9].entries())for(let n=0;n<6;n++){const y=-.45+n*.17;const c=i?[222,158,74]:copper;for(const [p,q] of [[[x-.28,y,-.8],[x-.28,y,.65]],[[x-.28,y,.65],[x+.28,y,.65]],[[x+.28,y,.65],[x+.28,y,-.8]],[[x+.28,y,-.8],[x-.28,y,-.8]]])t('winding'+(i+1),p,q,.055,c);}
   terminals(4);
  }else if(kind==='crystal'||kind==='oscillator'){
   shell('case',metal);b('base',[0,-.55,0],[2.6,.2,1.5],ceramic);terminals(4);
   if(inside){const x=kind==='oscillator'?-.55:0;b('quartz',[x,0,0],[kind==='oscillator'?1:1.8,.18,.9],[190,218,228]);
    if(kind==='crystal'){for(const y of [-.115,.115])b('electrode',[x,y+e*(y>0?.6:-.2),0],[1.65,.04,.8],metal);}
    else b('ic',[.73,.02+e*.4,0],[.75,.22,.95],[89,128,154]);
   }
  }else if(kind==='mos'){
   shell();terminals(3);
   if(inside){b('body',[0,-.2,0],[2.2,.4,1.1],d.id==='mos-p'?silicon:pink);for(const x of [-.75,.75])b('regions',[x,.02,0],[.55,.15,1.0],d.id==='mos-p'?pink:silicon);b('oxide',[0,.17+e*.25,0],[1.8,.065,1.1],[227,215,167]);b('gate',[0,.28+e*.65,0],[.75,.13,1.0],metal);}
  }else if(kind==='dualmos'||kind==='darlington'){
   shell();if(inside)b('base',[0,-.37,0],[2.4,.15,1.3],copper);terminals(kind==='dualmos'?6:3);
   if(inside)for(const [i,x] of [-.6,.6].entries())b(kind==='dualmos'?'die'+(i+1):'unit'+(i+1),[x,.05+e*i*.3,0],[.9,.3,.95],i?silicon:pink);
  }else if(kind==='schottky'){
   shell();terminals();if(inside){b('semiconductor',[0,-.18,0],[1.9,.5,1.1],silicon);b('metal',[0,.16+e*.5,0],[1.8,.12,1.05],metal);b('contact',[0,-.5-e*.15,0],[1.85,.09,1.05],copper);}
  }else if(kind==='pn'){
   shell();terminals();if(inside){b('p',[-.5,0,0],[.85,.55,1],pink);b('n',[.5,0,0],[.85,.55,1],silicon);b('junction',[0,e*.45,0],[.13,.55,1],[218,211,168]);}
  }else if(kind==='led'){
   shell('case',[149,205,219]);terminals();if(inside){b('substrate',[0,-.25,0],[1.4,.25,1],[192,217,231]);b('active',[0,-.03+e*.3,0],[1.2,.08,.9],[110,132,219]);b('contact',[0,.12+e*.6,0],[1.15,.055,.85],metal);}
  }else if(kind==='bjt'||kind==='digital'){
   shell();terminals(3);if(inside){const pnp=d.id==='bjt-pnp';b('emitter',[-.8,.02,0],[.65,.5,1],pnp?pink:silicon);b('base',[-.35,.02+e*.3,0],[.13,.5,1],pnp?silicon:pink);b('collector',[.4,.02,0],[1.2,.5,1],pnp?pink:silicon);if(kind==='digital')b('bias',[.5,.5+e*.8,0],[1.0,.15,.7],[199,171,124]);}
  }else if(d.baseline){
   // Baseline detailed models remain in the original renderer.
   for(const [i,p] of d.layers.entries())b(p.id,[i*.4,0,0],[.3,.3,.3],ceramic);
  }else throw new RangeError('Unimplemented geometry');
  const parts=d.layers.filter(p=>inside||d.outerIds.includes(p.id));
  return {faces:f,anchors:parts.filter(p=>points[p.id]).map(p=>({id:p.id,name:p.name,material:p.composition,point:points[p.id]}))};
 }
 const api=Object.freeze({build});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingCatalogGeometry=api;
})(typeof globalThis!=='undefined'?globalThis:this);
