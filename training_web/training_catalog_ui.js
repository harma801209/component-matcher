(function(){
 'use strict';
 const C=window.TrainingCatalog,L=window.TrainingCatalogLabs,V=window.TrainingModelVariant,$=id=>document.getElementById(id);
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const selectedByFamily=Object.fromEntries(C.families.map(f=>[f.id,f.default])),values={},answers={};
 let selected=selectedByFamily[V.family()];
 const notes={resistor:'按结构和用途阅读：采样、抗硫化可与厚膜等结构重叠。',capacitor:'安规是应用/认证类别，也可能使用薄膜或陶瓷结构。',inductor:'贴片是安装形式；这里的“贴片叠层”展示叠层结构，绕线与一体成型也可贴片。',crystal:'无源晶体与有源振荡器先区分；TCXO、VCXO是有源功能细分。',mos:'N/P按沟道极性区分，双MOS按器件组合区分。',diode:'按主要用途和结类型阅读，不代表每个型号只具有一种功能。',transistor:'NPN/PNP按极性区分，达林顿和带阻按结构/功能细分。'};
 function picker(){const d=C.lesson(selected);$('subtype-family-note').textContent=notes[d.family];$('subtype-intro').textContent=d.title+'：'+d.summary+'。常见应用：'+d.use+'。';$('subtypes').replaceChildren(...C.children(d.family).map(p=>{const b=node('button',p.title+(answers[p.id]?' · 已答对':''));b.type='button';b.dataset.subtype=p.id;b.setAttribute('aria-pressed',String(p.id===selected));b.addEventListener('click',()=>choose(p.id));return b;}));}
 function diagram(d){
  const box=(x,y,w,label)=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="42" rx="7" class="catalog-device"/><text x="'+(x+w/2)+'" y="'+(y+26)+'" text-anchor="middle">'+label+'</text>';
  const wire=p=>'<path class="catalog-wire" d="'+p+'"/>',arrow=(x,y)=>'<path d="M'+(x-6)+' '+(y-5)+'L'+(x+6)+' '+y+'L'+(x-6)+' '+(y+5)+'Z" fill="#246edf"/>';
  let shapes='',legend='功能连接示意，箭头不代表电子运动或动画速度；不是可生产的PCB布板图。';
  if(d.family==='crystal'){
   if(d.id==='xtal-passive'){shapes=box(25,60,195,'芯片内振荡放大器')+box(320,60,175,'无源晶体')+box(20,165,195,'芯片内部时钟')+wire('M220 80H320M270 80V185H215M495 80H525V135H122V102')+arrow(290,80)+'<text x="365" y="183" text-anchor="middle">晶体在反馈支路</text><text x="280" y="235" text-anchor="middle">时钟由放大器输出端取出；CL/ESR/驱动需匹配</text>';}
   else shapes=box(20,70,120,'VDD/GND供电')+box(180,70,170,d.title)+box(390,70,145,'芯片CLK输入')+wire('M140 90H180M350 90H390')+arrow(160,90)+arrow(370,90)+'<text x="265" y="159" text-anchor="middle">内含维持振荡的电路；OUT不是晶体两端</text>';
   legend+=' 时钟线传递基准信号，不能把图中的箭头当作负载供电电流。';
  }else if(d.lab==='safety'){
   shapes=wire('M35 70H510M35 150H510M440 150V192H275V70')+'<text x="10" y="74">L</text><text x="10" y="154">N</text>'+box(230,98,90,'X类位置')+box(355,98,135,'Y类位置')+'<text x="425" y="200">PE等接地位置</text>';
   // The boxes indicate positions, not electrically connecting X and Y together.
   shapes=wire('M35 60H510M35 175H510M270 60V85M270 130V175M420 60V85M420 130V200')+'<text x="10" y="64">L</text><text x="10" y="179">N</text>'+box(225,85,90,'X类')+box(370,85,100,'Y类')+'<text x="420" y="218" text-anchor="middle">保护接地等位置</text>';
   legend='仅说明X/Y常见位置；认证、设备标准和完整设计都须核对，不作为带电接线指导。';
  }else if(d.family==='capacitor'||['zener','tvs'].includes(d.lab)){
   shapes=box(20,65,115,'电源/输入')+box(205,65,115,['zener','tvs'].includes(d.lab)?'限流/源阻抗':'供电路径')+box(390,65,135,'负载/芯片')+box(235,143,155,d.title)+wire('M135 85H205M320 85H390M355 85V143M355 185V215H77V108M457 108V215')+arrow(175,85)+arrow(369,85);
   legend+=' 器件在并联支路；电容储能、稳压与瞬态钳位不是同一种作用。';
  }else if(d.lab==='common'){
   shapes=box(180,55,180,'第一绕组')+box(180,135,180,'第二绕组')+wire('M25 75H180M360 75H535M25 155H180M360 155H535')+'<text x="270" y="119" text-anchor="middle">共享磁芯，不短接导线</text>';
  }else{
   const switchLike=['mos','transistor'].includes(d.family),high=d.id==='mos-p'||d.id==='bjt-pnp',first=switchLike&&!high?'负载':d.title,last=switchLike&&!high?d.title:'负载';
   shapes=box(20,65,110,'电源')+box(180,65,170,first)+box(390,65,150,last)+wire('M130 85H180M350 85H390M465 108V180H75V108')+arrow(157,85)+arrow(370,85);
   if(switchLike){const x=high?265:465;shapes+=box(180,200,235,d.family==='mos'?'栅驱动：看VGS相对源极':'经偏置网络提供基流')+'<path class="catalog-control" d="M300 200V165H'+x+'V108"/>';legend+=' 虚线是控制关系，不表示MOS栅极持续载流。';}
   if(d.lab==='sense')shapes+='<text x="270" y="143" text-anchor="middle">采样压差 → 测量电路</text>';
  }
  return {html:'<svg viewBox="0 0 560 255" role="img" aria-label="'+d.title+'应用位置示意">'+shapes+'</svg>',legend};
 }
 function application(d){const out=$('subtype-application-body');out.replaceChildren();$('subtype-application-title').textContent=d.title+'：在电路里起什么作用？';const visual=node('div',undefined,'catalog-application-drawing'),picture=diagram(d);visual.innerHTML=picture.html;visual.append(node('small',picture.legend));const story=node('div',undefined,'catalog-application-story');story.append(node('h3','接入后会怎样？'),...d.principle.map(p=>node('p',p)),node('h3','先向客户确认'),...d.ask.map(p=>node('p','• '+p)));out.append(visual,story);}
 function plot(result,d){const out=node('div',undefined,'catalog-wave');if(!['loadcap','clock','ppm','pull','rectify'].includes(d.lab))return out;const series=result.series,lo=Math.min(0,...series.flat()),hi=Math.max(1,...series.flat()),x=i=>35+i/(series[0].length-1)*380,y=v=>125-(v-lo)/(hi-lo)*90;out.innerHTML='<svg viewBox="0 0 450 165" role="img" aria-label="'+d.title+'波形示意"><text x="18" y="20">'+(d.lab==='rectify'?'蓝色输入，橙色所选波形':'时钟状态示意（横轴慢放，不按真实速度）')+'</text><path class="catalog-axis" d="M35 35V130H425"/>'+series.map((points,j)=>'<path fill="none" stroke="'+(j?'#d17814':'#246edf')+'" stroke-width="2" d="'+points.map((v,i)=>(i?'L':'M')+x(i).toFixed(2)+' '+y(v).toFixed(2)).join(' ')+'"/>').join('')+'</svg>';return out;}
 function renderPerformance(){const d=C.lesson(selected),cfg=L.config(d.id),out=$('panel-performance');out.replaceChildren(node('h3','参数体验 · '+d.title),node('p','选一个课堂条件，观察数值或判断如何变化。例题数值不是某个型号的额定保证。','lead'));const label=node('label',cfg.label,'catalog-lab-label'),select=node('select');select.id='catalog-lab-choice';for(const [value,text] of cfg.options){const option=node('option',text);option.value=String(value);select.append(option);}values[d.id]??=cfg.initial;select.value=String(values[d.id]);label.htmlFor=select.id;label.append(select);const area=node('div');area.id='catalog-lab-results';out.append(label,area);function update(){const r=L.evaluate(d.id,values[d.id]),metrics=node('div',undefined,'metrics');metrics.append(...r.metrics.map(([k,v])=>{const m=node('div',undefined,'metric');m.append(node('small',k),node('strong',v));return m;}));const status=node('p',r.status,'status'+(r.warn?' warn':''));status.setAttribute('role','status');area.replaceChildren(metrics,status,plot(r,d));}select.addEventListener('change',()=>{values[d.id]=cfg.options.find(o=>String(o[0])===select.value)[0];update();});update();}
 function renderQuiz(){const d=C.lesson(selected),q=d.quiz,out=$('panel-quiz');out.replaceChildren(node('h3','一分钟检查 · '+d.title),node('p',q.question,'lead'));const feedback=node('div');feedback.id='catalog-quiz-feedback';feedback.setAttribute('aria-live','polite');for(const [i,text] of q.options.entries()){const b=node('button',String.fromCharCode(65+i)+' · '+text,'quiz-option');b.type='button';b.dataset.catalogAnswer=String(i);b.addEventListener('click',()=>{const correct=i===q.answer;answers[d.id]=correct;out.querySelectorAll('button').forEach(btn=>btn.classList.remove('correct','incorrect'));b.classList.add(correct?'correct':'incorrect');feedback.className='quiz-feedback';feedback.textContent=(correct?'回答正确。':'再想一想。')+q.explain;picker();});out.append(b);}out.append(feedback,node('p',answers[d.id]?'本次已答对，可再次复习。':'答题进度只保留本次页面。','storage-note'));}
 function knowledge(d){const spec=$('panel-spec');spec.replaceChildren(node('h3','先看'+d.title+'的关键规格'),node('p',d.summary,'lead'));const table=node('table',undefined,'spec-table'),body=node('tbody');for(const [k,v] of d.specs){const tr=node('tr'),th=node('th',k),td=node('td',v);th.scope='row';tr.append(th,td);body.append(tr);}table.append(body);spec.append(table);const principle=$('panel-principle');principle.replaceChildren(node('h3','从结构到电路作用'),...d.principle.map(p=>node('p',p,'catalog-principle-line')),node('h3','选型前向客户确认'),...d.ask.map(p=>node('p',p,'catalog-principle-line')));renderPerformance();renderQuiz();$('takeaways').replaceChildren(...d.ask.map(p=>node('p',p)));$('example').textContent=d.scope;$('sources').replaceChildren(...d.sources.map(([title,url])=>{const a=node('a',title+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}));}
 function choose(id){const d=C.lesson(id);if(d.family!==V.family())V.selectFamily(d.family);selected=id;selectedByFamily[d.family]=id;$('training-app').dataset.family=d.family;$('training-app').dataset.subtype=id;picker();const foundation=d.baseline;$('subtype-application').hidden=foundation;$('circuit-card').hidden=!foundation;$('games-card').hidden=false;document.querySelector('.practice-card').hidden=!foundation;document.querySelector('.takeaways').hidden=!foundation;
  if(foundation){V.use(null);}else{V.use(id);application(d);knowledge(d);window.TrainingCircuit?.selectStep(0);}window.dispatchEvent(new CustomEvent('training-subtype-change',{detail:{id}}));
 }
 window.addEventListener('training-family-change',e=>{choose(selectedByFamily[e.detail.family]);});
 window.TrainingCatalogUI=Object.freeze({current:()=>C.lesson(selected),choose,renderQuiz});
 choose(selected);
})();
