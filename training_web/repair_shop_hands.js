/* Bounded interaction progress, not screw torque or a soldering thermal model. */
(function(root){
 'use strict';
 const STEPS=Object.freeze([
  {op:'remove',title:'拆下旧件',body:'确认断电放电，模拟解除焊接并取下旧件，旧件留在桌上。'},
  {op:'clean',title:'清理并检查焊盘',body:'模拟清理后确认焊盘完整、没有连锡；不提供真实温度、溶剂或加热时长。'},
  {op:'orient',title:'核对位号和方向',body:'对照本板手册与极性/引脚标记，不凭外形相似判断方向。'},
  {op:'place',title:'放置并焊接新件',body:'模拟按已核对的焊盘和方向放置新件；动画不是实际焊接工艺验证。'},
  {op:'inspect',title:'检查焊点与邻近焊盘',body:'确认本关安装检查完成，再记账并进行电气复测。外观检查不等于功能合格。'}
 ]);
 const createService=(stockId,orientation)=>({stockId,orientation,index:0});
 const nextService=s=>STEPS[s?.index]||{op:'finish',title:'确认更换并记账',body:'分步换件检查已完成；确认安装后才扣备件金币，仍需通电复测。'};
 function service(s,op){if(!s||op!==nextService(s).op||s.index>=STEPS.length)return null;return {...s,index:s.index+1};}
 const tool=key=>({key,turns:0,active:false,complete:false});
 function turn(s,amount){if(!s||s.complete||!Number.isFinite(amount)||amount<0)return s;const turns=Math.min(2,s.turns+Math.min(.25,amount));return {...s,turns,complete:turns>=2-1e-8,active:turns<2-1e-8&&s.active};}
 const tick=(s,ms)=>s?.active?turn(s,Math.max(0,Math.min(100,ms))/800):s;
 const api=Object.freeze({STEPS,createService,nextService,service,tool,turn,tick});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopHands=api;
})(typeof globalThis!=='undefined'?globalThis:this);
