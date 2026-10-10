/* Learner-facing circuit consequences, derived from the same animation state. */
(function(root){
 'use strict';
 const circuits=typeof module!=='undefined'&&module.exports?require('./training_circuit_math.js'):root.TrainingCircuitMath;
 const lessons={
  resistor:{why:'电阻材料让电能转成热，并承担一部分电压差。相同电源下，阻值越大，整条串联支路的电流越小；不是电流进去多、出来少。',sales:'客户说“LED限流”，先问供电电压、LED工作电流，再确认阻值、功率、精度和封装。'},
  capacitor:{why:'电容先在两端电极之间储存能量。芯片突然多用电时，它通过外部回路放电，暂时补上电流，让供电电压下降得慢一些；直流不穿过中间的绝缘层。',sales:'客户说“芯片旁边去耦”，先问容量、耐压、封装、介质和工作电压；标称容量相同，不代表实际补电能力相同。'},
  inductor:{why:'电流让绕组建立磁场。磁场变化会产生反对电流突变的电压，所以电流逐渐上升或下降；断电后储存的能量沿续流回路继续送给负载。',sales:'客户说“电源用电感”，先问电感量、峰值电流、温升电流、DCR、尺寸和屏蔽要求；Isat与Irms要分别核对。'},
  diode:{why:'PN结对两个方向的电压响应不同：正向更容易导电，反向通常只有很小漏电。因此可以选择供电方向；导通时有压降，超过反向耐压可能损坏。',sales:'客户说“防反接”，先问电源电压、电流、正向压降、反向耐压和封装；不是所有二极管都适合直接替换。'}
 };
 function describe(course,step,r){
  if(!Object.hasOwn(lessons,course)||!Number.isInteger(step)||step<0||step>2)throw new RangeError('Unknown circuit lesson');
  let change,comparison,note;
  if(course==='resistor'){
   change=step===0?'回路断开，LED不亮。接通后，电阻帮助把电流控制在合适范围。':step===1?'LED亮起；电阻控制整条支路的电流，电阻本身会产生热量。':r.r===1000?'阻值从220 Ω增至1 kΩ，电流变小，LED示意亮度降低。':'选220 Ω时，电流比1 kΩ大，LED示意更亮；电阻功耗也更大。';
   comparison=[['220 Ω时的电流',3/220,'A'],['1 kΩ时的电流',.003,'A']];
   note=step===0?'对比接通后的情况；当前开关断开，电流为0。':'同样5 V电源、示例LED压降2 V。亮度仅作示意，实际要确认LED额定电流。';
  }else if(course==='capacitor'){
   const progress=Math.min(1,Math.max(0,r.t/(5*r.tau)));
   const withCap=circuits.evaluate(course,step,progress,{cap:true}).v;
   const withoutCap=circuits.evaluate(course,step,progress,{cap:false}).v;
   change=step===0?'平稳用电时，电源给芯片供电，电容保存储备能量。':step===1?(r.present?'芯片突然多用电，橙色补电也经过芯片。电压先被托住，再逐渐下降；电容不能一直供电。':'移除C1后，没有这份短时储备；本例芯片电压立即降到3.200 V。'):'用电量回落，电源一边给芯片供电，一边给电容回充，为下一次变化作准备。';
   comparison=[['有C1：芯片电压',withCap,'V'],['无C1：芯片电压',withoutCap,'V']];
   note='同一时刻、同样负载的对比；播放时电压会变化。这里只展示短时补电，不判定芯片是否复位。';
  }else if(course==='inductor'){
   change=step===0?'还没有储能，负载电流为0。接通后，电流不会一下跳到最大值。':step===1?'接通电源后，电流逐渐增加，负载功率也逐渐增加，同时磁场储存能量。':'电源断开后，橙色电流仍经过负载，再经D1返回。电流逐渐减小，不会立刻消失。';
   comparison=[['有L1：负载电流',r.i,'A'],['导线代替L1：负载电流',step===1?.5:0,'A']];
   note='同样5 V、10 Ω负载和理想开关；有电感的断电电流需要D1续流路径，不能直接开路。';
  }else{
   change=step===0?'未接电源，负载没有供电。':step===1?'正常方向接入，负载获得供电；二极管承担一部分压降，因此负载电压低于输入。':'电源接反，D1阻断主要反向电流，负载没有得到−5 V反向供电。';
   comparison=[['输入端电压',r.input,'V'],['经过D1：负载电压',r.output,'V']];
   note='本例正向压降取0.7 V；实际随型号、电流和温度变化。反向仍可能有小漏电。';
  }
  return {change,why:lessons[course].why,sales:lessons[course].sales,comparison,note};
 }
 const api=Object.freeze({describe});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingEffects=api;
})(typeof window==='undefined'?globalThis:window);
