/* Independent repair-shop entrance. Existing component lessons remain intact. */
(function(){
 'use strict';
 const D=window.RepairShopData,E=window.RepairShopEngine,V=window.RepairShopEvidence,C=window.RepairShopCoach,P=window.RepairShopPhysics,app=document.getElementById('training-app');
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const button=(text,fn,cls='',focusName='')=>{const b=el('button',text,cls);b.type='button';if(focusName)b.dataset.repairFocus=focusName;b.addEventListener('click',fn);return b;};
 const svg=(tag,attrs={})=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));return n;};
 function art(type,cls='rs-product-art'){
  const n=svg('svg',{viewBox:'0 0 200 140',class:cls,'aria-hidden':'true'});
  // Only authored, constant SVG markup is used; saved/user text never enters markup.
  const drawings={
   lamp:'<ellipse cx="100" cy="128" rx="63" ry="8" fill="#213d3920"/><path d="M89 111L111 58L80 26" fill="none" stroke="#344f50" stroke-width="9" stroke-linecap="round"/><path d="M69 13Q77 7 89 19L115 45L64 69L50 38Z" fill="#e3a849" stroke="#906f35" stroke-width="3"/><ellipse cx="83" cy="55" rx="29" ry="9" transform="rotate(-25 83 55)" fill="#ffe7a0"/><path d="M53 119Q52 105 70 105H125Q143 105 145 119Z" fill="#426c68"/><rect x="81" y="109" width="27" height="5" rx="2" fill="#84ada0"/>',
   fan:'<ellipse cx="100" cy="128" rx="61" ry="7" fill="#213d3920"/><path d="M87 77H110L117 113H76Z" fill="#708e86"/><rect x="59" y="112" width="79" height="12" rx="6" fill="#345956"/><circle cx="99" cy="53" r="44" fill="#cbd6bc" stroke="#385b58" stroke-width="6"/><path d="M99 52C52 18 65 66 96 59C72 104 128 98 106 57C158 54 125 15 103 47" fill="#729b8a"/><circle cx="100" cy="53" r="8" fill="#d5af61"/><circle cx="99" cy="53" r="35" fill="none" stroke="#385b5866" stroke-width="2"/><path d="M99 9V97M55 53H143M68 22L130 84M68 84L130 22" stroke="#385b5850" stroke-width="2"/>',
   speaker:'<ellipse cx="100" cy="128" rx="70" ry="7" fill="#213d3920"/><rect x="29" y="31" width="141" height="89" rx="14" fill="#3b5358" stroke="#263e43" stroke-width="3"/><rect x="38" y="42" width="123" height="65" rx="10" fill="#79938e"/><circle cx="71" cy="74" r="25" fill="#34494b"/><circle cx="127" cy="74" r="25" fill="#34494b"/><circle cx="71" cy="74" r="15" fill="#526b67"/><circle cx="127" cy="74" r="15" fill="#526b67"/><path d="M55 29Q51 8 75 8H127Q146 8 143 29" fill="none" stroke="#566b64" stroke-width="6"/><circle cx="98" cy="38" r="2" fill="#eac77d"/>',
   clock:'<ellipse cx="100" cy="127" rx="68" ry="7" fill="#213d3920"/><path d="M48 26H153L174 115H24Z" fill="#b07c58" stroke="#7e5b46" stroke-width="3"/><rect x="43" y="45" width="110" height="49" rx="5" fill="#d8dfb9"/><text x="98" y="78" font-size="29" text-anchor="middle" fill="#3e6354" font-family="monospace">08:24</text><rect x="68" y="20" width="61" height="8" rx="4" fill="#634f43"/><circle cx="147" cy="105" r="3" fill="#e7c88b"/>',
   sensor:'<ellipse cx="100" cy="126" rx="57" ry="7" fill="#213d3920"/><rect x="55" y="13" width="92" height="108" rx="17" fill="#e0e2ce" stroke="#6f8d7b" stroke-width="3"/><rect x="68" y="29" width="66" height="47" rx="5" fill="#9dbda5"/><text x="101" y="59" font-size="24" text-anchor="middle" fill="#36574a" font-family="monospace">24°</text><path d="M75 88H126M75 96H126M75 104H126" stroke="#819a87" stroke-width="3"/><circle cx="100" cy="115" r="2" fill="#59a37e"/>',
   router:'<ellipse cx="100" cy="128" rx="75" ry="7" fill="#213d3920"/><path d="M47 90L27 12M149 91L170 12" stroke="#526966" stroke-width="8" stroke-linecap="round"/><path d="M34 75H159L177 112Q177 120 167 120H31Q22 120 23 111Z" fill="#d7dac7" stroke="#6d867b" stroke-width="3"/><path d="M36 99H161" stroke="#a6b6a2" stroke-width="2"/><circle cx="50" cy="110" r="3" fill="#60a680"/><circle cx="64" cy="110" r="3" fill="#60a680"/><circle cx="78" cy="110" r="3" fill="#e0b365"/>'
  };
  n.innerHTML=drawings[type]||drawings.lamp;return n;
 }
 function scene(){
  const n=svg('svg',{viewBox:'0 0 560 320',class:'rs-scene','aria-label':'电子维修工作台插画',role:'img'});
  n.innerHTML='<rect width="560" height="320" fill="#e3e6d5"/><path d="M0 70H560M0 140H560" stroke="#c8d0bb"/><rect x="38" y="26" width="200" height="146" rx="8" fill="#c6d0bb"/><path d="M57 48H216M57 77H216M57 106H216M57 135H216" stroke="#a0b6a0" stroke-dasharray="3 14" stroke-width="3"/><path d="M71 57V129M94 85V145M118 48V94" stroke="#596e5c" stroke-width="6" stroke-linecap="round"/><rect x="154" y="58" width="42" height="65" rx="6" fill="#cf9b4e"/><rect x="161" y="66" width="28" height="18" rx="2" fill="#dfe6bd"/><circle cx="175" cy="104" r="10" fill="#566656"/><rect x="288" y="44" width="222" height="81" rx="4" fill="#f6f2de"/><text x="399" y="77" text-anchor="middle" fill="#3f6153" font-size="18" font-weight="700">旧物有新生</text><text x="399" y="101" text-anchor="middle" fill="#8c937c" font-size="10" letter-spacing="4">REPAIR · LEARN · REPEAT</text><rect x="25" y="215" width="511" height="30" rx="5" fill="#bc8b57"/><path d="M44 245V320M517 245V320" stroke="#8f714d" stroke-width="17"/><path d="M70 215L135 176H361L428 215Z" fill="#70a690"/><path d="M148 186H305L348 207H112Z" fill="#285b4c"/><path d="M161 190H287V201H131" fill="none" stroke="#90b69a" stroke-width="2"/><rect x="198" y="183" width="29" height="15" rx="2" fill="#283d3e"/><rect x="263" y="191" width="19" height="9" fill="#cdad68"/><path d="M420 211L461 155L434 102" fill="none" stroke="#405a50" stroke-width="7"/><path d="M414 87L454 110L422 133L393 111Z" fill="#d9ad5c"/><rect x="414" y="210" width="80" height="5" rx="2" fill="#405a50"/><rect x="42" y="171" width="46" height="44" rx="3" fill="#e9e5d1"/><path d="M80 178Q104 178 93 199H83" fill="none" stroke="#e9e5d1" stroke-width="6"/><path d="M57 160Q49 152 57 143M70 159Q62 152 71 141" fill="none" stroke="#a9b7a1" stroke-width="2"/><rect x="142" y="260" width="278" height="42" rx="4" fill="#9c7954"/><circle cx="282" cy="280" r="4" fill="#e4bb76"/>';
  return n;
 }
 const lessons=el('div');lessons.id='academy-lessons';while(app.firstChild)lessons.append(app.firstChild);app.append(lessons);
 const nav=el('nav',undefined,'academy-switch');nav.setAttribute('aria-label','培训模式');
 const shop=el('section');shop.id='repair-shop';shop.setAttribute('aria-label','电子维修店综合训练游戏');shop.hidden=true;
 const courseButton=button('器件课堂',()=>view(false)),shopButton=button('电子维修店',()=>view(true));nav.append(courseButton,shopButton);app.prepend(nav);app.append(shop);
 const entry=el('section',undefined,'repair-entry');entry.append(art('lamp','repair-entry-art'));const entryCopy=el('div');entryCopy.append(el('strong','开一家自己的电子维修店'),el('p','接待客人、测量找故障、选件维修，让学到的器件知识真正派上用场。'));entry.append(entryCopy,button('开门营业 →',()=>view(true)));lessons.prepend(entry);
 let state=E.create(),lastSaved=null,storageOK=true,store,selected=null,mode='voltage',diagnosis='',reason='',stock='',orientation='',meter=null,notice='',screen='work',confirmAbandon=false,seeds=[],memoryRevision=0,coachEnabled=true,hintsOpen=false,detailOpen=false;
 const COACH_KEY='fruition.repair-shop.coach.v1';
 const M=window.RepairShopMechanics,B=window.RepairShopBoard;let mechanicalTool='',inspection=false,selectedNet='';
 function pickMechanical(id){if(id==='@driver'){mechanicalTool='phillips';render();return;}const n=M.next(state.active.mechanics,state.active.tested);if(id.startsWith('@screw:')){if(['unscrew','tighten'].includes(n.op))dispatch({type:'mechanical',op:n.op,id:id.slice(7),tool:mechanicalTool});else{notice='这颗螺丝已妥善收好。先完成：'+n.title+'。';render();}return;}const kind={'@cover':'cover','@brace':'brace','@connector':'plug','@board':'board'}[id];if(kind&&n.op.includes(kind))dispatch({type:'mechanical',op:n.op,tool:mechanicalTool});else{notice='先完成：'+n.title+'。';render();}}
 let boardView=null,boardElement=null,boardKey='',boardFallback=false,boardError='';
 function disposeBoard(){boardView?.dispose();boardView=null;boardElement=null;boardKey='';}
 function freshSeeds(){const a=new Uint32Array(1);if(window.crypto?.getRandomValues)crypto.getRandomValues(a);else a[0]=(Date.now()+Math.random()*4294967295)>>>0;seeds=E.nextSeeds(a[0]);}
 function read(){try{const raw=store.getItem(E.KEY);lastSaved=raw;if(raw&&raw.length<350000)state=E.restore(JSON.parse(raw));}catch(_){storageOK=false;}}
 try{store=window.localStorage;read();}catch(_){storageOK=false;}
 coachEnabled=state.completed===0;try{const preference=store.getItem(COACH_KEY);if(preference==='on'||preference==='off')coachEnabled=preference==='on';}catch(_){}
 hintsOpen=Boolean(state.active?.hinted);
 freshSeeds();
 function save(){try{const raw=JSON.stringify(state);store.setItem(E.KEY,raw);lastSaved=raw;storageOK=true;}catch(_){storageOK=false;}}
 function clearChoices(){selected=null;diagnosis='';reason='';stock='';orientation='';meter=null;confirmAbandon=false;hintsOpen=false;detailOpen=false;mechanicalTool='';selectedNet='';inspection=false;}
 function teaching(value){coachEnabled=value;try{store.setItem(COACH_KEY,value?'on':'off');}catch(_){}render();}
 function dispatch(event){
  try{const latest=store.getItem(E.KEY);if(latest!==lastSaved){read();clearChoices();notice='另一窗口更新了维修存档，已载入最新进度。请重新确认本次操作。';render();return;}}catch(_){storageOK=false;}
  const result=E.apply(state,event);state=result.state;notice=result.message;
  if(event.type==='measure'&&result.ok)meter=state.active.measurements.find(m=>m.key===event.mode+':'+event.id+':'+Boolean(state.active.installed));
  if(['accept','abandon'].includes(event.type)&&result.ok){clearChoices();screen='work';if(event.type==='abandon')freshSeeds();}
  if(event.type==='deliver'&&result.ok)freshSeeds();
  if(event.type==='hint'&&result.ok)hintsOpen=true;
  if(state.revision!==memoryRevision){memoryRevision=state.revision;save();}
  render();
 }
 function view(isShop){lessons.hidden=isShop;shop.hidden=!isShop;courseButton.setAttribute('aria-pressed',String(!isShop));shopButton.setAttribute('aria-pressed',String(isShop));if(isShop)render();nav.scrollIntoView({block:'start'});}
 function heading(title,subtitle){const h=el('div',undefined,'rs-section-heading');h.append(el('h3',title));if(subtitle)h.append(el('small',subtitle));return h;}
 function select(labelText,values,current,onchange,id){const field=el('div'),label=el('label',labelText),control=el('select');control.id=id;label.htmlFor=id;const empty=el('option','请选择');empty.value='';control.append(empty);for(const [value,text] of values){const option=el('option',text);option.value=value;control.append(option);}control.value=current;control.addEventListener('change',()=>{onchange(control.value);refreshCoach();});field.append(label,control);return field;}
 function coachStep(){const a=state.active,j=E.offer(a.seed),required=j.product.parts.find(p=>p.id===j.fault.component),chosen=j.candidates.find(p=>p.stockId===stock);return C.step(j,a,{selected,mode,diagnosis,reason,stock,orientation,tool:mechanicalTool,partError:chosen?E.compatible(required,chosen):''});}
 function guideTarget(g){return g.target.startsWith('id:')?document.getElementById(g.target.slice(3)):[...shop.querySelectorAll('[data-repair-focus]')].find(n=>n.dataset.repairFocus===g.target);}
 function locate(){const target=guideTarget(coachStep());if(target&&!target.disabled){target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});}}
 function coachPanel(mini=false){
  const g=coachStep(),panel=el('section',undefined,mini?'rs-coach-mini':'rs-coach');panel.id=mini?'repair-coach-mini':'repair-coach';panel.dataset.step=g.id;panel.dataset.target=g.target;
  if(!mini){const tag=el('div',undefined,'rs-coach-caption');tag.append(el('span','师傅带你修 · '+g.group),el('small','操作教学不扣积分'));panel.append(tag);}
  const title=el(mini?'strong':'h3',g.title);if(!mini)title.id='repair-coach-next';panel.append(title,el('p',g.body));const go=button(mini?'去操作':'带我找到这一步',locate,'rs-primary');go.dataset.repairFocus=mini?'coach-mini-go':'coach-go';panel.append(go);return panel;
 }
 function markCoach(){
  for(const n of shop.querySelectorAll('.rs-coach-target')){n.classList.remove('rs-coach-target');if(n.getAttribute('aria-describedby')==='repair-coach-next')n.removeAttribute('aria-describedby');}
  if(!coachEnabled||!state.active||screen!=='work')return;const target=guideTarget(coachStep());if(target){target.classList.add('rs-coach-target');target.setAttribute('aria-describedby','repair-coach-next');}
 }
 function refreshCoach(){if(!coachEnabled||!state.active||screen!=='work')return;const panel=shop.querySelector('#repair-coach'),mini=shop.querySelector('#repair-coach-mini');if(panel)panel.replaceWith(coachPanel());if(mini)mini.replaceWith(coachPanel(true));markCoach();}
 function hintPanel(job){
  const panel=el('section',undefined,'rs-case-hints');panel.id='repair-case-hints';panel.append(el('h3','师傅提示 · 当前工单的维修思路'),el('p','先看排查方向；如果仍然不明白，可以展开详细定位。查看提示不扣积分，也不会自动选择答案或替你维修。'));
  const grid=el('div',undefined,'rs-hint-grid');for(const item of C.overview(job,state.active)){const row=el('article');row.append(el('h4',item.title),el('p',item.text));grid.append(row);}panel.append(grid);
  const detail=el('details',undefined,'rs-hint-detail');detail.open=detailOpen;detail.append(el('summary','看本单的具体定位与维修（会透露关键线索）'));detail.addEventListener('toggle',()=>{detailOpen=detail.open;});for(const item of C.detail(job,state.active)){const row=el('article');row.append(el('h4',item.title),el('p',item.text));detail.append(row);}panel.append(detail);
  panel.append(button('回到维修操作',()=>{hintsOpen=false;render();if(coachEnabled)locate();else{const target=shop.querySelector('.rs-probe-picker button');target?.scrollIntoView({block:'center'});target?.focus({preventScroll:true});}},'rs-hint-return'));return panel;
 }
 function help(){const details=el('details',undefined,'rs-help');details.append(el('summary','玩法与测量说明'));details.append(el('p','① 断电放电、拆螺丝，取下上盖和支架，断开J1再取板；② 依据症状与手册，在台架测量、断电隔离检测；③ 根据证据诊断并按规格换件；④ 板级测试通过后断电放电，装回并接线、上盖、拧紧螺丝；⑤ 成品复测后交付。'));details.append(el('p','这是低压等效电路教学模拟。读数由本关电路与参数计算，走线依据本关等效电路绘制，不是原厂布板；元件检测自动模拟隔离，MOS等使用声明条件的专用夹具。未模拟项目不作确定结论，晶振停振关暂时停用。请勿按游戏操作维修真实市电、高压或电池设备。'));for(const [text,url] of [['Fluke · 电阻测量','https://www.fluke.com/en-ie/learn/blog/digital-multimeters/how-to-measure-resistance'],['Fluke · 电容测量','https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-measure-capacitance'],['Murata · 电容选型','https://www.murata.com/products/capacitor/selectionguide']]){const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';details.append(a);}return details;}
 function evidenceChecklist(a){
  const panel=el('section',undefined,'rs-evidence-checklist');panel.setAttribute('aria-label','诊断证据进度');
  for(const item of V.checklist(a,selected)){const row=el('div',undefined,item.done?'done':'waiting');row.append(el('b',item.done?'✓':'○'),el('strong',item.label),el('small',item.text));panel.append(row);}return panel;
 }
 function verificationPanel(job){
  const report=V.report(job,state.active);if(!report)return null;
  const panel=el('section',undefined,'rs-verification');panel.id='repair-verification';panel.setAttribute('aria-label','维修前后对照');
  const title=el('div',undefined,'rs-verification-title');title.append(el('h3','维修前后对照'),el('span','✓ 已建模项目验收通过'));panel.append(title,el('p','验收计算值由等效电路、实际所选备件和规定负载重新计算，不是点击后预设通过。未记录的维修前读数不补写；未建模项目不算已验证。'));
  const list=el('ol');for(const row of report.rows){const item=el('li',undefined,'rs-verification-row');item.dataset.kind=row.kind;item.append(el('strong',row.label));for(const [label,value] of [['维修前记录',row.before],['验收计算值',row.after]]){const field=el('div');field.append(el('small',label),el('p',value??'未记录',value===null?'rs-reading-unknown':''));item.append(field);}item.append(el('span',row.pass?'✓ 通过':'未通过','rs-pass'));list.append(item);}panel.append(list);
  const limits=el('ul',undefined,'rs-acceptance-limits');for(const check of report.checks)limits.append(el('li',(check.pass?'✓ ':'× ')+check.label+'：'+check.actual));panel.append(limits,el('p','验证范围：'+job.product.model.limits));
  const used=el('p','更换 '+report.component+'：'+report.partSpec,'rs-installed-spec');panel.append(used);
  const money=el('div',undefined,'rs-job-economy');for(const [label,value] of [['备件成本',report.cost],['工单报酬',report.fee],['本单净收益',report.net]]){const item=el('div');item.append(el('small',label),el('strong',value+' 金币'));money.append(item);}panel.append(money,el('small',state.active.delivered?'本单已结算，不会重复发放。':'净收益为预计值，点击交付后才领取报酬；此面板不会发放金币。'));return panel;
 }
 function render(){
  const focus=document.activeElement?.dataset.repairFocus;
  if(!state.active||!E.offer(state.active.seed).fault.enabled)disposeBoard();
  shop.replaceChildren();shop.dataset.theme=state.theme;
  const header=el('header',undefined,'rs-header'),brand=el('div',undefined,'rs-brand'),name=el('div');name.append(el('strong',state.owned.includes('sign')?'妙手修复 · 电子维修店':'小小电子维修店'),el('small','THE REPAIR CORNER · 营业中'+(state.owned.includes('badge')?' · 诊断达人':'')));brand.append(el('span','⌁','rs-brand-icon'),name);header.append(brand);
  const wallet=el('div',undefined,'rs-wallet');for(const [label,value] of [['金币',state.coins],['学习积分',state.points],['已修复',state.completed]]){const item=el('div');item.append(el('span',label),el('strong',String(value)));wallet.append(item);}header.append(wallet,button(screen==='rewards'?'返回维修台':'奖励小铺',()=>{screen=screen==='rewards'?'work':'rewards';render();}));shop.append(header);
  const status=el('div',notice,'rs-status');status.id='repair-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');shop.append(status);
  if(!storageOK)shop.append(el('p','浏览器当前不允许保存进度，金币与工单只在本次打开期间保留。','rs-storage'));
  if(screen==='rewards')renderRewards();else if(state.active)renderWork();else renderLobby();
  shop.append(el('footer','低压教学模拟 · 金币、积分和兑换仅限游戏内，与会员账户或真实礼品无关。','rs-footer'));
  markCoach();
  boardView?.resize();
  if(focus)shop.querySelectorAll('[data-repair-focus]').forEach(n=>{if(n.dataset.repairFocus===focus)n.focus({preventScroll:true});});
 }
 function renderLobby(){
  const root=el('div',undefined,'rs-lobby'),hero=el('div',undefined,'rs-hero'),copy=el('div');copy.append(el('span','YOUR NEXT REPAIR','rs-eyebrow'),el('h2','把坏掉的日常，\n修成新的故事。'),el('p','今天会遇到什么客人？从一盏不亮的灯，到一块供电不稳的音箱板。用测量找到线索，选对备件，让它们重新工作。'));
  const method=el('div',undefined,'rs-method');for(const text of ['01 找线索','02 判故障','03 选件修','04 测试交付'])method.append(el('span',text));copy.append(method);hero.append(copy,scene());root.append(hero,heading('门口的客人','6类产品 · 17种已建模故障 · 晶振停振关暂停（旧成绩保留）'));
  const choice=el('div',undefined,'rs-teaching-choice');choice.append(el('strong','第一次维修？可以让师傅带你做。'));for(const [value,text] of [[true,'新手教学 · 一步步带着做'],[false,'自己诊断 · 随时可求助']]){const b=button(text,()=>teaching(value));b.setAttribute('aria-pressed',String(coachEnabled===value));choice.append(b);}choice.append(el('small','只指引操作，不替你答题；教学和提示都不扣积分。'));root.append(choice);
  const orders=el('div',undefined,'rs-orders');for(const seed of seeds){const job=E.offer(seed),card=el('article',undefined,'rs-order'),top=el('div',undefined,'rs-order-top'),customer=el('div');customer.append(el('strong',job.product.customer),el('small',job.id+' / '+job.product.tag));top.append(el('span',job.product.customer.slice(0,1),'rs-avatar'),customer);card.append(top,art(job.product.id),el('h3',job.product.name),el('p','“'+job.fault.symptom+'”'));const foot=el('div',undefined,'rs-order-foot');foot.append(el('strong','报酬 '+job.fee+' 金币'),button('接下这单',()=>dispatch({type:'accept',seed}),'rs-primary'));card.append(foot);orders.append(card);}root.append(orders,help());shop.append(root);
 }
 function board(job){
  if(boardKey!==job.id){disposeBoard();boardKey=job.id;boardFallback=false;
   const host=el('div',undefined,'rs-3d-board'),canvas=el('canvas');canvas.className='rs-board rs-board-canvas';canvas.tabIndex=0;canvas.setAttribute('role','img');canvas.setAttribute('aria-label','3D成品与电路板：拖动旋转、缩放，或俯视查线。铜箔检修显示引脚、走线、过孔与测试点，也可用下方按钮选择网络和测量目标。');host.append(canvas);
   try{boardView=window.RepairShopScene.create(canvas,job.product,id=>{if(id.startsWith('@')){pickMechanical(id);return;}if(id.startsWith('net:')){selectedNet=id.slice(4);selected=null;meter=null;render();return;}selectedNet='';selected=id;meter=null;render();boardElement.querySelector('canvas')?.focus({preventScroll:true});});
    const tools=el('div',undefined,'rs-3d-controls');tools.append(el('span','3D维修桌 · 拖动旋转 / 双指缩放'),button('全桌视角',()=>boardView?.reset(),'','board-reset'),button('聚焦电路板',()=>boardView?.focusBoard(),'','board-focus'),button('俯视查线',()=>boardView?.topView(),'','board-top'),button('铜箔检修（透视）',()=>{inspection=!inspection;render();},'','board-inspection'));host.append(tools);boardElement=host;
   }catch(error){boardError=String(error?.message||error);disposeBoard();boardKey=job.id;boardFallback=true;boardElement=boardFlat(job);}
  }
  if(boardView){const candidate=state.active.installed?job.candidates.find(c=>c.stockId===state.active.installed):null,result=P.solve(job.product,job.fault,candidate);boardView.update(selected,{mechanics:state.active.mechanics,inspection,net:selectedNet,power:state.active.power,current:result.metrics.current,rpm:result.metrics.rpm});const toggle=boardElement.querySelector('[data-repair-focus="board-inspection"]');if(toggle){toggle.setAttribute('aria-pressed',String(inspection));toggle.textContent=inspection?'关闭透视':'铜箔检修（透视）';toggle.title=inspection?'关闭透视，恢复元器件的正常外观':'手动开启透视，查看器件下方走线';}for(const key of ['board-focus','board-top','board-inspection']){const control=boardElement.querySelector('[data-repair-focus="'+key+'"]');if(control)control.disabled=!M.onTable(state.active.mechanics);}}
  if(boardFallback)boardElement=M.onTable(state.active.mechanics)?boardFlat(job):art(job.product.id);
  return boardElement;
 }
 function boardFlat(job){
  const a=state.active,p=job.product,n=svg('svg',{viewBox:'0 0 540 310',class:'rs-board',role:'group','aria-label':'维修板；选择位号查看手册与测试点'});
  const add=(tag,attrs,text)=>{const x=svg(tag,attrs);if(text!==undefined)x.textContent=text;n.append(x);return x;};
  add('rect',{x:9,y:10,width:522,height:286,rx:17,fill:'#266450',stroke:'#194f40','stroke-width':3});
  for(const [x,y] of [[31,32],[508,32],[31,273],[508,273]]){add('circle',{cx:x,cy:y,r:8,fill:'#b4be83'});add('circle',{cx:x,cy:y,r:4,fill:'#274c3f'});}
  add('text',{x:48,y:58,fill:'#b0d0b0','font-size':12},p.name+' / 器件位置示意 · 非接线图');
  // This is a location picker, not a netlist. Connectivity is shown explicitly
  // in the equivalent-circuit panel; decorative tracks must not teach wrong nets.
  const wire=()=>{};
  const label=(x,y,t,size=11)=>add('text',{x,y,fill:'#d5e3bc','font-size':size},t);
  const block=(x,y,w,h,t)=>{add('rect',{x,y,width:w,height:h,rx:5,fill:'#1d4f43',stroke:'#7b9f80','stroke-width':2});label(x+9,y+h/2+4,t);};
  wire('M45 259H495');label(444,280,'GND',12);label(43,83,'VIN '+p.voltage+'V');
  let positions,points;
  if(p.id==='lamp'){
   positions=[[110,116],[280,116],[440,202]];points=[[175,116],[215,116],[440,160]];
   wire('M45 116H61M159 116H231M329 116H440V183M440 236V259M45 116V88');
   label(188,146,'串联限流');label(455,168,'A');label(455,246,'K');
  }else if(p.id==='fan'){
   positions=[[110,112],[297,210],[446,170]];points=[[177,112],[297,170],[446,112]];
   points[1]=[297,182];
   wire('M45 88V112H61M159 112H446V151M297 112V130M297 174V191M297 244V259M446 204V248H365V182H297');
   block(255,130,84,44,'电机');wire('M180 224H248');label(172,212,'G=4.5V');label(459,138,'K');label(458,225,'A');
  }else if(p.id==='speaker'){
   positions=[[110,110],[270,195],[443,210]];points=[[179,110],[270,143],[443,169]];
   wire('M45 88V110H61M159 110H400M270 110V176M270 229V259M443 154V191M443 244V259M487 154V259');block(400,89,87,65,'功放/负载');label(386,181,'反馈支路');
  }else if(p.id==='clock'){
   positions=[[430,210],[252,119],[103,200]];points=[[430,170],[330,119],[103,130]];
   points[0]=[375,210];
   wire('M45 88V97H490M103 97V181M103 234V259M252 97V100M301 119H330V143M365 97V143M397 187V210H381M479 210H495V187H456M350 187V259');block(328,143,144,44,'控制/显示芯片');label(310,135,'RESET');
  }else if(p.id==='sensor'){
   positions=[[120,110],[260,205],[414,205]];points=[[193,110],[260,150],[480,205]];
   wire('M45 88V110H71M169 110H440M120 144V259M260 110V186M260 239V259M414 110V186M463 205H480V155M440 163V259');block(400,125,91,38,'传感器');label(483,189,'SDA');
  }else{
   positions=[[105,110],[430,110],[421,211]];points=[[172,110],[494,110],[421,161]];
   wire('M45 88V110H56M154 110H221M333 110H381M479 110H494V161H210V193M421 161V192M421 245V259M210 234V259');block(221,88,112,44,'降压开关级');block(162,193,96,41,'3.3V负载');
  }
  p.parts.forEach((part,i)=>{
   const [x,y]=positions[i],[tx,ty]=points[i];
   const g=svg('g',{class:'rs-node',role:'button',tabindex:0,'aria-pressed':String(selected===part.id),'aria-label':part.id+' '+part.name,'data-repair-focus':'board-'+part.id});
   const status=V.part(job,a,part.id);g.dataset.evidence=status.tone;g.setAttribute('aria-description',status.label);
   const choose=()=>{selected=part.id;selectedNet='';meter=null;render();shop.querySelector(`[data-repair-focus="board-${part.id}"]`)?.focus({preventScroll:true});};g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
   g.append(svg('rect',{x:x-49,y:y-19,width:98,height:53,rx:5,class:'rs-body'}));
   for(const dx of [-54,48])g.append(svg('rect',{x:x+dx,y:y-5,width:7,height:22,fill:'#c3c8ba'}));
   // Package silhouettes distinguish the physical categories without hiding the reference designator.
   if(part.type==='capacitor')g.append(svg('ellipse',{cx:x+30,cy:y-1,rx:8,ry:12,fill:'#9eada0',stroke:'#d2d9b8'}));
   if(part.type==='ceramic')g.append(svg('rect',{x:x+20,y:y-7,width:20,height:25,rx:2,fill:'#d5b981'}));
   if(part.type==='diode')g.append(svg('rect',{x:x+31,y:y-13,width:6,height:40,fill:'#d3d8c4'}));
   if(part.type==='inductor')g.append(svg('circle',{cx:x+31,cy:y+5,r:11,fill:'none',stroke:'#7c9c88','stroke-width':3}));
   const text=svg('text',{x:x-5,y:y+7,'text-anchor':'middle',fill:'#e3e9dc','font-size':18,'font-weight':700});text.textContent=part.id;g.append(text);
   const name=svg('text',{x,y:y+26,'text-anchor':'middle',fill:'#bbd1b6','font-size':9});name.textContent=part.name.slice(0,9);g.append(name);n.append(g);
   if(status.tone!=='unknown'){const badge=svg('text',{x,y:y+49,'text-anchor':'middle',class:'rs-board-evidence','font-size':10});badge.textContent=status.label;g.append(badge);}
   add('circle',{cx:tx,cy:ty,r:5,fill:'#e0bf6e',stroke:'#f0e3b1','stroke-width':2});
   if(a.diagnosed&&job.fault.component===part.id)add('circle',{cx:x+42,cy:y-22,r:7,fill:a.installed?'#c2e4a2':'#f5c575'});
  });
  return n;
 }
 function networkPanel(p){
  const plan=B.get(p.id),panel=el('section',undefined,'rs-network-panel');panel.id='repair-copper-inspector';panel.append(el('h3','沿铜箔查电路'),el('p','点网络可高亮它的全部焊盘、分支与过孔；点测试点只选择测量目标，不会自动记录读数或确认故障。'));
  const list=el('div',undefined,'rs-network-list');for(const net of plan.nets){const b=button(net.id+' · '+net.label,()=>{selectedNet=net.id;selected=null;meter=null;render();},'','net-'+net.id);b.setAttribute('aria-pressed',String(selectedNet===net.id));list.append(b);}list.append(button('显示全部走线',()=>{selectedNet='';selected=null;meter=null;render();},'','net-all'));panel.append(list);
  const net=plan.nets.find(n=>n.id===selectedNet);if(net)panel.append(el('p',net.id+' 同一网络连接：'+net.members.join('、'),'rs-net-members'));
  const ports=el('div',undefined,'rs-testpoint-list');for(const port of plan.ports)ports.append(button(port.id+' → '+port.part+' / '+p.model.ports[p.parts.findIndex(c=>c.id===port.part)],()=>{selected=port.part;selectedNet='';meter=null;render();},'','port-'+port.id));panel.append(ports);
  panel.append(el('small','铜箔检修模式：器件半透明、显示底层投影及引脚。交叉线不一定相连，带孔的金环才是层间过孔。测试电压以GND为参考。'));
  panel.append(el('small','标注“等效、理想、检验”的模块是固定教学电路块，不是可替换的原厂器件；布线与线宽为放大示意，不代表可制造PCB。'));
  if(p.id==='sensor')panel.append(el('small','U1为本板教学A引脚定义：1 IN、2 GND、3 EN（固定使能）、4 NC、5 OUT；不能套用到任意真实LDO。'));
  if(p.id==='clock')panel.append(el('small','X1两条灰色晶体支路只作拓扑展示，动态未建模。TP1测缓冲器VCC，不测晶体引脚。'));
  return panel;
 }
 function modelPanel(p){
  const panel=el('details',undefined,'rs-model-panel');panel.id='repair-physical-model';panel.open=true;
  panel.append(el('summary','计算依据 · '+p.model.title));
  const conditions=el('ul');for(const text of p.model.conditions)conditions.append(el('li',text));panel.append(conditions);
  const nets={
   lamp:'5V ─ F1(0.2Ω) ─ R1(220Ω) ─ D1(LED) ─ GND\nTP F1、TP R1：R1前；TP D1：LED阳极',
   fan:'5V/150mA ─ F1 ─┬─ 电机 ─┬─ Q1(D→S) ─ GND\n                └─ D1 ──┘\nD1：K接电机正端，A接Q1漏极；Q1栅极4.5V\nTP F1、TP D1：电机正端；TP Q1：漏极',
   speaker:'5V ─ F1(0.2Ω) ─ Rs(3.8Ω) ─┬─ 指定脉冲负载 ─ GND\n                            └─ ESR ─ C1 ─ GND\n非反相端：Vref + 100mVrms信号\n输出 ─ Rf(90kΩ) ─ 反相端 ─ R1(10kΩ) ─ Vref\nVref = 电源平均值 / 2（理想缓冲）\nTP F1（RC轨）、TP C1：Rs后的电源轨均值；TP R1：Vref',
   clock:'3.3V/50mA ─ VCC ─┬─ 1kΩ ─ GND\n                 ├─ C1 ─ GND\n                 └─ R1(10kΩ) ─ RESET(高阻输入)\nTP X1改测缓冲器VCC，不测晶体引脚；TP R1测RESET\nX1动态电路不在本关建模与验收范围',
   sensor:'5V → U1(Vset、1Ω输出电阻、100mA限流) → VOUT\nVOUT ─┬─ 100Ω负载 ─ GND\n      ├─ C1 ─ GND\n      └─ R1(4.7kΩ) ─ BUS(理想高阻)\nTP U1、TP C1：VOUT；TP R1：BUS',
   router:'输入：5V ─ F1(0.2Ω) ─ VIN ─ 等效输入100Ω ─ GND\nVIN≥4.5V时，输出按以下RLC网络计算：\n3.3V ─ 1.35Ω ─ L1(10µH+DCR 0.15Ω) ─┬─ 脉冲负载 ─ GND\n                                    └─ ESR ─ C1 ─ GND\nTP F1：VIN；TP L1、TP C1：输出平均值'
  };
  panel.append(el('pre',nets[p.id],'rs-circuit-netlist'),el('p','未建模范围：'+p.model.limits,'rs-model-boundary'));
  const ports=el('p','测试点：'+p.parts.map((part,i)=>part.id+' → '+p.model.ports[i]).join('；'));panel.append(ports);
  const sources=el('details');sources.append(el('summary','原理参考与模型说明'));
  sources.append(el('p','公式和参数是本关明确声明的等效模型，非原厂产品数据。用KCL/KVL、功率平衡及独立数值积分核对；不是完整SPICE或实物认证。'));
  for(const [title,url] of [['TI · 非反相放大器及理想模型假设','https://www.ti.com/lit/an/slaa068b/slaa068b.pdf'],['TI · LDO输出电容与稳定性','https://www.ti.com/lit/an/slva115a/slva115a.pdf'],['TI · I²C上拉与排查','https://www.ti.com/lit/an/scpa063/scpa063.pdf'],['Fluke · 电容测量前断电放电','https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-measure-capacitance']]){const link=el('a',title);link.href=url;link.target='_blank';link.rel='noopener noreferrer';sources.append(link);}panel.append(sources);return panel;
 }
 function deskInventory(a){const m=a.mechanics,panel=el('section',undefined,'rs-desk-inventory');panel.id='repair-desk-parts';panel.append(el('strong','同一张维修桌上的零件'));for(const [name,text] of [['成品底座','在维修区'],['外壳',m.cover?'已取下 · 桌面后方':'已安装'],['固定支架',m.brace?'已取下 · 桌面后方':'已安装'],['电路板',M.onTable(m)?'在检修垫':'在底座内'],['螺丝',m.loose.length+' / 4 颗在零件盘'],['J1连接线',m.unplugged?'已断开':'已连接']]){const row=el('div');row.append(el('span',name),el('b',text));panel.append(row);}return panel;}
 function renderMechanicalWork(job){
  const a=state.active,m=a.mechanics,n=M.next(m,a.tested),wrap=el('div',undefined,'rs-mechanical-workspace'),bench=el('section',undefined,'rs-bench'),tools=el('aside',undefined,'rs-tools');
  bench.append(el('h3',job.product.name+' · 3D成品维修桌'),el('p','通用低压教学结构示例，不是特定品牌拆机手册。外壳不附带电线，电路板通过J1连接成品内部组件。','rs-board-caption'));
  const stage=el('div',undefined,'rs-board-wrap');stage.append(board(job));bench.append(stage,el('p','全桌视角可查看底座、外壳、支架、电路板与螺丝盘；拆下的零件保留在桌上，不会消失。','rs-board-caption'),deskInventory(a));
  if(a.mechanics.entry==='legacy-open')bench.append(el('p','旧版工单沿用已打开的电路板进度，不清空金币与维修记录。','rs-model-boundary'));
  tools.append(el('h3',a.delivered?'已交付工单':n.title));if(coachEnabled)tools.append(coachPanel(true));
  if(a.delivered){const paid=el('section',undefined,'rs-settlement');paid.append(el('h3','维修完成 · 已结算'),el('p','客人的问题：'+job.fault.symptom),el('p','诊断复盘：'+job.fault.why));if(!a.legacyCompleted)paid.append(el('p','本单报酬 +'+job.fee+' 金币 · 学习积分 +'+(state.history.find(h=>h.id===job.id)?.points||0)));bench.append(paid);tools.append(el('p',a.legacyCompleted?'旧版已交付工单，新增拆装步骤不补记、不重复领取报酬。':'接线、结构复原和已建模项目复测已完成。'),button('接待下一位客人 →',()=>{state.active=null;clearChoices();save();freshSeeds();render();},'rs-primary','next-customer'));}
  else{
   tools.append(el('p',n.body),el('blockquote','“'+job.fault.symptom+'”'));
   tools.append(button(a.power?'关闭模拟电源':'开启模拟电源',()=>dispatch({type:'power'}),'','power'),button(a.discharged?'✓ 已断电放电':'断电后放电',()=>dispatch({type:'discharge'}),'','discharge'));
   const driver=button(mechanicalTool?'✓ 已拿起十字螺丝刀':'拿起十字螺丝刀',()=>{mechanicalTool='phillips';render();},'','mechanic-tool');driver.setAttribute('aria-pressed',String(Boolean(mechanicalTool)));tools.append(driver);
   if(['unscrew','tighten'].includes(n.op)){const list=el('div',undefined,'rs-screw-list');for(const id of M.SCREWS){const loose=m.loose.includes(id),b=button((n.op==='unscrew'?'拆下 ':'装回 ')+id,()=>dispatch({type:'mechanical',op:n.op,id,tool:mechanicalTool}),'','mechanic-'+id);b.disabled=n.op==='unscrew'?loose:!loose;list.append(b);}tools.append(list);}
   else if(n.op==='final')tools.append(a.finalTested?button('交付并领取报酬',()=>dispatch({type:'deliver'}),'rs-warm','deliver'):button('运行成品复测',()=>dispatch({type:'testAssembly'}),'rs-primary','assembly-test'));
   else if(n.op!=='service')tools.append(button(n.title,()=>dispatch({type:'mechanical',op:n.op,tool:mechanicalTool}),'rs-primary','mechanic-'+n.op));
   tools.append(el('p','机械操作不会自动测量、选故障答案或购买备件。板级检修采用手册给定的测试夹具；装回后的复测也只覆盖已建模项目。'),button('撤销此单',()=>{if(confirmAbandon)dispatch({type:'abandon'});else{confirmAbandon=true;notice='再次点击“撤销此单”确认，已购未交付备件会退款。';render();}}));
  }
  wrap.append(bench,tools);shop.append(wrap);const report=verificationPanel(job);if(report)shop.append(report);
 }
 function renderWork(){
  const a=state.active,job=E.offer(a.seed),p=job.product,phase=a.delivered?4:a.tested?3:a.installed?2:a.diagnosed?1:0;
  if(!job.fault.enabled){const paused=el('section',undefined,'rs-model-panel');paused.append(el('h3','这张旧工单已暂停'),el('p','晶振停振需要完整振荡器与负载模型，暂不提供未经验证的结论。已得金币与成绩保留，撤销后会返还未交付备件的采购金币。'),button('撤销旧单并换单',()=>dispatch({type:'abandon'}),'rs-primary'));shop.append(paused);return;}
  if(!M.onTable(a.mechanics)||a.tested||a.delivered){const bar=el('div',undefined,'rs-teaching-bar');bar.append(button(coachEnabled?'收起操作教学':'开启操作教学',()=>teaching(!coachEnabled),'','coach-toggle'));if(!a.delivered)bar.append(button(hintsOpen?'收起师傅提示':'师傅提示',()=>{if(hintsOpen){hintsOpen=false;render();}else dispatch({type:'hint'});},'','hints-toggle'));shop.append(bar);if(coachEnabled&&!a.legacyCompleted)shop.append(coachPanel());if(hintsOpen)shop.append(hintPanel(job));renderMechanicalWork(job);return;}
  const steps=el('nav',undefined,'rs-steps');steps.setAttribute('aria-label','维修进度');['诊断故障','核对与换件','通电测试','交付结算'].forEach((name,i)=>{const s=el('span',undefined,i<phase?'done':i===phase?'current':'');s.append(el('b',i<phase?'✓':String(i+1)),document.createTextNode(name));steps.append(s);});shop.append(steps);
  const teachingBar=el('div',undefined,'rs-teaching-bar');teachingBar.append(button(coachEnabled?'收起操作教学':'开启操作教学',()=>teaching(!coachEnabled),'','coach-toggle'));if(!a.delivered)teachingBar.append(button(hintsOpen?'收起师傅提示':'师傅提示',()=>{if(hintsOpen){hintsOpen=false;render();}else dispatch({type:'hint'});},'','hints-toggle'));teachingBar.append(el('span','看不懂术语或不知道下一步，都可以求助；不扣积分。'));shop.append(teachingBar);if(coachEnabled)shop.append(coachPanel());if(hintsOpen)shop.append(hintPanel(job));
  const work=el('div',undefined,'rs-workspace'),ticket=el('aside',undefined,'rs-ticket');ticket.append(el('span',job.id,'rs-eyebrow'),art(p.id),el('h3',p.name),el('p',p.customer+' · '+p.story),el('blockquote','“'+job.fault.symptom+'”'),el('span','交付报酬 '+job.fee+' 金币','rs-fee'));
  if(!a.delivered){if(confirmAbandon){ticket.append(el('p','确定撤销？未交付备件将退回并返还采购金币。'),button('确认撤销工单',()=>dispatch({type:'abandon'})),button('继续维修',()=>{confirmAbandon=false;render();}));}else ticket.append(button('撤销此单',()=>{confirmAbandon=true;render();}));}
  const bench=el('section',undefined,'rs-bench'),benchHead=el('div',undefined,'rs-bench-title');benchHead.append(el('h3','3D维修工作台'),el('span','点铜线追网络，点TP或器件选择测量目标'));bench.append(benchHead);const wrap=el('div',undefined,'rs-board-wrap');wrap.append(board(job));bench.append(wrap,el('p',(boardFallback?'本设备暂不能显示3D，已使用位置图。':'3D外观为放大教学模型，不是原厂CAD。')+'铜色实线是顶层铜箔，蓝色虚线是底层走线投影，只有过孔连接两层；灰色支路未建模。可点网络追线，实际测试条件见等效电路。','rs-board-caption'),networkPanel(p),deskInventory(a),modelPanel(p));
  const targets=el('div',undefined,'rs-probe-picker');targets.setAttribute('role','group');targets.setAttribute('aria-label','选择测量目标');for(const part of p.parts){const label=part.id+' · '+part.name,b=button(label,()=>{selected=part.id;selectedNet='';meter=null;render();}),status=V.part(job,a,part.id);b.setAttribute('aria-pressed',String(selected===part.id));b.setAttribute('aria-label',label);b.setAttribute('aria-description',status.label);b.dataset.repairFocus='target-'+part.id;b.dataset.evidence=status.tone;b.append(el('small',status.label));targets.append(b);}bench.append(targets,el('p','测量目标不等于故障答案：选择器件只决定测哪里，诊断需要在工具区亲自选择。','rs-board-caption'));
  const powerRow=el('div',undefined,'rs-power-row'),power=button(a.power?'关闭模拟电源':'开启模拟电源',()=>dispatch({type:'power'}),a.power?'rs-warm':'rs-primary'),discharge=button(a.discharged?'✓ 已断电放电':'断电后放电',()=>dispatch({type:'discharge'}));power.dataset.repairFocus='power';discharge.dataset.repairFocus='discharge';power.disabled=a.delivered;discharge.disabled=a.power||a.delivered;powerRow.append(power,discharge);bench.append(powerRow,el('span',a.power?'● 限流电源已开启':a.discharged?'○ 已断电、确认无电并模拟放电':'○ 电源关闭 · 元件检测前请放电','rs-power-label'+(a.power?' on':'')));
  const picked=p.parts.find(x=>x.id===selected),spec=el('div',undefined,'rs-component-spec');spec.append(el('strong',picked?picked.id+' · '+picked.name:'先在板上选择一个器件'),el('p',picked?D.spec(picked):'金色圆点表示对应电压测试点；黑色器件可点击。没有预选的诊断答案。'));bench.append(spec);
  const manual=el('details',undefined,'rs-manual');manual.open=true;manual.append(el('summary','维修手册 / 正常参考'));manual.append(el('p','输入：'+p.voltage+'V。'+p.behavior));for(const part of p.parts)manual.append(el('p',part.id+' · '+part.name+'：'+D.spec(part)));manual.append(el('p','所有替换件还须满足本板引脚、极性、系列与稳定性兼容要求。库存编号是本关教学编号，不是原厂型号。'));bench.append(manual);
  if(a.delivered){const panel=el('section',undefined,'rs-settlement');panel.append(el('span','REPAIR COMPLETE','rs-eyebrow'),el('h3','又一件旧物恢复了生机'),el('p','客人的问题：'+job.fault.symptom),el('p','诊断复盘：'+job.fault.why),el('p','原规格：'+D.spec(p.parts.find(x=>x.id===job.fault.component))),el('p','本单报酬 +'+job.fee+' 金币；学习积分 +'+state.history[0].points+'。备件采购已单独扣除。'));panel.append(button('接待下一位客人 →',()=>{state.active=null;clearChoices();notice='';save();freshSeeds();render();},'rs-primary','next-customer'));bench.append(panel);}
  const tools=el('aside',undefined,'rs-tools');tools.append(el('h3','诊断工具'));
  if(coachEnabled)tools.append(coachPanel(true));
  const meterPanel=el('div',undefined,'rs-meter'),meterTop=el('div',undefined,'rs-meter-top');meterTop.append(el('span','REPAIR / MULTI TESTER'),el('span',selected||'未接探针'));const display=el('div',undefined,'rs-meter-screen');display.id='repair-meter';display.append(el('small',meter?.label||'选择工具与位号后点击测量'),el('strong',meter?.value||'— —'),el('small',meter?'正常参考：'+meter.normal:'测量结果会自动记入笔记'));
  const modes=el('div',undefined,'rs-tool-modes');for(const [value,label] of [['voltage','直流电压'],['component','隔离元件检测'],['scope','运行 / 负载读数'],['visual','放大观察']]){const b=button(label,()=>{mode=value;meter=null;render();});b.setAttribute('aria-pressed',String(mode===value));b.dataset.repairFocus='mode-'+value;modes.append(b);}
  const measure=button('记录一次测量',()=>dispatch({type:'measure',id:selected,mode}));measure.disabled=!selected||a.delivered;measure.dataset.repairFocus='measure';meterPanel.append(meterTop,display,modes,measure);tools.append(meterPanel,el('p',mode==='component'?'元件检测需断电、确认无电并放电；游戏自动使用隔离 / 专用夹具。':mode==='scope'?'在产品专用缓冲 / 诊断口观察，不将探头直接加载到晶体振荡引脚。':'电压探针参考GND；实测应与维修手册的正常状态比较。','rs-meter-note'));
  if(meter){const f=V.describe(meter),feedback=el('section',undefined,'rs-meter-feedback');feedback.id='repair-meter-feedback';feedback.dataset.tone=f.tone;feedback.append(el('strong',f.label),el('p',f.text));tools.append(feedback);}if(!a.diagnosed)tools.append(evidenceChecklist(a));
  if(!a.delivered){const action=el('section',undefined,'rs-action');
   if(!a.diagnosed){action.append(el('h3','你的故障判断'),select('故障位号',p.parts.map(x=>[x.id,x.id+' · '+x.name]),diagnosis,v=>{diagnosis=v;},'repair-diagnosis'),select('失效类型',D.reasons,reason,v=>{reason=v;},'repair-reason'));const diagnose=button('提交诊断',()=>dispatch({type:'diagnose',id:diagnosis,reason}),'rs-primary');diagnose.dataset.repairFocus='diagnose';action.append(diagnose,el('p','需要一项通电观察，以及目标器件的断电隔离检测。'));
   }else if(!a.installed){action.append(el('h3','备件抽屉 · '+job.fault.component),el('p','请与左侧手册逐项比较。不是越贵越好；采购只有安装成功后才扣金币。'));const stockList=el('div',undefined,'rs-stock');stockList.tabIndex=-1;stockList.dataset.repairFocus='stock-list';stockList.setAttribute('role','group');stockList.setAttribute('aria-label','选择兼容备件');for(const candidate of job.candidates){const b=button('',()=>{stock=candidate.stockId;render();});b.dataset.repairFocus=candidate.stockId;b.setAttribute('aria-pressed',String(stock===candidate.stockId));b.append(el('strong',candidate.sku),el('span',D.spec(candidate)),el('em',candidate.price+' 金币'));stockList.append(b);}action.append(stockList);
    if(p.parts.find(x=>x.id===job.fault.component).polar)action.append(select('安装极性', [['correct','与本板A/K或正负极标记一致'],['reverse','与本板标记相反']],orientation,v=>{orientation=v;},'repair-orientation'));
    action.append(button('采购并更换',()=>dispatch({type:'install',stockId:stock,orientation}),'rs-primary','install'));
   }else if(!a.tested){action.append(el('h3','修好了，还要验证'),el('p','开启电源后执行功能与负载复测。测试不会因点了按钮就忽略未完成的维修。'),button('运行功能与负载测试',()=>dispatch({type:'test'}),'rs-primary','test'));
   }else{action.append(el('h3','✓ 验收通过'),el('p','✓ 本关已建模项目通过\n✓ 具体限值见计算验收报告\n未建模功能不视为通过'),button('查看维修前后对照',()=>shop.querySelector('#repair-verification')?.scrollIntoView({block:'start'})),button('交付并领取报酬',()=>dispatch({type:'deliver'}),'rs-warm','deliver'));}
   tools.append(action);
  }
  work.append(ticket,bench,tools);shop.append(work);const verification=verificationPanel(job);if(verification)shop.append(verification);
  const notes=el('details',undefined,'rs-notebook');notes.open=true;notes.append(el('summary','诊断笔记 · '+a.measurements.length+' 条测量记录'));if(!a.measurements.length)notes.append(el('p','还没有记录。先选器件，再选择工具测量。'));else{const list=el('ol');for(const m of a.measurements){const f=V.describe(m),li=el('li');li.dataset.readingPhase=m.key.endsWith(':true')?'after':'before';li.dataset.tone=f.tone;li.append(el('small',(li.dataset.readingPhase==='after'?'换件后':'维修前')+' · '+f.label),el('strong',m.label),el('p',m.value),el('small','正常参考：'+m.normal));list.append(li);}notes.append(list);}shop.append(notes);
 }
 function renderRewards(){
  const root=el('div',undefined,'rs-rewards');root.append(el('span','A LITTLE SOMETHING FOR YOUR SHOP','rs-eyebrow'),el('h2','认真修好，也值得一点奖励'),el('p','学习积分累计不扣除；金币用于采购和兑换。每次兑换后保留50金币周转金。'));
  const cards=el('div',undefined,'rs-reward-grid');D.rewards.forEach((reward,i)=>{const owned=state.owned.includes(reward.id),card=el('article',undefined,'rs-reward');card.append(el('span',['▧','⌂','✦'][i],'rs-reward-icon'),el('h3',reward.title),el('p',reward.description),el('small',reward.cost+' 金币 · 累计'+reward.points+' 学习积分可兑换'));const b=button(owned?'已兑换':'兑换奖励',()=>dispatch({type:'redeem',id:reward.id}),owned?'':'rs-primary');b.disabled=owned;card.append(b);cards.append(card);});root.append(cards);
  const history=el('section',undefined,'rs-history');history.append(el('h3','维修履历'));if(!state.history.length)history.append(el('p','第一张工单还在等你。完成诊断、更换和验收后，履历会出现在这里。'));else for(const h of state.history)history.append(el('p',h.product+' · '+h.component+'修复 · +'+h.fee+'金币 / +'+h.points+'积分'));root.append(history,help());shop.append(root);
 }
 window.addEventListener('storage',e=>{if(e.key===E.KEY){read();clearChoices();notice='已同步另一窗口的维修进度。';if(!shop.hidden)render();}});
 window.addEventListener('pagehide',disposeBoard);
 window.RepairShop=Object.freeze({open:()=>view(true),snapshot:()=>JSON.parse(JSON.stringify(state)),sceneSnapshot:()=>boardView?.snapshot()||(boardFallback?{renderer:'fallback',error:boardError}:null)});
 memoryRevision=state.revision;courseButton.setAttribute('aria-pressed','true');shopButton.setAttribute('aria-pressed','false');
 if(state.active&&!state.active.delivered)view(true);
})();
