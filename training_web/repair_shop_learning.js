/* Read-only progression and transfer questions; never award currency or answer for players. */
(function(root){
 'use strict';
 function support(completed,preference='auto'){
  const level=['full','steps','off'].includes(preference)?preference:completed===0?'full':completed===1?'steps':'off';
  return {level,label:{full:'详细带做',steps:'目标提示',off:'独立诊断'}[level],stage:Math.min(3,Math.max(1,completed+1))};
 }
 const questions={
  lamp:['另一盏灯使用相同电源和LED，把限流电阻从220Ω换成440Ω，怎样判断？',['电流会减小，但不能忽略LED的非线性就断言精确减半','电流必定完全不变','阻值越大，LED电流越大'],'串联回路满足KVL；增大限流电阻会降低电流，LED正向压降也随电流变化。额定功率不是阻值。'],
  fan:['新MOS的数据表阈值电压只有2V，但RDS(on)仅在10V下保证，本板驱动4.5V。能直接替换吗？',['不能仅凭阈值；还要核对4.5V驱动下的导通性能、引脚和额定值','阈值低于4.5V就一定能带动电机','只要封装相同就行'],'阈值不是充分导通条件。必须按实际栅极驱动和负载核对保证值，而不是只比较VGS(th)。'],
  speaker:['另一块音箱板电容容量接近标称，但大负载时供电纹波明显增大，应该怎样排查？',['结合ESR、供电源阻抗和负载波形继续测量','容量正常就能排除电容故障','直接换成任意更大容量就能保证稳定'],'容量与ESR是不同参数；还应核对电源和负载。容量更大不等于无条件兼容，也不能单凭纹波就锁定电容。'],
  clock:['另一块板的RESET只有一个上拉电阻，芯片输入近似高阻。电阻开路后，RESET一定是0V吗？',['不一定；节点浮空，需结合漏电、仪表加载和电路条件判断','一定为0V','一定仍是3.3V'],'失去唯一上拉后，理想高阻节点电位不确定；真实读数还受漏电、寄生与仪表输入阻抗影响。'],
  sensor:['另一块传感器板的稳压输出偏低，就能判定LDO坏了吗？',['不能；先比较输入、使能及输出负载，再隔离排查','可以，输出低只可能是LDO坏','只要换更高输出电压的LDO就行'],'负载短路、限流、输入或使能异常也会使输出偏低。需要测量和隔离证据，不能盲目更改供电电压。'],
  router:['同为10µH的替代电感，其DCR明显更大，可以只按电感量选吗？',['不行；还要核对DCR、饱和电流、温升电流、封装和电路条件','可以，电感量一样就完全相同','DCR越大，损耗一定越低'],'绕组直流损耗与I²R有关。同电感量并不保证电流能力、损耗或动态表现相同。']
 };
 function quiz(job){const q=questions[job.product.id],shift=job.seed%3,options=q[1].map((text,i)=>({id:'q'+i,text,correct:i===0}));return {id:job.product.id+'-transfer-v1',question:q[0],options:[...options.slice(shift),...options.slice(0,shift)],explanation:q[2]};}
 const goals={
  '安全拆装':'确认断电并处理残余电荷，再按结构顺序拆卸。',
  '选择拆装工具':'选择合适工具，避免跳过固定件。','拆装与归位':'沿结构顺序处理固定件与连接线，保留拆下的零件。',
  '选择测量目标':'根据客人描述和手册决定先查哪个区域。','通电观察':'用正确档位与接点记录电压，比较正常参考。',
  '观察工作状态':'记录负载下的运行表现，静态电压不能覆盖所有故障。','断电检测':'先断电放电，再隔离元件检查。',
  '检查器件本身':'比较实测与手册允许范围，不要只凭外观。','依据证据判断':'把通电现象与隔离检测结合，再自行选择位号及失效类型。',
  '核对备件':'比较参数、封装、引脚及兼容条件，不按价格猜答案。','核对极性':'对照本板标记确认方向。','执行维修':'核对安全状态后安装已选备件。',
  '安全换件':'关闭电源并放电，不能带电拆换。','维修后验证':'检查规定负载及验收限值；安装成功不代表修复成功。',
  '成品复测':'结构与接线复原后，再检验已建模项目。','交付结算':'核对验收与维修报告后交付。','复盘与迁移':'回看测量证据和换件理由，尝试换情境练习。'
 };
 function brief(g){return {...g,title:g.group,body:goals[g.group]||'根据维修手册决定下一步；需要时可展开详细操作。'};}
 const api=Object.freeze({VERSION:1,support,quiz,brief});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RepairShopLearning=api;
})(typeof globalThis!=='undefined'?globalThis:this);
