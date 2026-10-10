/* Original educational sections, not copied manufacturer drawings or part recipes. */
(function(root){
 'use strict';
 const lessons={
  resistor:{name:'厚膜贴片电阻',scope:'典型厚膜结构，不代表薄膜或金属合金电阻。层厚、修调槽与材料配比依型号变化。',caption:'沿器件长度方向剖开。膜层与镀层已放大；图中端部按基础电极→镍层→外镀层分开表示，不按实物厚度比例。',
   layers:[
    {id:'substrate',name:'陶瓷基板',brief:'氧化铝 Al₂O₃',composition:'常见为氧化铝（Al₂O₃）陶瓷。',role:'绝缘、支撑电阻膜，并帮助把热量传出。',scope:'陶瓷等级、纯度与添加物需查具体系列。',refs:[0]},
    {id:'film',name:'厚膜电阻膜',brief:'典型：RuO₂＋玻璃相',composition:'钌系陶瓷金属复合材料；RuO₂（二氧化钌）导电相与玻璃相是公开工艺示例。',role:'承担电阻作用；膜的材料、几何尺寸与修调共同决定阻值。',scope:'不是所有厚膜料号的固定配方，不给出未经披露的混合比例。',refs:[0,1]},
    {id:'cover',name:'保护层',brief:'玻璃保护层（示例）',composition:'此示例为烧结玻璃保护层。',role:'保护电阻膜，减少环境及加工影响。',scope:'也有不同树脂/复合保护工艺；不把厂家玻璃配方视为统一成分。',refs:[0]},
    {id:'electrode',name:'基础端电极',brief:'导电金属；Ag为工艺示例',composition:'连接膜层的导电金属；银（Ag）基电极见公开厚膜工艺。',role:'把电阻膜两端接到外部端子。',scope:'金属体系按系列确认，不能据此认定每颗电阻都使用银或银钯。',refs:[1]},
    {id:'nickel',name:'阻挡镀层',brief:'镍 Ni',composition:'镍（Ni）阻挡层。',role:'位于基础电极与可焊外层之间。',scope:'镀层厚度与结构依封装/系列；本图为典型层序。',refs:[0]},
    {id:'finish',name:'可焊外层',brief:'可焊镀层；无铅Sn示例',composition:'外部可焊金属镀层；锡（Sn）为无铅外层示例。',role:'用于与PCB焊盘焊接。',scope:'锡、含铅或其他端接版本必须按原厂订货规格确认。',refs:[2]}
   ],sources:[['Vishay · M系列材料与剖面结构','https://www.vishay.com/docs/60031/m.pdf'],['公开厚膜材料工艺 · EP2286420B1','https://patents.google.com/patent/EP2286420B1/en'],['Vishay · D/CRCW e3镍层与锡端接','https://www.vishay.com/docs/20035/dcrcwe3.pdf']]},
  capacitor:{name:'高介电常数MLCC',scope:'这里展示BaTiO₃基、镍内部电极的MLCC示例。不能把C0G或所有陶瓷电容都当作相同配方。',caption:'陶瓷层夹在相邻电极之间。内部电极交替接左、右端，未接端留有间隙；没有把两端短接。外层镀层厚度为观察放大。',
   layers:[
    {id:'dielectric',name:'陶瓷介质',brief:'钛酸钡 BaTiO₃基',composition:'高介电常数MLCC常见为钛酸钡（BaTiO₃）基陶瓷，含按性能设计的添加物。',role:'隔开电极，并在电场中储能。',scope:'X7R/X5R是温度特性分类，不是配方名称；C0G不得照用本例材料。',refs:[0]},
    {id:'internal',name:'内部电极',brief:'镍 Ni（本例）',composition:'本例使用镍（Ni）金属电极。',role:'交替连接两个端子，多层叠加有效电极面积。',scope:'镍属基底金属电极示例；其他电极工艺依产品确认。',refs:[0,1]},
    {id:'base',name:'端电极基础层',brief:'铜 Cu（本例）',composition:'铜（Cu）基础电极层。',role:'收集连接同一端的内部电极。',scope:'本例采用村田公开结构资料的材料层序，不替代其他系列材料声明。',refs:[1]},
    {id:'barrier',name:'端部阻挡层',brief:'镍 Ni',composition:'镍（Ni）镀层，位于铜基础层与锡层之间。',role:'形成端接阻挡层。',scope:'层厚及柔性端接等结构不由本图确定。',refs:[1]},
    {id:'tin',name:'端部可焊层',brief:'锡 Sn',composition:'锡（Sn）外镀层。',role:'提供外部可焊连接表面。',scope:'仅为此结构示例；具体端接版本以料号资料为准。',refs:[1]}
   ],sources:[['Murata · 钛酸钡介质与镍电极','https://article.murata.com/en-global/article/mlcc-for-5g-smartphone-2'],['Murata · MLCC剖面与材料表','https://search.murata.co.jp/Ceramy/image/img/A01X/1R0009A.pdf']]},
  inductor:{name:'绕线铁氧体电感',scope:'此图为绕线铁氧体结构，不代表空气芯、叠层电感或金属粉芯一体成型结构。屏蔽/封装形式也随系列变化。',caption:'穿过绕组的剖面。橙色圆面是铜线被切开的截面，外圈是绝缘膜，不是互不相连的独立小零件。',
   layers:[
    {id:'core',name:'磁芯 / 磁性屏蔽体',brief:'铁氧体：复合金属氧化物',composition:'铁氧体以铁氧化物为主要组成，结合锰、锌或镍等金属氧化物；MnZn、NiZn为材料类别示例。',role:'引导磁通；磁性屏蔽体有助于减少外泄磁场。',scope:'不是纯铁块；配比、气隙、损耗与饱和性能需查具体磁材/系列。',refs:[0,1]},
    {id:'copper',name:'绕组导体',brief:'铜 Cu（本例）',composition:'本例为铜（Cu）绕线。',role:'电流通过绕组建立磁场；导体电阻产生铜损。',scope:'线径、匝数与绕法不按图推算；特殊产品也可能用其他导体。',refs:[2]},
    {id:'insulation',name:'绕线绝缘膜',brief:'聚合物绝缘漆（示例）',composition:'漆包线绝缘膜可采用聚氨酯、聚酯亚胺等聚合物体系。',role:'隔离相邻匝与导体，防止匝间短路。',scope:'这些是漆包线材料例子，不宣称当前某个电感使用指定漆种或耐热等级。',refs:[2]},
    {id:'terminal',name:'外部端子',brief:'导电金属 / 可焊表面',composition:'金属连接端与可焊表面；此通用示例不指定未披露的合金、镀层配方。',role:'连接绕组与PCB焊盘。',scope:'具体金属、镀层及焊接结构应查原厂材料声明。',refs:[1]}
   ],sources:[['TDK · 铁氧体组成与磁性陶瓷','https://www.tdk.com/en/tech-mag/ferrite02/001'],['Coilcraft · 绕组损耗与屏蔽结构说明','https://cps.coilcraft.com/en-us/faq/'],['Elektrisola · 漆包线导体及绝缘材料','https://update.elektrisola.com/ja/Enamelled-Wire/Info']]},
  diode:{name:'硅PN结与玻璃封装',scope:'这是硅PN结和轴向玻璃封装的组合教学示意，不是某颗1N4148的真实工艺剖面；肖特基、LED、SiC等不能直接套用。',caption:'PN区属于同一硅芯片的不同掺杂区。这里横向展开便于认识，并不表示实际芯片的扩散形状、耗尽区尺寸或封装键合方式。',
   layers:[
    {id:'p',name:'P型区',brief:'硅 Si＋受主掺杂',composition:'硅（Si）中加入受主杂质；硼（B）是常见示例。',role:'形成以空穴为多数载流子的区域。',scope:'这是一般硅掺杂例子，不表示1N4148公开了本图所示掺杂配方或浓度。',refs:[0]},
    {id:'junction',name:'PN结 / 耗尽区',brief:'仍为硅，不是另加一层材料',composition:'仍在硅晶体中，是PN交界附近的电荷分布区域，不是夹入的金属或绝缘薄片。',role:'形成内建电场，随偏置条件改变。',scope:'宽度为定性示意；实际结形状和工艺需查具体设计。',refs:[2]},
    {id:'n',name:'N型区',brief:'硅 Si＋施主掺杂',composition:'硅（Si）中加入施主杂质；磷（P）、砷（As）是常见示例。',role:'形成以电子为多数载流子的区域。',scope:'不是把纯磷或纯砷拼在硅旁边；浓度与实际工艺不由本图确定。',refs:[0]},
    {id:'glass',name:'玻璃封装',brief:'密封玻璃；配方依封装',composition:'轴向玻璃封装；本例所引用的封装资料没有提供统一玻璃配方。',role:'保护芯片，黑色环标示阴极侧。',scope:'不能从玻璃外观推断半导体类型、材料比例或真实额定值。',refs:[1]},
    {id:'lead',name:'金属引线 / 连接',brief:'导电金属（具体合金待核对）',composition:'导电金属连接；具体合金与表面镀层应查原厂材料声明。',role:'把阳极、阴极引到外部电路。',scope:'连接线为示意，不冒充该料号真实芯片键合/支撑结构。',refs:[1]}
   ],sources:[['BYU洁净室 · 硅晶圆P/N掺杂说明','https://www.cleanroom.byu.edu/EW_wafer_specs'],['Nexperia · 1N4148玻璃封装与平面工艺','https://www.nexperia.com/product/1N4148'],['Toshiba · PN结形成与耗尽区','https://toshiba.semicon-storage.com/us/semiconductor/knowledge/e-learning/discrete/chap1/chap1-6.html']]}
 };
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 freeze(lessons);
 function lesson(course){if(!Object.hasOwn(lessons,course))throw new RangeError('Unknown material lesson');return lessons[course];}
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
 function select(id){const info=lesson(course).layers.find(p=>p.id===id);if(!info)return false;selected=id;document.querySelectorAll('[data-material]').forEach(n=>{const active=n.dataset.material===id;n.setAttribute('aria-pressed',String(active));n.classList.toggle('selected',active);});const detail=$('cross-section-detail');detail.replaceChildren(node('h3',info.name),node('p','成分：'+info.composition),node('p','作用：'+info.role),node('p','适用范围：'+info.scope,'material-scope'));const refs=node('p',undefined,'material-scope');refs.append(document.createTextNode('资料依据：'));for(const ref of info.refs){const source=lesson(course).sources[ref],a=node('a',source[0]+' ↗');a.href=source[1];a.target='_blank';a.rel='noopener noreferrer';refs.append(a,document.createTextNode(' '));}detail.append(refs);return true;}
 function render(){const data=lesson(course);$('cross-section-card').dataset.course=course;$('cross-section-type').textContent=data.name+' · 典型结构';$('cross-section-caption').textContent=data.caption;$('cross-section-limits').textContent='适用边界：'+data.scope;$('cross-section-drawing').innerHTML=drawing();$('cross-section-layers').replaceChildren(...data.layers.map((p,i)=>{const b=node('button');b.type='button';b.dataset.material=p.id;b.setAttribute('aria-pressed','false');const text=node('span');text.append(node('strong',p.name),node('small',p.brief));b.append(node('span',i+1,'material-number'),text);return b;}));document.querySelectorAll('[data-material]').forEach(n=>{n.addEventListener('click',()=>select(n.dataset.material));if(n.tagName.toLowerCase()==='g')n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(n.dataset.material);}});});$('cross-section-sources').replaceChildren(...data.sources.map(([label,url])=>{const a=node('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}));selected=data.layers[0].id;select(selected);}
 $('show-cross-section').addEventListener('click',()=>{$('cross-section-card').scrollIntoView({block:'start',behavior:'auto'});$('cross-section-title').focus({preventScroll:true});});
 root.addEventListener('training-course-change',e=>{if(Object.hasOwn(lessons,e.detail.course)){course=e.detail.course;render();}});
 render();root.TrainingMaterials=Object.freeze({current:()=>({course,selected}),lesson,select});
})(typeof window==='undefined'?globalThis:window);
