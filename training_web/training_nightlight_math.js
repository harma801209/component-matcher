/* One bounded product circuit. Values are exercise assumptions, not ratings. */
(function(root){
 'use strict';
 const key='fruition.training.nightlight.v1',resistors=[100,330,1000],capacitors=[.00047,.0022,.01];
 const chapters=[
  {title:'让第一盏灯亮起来',goal:'装入一个电阻，再打开电源。',hint:'先选一个电阻，蓝色按钮就会让灯亮起来。',learned:'电源、LED和完整回路一起工作；电阻负责限制这条回路的电流。'},
  {title:'做成柔和的小夜灯',goal:'这盏灯太亮了。换电阻，把回路电流调到8～12 mA。',hint:'试试330 Ω。换件后灯光和电流立即一起改变。',learned:'阻值变大，整条串联回路的电流减小；电阻前后不是两种电流。'},
  {title:'接反也不反向供电',goal:'加一颗保护二极管，测试电源接反，再恢复正常亮灯。',hint:'正常电源从A流向K。先测试接反，再恢复正常供电。',learned:'串联二极管在本例中阻断反向供电；正常供电也会有压降。'},
  {title:'断电时，短暂留一盏灯',goal:'换电容，让断电2秒后的回路电流仍不少于4 mA。',hint:'试试10000 µF，再断电观察完整2秒。储能有限，灯会逐渐变暗。',learned:'电容的储能经过LED形成回路；容量较大可在本例中维持更久，但不是无限电源。'},
  {title:'让按钮控制小夜灯',goal:'装入MOS管，按按钮让灯亮、灭，再亮一次。',hint:'MOS装好后，按钮只控制栅极；灯的电能仍来自电源。',learned:'本例N沟道MOS在低边控制负载；栅压相对源极改变，决定本例是否导通。'}
 ];
 chapters.forEach(Object.freeze);Object.freeze(chapters);
 function blank(){return {index:0,cleared:0,resistance:null,diode:'none',capacitance:0,mos:false,gate:false,power:false,reverse:false,elapsed:0,running:false,acted:false,tested:false,sawOn:false,sawOff:false};}
 function validateRecord(raw){
  if(!raw||raw.version!==1||!Number.isInteger(raw.cleared)||raw.cleared<0||raw.cleared>5||!Number.isInteger(raw.index)||raw.index<0||raw.index>Math.min(raw.cleared,4))return {version:1,cleared:0,index:0};
  return {version:1,cleared:raw.cleared,index:raw.index};
 }
 function setup(index,cleared=0){
  if(!Number.isInteger(index)||index<0||index>4||!Number.isInteger(cleared)||cleared<index||cleared>5)throw new RangeError('Invalid chapter');
  const s={...blank(),index,cleared,resistance:index===0?null:index===1?100:330,power:index>0,diode:index>=3?'forward':'none',capacitance:index===3?.00047:index===4?.01:0};
  return cleared===5&&index===4?{...s,mos:true,gate:true,acted:true,sawOn:true,sawOff:true}:s;
 }
 function restore(raw){const r=validateRecord(raw);const s=setup(r.index,r.cleared);if(r.cleared===5&&r.index===4)return {...s,mos:true,gate:true,acted:true,sawOn:true,sawOff:true};return s;}
 function record(s){return {version:1,cleared:s.cleared,index:passed(s)?Math.min(s.index+1,4):s.index};}
 function result(s){
  const supply=5,vf=.3,led=2,ron=s.mos&&s.gate?2:0,R=(s.resistance||330)+ron;
  let voltage=0,current=0,unknown=false,source='off';
  const connected=s.resistance!==null&&(s.index<4||s.mos&&s.gate);
  if(s.power){
   source='supply';
   if(s.reverse){if(s.diode!=='forward')unknown=true;}
   else if(s.diode!=='backward'){voltage=s.diode==='forward'?supply-vf:supply;if(connected)current=Math.max(0,voltage-led)/R;}
  }else if(s.running||s.elapsed>0){
   source='capacitor';
   if(s.capacitance>0&&connected){voltage=led+(supply-vf-led)*Math.exp(-s.elapsed/(R*s.capacitance));current=Math.max(0,voltage-led)/R;}
  }
  const brightness=Math.min(1,Math.max(0,current/.015));
  return {voltage,current,brightness,unknown,source,resistorPower:current*current*(s.resistance||0),diodeDrop:s.power&&!s.reverse&&s.diode==='forward'?vf:0,energy:s.capacitance*voltage*voltage/2};
 }
 function passed(s){
  if(!s.acted)return false;const r=result(s);
  if(s.index===0)return s.power&&!s.reverse&&r.current>0;
  if(s.index===1)return s.power&&r.current>=.008&&r.current<=.012;
  if(s.index===2)return s.tested&&s.power&&!s.reverse&&s.diode==='forward'&&r.current>0;
  if(s.index===3)return !s.power&&s.elapsed>=2&&r.current>=.004-1e-12;
  return s.power&&s.mos&&s.gate&&s.sawOn&&s.sawOff&&r.current>0;
 }
 function judge(s){return passed(s)&&s.cleared===s.index?{...s,cleared:s.cleared+1}:s;}
 function action(state,type,value){
  let s={...state};
  if(type==='visit'){if(!Number.isInteger(value)||value<0||value>Math.min(s.cleared,4))return s;return setup(value,s.cleared);}
  if(type==='next'){return s.cleared>s.index&&s.index<4?setup(s.index+1,s.cleared):s;}
  if(type==='reset')return setup(s.index,s.cleared);
  if(type==='resistance'&&s.index<=1&&resistors.includes(value)){s.resistance=value;s.acted=true;}
  else if(type==='diode'&&s.index===2&&['none','forward','backward'].includes(value)){s.diode=value;s.tested=false;s.reverse=false;s.acted=true;}
  else if(type==='capacitance'&&s.index===3&&capacitors.includes(value)){s.capacitance=value;s.elapsed=0;s.running=false;s.acted=true;}
  else if(type==='mos'&&s.index===4){s.mos=true;s.gate=false;s.sawOn=false;s.sawOff=false;s.acted=true;}
  else if(type==='power'){
   s.acted=true;s.power=!s.power;s.elapsed=0;s.running=s.index===3&&!s.power&&s.capacitance>0;
  }
  else if(type==='primary'){
   s.acted=true;
   if(s.index===0)s.power=true;
   else if(s.index===1)s.power=true;
   else if(s.index===2&&s.power){s.reverse=!s.reverse;if(s.reverse&&s.diode==='forward')s.tested=true;}
   else if(s.index===3){if(s.power){s.power=false;s.elapsed=0;s.running=true;}else{s.power=true;s.elapsed=0;s.running=false;}}
   else if(s.mos&&s.power){s.gate=!s.gate;if(s.gate)s.sawOn=true;else if(s.sawOn)s.sawOff=true;}
  }else if(type==='tick'&&s.index===3&&s.running&&Number.isFinite(value)&&value>0){s.elapsed=Math.min(2,s.elapsed+Math.min(value,.5));if(s.elapsed>=2)s.running=false;}
  return judge(s);
 }
 const api=Object.freeze({key,chapters,resistors:Object.freeze(resistors),capacitors:Object.freeze(capacitors),setup,restore,validateRecord,record,result,passed,action});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingNightlightMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);
