/* Model state and visual state share these explicit classroom conditions. */
(function(root){
 'use strict';
 const data={
  resistor:{title:'换个电阻，看看灯会怎样',intro:'亲手换电阻，看灯光和回路电流一起变化。',action:'选一个电阻，放到亮起的位置',choices:[[100,'100 Ω'],[330,'330 Ω'],[1000,'1 kΩ']],initial:330,
   note:'5 V电源、LED正向压降按2 V估算。亮度只展示相对趋势，不代表实际光度或额定安全范围。',why:'电阻产生压降，把一部分电能转成热；同一串联回路各处电流相同，电阻不是把电流吃掉。'},
  capacitor:{title:'接上电容，看看芯片如何补电',intro:'模拟芯片突然多用电，观察电容补电与回充。',action:'换一个有效容量，试一次突然用电',choices:[[1,'1 µF'],[10,'10 µF'],[22,'22 µF']],initial:10,
   note:'初始3.3 V，电源维持5 mA；新增20 mA由电容承担50 µs，之后同样补回。忽略ESR/ESL与电源动态。远近只比较回路长度，不编造距离导致的压降。',why:'两端电压变化伴随储能变化。补电时电容的电流同样经过芯片，并回到电容；介质里面不画导电路径。'},
  inductor:{title:'换个电感，看看电流怎样上升',intro:'施加相同电压，比较电流上升快慢。',action:'换电感，重播一次上升过程',choices:[[22,'22 µH'],[100,'100 µH'],[220,'220 µH']],initial:100,
   note:'初始1 A；电感两端保持3 V，观察20 µs。示例Isat=3 A，触及后停止线性预测，Isat不等于损坏电流；未计算铜损或磁芯损耗。',why:'电流变化会建立变化的磁场，产生反对突变的电压；同样的电压和时间下，电感量越大，电流上升越慢。'},
  diode:{title:'翻转二极管，看看电流能否通过',intro:'先改变安装方向，再试着接反电源。',action:'选一个方向，放到亮起的位置',choices:[[true,'A → K'],[false,'K → A']],initial:true,
   note:'5 V电源、1 kΩ负载，正向压降按0.7 V估算；反向测试假定未超耐压、忽略漏电。击穿与恢复过程不在本次例题范围内。',why:'正向约定电流从A到K；反向偏置下，这个简化模型阻断电流。实际仍有漏电、耐压和动态条件。'}
 };
 for(const d of Object.values(data)){Object.freeze(d.choices.map(Object.freeze));Object.freeze(d.choices);Object.freeze(d);}Object.freeze(data);
 function lesson(course){if(!Object.hasOwn(data,course))throw new RangeError('Unknown 3D lesson');return data[course];}
 function evaluate(course,p,phase=0){
  const d=lesson(course);if(!p||!d.choices.some(o=>o[0]===p.value)||typeof p.power!=='boolean'||typeof p.reverse!=='boolean'||typeof p.near!=='boolean'||!Number.isFinite(phase)||phase<0||phase>3)throw new RangeError('Invalid 3D state');
  let current=0,voltage=0,brightness=0,storage=0,source=0,load=0,unknown=false,stage='',story='',detail='',metric='',value='',power=0;
  const u=Math.max(0,Math.min(1,phase-1));
  if(course==='resistor'){
   current=p.power?3/p.value:0;voltage=p.power?2:0;power=current*current*p.value;brightness=Math.min(1,current/.02);
   stage=p.power?'灯光与电流一起变化':'电源关闭';metric='回路电流';value=(current*1000).toFixed(1)+' mA';
   story=p.power?'阻值增大，整个回路的电流变小，灯光也变弱。':'电源关闭时，灯灭了，完整回路里没有持续电流。';
   detail=p.power?'电阻功耗 '+(power*1000).toFixed(1)+' mW；电阻前后电流相同。':'打开电源，再换一个电阻试试。';source=load=current;
  }else if(course==='capacitor'){
   const drop=.02*50e-6/(p.value*1e-6),charging=phase>=2,finished=phase===3;
   stage=finished?'已恢复平稳供电':phase<1?'平稳供电':charging?'电源给电容回充':'芯片突然多用电';
   voltage=p.power?(phase<1?3.3:charging?3.3-drop*(3-phase):3.3-drop*u):0;
   storage=p.power&&phase>=1&&!finished?(charging?.02:-.02):0;load=p.power?(phase>=1&&phase<2?.025:.005):0;source=load+storage;current=load;brightness=voltage/3.3;
   metric='芯片供电';value=voltage.toFixed(3)+' V';story=!p.power?'电源关闭；这个演示停止供电。':finished?'电容已补回本次放出的储能，回充电流停止；现在只由电源供电。':phase<1?'平稳时由电源供电，电容暂时不补电。':charging?'负载回落后，电源除了供电，还把电容的储能补回来。':'蓝色是电源送来的电流，橙色是电容补上的电流；两者都经过芯片。';
   detail=!p.power?'打开电源继续观察。':finished?'可以重播，再换一个容量作对比。':charging?'回充电流 20 mA（题设）':phase<1?'点击“模拟突然用电”观察一次变化。':'相同时间内，有效容量越大，供电电压下降越小。';
  }else if(course==='inductor'){
   const elapsed=Math.min(1,phase/3),predicted=1+3*20e-6*elapsed/(p.value*1e-6);unknown=p.power&&predicted>=3;current=p.power?Math.min(predicted,3):0;source=load=current;voltage=p.power?3:0;
   stage=!p.power?'电源关闭':unknown?'触及示例Isat，停止外推':phase===3?'20 µs结束，本次结果':'电流正在上升';metric=unknown?'后续电流':'电感电流';value=unknown?'不再预测':current.toFixed(3)+' A';
   brightness=Math.min(1,current/3);story=!p.power?'这里仅停止例题；实际断电后的续流需要另看完整电路。':unknown?'已触及本例的磁性能判据，不能继续用固定电感量推算。':'同样施加3 V，电感量越大，20 µs内电流增加越慢。';
   detail=unknown?'这不代表器件烧毁；真实选型还要核对Isat、Irms与损耗。':'初始1 A → 20 µs；动画慢放，循环只代表重播例题。';
  }else{
   const on=p.power&&(p.reverse?!p.value:p.value);voltage=on?(p.reverse?-4.3:4.3):0;current=voltage/1000;source=load=current;brightness=on?.7:0;
   stage=!p.power?'电源关闭':on?'本方向导通':'反向偏置，被阻断';metric='负载电压';value=voltage.toFixed(1)+' V';
   story=!p.power?'打开电源，观察安装方向。':on?'这一方向能导通，但负载拿到的电压比电源低；二极管也有压降。':'回路中没有持续导通电流。翻转二极管或试着接反电源，看结果如何改变。';
   detail=p.reverse?'现在是接反电源，不要把反向负载电压当作正常供电。':'金属环标是本图的K端；正向约定电流从A到K。';
  }
  if(!p.power)stage=course==='inductor'?'例题停止':'电源关闭';
  return {current,voltage,brightness,storage,source,load,unknown,stage,story,detail,metric,value,power};
 }
 const api=Object.freeze({courses:Object.freeze(Object.keys(data)),lesson,evaluate});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingPlaygroundMath=api;
})(typeof globalThis==='undefined'?this:globalThis);
