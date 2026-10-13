/* 26 distinct teaching experiments. Explicit conditions, never vendor ratings. */
(function(root){
 'use strict';
 const C=typeof module!=='undefined'&&module.exports?require('./training_catalog.js'):root.TrainingCatalog;
 const profiles={};
 const field=(key,label,options)=>({key,label,options});
 const mission=(title,goal,setup,check,learned,hint)=>({title,goal,setup,check,learned,hint});
 const n=(v,u)=>Number(v.toPrecision(5))+' '+u,near=(a,b)=>Math.abs(a-b)<1e-9;
 const result=(values,metrics,story,visual={})=>({values,metrics,story,visual:{known:true,active:true,brightness:.5,heat:0,flow:'current',...visual}});
 function add(id,topology,title,fields,note,calculate,missions){profiles[id]={id,topology,title,fields,note,calculate,missions};}
 const temp=field('temperature','升温幅度',[[0,'不升温'],[40,'升高40 K'],[80,'升高80 K']]);
 add('res-thin','series','让精密读数少漂一点',[
  field('tcr','电阻温漂',[[5,'5 ppm/K'],[25,'25 ppm/K'],[100,'100 ppm/K']]),temp
 ],'题设R₀=1 kΩ、测量电流1 mA，用线性TCR计算。温漂不是初始精度；实际温度曲线请按具体型号确认。',p=>{
  const drift=1000*p.tcr*1e-6*p.temperature;
  return result({drift,resistance:1000+drift},[['阻值',n(1000+drift,'Ω')],['温漂造成的变化',n(drift,'Ω')]],'升温使本例阻值增加；换低TCR可减少漂移。保护层印字不会消除温漂。',{current:.001,heat:p.temperature/160,brightness:1-drift/10,flow:'measurement'});
 },[
  mission('让温漂现形','升温至少40 K，看阻值比1 kΩ增加。',{tcr:25,temperature:0},(p,r)=>p.temperature>=40&&r.drift>=1-1e-9,'温度变化会改变阻值，初始精度不能替代TCR。','点“升高40 K”，再开始观察。'),
  mission('守住精密读数','保持升温80 K，换电阻，把变化降到0.5 Ω以内。',{tcr:100,temperature:80},(p,r)=>p.temperature===80&&r.drift<=.5,'同样升温，低TCR电阻的读数变化更小。','温度不动，试更低的TCR。'),
  mission('把环境恢复','让升温幅度回到0 K，看看题设温漂项归零。',{tcr:25,temperature:80},(p,r)=>p.temperature===0&&r.drift===0,'环境恢复时，这个线性温漂项归零；长期漂移和初始误差仍是另外的事。','恢复温度，不必猜阻值。')
 ]);
 add('res-sense','series','用小电压看见大电流',[
  field('resistance','采样阻值',[[5,'5 mΩ'],[10,'10 mΩ'],[50,'50 mΩ']]),field('load','被测电流',[[.5,'0.5 A'],[1,'1 A'],[2,'2 A']])
 ],'理想V=IR、P=I²R，未计接触电阻。测量线是高阻采样输入，不是另一条负载回路。',p=>{
  const voltage=p.load*p.resistance/1000,loss=p.load*p.load*p.resistance/1000;
  return result({voltage,loss},[['采样电压',n(voltage*1000,'mV')],['电阻损耗',n(loss*1000,'mW')]],'电流经过小阻值产生小压差，测量电路读这个压差；它也带来损耗。',{current:p.load,voltage,heat:loss*5,flow:'measurement'});
 },[
  mission('电流变大，读数怎样变','保持10 mΩ，把被测电流加到2 A，看到20 mV。',{resistance:10,load:.5},(p,r)=>p.resistance===10&&p.load===2&&near(r.voltage,.02),'同一采样阻值下，电流加倍，采样电压也加倍。','调被测电流，看右边读数。'),
  mission('少一点额外损耗','保持2 A，把采样损耗降到20 mW以内，电压仍要可测。',{resistance:50,load:2},(p,r)=>p.load===2&&r.loss<=.020001&&r.voltage>0,'更小的采样阻值损耗更低，但信号也更小，测量精度要一起考虑。','试较小阻值，不要把电流改小来绕过目标。'),
  mission('测小电流','保持10 mΩ，把电流降到0.5 A，观察5 mV信号。',{resistance:10,load:2},(p,r)=>p.resistance===10&&p.load===.5&&near(r.voltage,.005),'小电流的压差信号也更小，连接及测量电路的误差更不能忽略。','降低被测电流。')
 ]);
 add('res-sulfur','series','给端接选对环境防护',[
  field('design','端接设计', [['ordinary','普通声明示例'],['resistant','带耐硫化声明示例']]),field('environment','环境', [['clean','一般环境'],['sulfur','含硫环境要求']])
 ],'定性对比端接设计与环境要求。不预测硫化速率、实际寿命或通断，不把一项声明当作整机合格。',p=>result({requirement:p.environment==='sulfur',dedicated:p.design==='resistant'},[['环境',p.environment==='sulfur'?'需确认耐硫化':'一般环境'],['端接',p.design==='resistant'?'专用声明示例':'普通声明示例']],'本图橙色提示的是环境要求，不是已经损坏。专用设计也要核对厂商试验和电气参数。',{current:.001,flow:'environment',warning:p.environment==='sulfur'&&p.design==='ordinary',protected:p.design==='resistant'}),[
  mission('把环境要求显出来','切到含硫环境，看普通端接为什么需要进一步核对。',{design:'ordinary',environment:'clean'},(p,r)=>r.requirement&&!r.dedicated,'含硫环境是新的可靠性要求，不能凭普通阻值与尺寸就宣布可替代。','切换环境，再看橙色提示。'),
  mission('补上专用声明','保持含硫环境，换成带耐硫化声明的端接示例。',{design:'ordinary',environment:'sulfur'},(p,r)=>r.requirement&&r.dedicated,'耐硫化是端接和防护的可靠性特性，不是新的阻值单位。','换端接设计，看防护标识出现。'),
  mission('区别作用与环境要求','换回一般环境和普通示例，观察它仍有电阻的基本作用。',{design:'resistant',environment:'sulfur'},(p,r)=>!r.requirement&&!r.dedicated,'抗硫化不替代基本电气参数；一般环境也需核对完整工作条件。','环境与端接设计各改一次。')
 ]);
 add('cap-aluminum','parallel','让电解电容少一点纹波损耗',[
  field('esr','ESR',[[.05,'0.05 Ω'],[.2,'0.2 Ω'],[1,'1 Ω']]),field('ripple','纹波有效值',[[.5,'0.5 A'],[1,'1 A'],[2,'2 A']])
 ],'P=Iᵣₘₛ²×ESR。只比较纹波损耗，热光不是温度；输出总纹波、温升或寿命需另行核对。供电蓝线与纹波支路橙线分开。',p=>{
  const loss=p.ripple*p.ripple*p.esr;
  return result({loss},[['纹波损耗',n(loss,'W')],['纹波有效值',n(p.ripple,'A')]],'纹波电流流过ESR会产生损耗。更大纹波或更高ESR，发热负担更大；这里不推算温度和寿命。',{current:p.ripple,storage:p.ripple,heat:Math.min(1,loss),flow:'ripple'});
 },[
  mission('看纹波带来的负担','保持0.2 Ω，把纹波加到2 A，观察损耗增加到0.8 W。',{esr:.2,ripple:.5},(p,r)=>p.esr===.2&&p.ripple===2&&near(r.loss,.8),'损耗随电流平方增加，不是纹波加倍就只多一倍。','增加纹波，看橙色支路和损耗。'),
  mission('在同样纹波下减损耗','保持2 A，换ESR，把损耗降到0.25 W以内。',{esr:1,ripple:2},(p,r)=>p.ripple===2&&r.loss<=.25,'低ESR能减少这一项纹波损耗，寿命仍需看温度和系列条件。','纹波保持不变，试低ESR。'),
  mission('降低纹波也有效','保持0.2 Ω，把纹波降到0.5 A，让损耗不超过0.05 W。',{esr:.2,ripple:2},(p,r)=>p.esr===.2&&p.ripple===.5&&r.loss<=.050001,'改善电路纹波和换低损耗器件是两种不同的办法。','这次只调纹波。')
 ]);
 add('cap-safety','safety','把X与Y放到正确位置',[
  field('category','类别示例',[['X','X类'],['Y','Y类']]),field('position','应用位置',[['line','线与线之间'],['earth','线与保护接地等位置']])
 ],'隔离的虚拟教学板，没有实际市电。只学习常见位置，不能凭X/Y名称判断实际设备认证、安全或完整接线。',p=>result({match:p.category===(p.position==='line'?'X':'Y')},[['当前类别',p.category+'类示例'],['位置',p.position==='line'?'线间':'线与接地等位置']],'线间常见X类；线与保护接地等位置常见Y类。两种认证与故障要求不同，不能随意替换。',{flow:'position',warning:p.category!==(p.position==='line'?'X':'Y'),position:p.position}),[
  mission('先放在线间','把虚拟位置放在线与线之间，并选X类示例。',{category:'Y',position:'earth'},(p,r)=>p.position==='line'&&r.match,'X类的常见位置是线间；这个模型不是带电接线指导。','先看两端连接到哪里，再选类别。'),
  mission('改到接地支路','把位置改为线与接地等位置，并选Y类示例。',{category:'X',position:'line'},(p,r)=>p.position==='earth'&&r.match,'位置改变后，类别要求也变了，还必须核对设备标准与认证等级。','位置和类别都要改变。'),
  mission('两项一起复核','从当前接地支路返回线间X类位置，确认不能只换名称。',{category:'Y',position:'earth'},(p,r)=>p.position==='line'&&p.category==='X','实际替代要同时看位置、等级、额定值和认证，不能只看容量。','观察3D上的第二根线移动到哪里。')
 ]);
 add('cap-film','parallel','把脉冲电流变温和',[
  field('capacitance','容量',[[.1,'0.1 µF'],[.22,'0.22 µF'],[1,'1 µF']]),field('slew','电压变化率',[[10,'10 V/µs'],[50,'50 V/µs'],[100,'100 V/µs']])
 ],'理想I=C×dV/dt，显示给定斜坡段的电流。实际脉冲承受能力、自愈与可靠性请按具体系列确认。',p=>{
  const current=p.capacitance*p.slew;
  return result({current},[['斜坡段电流',n(current,'A')],['电压变化率',n(p.slew,'V/µs')]],'同样容量，电压变化更快，需要更大电流；同样变化率，容量更大，电流也更大。',{current,storage:current,flow:'charge',brightness:Math.min(1,current/10)});
 },[
  mission('放慢变化','保持0.1 µF，把斜坡电流降到1 A。',{capacitance:.1,slew:100},(p,r)=>p.capacitance===.1&&near(r.current,1),'放慢电压变化，电容支路的充放电电流随之减小。','只调电压变化率。'),
  mission('容量也会影响电流','保持10 V/µs，换到1 µF，观察10 A的题设电流。',{capacitance:.1,slew:10},(p,r)=>p.slew===10&&p.capacitance===1&&near(r.current,10),'容量更大，不代表脉冲电流一定更小；要核对端接与允许脉冲。','把容量增大，观察同一斜坡。'),
  mission('按这次电路目标换容量','保持50 V/µs，把题设支路电流限制在5 A以内。',{capacitance:1,slew:50},(p,r)=>p.slew===50&&r.current<=5,'先知道电路如何变化，再检查具体型号能否承担所需电流。','变化率固定，试小容量。')
 ]);
 add('cap-tantalum','parallel','先看极性，再看储能',[
  field('forward','极性',[[true,'正端接正电源'],[false,'正端接负端']]),field('capacitance','有效容量',[[1,'1 µF'],[10,'10 µF'],[22,'22 µF']])
 ],'有极性钽示例。初始5 V，电源维持5 mA，芯片新增20 mA由电容补50 µs，ΔV=IΔt/C；观察结束后定格在补电终点，不是无限供电。接反时不预测电流/损坏。忽略ESR与供电动态。', (p,t)=>{
  const voltage=5-.02*50e-6/(p.capacitance*1e-6)*t;
  return result({voltage:p.forward?voltage:null,drop:p.forward?5-voltage:null},[['供电电压',p.forward?n(voltage,'V'):'接反：不作正常预测'],['有效容量',n(p.capacitance,'µF')]],p.forward?'电容临时补电，放出的电流经过芯片并返回电容；容量越小，电压下降越多。':'有极性钽不能任意反接。先修正正负端，错误方向不能作正常供电预测。',{known:p.forward,active:p.forward,current:.005,source:.005,load:p.forward?.025:null,storage:p.forward?-.02:null,brightness:p.forward?voltage/5:0,flow:'discharge',warning:!p.forward});
 },[
  mission('先修正极性','把电容正端接回正电源，再观察补电。',{forward:false,capacitance:10},p=>p.forward,'外壳形状不能替代极性标记；有极性器件要先核对方向。','点击正确极性，再启动。'),
  mission('守住4.9 V','极性保持正确，换容量，让本次补电结束仍至少4.9 V。',{forward:true,capacitance:1},(p,r)=>p.forward&&r.voltage>=4.9-1e-9,'同样补电需求下，较大的有效容量电压下降更小。','看供电读数，尝试更大容量。'),
  mission('看见容量不足的后果','保持正确极性，换1 µF，观察题设电压降到4 V。',{forward:true,capacitance:22},(p,r)=>p.forward&&p.capacitance===1&&near(r.voltage,4),'这次是观察不足，不是推荐这样选型；容量、极性、降额和浪涌条件都要确认。','只换小容量，观察完整补电。')
 ]);
 add('ind-layered','series','让高频信号和低频信号分开',[
  field('inductance','电感量',[[.1,'0.1 µH'],[1,'1 µH'],[10,'10 µH']]),field('frequency','输入频率',[[1e4,'10 kHz'],[1e5,'100 kHz'],[1e6,'1 MHz']])
 ],'理想串联L、负载100 Ω，输出比R/√(R²+(2πfL)²)。忽略DCR、材料损耗及寄生，不在SRF附近外推。',p=>{
  const reactance=2*Math.PI*p.frequency*p.inductance*1e-6,gain=100/Math.hypot(100,reactance);
  return result({reactance,gain},[['理想感抗',n(reactance,'Ω')],['输出幅度比',n(gain*100,'%')]],'频率越高或电感量越大，本例感抗越大，负载上的交流幅度越小；不是把电流吃掉。',{current:.05*gain,flow:'ac',brightness:gain,inputFrequency:p.frequency});
 },[
  mission('削弱这次高频分量','保持1 MHz，把输出幅度比降到85%以下。',{inductance:.1,frequency:1e6},(p,r)=>p.frequency===1e6&&r.gain<=.85,'电感可在特定电路中帮助滤波，但必须带使用频率看阻抗。','频率不动，增大电感。'),
  mission('让低频通过','保持10 µH，降低频率，让输出幅度比至少99%。',{inductance:10,frequency:1e6},(p,r)=>p.inductance===10&&r.gain>=.99,'同一个电感对不同频率有不同的影响。','试低频，比较输出。'),
  mission('同频率比较不同L','保持1 MHz，换小电感，让输出至少99%。',{inductance:10,frequency:1e6},(p,r)=>p.frequency===1e6&&r.gain>=.99,'结构名称不是频率性能保证，实际还要看Q、SRF和曲线。','这次频率固定，只换L。')
 ]);
 add('ind-molded','series','大电流也要看磁性能边界',[
  field('isat','题设Isat',[[2,'2 A示例'],[4,'4 A示例']]),field('load','工作电流',[[.5,'0.5 A'],[1,'1 A'],[3,'3 A']])
 ],'DCR=0.1 Ω示例，铜损I²DCR；达到Isat仅标明磁性能判据，不推算L下降、后续波形、温升或损坏。',p=>{
  const loss=p.load*p.load*.1,boundary=p.load>=p.isat;
  return result({loss,boundary},[['直流铜损',n(loss,'W')],['磁性能边界',boundary?'触及题设Isat；L变化另查':'低于题设Isat']],'一体成型仍有磁性能与热限制。Isat和直流铜损是两项不同的检查；电流是给定条件，并没有据固定L预测后续波形。',{current:p.load,flow:'magnetic',heat:loss,warning:boundary});
 },[
  mission('看见磁性能边界','保持Isat=2 A，把工作电流加到3 A，观察边界提示。',{isat:2,load:.5},(p,r)=>p.isat===2&&r.boundary,'触及Isat不是器件烧毁动画，也不能继续当作固定L预测。','把工作电流加大，别猜温度。'),
  mission('换回边界以内','保持3 A，换题设Isat，让工作点低于该判据。',{isat:2,load:3},(p,r)=>p.load===3&&!r.boundary,'峰值工作点和磁性能判据要匹配，之后仍要检查铜损与温升。','工作电流不变，换更高的Isat示例。'),
  mission('把铜损降下来','保持Isat=4 A，把工作电流降到1 A以内，铜损不超过0.1 W。',{isat:4,load:3},(p,r)=>p.isat===4&&r.loss<=.100001,'磁性能满足不代表没有发热，工作电流降低也会减少铜损。','这次调工作电流。')
 ]);
 add('ind-common','common','看两根线的磁通怎样相加',[
  field('mode','电流模式',[['common','同向共模'],['differential','等大反向差模']]),field('installed','共模磁路',[[false,'移除共模磁路'],[true,'装回共模电感']])
 ],'正确绕向下的理想平衡对比。紫色仅表示磁通趋势，不给出抑制dB或保证完全无差模阻抗；两绕组电气独立。',p=>{
  const flux=p.installed?(p.mode==='common'?2:0):0;
  return result({flux},[['共享磁芯趋势',!p.installed?'未接入':flux?'磁通叠加':'理想磁通抵消'],['电流模式',p.mode==='common'?'同向':'等大反向']],'两绕组共享磁路，但不是两根线短接。共模磁通叠加，理想平衡差模磁通抵消。',{flow:'common',flux,common:p.mode==='common',installed:p.installed});
 },[
  mission('让两根线同向','装有共模电感时切到同向共模，观察紫色磁通叠加。',{mode:'differential',installed:true},(p,r)=>p.installed&&r.flux===2,'电流方向与绕向决定磁通趋势，不是只看器件名字。','改变电流模式。'),
  mission('装回共享磁路','保持同向模式，装回共模电感，比较是否出现共享磁通。',{mode:'common',installed:false},(p,r)=>p.installed&&r.flux===2,'共享磁路使共模变化建立反对变化的作用；实际抑制能力需看频率曲线。','装回共模磁路。'),
  mission('让理想差模通过','保持电感接入，改成等大反向差模，观察共享磁通抵消。',{mode:'common',installed:true},(p,r)=>p.installed&&r.flux===0,'抵消指理想平衡共享磁通；漏感和寄生仍可能影响差模信号。','看两条箭头方向改变。')
 ]);
 add('xtal-passive','clock','给无源晶体一个振荡伙伴',[
  field('amplifier','外部振荡电路',[[false,'未接入'],[true,'接入振荡放大器']]),field('load','C1/C2各为',[[15,'15 pF'],[20,'20 pF'],[30,'30 pF']])
 ],'CL≈C1C2/(C1+C2)+2 pF，题设目标9.5 pF。接入放大器后的时钟假设其余起振/驱动条件已满足；CL匹配本身不保证起振。',p=>{
  const cl=p.load/2+2;
  return result({cl,clock:p.amplifier},[['有效CL',n(cl,'pF')],['时钟',p.amplifier?'放大器输出示意':'没有维持振荡的电路']],'无源晶体提供谐振选择，放大器提供维持能量。时钟从振荡电路输出，不从晶体独立产生。',{flow:'clock',active:p.amplifier,clock:p.amplifier,powered:p.amplifier,matched:near(cl,9.5),brightness:p.amplifier?.6:0});
 },[
  mission('接上伙伴','接入外部振荡电路，看到绿色时钟示意。',{amplifier:false,load:20},(p,r)=>r.clock,'无源晶体不能脱离振荡电路持续独立输出时钟。','接入振荡放大器，再启动观察。'),
  mission('配对负载电容','保持振荡电路接入，把有效CL调到题设9.5 pF。',{amplifier:true,load:30},(p,r)=>r.clock&&near(r.cl,9.5),'CL由两电容和寄生共同形成，不是直接等于其中一颗的容量。','试不同C1/C2，看有效CL。'),
  mission('移除维持能量的伙伴','移除外部振荡电路，确认晶体本身不继续送时钟。',{amplifier:true,load:15},(p,r)=>!r.clock,'没有持续能量与反馈，不能把无源晶体当作XO使用。','移除振荡放大器，观察绿色脉冲停止。')
 ]);
 add('xtal-active','clock','让时钟跟着供电和使能变化',[
  field('vdd','模块供电',[[false,'没有VDD'],[true,'正常VDD']]),field('oe','输出使能',[[false,'OE关闭'],[true,'OE使能']])
 ],'题设满足接口条件的24 MHz XO，未使能时本例无有效时钟；实际OE/ST输出状态、启动时间依系列。绿色是信号，不是负载供电电流。',p=>{
  const clock=p.vdd&&p.oe;
  return result({clock,powered:p.vdd},[['时钟输出',clock?'24 MHz（题设）':'本例无有效时钟'],['周期',clock?'41.667 ns':'—']],'蓝色VDD/GND为模块供能，绿色OUT向芯片送时钟。供电与使能是两个条件。',{flow:'clock',clock,active:clock,powered:p.vdd,frequency:clock?24e6:0,brightness:clock?.8:0});
 },[
  mission('先给模块供电','打开VDD，但保持OE关闭，观察有供电还没有有效时钟。',{vdd:false,oe:false},(p,r)=>r.powered&&!r.clock,'已供电不代表输出已经使能。','先只打开VDD，不要改OE。'),
  mission('送出时钟','保持VDD正常，再使能OE，让芯片收到时钟。',{vdd:true,oe:false},(p,r)=>r.clock,'XO内部电路维持振荡并驱动OUT，不是无源晶体的两信号脚。','打开OE，再观察绿色脉冲。'),
  mission('只停止输出','VDD保持正常，关闭OE，让绿色时钟停止。',{vdd:true,oe:true},(p,r)=>r.powered&&!r.clock,'控制输出和断电不同；真实器件未使能状态要按具体规格书。','只关OE，看看蓝色供电仍保留。')
 ]);
 add('xtal-tcxo','clock','把升温后的频偏缩小',[
  field('design','时钟模块示例',[['basic','未补偿示例'],['compensated','温补示例']]),field('temperature','环境对比点',[[25,'25 ℃参考点'],[85,'85 ℃对比点']])
 ],'26 MHz参考；题设85 ℃相对参考点未补偿+20 ppm、已补偿+2.5 ppm。只是两个对比工作点，不是厂商温度曲线，也不是可切换的TCXO引脚。',p=>{
  const ppm=p.temperature===25?0:p.design==='compensated'?2.5:20,offset=26*ppm;
  return result({ppm,offset},[['相对参考频偏',n(offset,'Hz')],['题设频偏',n(ppm,'ppm')]],'温补示例减小这个温度点的频偏，并没有把误差变为零；绿色时钟相对黄色参考的差异已放大。',{flow:'clock',clock:true,frequency:26e6+offset,offset,temperature:p.temperature,brightness:1-ppm/25});
 },[
  mission('升温看偏移','未补偿示例保持不变，切到85 ℃，看到520 Hz频偏。',{design:'basic',temperature:25},(p,r)=>p.design==='basic'&&p.temperature===85&&near(r.offset,520),'环境变化可以影响时钟频率，频率相同不代表温度稳定度相同。','先升温，比较绿色与黄色参考。'),
  mission('缩小频偏','保持85 ℃，换温补示例，让频偏不超过65 Hz。',{design:'basic',temperature:85},(p,r)=>p.temperature===85&&r.offset<=65,'本例温补减小了偏移，但仍有非零频偏；老化等误差另查。','环境不动，换时钟模块示例。'),
  mission('回到参考点','保持温补示例，返回25 ℃参考点，观察相对偏移归零。',{design:'compensated',temperature:85},(p,r)=>p.design==='compensated'&&p.temperature===25&&r.offset===0,'归零只指本例相对参考点，不等于真实器件总误差为零。','把环境返回参考点。')
 ]);
 add('xtal-vcxo','clock','把时钟微调到目标附近',[
  field('offset','题设调谐位置',[[-50,'下偏50 ppm'],[0,'中心位置'],[50,'上偏50 ppm']])
 ],'中心26 MHz，三档为给定频偏位置，非实际控制电压曲线。只做Δf=f₀×ppm/10⁶换算；图中频率差异放大慢放。',p=>{
  const offset=p.offset*26;
  return result({offset,frequency:26e6+offset},[['频率',n((26e6+offset)/1e6,'MHz')],['相对中心偏移',n(offset,'Hz')]],'VCXO在规定范围微调频率，不是任意频率发生器；控制规律要按型号确认。',{flow:'clock',clock:true,frequency:26e6+offset,offset,brightness:.8});
 },[
  mission('向低处微调','把频率调到25.9987 MHz，观察相对中心变慢。',{offset:0},(p,r)=>near(r.frequency,25998700),'有限负频偏会使本例输出略慢，图中的差异已放大。','试下偏档，观察频率读数。'),
  mission('向高处微调','把频率调到26.0013 MHz，观察相对中心变快。',{offset:-50},(p,r)=>near(r.frequency,26001300),'正频偏把输出调高，但范围不是无限的。','试上偏档。'),
  mission('回到中心','把输出恢复到26 MHz中心频率。',{offset:50},(p,r)=>near(r.frequency,26e6),'牵引范围、中心频率和温度补偿是不同的规格。','返回中心位置。')
 ]);
 const mosFields=[field('drive','相对源极的栅驱动',[[0,'VGS=0'],[2.5,'|VGS|=2.5 V'],[10,'|VGS|=10 V']]),field('load','题设负载电流',[[1,'1 A'],[2,'2 A'],[3,'3 A']])];
 for(const id of ['mos-n','mos-p']){
  const high=id==='mos-p';
  add(id,high?'switch-high':'switch-low',high?'用负VGS控制高边供电':'用栅压控制低边回路',mosFields,
   '12 V供电示例。Ron=20 mΩ仅在正确极性|VGS|=10 V给出；2.5 V不预测负载电流，0 V为本例关断。忽略体二极管、栅电荷瞬态及开关损耗。',p=>{
    const known=p.drive!==2.5,on=p.drive===10,loss=on?p.load*p.load*.02:null;
    return result({on,known,loss,vgs:high?-p.drive:p.drive},[['VGS',n(high?-p.drive:p.drive,'V')],['导通损耗',on?n(loss,'W'):known?'本例关断':'Ron未提供，不预测']],'看栅极相对源极的电位，不只看对地电压。超过阈值不能单独保证充分导通。',{known,active:on,current:on?p.load:0,heat:loss||0,brightness:on?.8:0,flow:'gate',unknown:!known,gate:on});
   },[
    mission(high?'从供电侧打开负载':'从返回侧打开负载','负载现在没有工作。改变控制端的驱动，让本例已知导通的档位接通主回路。',{drive:0,load:2},(p,r)=>r.on,'控制端的电场改变沟道，负载能量仍来自电源；N与P沟道的驱动极性不同。','选择“本例已知导通”档；N沟道为+10 V，P沟道为−10 V，都是G相对于S。'),
    mission('驱动变弱，还能保证吗？','保持同样负载，换到“较弱”驱动，观察为什么结果变成未知，而不是直接显示零电流。',{drive:10,load:2},(p,r)=>!r.known,'缺少这个工作点的导通电阻，不能把阈值当作低阻保证，也不能编造负载电流。','选“较弱”驱动，看黄色提示和“不预测”；这不等于器件完全关断。'),
    mission('负载少用电，发热会怎样？','驱动条件保持不变。把负载需求降到1 A，观察导通损耗降到20 mW以内。',{drive:10,load:3},(p,r)=>r.on&&r.loss<=.020001,'相同导通电阻，电流减小时导通损耗变小；真实选型还要看结温、SOA和切换条件。','控制端不动，这次只降低负载需要的电流。')
   ]);
 }
 add('mos-dual','switch-low','同时检查两颗MOS',[
  field('gates','背靠背双N示例',[['none','两颗关闭'],['one','只驱动一颗'],['both','两颗充分驱动']]),field('load','题设电流',[[1,'1 A'],[2,'2 A'],[3,'3 A']])
 ],'背靠背双N通道示例，两管开启时各20 mΩ。单管开启可能涉及体二极管，不预测此时电流；两管关闭按未击穿、忽略漏电处理。不是所有双MOS的内部连接。',p=>{
  const on=p.gates==='both',known=p.gates!=='one',loss=on?p.load*p.load*.04:null;
  return result({on,known,loss},[['两个通道',on?'都开启':known?'都关闭':'仅一个：需查完整电路'],['导通损耗',on?n(loss,'W'):'本例不预测']],'两颗集成不等于并联。这个背靠背示例要共同检查两个通道和体二极管方向。',{active:on,known,current:on?p.load:0,flow:'gate',heat:loss||0,brightness:on?.8:0,unknown:!known,gate:on});
 },[
  mission('先让两颗关闭','从单颗驱动状态关闭两颗，观察本例阻断状态。',{gates:'one',load:2},(p,r)=>p.gates==='none'&&r.known&&!r.on,'一颗关闭不能脱离体二极管和互连判断；这里先看两管关闭。','选择两颗关闭，再观察。'),
  mission('共同开启通道','让两颗都充分驱动，看到题设串联通道工作。',{gates:'none',load:2},(p,r)=>r.on,'本例两颗串联，通道电阻相加；双MOS不能一律按并联计算。','同时驱动两颗。'),
  mission('减少串联损耗','两颗保持开启，把电流降到1 A，使损耗不超过0.04 W。',{gates:'both',load:3},(p,r)=>r.on&&r.loss<=.040001,'集成省空间，不消除两通道损耗和热耦合。','这次只调题设电流。')
 ]);
 add('dio-rectifier','series','让交流只留下一个半周',[
  field('forward','二极管方向',[[true,'放行正半周'],[false,'放行负半周']]),field('load','负载电阻',[[100,'100 Ω'],[1000,'1 kΩ']])
 ],'输入峰值5 V的正弦，固定Vf=0.7 V，理想半波输出，未加滤波或稳压。动画显示慢放的正负周期，不按实际频率。',p=>{
  const peak=p.forward?4.3:-4.3,current=peak/p.load;
  return result({peak,current},[['输出峰值',n(peak,'V')],['电流峰值',n(current*1000,'mA')]],'一颗二极管按方向放行半周，输出仍然脉动；整流不是滤波或稳压。',{flow:'rectify',current,forward:p.forward,brightness:1,voltage:peak});
 },[
  mission('留下正半周','修正二极管方向，让输出只保留正半周。',{forward:false,load:1000},(p,r)=>r.peak>0,'正向半周超过压降后导通，另半周被本例阻断。','改变方向，观察输入蓝波与输出橙波。'),
  mission('反过来看负半周','翻转二极管，观察输出变成负半周，而不是稳定直流。',{forward:true,load:1000},(p,r)=>r.peak<0,'方向改变也改变输出极性，不能把有波形就当作正确供电。','翻转方向；这是观察错误极性，不是推荐接法。'),
  mission('限制正半周峰值电流','恢复正向，把峰值电流限制在5 mA以内。',{forward:false,load:100},(p,r)=>p.forward&&r.current>0&&r.current<=.005,'负载影响峰值电流；滤波、浪涌与恢复条件还需另外核对。','方向先恢复，再换较大的负载电阻。')
 ]);
 add('dio-schottky','series','在同一工作点比较导通损耗',[
  field('vf','题设工作点Vf',[[.3,'0.3 V'],[.5,'0.5 V'],[.7,'0.7 V']]),field('load','题设电流',[[.5,'0.5 A'],[1,'1 A'],[2,'2 A']])
 ],'5 V输入，在所选电流下给定Vf，P=IVf；不把三档当作同一真实器件的I-V曲线，温度、漏电与耐压须另查。',p=>{
  const loss=p.vf*p.load,voltage=5-p.vf;
  return result({loss,voltage},[['负载电压',n(voltage,'V')],['二极管损耗',n(loss,'W')]],'较小压降把更多电压留给负载，但仍有损耗。真实比较还要看相同电流、温度下的漏电和耐压。',{current:p.load,heat:Math.min(1,loss),voltage,brightness:voltage/5});
 },[
  mission('少一点压降损耗','保持1 A，把导通损耗降到0.35 W以内。',{vf:.7,load:1},(p,r)=>p.load===1&&r.loss<=.35,'必须在同一工作点比较Vf，不能脱离电流与温度。','电流不变，选低Vf工作点示例。'),
  mission('加电流看看损耗','保持Vf=0.3 V，把电流加到2 A，观察0.6 W损耗。',{vf:.3,load:.5},(p,r)=>p.vf===.3&&p.load===2&&near(r.loss,.6),'低Vf也不是无损耗，电流增大仍加重发热负担。','增加题设电流。'),
  mission('减少电流负担','保持Vf=0.3 V，把电流降到0.5 A，损耗不超过0.15 W。',{vf:.3,load:2},(p,r)=>p.vf===.3&&r.loss<=.150001,'损耗不等于温度，还要考虑封装与散热。','降低电流，看损耗光圈变弱。')
 ]);
 add('dio-zener','parallel','让限流与分流一起工作',[
  field('input','输入电压',[[3,'3 V'],[9,'9 V'],[12,'12 V']]),field('series','串联限流电阻',[[200,'200 Ω'],[1000,'1 kΩ'],[2000,'2 kΩ']])
 ],'理想Vz=5.1 V、RL=1 kΩ，先计算未钳位分压；稳压支路电流不足就不保持5.1 V。忽略动态电阻、测试电流下限与热。',p=>{
  const voltage=Math.min(5.1,p.input*1000/(p.series+1000)),load=voltage/1000,shunt=Math.max(0,(p.input-voltage)/p.series-load),loss=voltage*shunt;
  return result({voltage,shunt,loss},[['负载电压',n(voltage,'V')],['稳压支路电流',n(shunt*1000,'mA')],['稳压管损耗',n(loss*1000,'mW')]],shunt>0?'蓝色供负载，橙色走反向稳压支路；限流电阻决定支路能得到多少电流。':'输入或限流条件不足，本例不能保持5.1 V。',{flow:'shunt',current:load,shunt,voltage,heat:loss*5,brightness:voltage/5.1,regulated:shunt>0});
 },[
  mission('建立稳压支路','保持200 Ω，把输入提高，让负载得到5.1 V并有稳压支路电流。',{input:3,series:200},(p,r)=>p.series===200&&near(r.voltage,5.1)&&r.shunt>0,'稳压管需要合适的反向支路电流，不是无条件的理想电源。','提高输入，看橙色分流支路。'),
  mission('看看输入不足','保持200 Ω，把输入降到3 V，观察5.1 V不能维持。',{input:9,series:200},(p,r)=>p.input===3&&p.series===200&&r.voltage<5.1&&r.shunt===0,'输入不足时稳压支路不工作，不能承诺仍输出标称稳压值。','降低输入，观察支路停止。'),
  mission('减少稳压管负担','保持12 V，在仍有5.1 V输出与分流的前提下，把稳压管损耗降到20 mW以内。',{input:12,series:200},(p,r)=>p.input===12&&near(r.voltage,5.1)&&r.shunt>0&&r.loss<=.02,'增大限流电阻可降低支路损耗，但过大又可能失去稳压。','试不同限流阻值，同时看电压与支路电流。')
 ]);
 add('dio-tvs','parallel','不要把保持电压当钳位电压',[
  field('clamp','保护支路示例',[[0,'移除TVS'],[10,'10 V @ 1 A'],[6,'6 V @ 3 A']]),field('event','输入事件',[['normal','正常3.3 V'],['surge','12 V脉冲示例']])
 ],'脉冲源12 V、源阻抗2 Ω，芯片输入按高阻处理；给定两个钳位工作点，题设芯片允许峰值8 V。动态图重复示意同一脉冲，不代表连续稳压。不是完整TVS曲线，不保证器件承受能力；正常3.3 V下假设均不动作。',p=>{
  const voltage=p.event==='normal'?3.3:p.clamp||12,shunt=p.event==='surge'&&p.clamp?(12-p.clamp)/2:0;
  return result({voltage,shunt,within:voltage<=8},[['芯片端峰值',n(voltage,'V')],['脉冲分流',n(shunt,'A')]],p.event==='normal'?'正常信号下，本例TVS支路不动作。':'橙色是脉冲分流。保护后的电压要和芯片允许值比较，不能只看TVS名称或保持电压。',{flow:'shunt',current:0,shunt,voltage,warning:voltage>8,brightness:voltage<=8?.7:.1,heat:Math.min(1,shunt/3),pulse:p.event==='surge'});
 },[
  mission('看未保护的脉冲','保持TVS移除，模拟12 V脉冲，观察芯片端超过8 V。',{clamp:0,event:'normal'},(p,r)=>p.event==='surge'&&p.clamp===0&&!r.within,'没有保护支路时，本例脉冲直接到芯片端。','切换脉冲事件，观察峰值。'),
  mission('有钳位不等于够用','保持脉冲，装入10 V@1 A示例，看看为什么仍超过8 V。',{clamp:0,event:'surge'},(p,r)=>p.event==='surge'&&p.clamp===10&&r.shunt===1&&!r.within,'有分流不代表芯片得到足够低的电压，必须看VC@Ipp。','装入10 V工作点，比较芯片允许值。'),
  mission('按芯片端电压比较','保持脉冲，换示例，使芯片端峰值不超过8 V。',{clamp:10,event:'surge'},(p,r)=>p.event==='surge'&&r.shunt>0&&r.within,'更低钳位伴随更大的分流要求；脉冲波形、功率和器件承受能力仍要核对。','试另一个钳位工作点。')
 ]);
 add('dio-led','series','让发光电流刚刚好',[
  field('forward','LED方向',[[true,'正向接入'],[false,'反向接入']]),field('resistance','限流电阻',[[100,'100 Ω'],[330,'330 Ω'],[1000,'1 kΩ']])
 ],'5 V电源、蓝光LED Vf=3 V固定近似，I=(5−3)/R。反向按未击穿、忽略漏电；相对光强非实测光度，不判断真实额定安全。',p=>{
  const current=p.forward?2/p.resistance:0,brightness=Math.min(1,current/.02);
  return result({current,brightness},[['LED电流',n(current*1000,'mA')],['LED输入功率',n(current*3*1000,'mW')]],'LED把部分电能变成光，也会有热。方向正确还要限流，不能直接按Vf接电源。',{current,brightness,heat:current*3*3,flow:'led',active:p.forward});
 },[
  mission('修正LED方向','让LED正向接入，看到蓝光亮起。',{forward:false,resistance:330},(p,r)=>p.forward&&r.current>0,'LED也有方向，反向不发光不是限流问题。','先改方向，再启动。'),
  mission('柔和的提示光','保持正向，把电流调到5～8 mA。',{forward:true,resistance:100},(p,r)=>p.forward&&r.current>=.005&&r.current<=.008,'电流改变时光强趋势也变，不必背某一个电阻值。','换限流电阻，边看亮度边看电流。'),
  mission('低电流仍有光','保持发光，把题设电流降到3 mA以内。',{forward:true,resistance:330},(p,r)=>p.forward&&r.current>0&&r.current<=.003,'低电流会减少光和功耗，真实光学需求还要核对LED规格。','试更大阻值，不要用反接来过关。')
 ]);
 for(const id of ['bjt-npn','bjt-pnp']){
  const high=id==='bjt-pnp';
  add(id,high?'switch-high':'switch-low',high?'用相反极性的基流控制高边':'给基极足够的驱动',[
   field('base','正确极性基流幅度',[[0,'0 mA'],[.1,'0.1 mA'],[2,'2 mA']]),field('load','题设负载电流',[[10,'10 mA'],[20,'20 mA'],[40,'40 mA']])
  ],'5 V供电，题设强迫β=10；基流达到目标时用VCE(sat)=0.2 V，否则不预测实际负载电流。NPN/PNP驱动极性相反，未模拟实际hFE曲线。',p=>{
   const on=p.base>=p.load/10,known=on||p.base===0,loss=on?p.load/1000*.2:null;
   return result({on,known,loss},[['目标基流幅度',n(p.load/10,'mA')],['已提供',n(p.base,'mA')],['负载状态',on?'满足题设开关条件':known?'本例无基流':'基流不足，不预测负载电流']],'橙色基流参与控制，蓝色主回路供负载。B/C/E不是MOS的G/S/D。',{current:on?p.load/1000:0,base:p.base/1000,active:on,known,flow:'base',brightness:on?.8:0,heat:loss||0,unknown:!known,high});
  },[
   mission('给负载足够的基流','保持20 mA负载，提供达到题设目标的基流，观察主回路工作。',{base:0,load:20},(p,r)=>p.load===20&&r.on,'开关任务要核对基流与饱和条件，不能只用放大区hFE。','试更多正确极性基流，看橙色控制支路。'),
   mission('观察基流不足','保持20 mA负载，把基流降到0.1 mA，看到不再预测负载电流。',{base:2,load:20},(p,r)=>p.load===20&&!r.known,'基流不足不等于精确零电流，只是本例不能保证饱和。','降低基流，观察黄色提示而不是猜实际电流。'),
   mission('按驱动能力调负载','保持2 mA基流，让负载10 mA，观察更小的题设导通损耗。',{base:2,load:40},(p,r)=>p.base===2&&p.load===10&&r.on,'驱动能力、负载和热条件要一起匹配。','这次只降低负载目标。')
  ]);
 }
 add('bjt-darlington','switch-low','两级增益不等于没有发热',[
  field('base','基流幅度',[[1,'1 mA'],[10,'10 mA'],[20,'20 mA']]),field('load','题设负载电流',[[.1,'0.1 A'],[1,'1 A'],[2,'2 A']])
 ],'两级达林顿示例，课堂强迫β=100、VCE(sat)=1 V；满足基流条件时P=VCE×IC，不推广为所有器件的保证。未计切换与基极损耗。',p=>{
  const on=p.base/1000>=p.load/100,loss=on?p.load:null;
  return result({on,loss},[['基流目标',n(p.load*10,'mA')],['导通损耗',on?n(loss,'W'):'驱动不足，不预测']],'第一级驱动第二级，但高增益不自动消除饱和压降。负载越大，题设损耗越大。',{current:on?p.load:0,base:p.base/1000,active:on,known:on,flow:'base',heat:loss||0,brightness:on?.8:0,unknown:!on});
 },[
  mission('驱动两级通道','保持1 A负载，增加基流达到题设条件，观察两级控制。',{base:1,load:1},(p,r)=>p.load===1&&r.on,'级联提高控制增益，但仍要满足具体工作点的输入条件。','增加基流，看两级控制标识。'),
  mission('看见大负载的损耗','把负载调到2 A，并给够基流，观察2 W导通损耗。',{base:10,load:.1},(p,r)=>p.load===2&&r.on&&near(r.loss,2),'高增益也会有较高压降损耗，不能把它当作零压降开关。','负载和驱动都要调整。'),
  mission('减轻热负担','保持10 mA基流，把负载降到0.1 A，使题设损耗为0.1 W。',{base:10,load:1},(p,r)=>p.base===10&&p.load===.1&&r.on,'热、速度、增益和输入条件是不同的选型指标。','降低负载电流。')
 ]);
 add('bjt-digital','switch-low','内置电阻也需要匹配输入',[
  field('input','输入电压',[[0,'0 V'],[1,'1 V'],[3.3,'3.3 V']]),field('load','题设负载电流',[[1,'1 mA'],[2,'2 mA'],[10,'10 mA']])
 ],'R1=R2=4.7 kΩ，VBE≈0.7 V，IB≈max(0,(VIN−0.7)/R1−0.7/R2)，强迫β=10示例。不是实际输入阈值曲线或任意逻辑电平保证。',p=>{
  const base=Math.max(0,(p.input-.7)/4700-.7/4700),on=base>=p.load/1000/10;
  return result({base,on},[['近似可用基流',n(base*1e6,'µA')],['负载基流目标',n(p.load*100,'µA')]],'R1限制输入电流，R2也分流。内置电阻方便接入，但不等于任意输入都能驱动任意负载。',{current:on?p.load/1000:0,base,active:on,known:on||p.input===0,flow:'base',brightness:on?.8:0,unknown:!on&&p.input!==0});
 },[
  mission('匹配这次输入','保持2 mA负载，提高输入，使近似可用基流达到目标。',{input:0,load:2},(p,r)=>p.load===2&&r.on,'输入、R1/R2和负载共同决定本例驱动能力。','试输入高电平，看可用基流。'),
  mission('看低输入为什么不够','保持2 mA负载，把输入降到1 V，观察题设基流不足。',{input:3.3,load:2},(p,r)=>p.input===1&&p.load===2&&!r.on,'本例近似无可用正基流，不代表知道真实器件完整阈值曲线。','降低输入电压。'),
  mission('不要把小输出当大开关','保持3.3 V输入，把负载从10 mA降到2 mA，让驱动重新满足目标。',{input:3.3,load:10},(p,r)=>p.input===3.3&&p.load===2&&r.on,'带阻器件也要确认输出电流、压降、输入条件与极性。','输入不动，调低负载目标。')
 ]);
 function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
 for(const d of C.lessons.filter(d=>!d.baseline))if(!Object.hasOwn(profiles,d.id))throw new Error('Missing subtype game '+d.id);
 freeze(profiles);
 function profile(id){if(!Object.hasOwn(profiles,id))throw new RangeError('Unknown subtype game');return profiles[id];}
 function validateParams(id,p){const d=profile(id);if(!p||Object.keys(p).length!==d.fields.length||!d.fields.every(f=>Object.hasOwn(p,f.key)&&f.options.some(o=>o[0]===p[f.key])))throw new RangeError('Invalid game parameters');return d;}
 function evaluate(id,p,time=1){const d=validateParams(id,p);if(!Number.isFinite(time)||time<0||time>1)throw new RangeError('Invalid observed phase');return d.calculate(p,time);}
 function level(id,index){const d=profile(id);if(!Number.isInteger(index)||!d.missions[index])throw new RangeError('Invalid subtype mission');return d.missions[index];}
 function create(id){return {id,index:0,cleared:[],params:{...level(id,0).setup},started:false,observed:0};}
 function validate(s){if(!s||!Array.isArray(s.cleared)||typeof s.started!=='boolean'||!Number.isFinite(s.observed)||s.observed<0||s.observed>1.2)throw new RangeError('Invalid game state');validateParams(s.id,s.params);level(s.id,s.index);if(s.cleared.length>3||s.cleared.some((x,i)=>x!==i)||s.index>Math.min(s.cleared.length,2))throw new RangeError('Invalid game progress');}
 function judge(s){validate(s);const l=level(s.id,s.index),r=evaluate(s.id,s.params,Math.min(1,s.observed));return {passed:s.started&&s.observed>=1&&l.check(s.params,r.values),result:r,hint:l.hint,learned:l.learned};}
 function change(s,key,value){validate(s);const p={...s.params,[key]:value};validateParams(s.id,p);return {...s,params:p,cleared:[...s.cleared],started:false,observed:0};}
 function start(s){validate(s);return {...s,params:{...s.params},cleared:[...s.cleared],started:true,observed:0};}
 function stop(s){validate(s);return {...s,params:{...s.params},cleared:[...s.cleared],started:false,observed:0};}
 function observe(s,dt){validate(s);if(!Number.isFinite(dt)||dt<0||dt>.6)throw new RangeError('Invalid observation step');if(!s.started)return s;const next={...s,observed:Math.min(1.2,s.observed+dt)};return judge(next).passed&&next.index===next.cleared.length?{...next,cleared:[...next.cleared,next.index]}:next;}
 function visit(s,index){validate(s);const l=level(s.id,index);if(index>Math.min(s.cleared.length,2))return s;return {...s,index,params:{...l.setup},cleared:[...s.cleared],started:false,observed:0};}
 const api=Object.freeze({ids:Object.freeze(Object.keys(profiles)),profile,evaluate,level,create,validate,judge,change,start,stop,observe,visit});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingSubtypeGameMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);
