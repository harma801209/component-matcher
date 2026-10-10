/* Interactive reference section; shares materials with the 3D viewer. */
(function(root){
 'use strict';
 const {lesson}=typeof module!=='undefined'&&module.exports?require('./training_material_data.js'):root.TrainingMaterialData;
 if(typeof module!=='undefined'&&module.exports){module.exports=Object.freeze({lesson});return;}
 const $=id=>document.getElementById(id),escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let course=root.TrainingLesson.current().course,selected=lesson(course).layers[0].id;
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 function region(id,shapes,x,y,leader,label){const info=lesson(course).layers.find(p=>p.id===id),index=lesson(course).layers.indexOf(info)+1;return '<g class="material-region" data-material="'+id+'" role="button" tabindex="0" aria-pressed="false" aria-label="'+escape(info.name+'：'+info.brief)+'">'+shapes+'<path class="leader" d="'+leader+'"/><circle class="number" cx="'+x+'" cy="'+y+'" r="13"/><text class="number-text" x="'+x+'" y="'+(y+5)+'">'+index+'</text><text x="'+(x+19)+'" y="'+(y+5)+'">'+escape(label)+'</text></g>';}
 const rect=(x,y,w,h,color)=>'<rect class="layer-shape" x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" fill="'+color+'"/>';
 function drawing(){
  let shapes='';
  if(course==='resistor'){
   shapes=region('substrate',rect(145,137,295,62,'#e2e7ec'),190,290,'M205 270V185','Al₂O₃基板')+
    region('film',rect(160,125,263,12,'#525866'),220,35,'M235 55V130','RuO₂＋玻璃相')+
    region('cover',rect(160,108,263,17,'#c5dced'),220,78,'M235 94V113','保护玻璃')+
    region('electrode',rect(137,126,12,83,'#bdad8a')+rect(149,125,24,12,'#bdad8a')+rect(423,125,15,12,'#bdad8a')+rect(438,126,12,83,'#bdad8a'),26,65,'M45 73H100L143 145','基础电极')+
    region('nickel',rect(128,126,9,88,'#a8b8cc')+rect(450,126,9,88,'#a8b8cc'),26,253,'M127 249L132 182','Ni镍层')+
    region('finish',rect(119,126,9,93,'#d4dce7')+rect(459,126,9,93,'#d4dce7'),403,253,'M420 235L464 191','可焊外层');
  }else if(course==='capacitor'){
   let plates='';for(let i=0;i<6;i++)plates+=rect(i%2?169:145,117+i*16,260,3,'#8396ad');
   shapes=region('dielectric',rect(145,100,284,122,'#f1dfaf'),204,288,'M219 270V208','BaTiO₃基陶瓷')+
    region('internal',plates,204,38,'M219 55V118','Ni内部电极')+
    region('base',rect(132,96,13,130,'#bb7d49')+rect(429,96,13,130,'#bb7d49'),26,65,'M45 75H95L138 125','Cu端电极')+
    region('barrier',rect(121,96,11,130,'#a4b4c8')+rect(442,96,11,130,'#a4b4c8'),26,262,'M45 249H88L126 193','Ni阻挡层')+
    region('tin',rect(110,96,11,130,'#d7dfe8')+rect(453,96,11,130,'#d7dfe8'),415,262,'M430 244L459 193','Sn外层');
  }else if(course==='inductor'){
   const core='<path class="layer-shape" fill="#a3b2c5" fill-rule="evenodd" d="M143 92H430V224H143Z M169 118V198H404V118Z"/>'+rect(269,112,34,92,'#a3b2c5');
   let copper='',insulation='';for(const x of [209,363])for(let i=0;i<4;i++){const y=130+i*20;insulation+='<circle class="layer-shape" cx="'+x+'" cy="'+y+'" r="9" fill="#e7c867"/>';copper+='<circle class="layer-shape" cx="'+x+'" cy="'+y+'" r="5" fill="#c18044"/>';}
   shapes=region('core',core,215,38,'M231 56V100','铁氧体磁性结构')+
    region('insulation',insulation,397,270,'M413 250L370 169','绝缘漆膜')+
    region('copper',copper,26,151,'M155 151H180L204 150','Cu铜线截面')+
    region('terminal',rect(157,224,48,11,'#cbd5e2')+rect(368,224,48,11,'#cbd5e2'),122,285,'M138 267L180 229','金属端子');
  }else{
   shapes=region('glass','<rect class="layer-shape" x="135" y="105" width="290" height="112" rx="28" fill="#f6e3c8"/><rect x="391" y="107" width="12" height="108" rx="3" fill="#4b5565"/>',217,39,'M233 57H420V110','密封玻璃壳')+
    region('lead',rect(57,153,178,9,'#a7bacf')+rect(338,153,180,9,'#a7bacf'),376,283,'M392 264L460 157','金属引线')+
    region('p',rect(235,137,43,42,'#edc1ac'),24,260,'M191 253L255 171','Si＋受主（例B）')+
    region('junction',rect(278,137,19,42,'#edeae3'),184,78,'M202 88H287V140','PN交界（仍为Si）')+
    region('n',rect(297,137,43,42,'#aacbee'),343,248,'M358 230L320 174','Si＋施主');
  }
  return '<svg viewBox="0 0 600 330" role="group" aria-label="'+escape(lesson(course).name+'内部剖面示意，材料编号可选择')+'"><title>'+escape(lesson(course).name+'典型剖面')+'</title>'+shapes+'</svg>';
 }
 function select(id){const info=lesson(course).layers.find(p=>p.id===id);if(!info)return false;selected=id;document.querySelectorAll('[data-material]').forEach(n=>{const active=n.dataset.material===id;n.setAttribute('aria-pressed',String(active));n.classList.toggle('selected',active);});const detail=$('cross-section-detail');detail.replaceChildren(node('h3',info.name),node('p','成分：'+info.composition),node('p','作用：'+info.role));const more=node('details',undefined,'lesson-more');more.append(node('summary','产品差异与资料'),node('p',info.scope,'material-scope'));const refs=node('p',undefined,'material-scope');refs.append(document.createTextNode('资料依据：'));for(const ref of info.refs){const source=lesson(course).sources[ref],a=node('a',source[0]+' ↗');a.href=source[1];a.target='_blank';a.rel='noopener noreferrer';refs.append(a,document.createTextNode(' '));}more.append(refs);detail.append(more);if(root.TrainingLesson.current().modelMode==='materials'&&root.TrainingLesson.current().part!==id)root.TrainingLesson.selectMaterial(id);return true;}
 function render(){const data=lesson(course);$('cross-section-card').dataset.course=course;$('cross-section-type').textContent=data.name+' · 典型结构';$('cross-section-caption').textContent=data.caption;$('cross-section-limits').textContent='不同产品有什么区别：'+data.scope;$('cross-section-drawing').innerHTML=drawing();$('cross-section-layers').replaceChildren(...data.layers.map((p,i)=>{const b=node('button');b.type='button';b.dataset.material=p.id;b.setAttribute('aria-pressed','false');const text=node('span');text.append(node('strong',p.name),node('small',p.brief));b.append(node('span',i+1,'material-number'),text);return b;}));document.querySelectorAll('[data-material]').forEach(n=>{n.addEventListener('click',()=>select(n.dataset.material));if(n.tagName.toLowerCase()==='g')n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(n.dataset.material);}});});$('cross-section-sources').replaceChildren(...data.sources.map(([label,url])=>{const a=node('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}));selected=data.layers[0].id;select(selected);}

 root.addEventListener('training-course-change',e=>{if(['resistor','capacitor','inductor','diode'].includes(e.detail.course)){course=e.detail.course;render();}});
 render();root.TrainingMaterials=Object.freeze({current:()=>({course,selected}),lesson,select});
})(typeof window==='undefined'?globalThis:window);
