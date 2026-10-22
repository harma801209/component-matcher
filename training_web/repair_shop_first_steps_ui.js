/* Beginner-only presentation. Paid repair state never enters this controller. */
(function(root){
 'use strict';
 const I=root.RepairShopFirstSteps,D=root.RepairShopData,M=root.RepairShopMechanics;
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 function create(host,onExit){
  let state=I.create(),notice='',storageOK=true,view=null,canvasBox=null,viewKey='',saved=null,reason='',disposed=false,restartPending=false;
  const mechanics={...M.create('legacy-open'),entry:'prepared-lesson'};
  try{saved=root.localStorage.getItem(I.KEY);if(saved&&saved.length<150000)state=I.restore(JSON.parse(saved));}catch(_){storageOK=false;}
  const titles=['第一次修好它','先猜，再亲手验证','换一盏灯，自己判断'];
  const names={lower:'电流会减小',same:'电流不变',higher:'电流会增大'};
  const ma=x=>(x*1000).toFixed(2)+' mA';
  // The auto-height lesson iframe is taller than the phone screen. Measure
  // only its own trusted host viewport, never use iframe vh as screen height.
  let viewportOwner=root;try{viewportOwner=root.frameElement?.ownerDocument.defaultView||root;}catch(_){}
  function fit(){const height=viewportOwner.visualViewport?.height||viewportOwner.innerHeight;host.style.setProperty('--rs-first-viewport',Math.max(320,Math.min(1200,height))+'px');view?.resize();}
  viewportOwner.addEventListener('resize',fit);
  function button(text,fn,key,primary=false){const b=el('button',text,primary?'rs-primary':'');b.type='button';b.dataset.firstAction=key;b.addEventListener('click',fn);return b;}
  function act(type,extra={}){
   try{const latest=root.localStorage.getItem(I.KEY);if(latest!==saved){saved=latest;state=latest?I.restore(JSON.parse(latest)):I.create();notice='另一窗口更新了练习，已同步。请重新确认当前步骤。';render();return;}}catch(_){storageOK=false;}
   const r=I.apply(state,{type,...extra});state=r.state;notice=r.message;
   try{saved=JSON.stringify(state);root.localStorage.setItem(I.KEY,saved);storageOK=true;}catch(_){storageOK=false;}
   render();if(root.matchMedia('(max-width:760px)').matches){root.TrainingEmbedLayout?.flush();host.querySelector('.rs-first-work')?.scrollIntoView({block:'start',behavior:'instant'});}
  }
  function controls(parent,items){const row=el('div',undefined,'rs-first-actions');for(const [label,type,extra,key,primary] of items)row.append(button(label,()=>act(type,extra),key||type,primary));parent.append(row);}
  function scene(){
   const p=I.product(state),key=state.episode+':'+p.parts.find(x=>x.id==='R1').value;
   if(key!==viewKey){view?.dispose();view=null;viewKey=key;canvasBox=el('div',undefined,'rs-first-canvas');const canvas=el('canvas');canvas.setAttribute('aria-label',p.name+'的低压教学电路板，可拖动查看；器件也可通过下方按钮选择');canvasBox.append(canvas);
    try{view=root.RepairShopScene.create(canvas,p,id=>{if(p.parts.some(x=>x.id===id))act('select',{id});});}catch(_){canvasBox.replaceChildren(el('p','当前设备暂不支持3D。下方器件按钮、手册和全部测量仍可使用。','rs-first-fallback'));}
   }
   const current=I.result(state).metrics.current;
   view?.update(state.selected,{mechanics,inspection:false,leads:{red:null,black:null},activeLead:null,power:state.power,current});
   return canvasBox;
  }
  function powerControls(parent){
   const items=[];
   if(!state.fixture)items.push(['接好教学夹具','fixture',{},'fixture',true]);
   else{items.push([state.power?'关闭电源':'开启电源','power',{on:!state.power},'power']);if(!state.power&&!state.discharged)items.push(['确认无电并放电','discharge',{},'discharge',true]);}
   controls(parent,items);
  }
  function parts(parent){
   const row=el('div',undefined,'rs-first-parts');row.setAttribute('role','group');row.setAttribute('aria-label','选择板上器件');
   for(const p of I.product(state).parts){const b=button(p.id+' · '+p.name,()=>act('select',{id:p.id}),'part-'+p.id);b.setAttribute('aria-pressed',String(state.selected===p.id));row.append(b);}parent.append(row);
  }
  function manual(){const box=el('details',undefined,'rs-first-manual');box.open=state.episode===2;box.append(el('summary','本机手册 · 正常参考'));
   box.append(el('p','5 V低压直流；同一颗红色LED；正常工作电流10–20 mA。'));
   for(const p of I.product(state).parts)box.append(el('p',p.id+' · '+D.spec(p)));
   box.append(el('small','这是教学等效电路，不是品牌拆机资料。供电支路电流由师傅预接的理想串联电流夹具读取；隔离检测前需断电放电。'));return box;
  }
  function readings(parent){
   const box=el('div',undefined,'rs-first-reading');box.setAttribute('aria-label','已记录的测量');
   if(state.observed)box.append(el('span','通电记录'),el('strong',ma(state.observed.current)));
   else box.append(el('span','还没有通电记录'),el('strong','— mA'));
   for(const [id,r] of Object.entries(state.inspected))box.append(el('span',id+' 隔离检测'),el('strong',r.value));
   parent.append(box);
  }
  function diagnosis(parent){
   const group=el('div',undefined,'rs-first-diagnosis'),label=el('label','根据证据，故障类型是？'),s=el('select');s.id='first-reason';label.htmlFor=s.id;
   for(const [value,text] of [['','请选择'],['open','开路：电流路径断开'],['drift','阻值偏移：与手册值不同']]){const o=el('option',text);o.value=value;s.append(o);}s.value=reason;s.addEventListener('change',()=>{reason=s.value;});group.append(label,s);
   const b=button('提交 '+(state.selected||'所选器件')+' 的判断',()=>act('diagnose',{id:state.selected,reason}),'diagnose',true);b.disabled=!state.observed||!state.inspected.R1?.proof;group.append(b);parent.append(group);
  }
  function install(parent){
   parent.append(el('p','对照手册选一枚备件：阻值、额定功率与封装都要合适。'));
   const row=el('div',undefined,'rs-first-stock');for(const c of I.stock(state)){const b=button(D.spec(c),()=>act('install',{id:c.id}),'stock-'+c.id);b.disabled=state.power||!state.discharged;row.append(b);}parent.append(row);
  }
  function repair(parent){
   const stage=I.stage(state),independent=state.episode===2;
   const messages={fixture:['一盏不亮的灯','小林：“这是我睡前看书用的小灯，还能救回来吗？” 师傅已安全拆开外壳，把低压电路板放到桌上。这一章先学会凭证据修好它，拆装留到自由接单。'],observe:['先看它怎么不工作','开启5 V练习电源，亲自记录供电支路电流。电流为零只说明回路没有导通，不能单凭它确定哪颗坏了。'],inspect:['断电后，找出断在哪里','先关电源、确认无电并放电。选择器件，再做隔离检测，与本机手册比较。OL表示在本测试条件下开路，不是0 Ω。'],diagnose:['把两条线索连起来','对照通电记录与隔离读数：哪个器件没有符合手册？选择位号和故障类型。'],install:['找对备件，不是选最大的','保持断电放电，按手册规格更换；错误备件不会被装入，也不会扣金币。'],test:['装上不等于修好','重新通电复测，确认工作电流与电阻损耗都符合本机规定，再交还客人。'],investigate:['另一位客人的灯，表现不一样了','阿悦：“灯能亮，但工作不正常。” 这次不逐步指定你检查哪里。使用手册、通电记录与断电隔离检测，自己作出判断。']};
   const [title,body]=messages[stage]||messages.test;parent.append(el('h3',title),el('p',body));
   powerControls(parent);
   if(state.fixture&&state.power&&!state.installed)controls(parent,[['记录通电结果','observe',{},'observe',true]]);
   if(['inspect','diagnose','investigate'].includes(stage)){
    parts(parent);const b=button('隔离检测 '+(state.selected||'所选器件'),()=>act('inspect',{id:state.selected}),'inspect',true);b.disabled=!state.selected||state.power||!state.discharged;parent.append(b);
   }
   if(stage==='diagnose'||stage==='investigate')diagnosis(parent);
   if(stage==='install')install(parent);
   if(stage==='test'){const b=button('通电复测并验收',()=>act('test'),'test',true);b.disabled=!state.power;parent.append(b);}
   if(independent&&!state.helpUsed)parent.append(button('需要一点排查提示',()=>act('help'),'help'));
   if(independent&&state.helpUsed)parent.append(el('p','排查提示：先比较工作电流，再断电隔离检测。把实测值与手册逐项对照；电流小不等于一定是某个器件坏了。','rs-first-hint'));
   readings(parent);
  }
  function comparison(parent){
   const stage=I.stage(state);parent.append(el('h3',stage==='predict'?'同一盏灯，换个电阻会怎样？':'只改变一个条件，比较两次记录'));
   if(stage==='predict'){
    parent.append(el('p','电源仍是5 V，LED不变。把串联电阻从220 Ω改为440 Ω，电流会怎样？先猜一猜，猜错不扣分。'));
    controls(parent,Object.entries(names).map(([answer,text])=>[text,'predict',{answer},'predict-'+answer]));return;
   }
   parent.append(el('p','你的首次预测：'+names[state.prediction]+'。先测220 Ω，再断电放电换到440 Ω。实验调参不代表440 Ω就是原机合格替代件。'));
   powerControls(parent);
   if(state.fixture){const row=el('div',undefined,'rs-first-actions');for(const value of [220,440]){const b=button('实验R1：'+value+' Ω',()=>act('resistor',{value}),'resistor-'+value);b.setAttribute('aria-pressed',String(state.ohms===value));b.disabled=state.power||!state.discharged;row.append(b);}parent.append(row);if(state.power)controls(parent,[['记录 '+state.ohms+' Ω 的电流','observe',{},'observe',true]]);}
   const table=el('table',undefined,'rs-first-comparison'),head=el('tr');for(const t of ['串联电阻','记录的电流'])head.append(el('th',t));const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');for(const value of [220,440]){const tr=el('tr');tr.append(el('th',value+' Ω'),el('td',state.comparisons[value]?ma(state.comparisons[value].current):'尚未记录'));body.append(tr);}table.append(body);parent.append(table);
   if(stage==='principle'){
    parent.append(el('h4','哪一个解释符合这两次实验？'));
    controls(parent,[['相同电源和LED，串联电阻增大使电流减小','principle',{answer:'series'},'principle-series'],['额定功率越大，电流就越大','principle',{answer:'power'},'principle-power'],['换电阻会把5 V电源直接改成10 V','principle',{answer:'supply'},'principle-supply']]);
   }
  }
  function celebration(parent){
   const r=I.result(state);parent.append(el('span','✓ 本章完成','rs-first-success'));
   if(state.episode===1){const x=state.comparisons['220'].current,y=state.comparisons['440'].current;parent.append(el('h3','把猜测，变成自己的证据'),el('p','220 Ω：'+ma(x)+' → 440 Ω：'+ma(y)+'。你的首次预测'+(state.prediction==='lower'?'与结果一致。':'与结果不同，现在可以用测量修正它。')),el('p','这两个条件下，串联电阻增大，电流减小。LED压降也随电流改变，所以不能机械地认定“电阻翻倍，电流精确减半”。'));
   }else{parent.append(el('h3',state.episode===0?'小林：“我的小灯又能用了！”':'阿悦：“这次工作正常了，谢谢你。”'),el('p','复测电流 '+ma(r.metrics.current)+'；电阻损耗 '+(r.metrics.resistorPower*1000).toFixed(2)+' mW，低于本件额定125 mW。'),el('p',state.episode===0?'你做的不是猜答案：先记录回路无电流，再隔离发现R1开路，换上符合规格的器件，最后通电验证。':'这次手册阻值是180 Ω，不是第一章的220 Ω。维修要恢复本机要求，不能背一个固定按钮或数值。'));}
   controls(parent,[[state.episode===2?'查看本次练习报告':'下一章 →','next',{},'next',true]]);
  }
  function report(){
   const card=el('section',undefined,'rs-first-report');card.append(el('span','三章练习完成','rs-first-success'),el('h2','你让两盏灯重新工作了。'));
   const r=state.records[2],p=state.records[1];card.append(el('p','实验首次预测：'+names[p.firstPrediction]+'；'+(p.firstPredictionCorrect?'与记录一致。':'通过两组测量修正了最初猜测。')),el('p','换情境判断：'+(r.helpUsed?'借助排查提示完成。':r.attempts?'经过修改判断或选件后完成。':'未使用排查提示、首次判断与选件通过。')));
   card.append(el('p','这只是本次低压LED串联电路的练习记录，不等于已经掌握所有元器件，也不能作为真实维修资质。下一步可以自由接单：完整拆装、手动放表笔、更多器件与故障。'));
   card.append(button('去自由接单 →',onExit,'exit-report',true),el('small','自由接单保留原来的金币、积分和存档；本练习不发放或扣除它们。'));return card;
  }
  function render(){
   if(disposed)return;fit();const focus=document.activeElement?.dataset.firstAction;host.replaceChildren();host.className='rs-first';host.dataset.version='1';host.dataset.episode=String(state.episode);host.dataset.stage=I.stage(state);
   const header=el('header',undefined,'rs-first-header');header.append(el('div','零基础 · 约10分钟 · '+(state.done?'练习报告':(state.episode+1)+'/3 '+titles[state.episode])),button('返回自由维修',onExit,'exit'));host.append(header);
   if(state.done){view?.dispose();view=null;canvasBox=null;viewKey='';host.append(report());}
   else{
    const work=el('div',undefined,'rs-first-work'),board=el('section',undefined,'rs-first-board');board.append(scene());const caption=el('div',undefined,'rs-first-board-caption');caption.append(el('span',I.product(state).name+' · '+(state.power?'5 V电源已开':'已断电')+' · R1 '+I.product(state).parts.find(x=>x.id==='R1').value+' Ω'),button('俯视电路',()=>view?.topView(),'top'));board.append(caption);
    const action=el('section',undefined,'rs-first-task');action.setAttribute('aria-label','当前练习操作');action.setAttribute('tabindex','0');action.append(el('small','操作区可上下滑动，电路保持可见','rs-first-scroll-hint'));if(I.stage(state)==='celebrate')celebration(action);else if(state.episode===1)comparison(action);else repair(action);
    if(notice){const n=el('p',notice,'rs-first-feedback');n.setAttribute('role','status');n.setAttribute('aria-live','polite');action.append(n);}work.append(board,action);host.append(work);
    const more=el('div',undefined,'rs-first-reference');more.append(manual(),el('p','低压教学模拟。桌面亮光只表示通电状态，不是照度测量；不模拟焊接热过程、真实市电维修或所有失效机理。','rs-first-limits'));host.append(more);
   }
   host.append(el('small',storageOK?'仅保存本机练习进度 · 与正式工单和积分分开':'浏览器无法保存；练习仅在本次打开期间保留。','rs-first-save'));
   const restart=el('details',undefined,'rs-first-restart');restart.append(el('summary','重新练习'));
   if(restartPending){restart.open=true;restart.append(el('p','只重新开始这三章；不会重置自由维修的工单、金币或积分。'),button('确认重新开始三章',()=>{state=I.create();reason='';notice='已重新开始新手练习。';restartPending=false;try{saved=JSON.stringify(state);root.localStorage.setItem(I.KEY,saved);}catch(_){storageOK=false;}render();},'restart-confirm'),button('取消',()=>{restartPending=false;render();},'restart-cancel'));}
   else restart.append(button('准备重新开始三章',()=>{restartPending=true;render();},'restart'));
   host.append(restart);
   view?.resize();if(focus)host.querySelector('[data-first-action="'+focus+'"]')?.focus({preventScroll:true});
  }
  render();return Object.freeze({render,snapshot:()=>JSON.parse(JSON.stringify(state)),sceneSnapshot:()=>view?.snapshot()||null,dispose:()=>{disposed=true;viewportOwner.removeEventListener('resize',fit);view?.dispose();view=null;}});
 }
 const api=Object.freeze({VERSION:1,create});root.RepairShopFirstStepsUI=api;
})(window);
