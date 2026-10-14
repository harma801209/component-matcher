/* Learner explanations share the live model; no new progress or business storage. */
(function(root){
 'use strict';
 const lessons={
  resistor:{purpose:'电阻：调节整条回路的电流，让灯达到需要的亮度。',words:[['电压（V）','两个位置之间的电位差；本例电源保持5 V。'],['电流（mA）','回路中电荷流动的量；同一串联回路各处电流相同。'],['阻值（Ω）','本例阻值越大，回路电流越小。']],focus:'R1 · 压降与发热'},
  capacitor:{purpose:'电容：先存储能量，在芯片突然多用电时短暂补电。',words:[['容量（µF）','本例相同补电需求下，容量越大，电压下降越小。'],['补电','把先前存下的能量短暂送给芯片，不是持续发电。'],['回充','需求回落后，电源把电容放出的能量补回来。']],focus:'C1 · 储能与补电'},
  'mos-n':{purpose:'N沟道MOS：用控制端的电压，控制负载的返回通路。',words:[['G：栅极','控制端。改变它相对于S的电压，可以控制沟道。'],['S：源极 / D：漏极','主回路两端。本图S在返回端，D连接负载。'],['VGS / 导通电阻','VGS是G相对S的电压；导通电阻描述已开启通道的阻力，必须带工作条件。']],focus:'MOS · 返回侧开关'},
  'mos-p':{purpose:'P沟道MOS：用控制端的电压，控制送往负载的供电通路。',words:[['G：栅极','控制端。本例G比S低，使用负的VGS。'],['S：源极 / D：漏极','主回路两端。本图S在电源侧，D连接负载。'],['VGS / 导通电阻','看G相对于S，而不是只看对地电压；导通参数必须带工作条件。']],focus:'MOS · 供电侧开关'}
 };
 for(const l of Object.values(lessons)){l.words.forEach(Object.freeze);Object.freeze(l.words);Object.freeze(l);}Object.freeze(lessons);
 const supported=id=>Object.hasOwn(lessons,id),lesson=id=>{if(!supported(id))throw new RangeError('Unknown beginner lesson');return lessons[id];};
 function fields(id,index){lesson(id);if(!Number.isInteger(index)||index<0||index>(id.startsWith('mos-')?2:3))throw new RangeError('Invalid beginner level');return id.startsWith('mos-')?[index===2?'load':'drive']:[];}
 function fixed(id,index){
  fields(id,index);
  if(id==='resistor')return index===0?'先只打开电源，不用换电阻。':'本例电源5 V、LED压降2 V保持不变；只换阻值。';
  if(id==='capacitor')return ['容量先固定10 µF；先看一次补电，不用换件。','突然用电的需求和时间相同；这次只换容量。','容量固定22 µF；这次只改变电容的位置。','容量和位置保持不变；这次只观察补电后如何回充。'][index];
  return index===2?'驱动保持在本例已给出导通参数的档位；这次只改变负载电流。':'负载需求固定2 A；这次只改变控制端的驱动。';
 }
 function fieldLabel(id,key){return key==='drive'?'控制端驱动（G相对S）':key==='load'?'负载需要的电流':key;}
 function hint(id,index){
  fields(id,index);
  if(id==='resistor')return index===0?'先找让回路供电的开关。电阻自己不会发电。':'先看亮度和回路电流：阻值变大时，它们会一起变小。';
  if(id==='capacitor')return index===2?'看电容到芯片的补电回路：哪种位置让接线更短？':'先看橙色路径：电容补电时，它应该经过芯片；回充时方向会改变。';
  return index===2?'本关控制端不变。负载电流减小时，通道中的发热损耗也会减小。':'先区分控制端G和负载回路。注意G相对于S的电压，不只看对地电压。';
 }
 function optionLabel(id,key,value,fallback){
  if(key!=='drive'||!id.startsWith('mos-'))return fallback;
  const sign=id==='mos-p'?'−':'+';
  return value===0?'关闭 · 0 V':value===2.5?'较弱 · '+sign+'2.5 V':'本例已知导通 · '+sign+'10 V';
 }
 function explain(id,p,r,phase=0,started=true){
  lesson(id);let title,change,why;
  if(id==='resistor'){
   title=p.power?'电阻处就有压降和发热':'先接通完整回路';
   change=p.power?'电阻两端：5 V → 2 V，压降3 V；发热功率 '+(r.power*1000).toFixed(1)+' mW。整条回路都是 '+(r.current*1000).toFixed(1)+' mA。':'电源仍是5 V；回路未供电，灯不亮、持续电流为0。';
   why=p.power?'阻值决定这条回路的电流大小。电阻把一部分电能转成热，不会把流入的电流吃掉；电流和灯光同时改变。':'灯要亮，先要有电源和完整回路。电阻只能调节电流，不能自己供电。';
  }else if(id==='capacitor'){
   title=!p.power?'演示停止':phase<1?'电源供电，电容暂不补电':phase<2?'电容把储能送向芯片':phase<3?'电源给电容补回储能':'储能补回，回充停止';
   change=!p.power?'本次演示未供电。':phase<1?'蓝色电源供电5 mA；橙色补电为0。':phase<2?'电源5 mA + 电容20 mA = 芯片25 mA；芯片电压 '+r.voltage.toFixed(3)+' V。':phase<3?'电源25 mA = 芯片5 mA + 电容回充20 mA。':'电源只供芯片5 mA；电容回充为0，芯片恢复3.3 V。';
   why=!p.power?'这里仅停止供电演示；实际断电后的过程需要完整电路条件。':phase<1?'点击“模拟突然用电”，看芯片需求增加时谁来补上。':phase<2?'放出储能时，电容电压逐渐下降。相同需求和时间下，有效容量越大，下降越小；补电回路经过芯片再回到电容端子。':phase<3?'芯片不再需要额外电流，电源把刚才放出的储能补回来，准备应对下一次变化。':'电容不是无限电源。下一次补电还要依靠先前存下的能量；介质不是导电通道。';
  }else{
   const high=id==='mos-p',v=high?-p.drive:p.drive;
   title=!started?'先选驱动，再开始观察':!r.values.known?'这个驱动下，负载电流未知':r.values.on?'控制改变，主回路接通':'本例主回路关断';
   change=(!started?'开始前的条件试算：':'')+'控制端：G相对S为 '+v+' V。'+(!r.values.known?'该档位未给出导通电阻，不能据此计算负载电流或损耗。':r.values.on?'主回路承担题设 '+p.load+' A，MOS导通损耗 '+(r.values.loss*1000).toFixed(0)+' mW。':'本例持续负载电流为0。');
   why=(high?'P沟道位于供电侧：G要相对S降低。':'N沟道位于返回侧：G要相对S升高。')+'栅极电场控制内部沟道；负载能量来自电源，不是从G端送入。'+(!r.values.known?'“开始导通的阈值”不等于“大电流低阻保证”。':'本例仅在正确极性10 V驱动给出了导通参数。');
  }
  return {title,change,why,focus:lesson(id).focus};
 }
 function practice(id,index){
  fields(id,index);
  const task=(question,answers,explanation,trial,verify)=>({question,answers,correct:0,explanation,trial,verify});
  if(id==='resistor')return [
   task('换个情况：电阻还在板上，把电源关掉，灯会怎样？',['灯熄灭，持续回路电流为0','电阻继续给灯供电','只要电阻小，灯就不会灭'],'电阻不是电源。关闭本例电源后没有持续电流，电阻和灯都不再释放本例功率。',{power:false},'关闭电源，验证电阻不会供电'),
   task('换个用途：想把小夜灯调暗。换成较大的1 kΩ后会怎样？',['整条回路电流变小，灯变暗','只有电阻后面的电流变小','电源电压自动变低'],'较大阻值使这条串联回路的电流整体变小；电阻前后电流相同，电源仍是5 V。',{value:1000},'换成1 kΩ，看回路电流和灯光'),
   task('换成待机指示灯：本例只允许最多4 mA，哪种变化更合适？',['换成较大的1 kΩ','换成较小的100 Ω','把电源电压当作电阻压降'],'1 kΩ时本例回路是3 mA，灯仍供电；100 Ω会增加电流。这里只比较题设，不保证真实LED亮度。',{value:1000},'换成1 kΩ，查看是否仍供电'),
   task('现在改做更亮的提示灯：从1 kΩ换回330 Ω，会怎样？',['整条回路电流增大，灯变亮','电流被电阻全部吃掉','电源会自己增加电压'],'本例电流从3 mA变为约9.1 mA，电源仍保持5 V；LED相对亮度随之增加。',{value:330},'换回330 Ω，比较亮度')
  ][index];
  if(id==='capacitor')return [
   task('换个条件：突然用电需求相同，把有效容量从10 µF换成22 µF，会怎样？',['补电阶段的电压下降更小','电容变成永久电源','回充再也不需要电源'],'在本例相同需求下，容量更大，电压下降更小；储能用过后仍需要回充。',{value:22,trigger:true},'用22 µF再观察一次补电'),
   task('换件后容量只剩1 µF：同样补电需求下，芯片电压会怎样？',['补电阶段下降得更多','容量越小越能保持电压','芯片需求自动消失'],'相同电流和时间下，小容量的电压下降更多。先看补电末端，再看回充恢复。',{value:1,trigger:true},'用1 µF观察补电末端'),
   task('换个布局：把电容从芯片旁移远，补电回路会怎样？',['接线变长；本图不据此计算压降','电容能持续发电','距离不会改变接线长度'],'靠近芯片可以缩短补电回路。这张虚拟板只比较位置，不把距离换算成虚构的压降。',{near:false},'把电容移远，比较回路'),
   task('芯片又一次突然多用电，电容为什么还能短暂补电？',['刚才回充补回了储能','电容能无限创造能量','介质把电源电流直接导通过去'],'回充后又有可释放的储能；电容不是无限电源，介质也不是导电通道。',{trigger:true},'再模拟一次突然用电')
  ][index];
  return [
   task('负载已经工作，现在把G相对S恢复到0 V，会怎样？',['本例主回路关断','G端继续给负载供电','电源自动消失'],'0 V是本例关断条件，主回路不再承担持续负载电流；12 V电源本身没有因此消失。',{drive:0,load:2,trigger:true},'把控制驱动恢复0 V验证'),
   task('换回正确极性的10 V档位，为什么本例又能计算导通损耗？',['给出了这个驱动条件下的导通电阻','任何超过阈值的电压都保证同样低阻','不知道参数也可以直接写零电流'],'本例只在正确极性10 V驱动给出了20 mΩ；恢复后2 A对应80 mW。真实器件需按具体条件核对。',{drive:10,load:2,trigger:true},'恢复本例已知驱动，看结果'),
   task('驱动不变，负载需求从1 A升到2 A，导通损耗会怎样？',['变成原来的四倍','完全不变','只变成两倍'],'同样导通电阻，损耗随电流平方变化；本例20 mW变为80 mW。这不是实际温度预测。',{drive:10,load:2,trigger:true},'用2 A验证损耗变化')
  ][index];
 }
 function create(id,viewport,console,verify){
  const l=lesson(id),make=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
  const intro=make('section',null,'play-beginner-intro'),purpose=make('p',l.purpose),words=make('details'),summary=make('summary','这些词是什么意思？');words.append(summary);for(const [name,text] of l.words){const row=make('p');row.append(make('strong',name+'：'),document.createTextNode(text));words.append(row);}intro.append(purpose,words);console.prepend(intro);
  const scope=make('p',null,'play-fixed-condition');console.querySelector('.play-goal').after(scope);
  const board=make('div',null,'play-board-column');viewport.replaceWith(board);board.append(viewport);
  const focus=make('span',l.focus,'play-device-focus');focus.setAttribute('aria-hidden','true');viewport.append(focus);
  const cause=make('section',null,'play-cause'),causeTitle=make('h5'),change=make('p'),reason=make('p');cause.setAttribute('aria-label','器件发生了什么变化');cause.append(causeTitle,change,reason);board.append(cause);
  const transfer=make('details',null,'play-transfer'),question=make('p'),answers=make('div',null,'play-transfer-answers'),feedback=make('p',null,'play-transfer-feedback'),apply=make('button');transfer.hidden=true;transfer.setAttribute('aria-label','换个场景试一试');transfer.append(make('summary','换个场景，先猜再验证'),question,answers,feedback,apply);console.append(transfer);feedback.setAttribute('role','status');apply.type='button';apply.className='play-secondary';apply.hidden=true;
  let key='',task=null,answer=null,verified=false;
  apply.addEventListener('click',()=>{verified=true;transfer.dataset.verified='true';verify(task.trial);apply.textContent='已换好条件 · 看电路验证';feedback.textContent='这次是验证练习，不会重复增加通关数。'+task.explanation;});
  function update({params,result,phase=0,started=true,index,mode,done},view){
   const value=explain(id,params,result,phase,started);causeTitle.textContent=value.title;change.textContent=value.change;reason.textContent=value.why;scope.textContent=fixed(id,index);scope.hidden=mode==='free'||done;focus.hidden=!view;
   transfer.hidden=mode!=='challenge'||!done;
   const newKey=mode+':'+index;if(newKey!==key){key=newKey;answer=null;verified=false;transfer.open=false;task=practice(id,index);question.textContent=task.question;answers.replaceChildren();feedback.textContent='可以试错，不扣分；也可以先继续下一关。';apply.hidden=true;apply.textContent=task.verify;
    // Keep the correct option in different positions across levels; do not teach a fixed button location.
    const order=[0,1,2].map((_,i)=>(i+index)%3);
    for(const i of order){const b=make('button',task.answers[i]);b.type='button';b.dataset.transferAnswer=String(i);b.setAttribute('aria-pressed','false');b.addEventListener('click',()=>{answer=i;transfer.dataset.answered='true';transfer.dataset.correct=String(i===task.correct);for(const button of answers.children)button.setAttribute('aria-pressed',String(button===b));feedback.textContent=(i===task.correct?'判断对了。':'再想一想：')+task.explanation;apply.hidden=false;});answers.append(b);}
   }
   transfer.dataset.answered=String(answer!==null);transfer.dataset.correct=String(answer===task.correct);transfer.dataset.verified=String(verified);
  }
  return {update};
 }
 const api=Object.freeze({supported,lesson,fields,fixed,fieldLabel,optionLabel,hint,explain,practice,create});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingBeginner=api;
})(typeof globalThis==='undefined'?this:globalThis);
