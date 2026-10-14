/* Page-only sequential missions; goals use the same model as the live 3D view. */
(function(root){
 'use strict';const M=typeof module!=='undefined'&&module.exports?require('./training_playground_math.js'):root.TrainingPlaygroundMath;
 const seed=(value,extra={})=>({value,power:true,reverse:false,near:true,...extra});
 const levels={
  resistor:[
   {title:'先让灯亮起来',goal:'灯现在不亮。打开电源，让完整回路开始供电。',hint:'先看电源是否打开，不用急着换电阻。',learned:'电源与完整回路是亮灯的前提；电阻不是电源。',setup:seed(330,{power:false}),check:p=>p.power},
   {title:'把小夜灯调亮',goal:'换一个电阻，让灯比现在更亮，达到亮度条的80%以上。',hint:'试着减小阻值，观察整个回路的电流和亮度。',learned:'阻值变小，整个串联回路的电流增大，灯更亮；亮度条只是相对趋势。',setup:seed(1000),check:(p,r)=>p.power&&r.brightness>=.8},
   {title:'不刺眼的提示灯',goal:'灯太亮了。把回路电流调到8～12 mA，做一盏柔和的提示灯。',hint:'选择比现在更大的阻值，看实时电流是否进入目标范围。',learned:'不同用途需要不同亮度。限流靠电阻的压降，不是把前后电流变成两种大小。',setup:seed(100),check:(p,r)=>p.power&&r.current>=.008&&r.current<=.012},
   {title:'低电流待机灯',goal:'灯仍要亮，但这次只允许最多4 mA。换件把电流降下来。',hint:'增加阻值；关闭电源不算完成，因为灯仍要亮。',learned:'较大的阻值可降低这条回路的电流。实际亮度和能否满足用途还要看LED规格。',setup:seed(330),check:(p,r)=>p.power&&r.current>0&&r.current<=.004}
  ],
  capacitor:[
   {title:'叫醒备用储能',goal:'让芯片突然多用电，看橙色电流从电容送到芯片。',hint:'先打开电源，再点“模拟突然用电”，观察补电和回充。',learned:'电容放出的电流经过芯片并回到电容端子，和电源一起补上这次需求。',setup:seed(10),check:(p,r,phase,s)=>p.power&&s.started&&phase>=1&&r.storage<0},
   {title:'守住芯片电压',goal:'芯片再次突然用电。换容量，使整个补电阶段的最低电压不低于3.25 V。',hint:'先换容量，再模拟一次。相同用电时间内，有效容量越大，电压下降越小。',learned:'同样放出这些储能时，较大有效容量的电压下降较小；实际还受偏压和寄生参数影响。',setup:seed(1),check:(p,r,phase,s)=>p.power&&s.started&&phase>=2&&M.evaluate('capacitor',p,2).voltage>=3.25-1e-10},
   {title:'把储备放在身边',goal:'电容离芯片较远。把它移回靠近芯片的位置，缩短补电回路。',hint:'点击“把电容移近芯片”，直接观察接线变短。',learned:'靠近芯片可缩短补电回路；本图只比较位置，不给距离编造电压数值。',setup:seed(22,{near:false}),check:p=>p.power&&p.near},
   {title:'补电后也要补回来',goal:'再模拟一次突然用电，观察橙色电流回充，直到芯片回到3.3 V、回充停止。',hint:'用“模拟突然用电”开始；等待这一轮动画完成，观察回充结束。',learned:'电容不是无限电源。补电后，需要电源把储能补回来才能继续应对变化。',setup:seed(22),check:(p,r,phase,s)=>p.power&&s.started&&phase===3&&r.storage===0&&Math.abs(r.voltage-3.3)<1e-10}
  ],
  inductor:[
   {title:'看看电流爬坡',goal:'施加本例电压，观察电感电流从1 A开始逐渐上升。',hint:'先点“打开电源”，观察电流逐渐上升。',learned:'电感反对电流突变；电流变化伴随磁场储能变化，并非一通电就跳到任意值。',setup:seed(100),check:(p,r,phase,s)=>p.power&&s.started&&phase>=1.5&&!r.unknown&&r.current>1},
   {title:'把爬坡速度放慢',goal:'换一个电感，完整观察20 µs；末端电流不要超过1.3 A。',hint:'选择更大的电感，打开电源观察同样的电压和时间；不用背公式。',learned:'相同电压和时间下，电感量较大，电流增加得较慢。',setup:seed(22),check:(p,r,phase,s)=>p.power&&s.started&&phase===3&&!r.unknown&&r.current<=1.3+1e-10},
   {title:'找到不能继续算的边界',goal:'换件并重播，让电流触及本例Isat 3 A，看看为什么后面显示“不再预测”。',hint:'较小电感上升更快；观察到边界，不要把它当作烧毁动画。',learned:'触及题设Isat后，固定电感量的直线估算不能继续外推；这不等于器件烧毁。',setup:seed(220),check:(p,r,phase,s)=>p.power&&s.started&&r.unknown},
   {title:'换回可预测的范围',goal:'这次换件，使完整20 µs都不触及本例Isat，得到一个有效的末端结果。',hint:'从目前过快的爬坡中换一个较大的电感，再重播。',learned:'选型需考虑工作点与磁性能边界，也要另看Irms、温升和损耗；不能只看电感量。',setup:seed(22),check:(p,r,phase,s)=>p.power&&s.started&&phase===3&&!r.unknown&&r.current<3}
  ],
  diode:[
   {title:'找到能通电的方向',goal:'负载没有电。翻转二极管，让负载得到正向电压。',hint:'看A与K：本图正向约定电流从A流到K。',learned:'二极管有方向；正向导通仍有压降，并不等于一根理想导线。',setup:seed(false),check:(p,r)=>p.power&&!p.reverse&&r.voltage>4},
   {title:'试一次电源接反',goal:'保持这个器件方向，把电源接反，观察它挡住持续反向供电。',hint:'点击“试着接反电源”，观察负载电压与电流。',learned:'在未超耐压、忽略漏电的本例中，反向偏置阻断持续电流；真实器件不是无限耐压。',setup:seed(true),check:(p,r)=>p.power&&p.reverse&&Math.abs(r.current)<1e-12},
   {title:'为什么方向不能随便换',goal:'电源仍接反。再翻一次器件，让你看见负载电压变成负数的错误接法。',hint:'翻器件看电流反向；负电压不是恢复正常供电。',learned:'器件和电源的方向要一起看；负载拿到反向电压，即使有电流也不代表正常工作。',setup:seed(true,{reverse:true}),check:(p,r)=>p.power&&p.reverse&&r.voltage<0},
   {title:'恢复正常供电',goal:'同时修正电源和二极管的方向，让负载重新得到正向电压。',hint:'电源恢复正常，再把器件转成A到K的导通方向；两步顺序都可以。',learned:'正常供电要核对电源、A/K方向和负载电压；“有电流”不是唯一判断。',setup:seed(false,{reverse:true}),check:(p,r)=>p.power&&!p.reverse&&p.value&&r.voltage>4}
  ]
 };
 for(const list of Object.values(levels)){for(const l of list){Object.freeze(l.setup);Object.freeze(l);}Object.freeze(list);}Object.freeze(levels);
 function list(c){M.lesson(c);return levels[c];}
 function level(c,i){if(!Number.isInteger(i)||!list(c)[i])throw new RangeError('Invalid mission');return list(c)[i];}
 function create(course){list(course);return {course,index:0,cleared:[],interacted:false,started:false};}
 function validate(s){if(!s||typeof s.interacted!=='boolean'||typeof s.started!=='boolean'||!Array.isArray(s.cleared))throw new RangeError('Invalid progress');level(s.course,s.index);if(s.cleared.some((v,i)=>v!==i)||s.cleared.length>list(s.course).length||s.index>Math.min(s.cleared.length,3))throw new RangeError('Invalid progress');}
 function action(s,event){validate(s);if(!['change','power','trigger','near','reverse','step'].includes(event))throw new RangeError('Invalid action');return {...s,cleared:[...s.cleared],interacted:true,started:s.started||['trigger','step'].includes(event)};}
 function judge(s,p,phase){validate(s);const l=level(s.course,s.index),r=M.evaluate(s.course,p,phase),passed=s.interacted&&l.check(p,r,phase,s);let feedback=l.hint;
  if(!p.power)feedback='当前没有供电。先打开电源，再观察器件的作用。';
  else if(s.course==='capacitor'&&[0,1,3].includes(s.index)){
   if(!s.started)feedback='换好器件后，点“模拟突然用电”，观察变化。';
   else if(s.index===1)feedback=phase<2?'这次补电还在进行，请观察到阶段结束。':'这次最低电压仍低于3.25 V。换较大的有效容量，再模拟一次。';
   else if(s.index===3&&phase<3)feedback='这次补电与回充还没结束。等待本轮观察完成；需要停止时可以关闭电源。';
  }else if(s.course==='inductor'){
   if(!s.started)feedback='换好器件后点“打开电源”，观察电流上升。';
   else if(r.unknown&&s.index!==2)feedback='已触及本例Isat，不能作为有效的末端估算。换更大的电感再试。';
   else if(phase<3&&!passed)feedback='电流正在变化。等待本轮观察完成；需要停止时可以关闭电源。';
  }
  return {passed,hint:l.hint,learned:l.learned,feedback};}
 function record(s,p,phase){const verdict=judge(s,p,phase);return verdict.passed&&s.index===s.cleared.length?{...s,cleared:[...s.cleared,s.index]}:s;}
 function visit(s,index){validate(s);level(s.course,index);if(index>Math.min(s.cleared.length,3))return s;return {...s,index,cleared:[...s.cleared],interacted:false,started:false};}
 function attempt(s){validate(s);return {...s,cleared:[...s.cleared],interacted:false,started:false};}
 const api=Object.freeze({list,level,create,action,judge,record,visit,attempt});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingPlaygroundLevels=api;
})(typeof globalThis==='undefined'?this:globalThis);
