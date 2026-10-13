/* Learner-facing chapters. Categories are navigation, not mutually exclusive taxonomies. */
(function(root){
 'use strict';
 const frozen=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(frozen);Object.freeze(x);}return x;};
 const refs={
  resistor:['Vishay · 电阻产品与技术资料','https://www.vishay.com/en/resistors-fixed/'],
  sulfur:['Vishay · 抗硫化厚膜RCA','https://www.vishay.com/en/product/20034/'],
  thin:['Vishay · 薄膜电阻','https://www.vishay.com/en/resistors-fixed/thinfilm/'],
  shunt:['Vishay · 电流检测电阻术语','https://www.vishay.com/doc?49873='],
  mlcc:['Murata · 陶瓷电容基础','https://www.murata.com/en-global/products/capacitor/ceramiccapacitor'],
  aluminum:['TDK · 电解电容结构','https://www.tdk.com/en/tech-mag/electronics_primer/9'],
  film:['TDK · 薄膜材料与自愈','https://www.tdk.com/en/tech-mag/electronics_primer/8'],
  safety:['Murata · 安规电容位置与认证','https://www.murata.com/en-in/news/capacitor/ceramiccapacitor/2016/1206'],
  tantalum:['KYOCERA AVX · 钽电容结构与选型','https://www.kyocera-avx.com/docs/techinfo/Tantalum-NiobiumCapacitors/Tantalum-Capacitors-Characteristics-and-Component.pdf'],
  inductor:['Murata · 绕线与叠层结构','https://www.murata.com/en-global/products/inductor/overview/learn/basic/structure'],
  current:['Coilcraft · Isat与温升电流','https://www.coilcraft.com/en-us/resources/application-notes/current-and-temperature-ratings/'],
  choke:['Coilcraft · 共模与差模','https://www.coilcraft.com/en-us/resources/application-notes/common-mode-filter-design-guide/'],
  crystal:['Epson · 晶体与振荡器','https://www.epsondevice.com/crystal/en/products/crystal-oscillator/index.html'],
  crystaltech:['Epson · 晶体振荡技术说明','https://www.epsondevice.com/crystal/en/techinfo/pdf/tech_notes_e201302.pdf'],
  mos:['Infineon · MOSFET结构与驱动','https://www.infineon.com/technology/mosfets'],
  mosdrive:['Infineon · VGS与RDS(on)测试条件','https://www.infineon.com/product-table/mosfet-finder'],
  diode:['Vishay · 二极管技术资料','https://www.vishay.com/en/diodes/'],
  tvs:['Littelfuse · TVS电压指标','https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes'],
  schottky:['ROHM · 肖特基产品资料','https://www.rohm.com/products/diodes/schottky-barrier-diodes'],
  bjt:['ROHM · NPN/PNP半导体结构','https://www.rohm.com/analogpower/powertech'],
  digital:['ROHM · 带阻三极管与R1/R2','https://techweb.rohm.com/product/transistors-diodes/transistors/23716/'],
  darlington:['ST · 达林顿内部连接与参数条件','https://www.st.com/resource/en/datasheet/tip102.pdf'],
  led:['Vishay · LED发光材料与物理基础','https://www.vishay.com/docs/led_physics.pdf'],
  ledstructure:['Nichia · 蓝光LED外延与衬底结构示例','https://www.nichia.co.jp/specification/newsroom/press/2011_020401_EP936682B9.pdf']
 };
 const families=[
  {id:'capacitor',name:'电容',summary:'储能 · 滤波 · 电源',default:'cap-mlcc'},
  {id:'resistor',name:'电阻',summary:'限流 · 采样 · 精度',default:'res-thick'},
  {id:'inductor',name:'电感',summary:'磁场储能 · 噪声抑制',default:'ind-wound'},
  {id:'crystal',name:'晶振',summary:'频率基准 · 时钟',default:'xtal-passive'},
  {id:'mos',name:'MOS管',summary:'栅压驱动 · 开关',default:'mos-n'},
  {id:'diode',name:'二极管',summary:'整流 · 钳位 · 发光',default:'dio-switch'},
  {id:'transistor',name:'三极管',summary:'基流驱动 · 放大',default:'bjt-npn'}
 ];
 const materials={
  filmres:[['substrate','绝缘基板','氧化铝陶瓷（Al₂O₃）示例','支撑和绝缘，也参与传热。'],['element','电阻膜','薄膜常用NiCr等合金；厚膜常用金属氧化物/玻璃体系','材料与几何形状决定阻值；不是保护层印字决定阻值。'],['cover','保护层','玻璃/树脂等，随系列变化','保护电阻膜。'],['terminal','端接','导电金属与可焊镀层，依系列','连接PCB；抗硫化设计要核对专用端接及防护工艺。']],
  shunt:[['element','合金电阻体','锰铜、铜镍或其他电阻合金，依系列','小阻值把电流转成可测电压。'],['terminal','端接','铜及可焊镀层示例','连接大电流；四端Kelvin型另有采样端。'],['cover','保护/绝缘','树脂或涂层，依结构','减少环境及接触影响。']],
  aluminum:[['foil','阳极箔','蚀刻铝箔Al','增大有效面积。'],['oxide','介质膜','氧化铝Al₂O₃','真正隔开电荷的介质；不是电解纸。'],['paper','隔离纸','浸润电解液的纤维纸','隔开箔并保持电解液。'],['cathode','阴极系统','阴极铝箔及电解液','电解液参与阴极接触，不是绝缘介质本身。'],['case','铝壳与密封','铝、橡胶等，依系列','封装、密封；防爆阀不等于可安全超额定。'],['terminal','引出端','金属引线或端子','接入PCB；本章为有极性湿式示例。']],
  filmcap:[['dielectric','塑料介质','PP聚丙烯或PET聚酯，依系列','隔开两组电极。'],['metal','电极','蒸镀金属或金属箔','本图为金属化薄膜示例。'],['end','喷金端接','端面金属连接层','把每组电极连接到引脚。'],['case','外壳/灌封','树脂及塑料外壳，依系列','保护卷绕芯；安规也可能使用陶瓷，不只薄膜。'],['terminal','引脚','导电金属','连接电路；针距要按型号核对。']],
  tantalum:[['anode','多孔钽阳极','烧结钽Ta','多孔结构提供面积。'],['dielectric','介质','五氧化二钽Ta₂O₅','覆盖阳极孔隙表面，图中薄层已放大。'],['cathode','阴极系统','MnO₂或导电聚合物；本图为MnO₂示例','不同阴极体系的损耗与可靠性条件不同。'],['case','模塑封装','环氧树脂示例','封装不决定电气极性；须读极性标记。'],['terminal','正负端接','金属引框、导电连接层','正端连接钽阳极；不允许任意反接。']],
  multilayer:[['core','叠层本体','铁氧体或陶瓷，依系列','本章以叠层铁氧体示意。'],['winding','印刷导体','银等导电金属，依工艺','导体图形通过连接孔形成线圈，不是漆包线绕组。'],['via','层间连接','导电金属','连接相邻导体层。'],['terminal','端接','金属及可焊镀层','贴片是安装形式；绕线和一体成型也可以贴片。']],
  molded:[['core','磁性包覆体','绝缘处理金属磁粉与黏结体系，依系列','压制包围线圈，不是单独的一块铁。'],['winding','绕组','铜Cu','载流并产生磁场。'],['insulation','绕组绝缘','漆膜/绝缘材料，依工艺','隔离线圈匝间以及磁性材料。'],['terminal','端接','铜及可焊表层示例','连接PCB；Isat、Irms、DCR需分别确认。']],
  choke:[['core','共用磁芯','铁氧体等，依系列','两组绕组共享磁路。'],['winding1','第一绕组','绝缘铜线示例','磁通方向取决于绕向与电流方向。'],['winding2','第二绕组','绝缘铜线示例','共模磁通叠加，理想平衡差模磁通抵消。'],['terminal','端子','金属引出端','两组绕组是独立电路，不在内部短接。']],
  crystal:[['quartz','石英谐振片','石英SiO₂','利用压电效应形成机械谐振。'],['electrode','表面电极','金属薄膜，依系列','向石英片施加电场。'],['base','基座','陶瓷/玻璃等绝缘结构，依封装','承载石英片及电气连接。'],['case','密封壳','金属盖或其他封装，依系列','隔离环境；无源器件也可能有四焊盘。'],['terminal','焊盘','金属端接','晶体信号脚与外壳接地脚须按规格书区别。']],
  oscillator:[['quartz','石英谐振单元','石英SiO₂与电极','提供频率基准。'],['ic','振荡/输出IC','硅Si及内部电路','提供能量、维持振荡并输出时钟。'],['base','互连基座','陶瓷及金属互连示例','连接谐振单元、IC与外部焊盘。'],['case','密封封装','金属盖等，依系列','封装中不只一片石英。'],['terminal','外部焊盘','金属端接','VDD、GND、OUT及OE等功能以具体型号为准。']],
  mos:[['body','半导体体区','掺杂硅Si','N/P沟道与体区极性相反；此图是简化平面剖面。'],['regions','源/漏区','重掺杂硅；极性依N/P沟道','源漏载流，与绝缘栅极不是同一条通路。'],['oxide','栅绝缘层','SiO₂等绝缘介质，依工艺','栅极主要通过电场控制，不是持续注入基流。'],['gate','栅电极','多晶硅或金属，依工艺','栅电容在切换时需要充放电。'],['case','封装','模塑树脂与引框示例','散热、引脚及体二极管需看实际规格。'],['terminal','外部端子','G/S/D导电端接示例','不提供通用封装针脚顺序。']],
  dualmos:[['die1','MOS单元1','硅Si与绝缘栅结构','图为双N单元示例。'],['die2','MOS单元2','硅Si与绝缘栅结构','也有互补N+P等组合；不默认并联。'],['base','引框与互连','铜等导电金属，依封装','共源、共漏或独立连接依数据手册。'],['case','外封装','模塑树脂示例','多个器件共用封装，不等于完全同参数。'],['terminal','端子','金属及可焊镀层','必须按实际组合和针脚确认。']],
  pn:[['p','P区','P型掺杂硅示意','与N区形成PN结。'],['n','N区','N型掺杂硅示意','结的电气行为与掺杂和几何结构相关。'],['junction','结区','半导体内的耗尽区','不是插入的一层绝缘材料；宽度仅为示意。'],['case','封装','树脂或玻璃，依系列','开关、整流、稳压和TVS的芯片设计不相同。'],['terminal','阳极/阴极连接','金属连接及端接','反向击穿是否属于正常工作，取决于器件用途。']],
  schottky:[['semiconductor','半导体','掺杂硅Si示例；也有SiC类型','本课显示硅肖特基，不把所有材料混为一类。'],['metal','势垒金属','金属材料依具体工艺','形成金属—半导体整流势垒，不是PN结。'],['contact','欧姆接触','金属接触层','另一侧用于低阻引出，不等同势垒接触。'],['case','封装','树脂示例','漏电、结电容和热特性仍须核对。'],['terminal','端接','导电金属','Vf必须在相同If和温度下比较。']],
  led:[['substrate','芯片衬底','蓝光示例：蓝宝石等，依工艺','支撑外延结构。'],['active','发光外延区','蓝光示例：GaN/InGaN体系','载流子复合，把部分能量转换成光，仍会产生热。'],['contact','电极连接','金属及键合/倒装互连，依封装','向芯片提供电流。'],['case','透光封装','硅胶或其他材料，依系列','白光产品可能另有荧光转换层，本图为蓝光示意。'],['terminal','端接','金属引框或焊盘','LED必须限流，不能当作零压降导线。']],
  bjt:[['emitter','发射区E','NPN为N型；PNP为P型掺杂硅','主要载流子由此注入基区。'],['base','基区B','NPN为P型；PNP为N型掺杂硅','基区较薄；此图不是厂家实际芯片布局。'],['collector','集电区C','NPN为N型；PNP为P型掺杂硅','收集载流子；BJT并非两个独立二极管直接相接。'],['case','封装','树脂、引框等，依系列','热限制与封装、PCB有关。'],['terminal','B/C/E端接','导电金属','端子顺序不同于MOS的G/S/D，针脚不可按外观猜。']],
  darlington:[['unit1','第一级BJT','掺杂硅示意','第一级发射极驱动第二级基极。'],['unit2','第二级BJT','掺杂硅示意','两级放大；也可集成在同一芯片。'],['base','互连','导电金属','典型共集电极结构，不是任意串联。'],['case','封装','树脂等，依系列','较高饱和压降带来的损耗需检查。'],['terminal','外部B/C/E','导电金属','本图为功能单元示意，不规定实际管脚。']],
  digital:[['emitter','发射区E','掺杂硅','本章采用NPN带阻示例，亦有PNP。'],['base','基区B','掺杂硅','仍是双极型结构，不是MOS绝缘栅。'],['collector','集电区C','掺杂硅','输出载流端。'],['bias','偏置电阻R1/R2','片上电阻，工艺依系列','功能块放大显示；有仅R1、仅R2和两者都含的产品。'],['case','封装','树脂示例','“数字三极管”不代表可以忽略输入/输出条件。'],['terminal','IN/OUT/GND端接','导电金属','端口命名及极性以型号为准。']]
 };
 materials.mlcc=[['dielectric','陶瓷介质','BaTiO₃体系或其他陶瓷，依介质类别','隔开相邻电极。'],['internal','内部电极','镍Ni等，依工艺','相邻层交替连接两端。'],['case','陶瓷本体及盖层','烧结陶瓷','包覆内部，盖层不含内电极。'],['terminal','端电极','基础金属及Ni/Sn等镀层','连接PCB，端接有不同工艺。']];
 materials.wound=[['core','磁芯','铁氧体等，依系列','引导磁通。'],['winding','铜绕组','绝缘铜线','建立磁场。'],['case','屏蔽/封装','磁性材料或其他包覆，依系列','保护绕组并影响漏磁。'],['terminal','端子','导电金属','连接PCB。']];
 const lessons={};
 function add(id,family,title,kind,summary,use,specs,principle,ask,quiz,sourceKeys,lab,baseline=false){
  if(id==='cap-mlcc')kind='mlcc';if(id==='ind-wound')kind='wound';
  const layers=(materials[kind]||[]).map(([id,name,composition,role])=>({id,name,composition,role}));
  const exterior={filmres:['cover','terminal'],shunt:['element','cover','terminal'],multilayer:['core','terminal'],molded:['core','terminal'],choke:['core','winding1','winding2','terminal'],crystal:['base','case','terminal'],oscillator:['base','case','terminal']};
  const outerIds=(exterior[kind]||['case','terminal']).filter(id=>layers.some(p=>p.id===id));
  if(kind==='filmres')layers.find(p=>p.id==='element').composition=id==='res-thin'?'NiCr等电阻合金薄膜，依系列':'金属氧化物与玻璃体系；RuO₂为典型示例，依系列';
  if(id==='res-sulfur')layers.find(p=>p.id==='terminal').role='专用耐硫化端接/防护设计，材料与工艺依系列；不以外观保证寿命。';
  if(kind==='mos'){const p=id==='mos-p';layers.find(l=>l.id==='body').composition=(p?'N':'P')+'型掺杂硅Si（本图平面示例）';layers.find(l=>l.id==='regions').composition=(p?'P⁺':'N⁺')+'重掺杂硅源/漏区（本图示例）';}
  if(kind==='bjt'||kind==='digital'){const p=id==='bjt-pnp';for(const name of ['emitter','collector'])layers.find(l=>l.id===name).composition=(p?'P':'N')+'型掺杂硅Si（本章示例）';layers.find(l=>l.id==='base').composition=(p?'N':'P')+'型掺杂硅Si（本章示例）';}
  if(id==='xtal-tcxo'){const ic=layers.find(l=>l.id==='ic');ic.name='振荡与温度补偿电路';ic.role='维持振荡、输出时钟，并补偿温度引起的频偏；实际实现依系列。';}
  if(id==='xtal-vcxo'){const ic=layers.find(l=>l.id==='ic');ic.name='振荡与压控调谐电路';ic.role='通过控制端改变调谐条件，在规定牵引范围内微调频率。';}
  if(kind==='aluminum')layers.find(l=>l.id==='oxide').role='氧化膜贴合蚀刻阳极箔表面，是实际介质；图把卷芯局部展开并放大，不是平板实际布局。';
  if(kind==='tantalum')layers.find(l=>l.id==='dielectric').role='介质覆盖多孔阳极内外表面。图把孔隙与涂层分开、放大显示，并非只覆盖阳极外侧的一块平板。';
  lessons[id]={id,family,title,kind,summary,use,specs,principle,ask,quiz:{question:quiz[0],options:quiz[1],answer:quiz[2],explain:quiz[3]},sources:sourceKeys.map(k=>refs[k]),lab,baseline,layers,outerIds,
   scope:'典型结构和功能分区示意；层厚、颜色已放大，不代表所有厂家或系列。实际材料、布局和针脚以具体型号资料为准。'};
  if(kind==='aluminum'||kind==='filmcap')lessons[id].scope+=' 图中把卷绕芯局部展开，便于辨认相邻材料。';
  if(kind==='tantalum')lessons[id].scope+=' 多孔阳极与涂层为分区放大示意，不按真实孔隙形状绘制。';
  if(id==='dio-led')lessons[id].sources=[refs.led,refs.ledstructure];
  if(id==='bjt-darlington')lessons[id].sources=[refs.darlington,refs.bjt];
 }
 add('res-thick','resistor','厚膜电阻','filmres','通用限流与分压','LED限流、上拉、一般信号电路',[['阻值/精度','Ω/kΩ/MΩ、±1%/±5%等'],['功率/电压','同时检查温度降额和电压限制'],['温漂TCR','按系列与阻值范围核对']],['厚膜电阻膜决定阻值；保护层只保护及标识。','串联阻值改变回路电流，也产生压降与发热。'],['目标阻值与精度？','工作电流、电压、温度和脉冲？'],['阻值相同就能直接替代吗？',['能，只要尺寸一样','不能，还要确认功率、温漂和工作条件','只比较价格即可'],1,'相同阻值不代表可靠性与所有电气参数相同。'],['resistor'],'ohm',true);
 add('res-thin','resistor','薄膜电阻','filmres','关注精度、温漂和稳定性','精密测量、模拟信号、精密分压',[['精度','不由“薄膜”名称单独保证'],['TCR','ppm/K与初始误差是两项'],['长期稳定性','漂移、噪声与条件分别检查'],['功率/脉冲','薄膜不等于能承受任意脉冲']],['NiCr等薄膜经图形化/修调形成阻体。','温度改变阻值，精密分压比例也可能变化；成组跟踪温漂另行确认。'],['允许总误差、TCR和温度范围？','是否需要匹配网络或长期稳定性？'],['±0.1%能保证任何温度下都不漂移吗？',['不能，仍要看TCR与长期漂移','能，精度已包含全部温度影响','只看封装即可'],0,'初始误差、温漂和长期漂移应分别核对。'],['thin'],'tcr');
 add('res-sense','resistor','采样电阻','shunt','把电流变成可测的小电压','电流检测、电池/电源保护',[['小阻值','mΩ不等于MΩ'],['功耗','I²R及脉冲承受条件'],['TCR/连接','小阻值时连接电阻影响明显'],['Kelvin端接','四端采样不是所有采样电阻都有']],['V＝IR，把大电流转换成小压差信号送给采样电路。','采样也会产生发热与损耗；本图采用合金结构，另有厚膜采样产品。'],['电流峰值/有效值和允许压降？','两端还是四端、TCR与采样精度要求？'],['2 A经过10 mΩ，采样电压是多少？',['20 V','20 mV','2 mV'],1,'2×0.01＝0.02 V＝20 mV；还应检查40 mW功耗及连接影响。'],['shunt'],'sense');
 add('res-sulfur','resistor','抗硫化电阻','filmres','降低含硫环境引起的端接失效风险','汽车、工业及含硫环境',[['耐硫化声明','确认厂家试验与判据'],['材料/端接','设计依系列，不只看保护层颜色'],['基本参数','阻值、功率、精度和TCR仍需匹配']],['含硫环境可能影响易受硫侵蚀的端接材料。','专门的端接与防护设计提高抵抗能力；抗硫化不等于对所有腐蚀永久免疫。'],['环境是否含硫及其他腐蚀物？','需要哪种可靠性试验或汽车等级？'],['抗硫化能保证永久不失效吗？',['能，名称已经保证','不能，要核对试验、环境与电气条件','它只代表更大的功率'],1,'它是可靠性特性，可与厚膜等结构重叠。'],['sulfur'],'sulfur');
 add('cap-mlcc','capacitor','MLCC陶瓷电容','filmcap','小体积去耦与高频应用','芯片电源旁、信号滤波',[['容量/介质','C0G、X7R、X5R等'],['有效容量','偏压、温度、误差共同影响'],['ESR/ESL','按频率及具体型号曲线确认']],['相邻内电极交替连接两端，陶瓷层隔开电荷。','瞬态多用电时短时间补电；高频表现不能只用名义容量判断。'],['工作电压下需要多少有效容量？','安装位置、尺寸与阻抗要求？'],['标称10 µF是否等于工作点始终10 µF？',['是','不是，需要查有效容量','只看尺寸'],1,'高介电常数材料可能受直流偏压等影响。'],['mlcc'],'cap',true);
 add('cap-aluminum','capacitor','铝电解电容','aluminum','大容量储能与电源滤波','电源输入/输出、大纹波节点',[['极性/耐压','本章为有极性湿式示例'],['容量/ESR','影响储能、纹波与瞬时压降'],['纹波电流','要带频率和温度条件'],['寿命','额定小时数要带温度与负载条件']],['蚀刻铝箔与氧化铝介质形成大面积储能结构。','ESR产生纹波发热，温度及负载影响寿命；聚合物与湿式结构应分别比较。'],['纹波电流、频率、环境温度？','寿命要求、直径/高度/脚距、极性？'],['电解纸就是储能介质吗？',['是','不是，氧化铝膜是介质，纸保持隔离与电解液','电解液完全绝缘'],1,'不能把隔离纸、电解液和氧化膜的作用混为一谈。'],['aluminum'],'esr');
 add('cap-safety','capacitor','安规电容','filmcap','先确认X/Y类别与认证','交流输入干扰抑制位置',[['X/Y类别','X用于线间，Y用于线与保护接地等位置，按设备要求核对'],['AC额定值/认证','不能用普通DC耐压或容量替代'],['漏电/结构','需考虑电流、爬电及设备标准'],['材料','可为薄膜或陶瓷，本图为薄膜示例']],['为指定安全相关位置选择经过相应认证的器件。','对噪声提供通路，但要同时满足安规约束；本页不是带电接线指南。'],['使用位置和设备要求的X/Y等级？','AC额定值、认证、空间与允许漏电？'],['普通高耐压电容能直接代替Y电容吗？',['能，耐压高就够','不能，需要相应安规类别和认证','只需容量相同'],1,'安规电容不是只按“耐压更高”进行比较。'],['safety'],'safety');
 add('cap-film','capacitor','薄膜电容','filmcap','低损耗、脉冲与交流应用','谐振、吸收、DC-link等',[['介质','PP/PET等，性能不能混用'],['AC/DC额定值','要核对应用与频率'],['脉冲/纹波','dV/dt及允许电流'],['自愈','金属化结构的能力依系列与条件']],['塑料薄膜隔开金属电极；可卷绕或叠层。','某些金属化结构局部击穿可清除缺陷区域，反复自愈仍可能改变容量。'],['用于吸收、谐振还是母线？','电压、频率、dV/dt、纹波与尺寸？'],['自愈等于可以无限次承受过压吗？',['是','不是，仍有额定和寿命条件','所有薄膜都是相同结构'],1,'金属化与箔式结构不同，自愈也不等于无限耐压。'],['film'],'pulse');
 add('cap-tantalum','capacitor','钽电容','tantalum','极性、ESR与浪涌一起检查','紧凑电源滤波',[['阴极体系','MnO₂/聚合物须区别'],['耐压与降额','按系列和应用核对'],['ESR/浪涌','电源阻抗及启动浪涌重要'],['极性','不可按MLCC无极性方式使用']],['多孔钽阳极表面的Ta₂O₅是介质。','MnO₂或聚合物形成阴极系统，结构和可靠性条件不能混用。'],['启动浪涌和源阻抗？','阴极类型、降额政策、极性与尺寸？'],['钽电容能随意反接吗？',['能，电容都无极性','不能，应确认极性及系列要求','只要暂时电压低就能反接'],1,'本章是有极性结构，不把MLCC的使用方式套过来。'],['tantalum'],'polarity');
 add('ind-wound','inductor','绕线电感','molded','绕组与磁芯共同影响性能','电源储能或高频应用，按系列区分',[['L/Q/DCR','还要带测量频率'],['Isat/Irms','磁性能和热限制分别核对'],['磁芯/屏蔽','不由外观单独决定']],['铜绕组建立磁场；L反对电流突变。','同样绕线结构也可有不同磁芯和用途，不能把RF与功率系列互换。'],['频率、峰值/有效值电流？','电感下降、损耗、尺寸与屏蔽要求？'],['Isat能替代Irms吗？',['能','不能，两项判据不同','它们都是烧毁电流'],1,'磁饱和与温升限制分别检查。'],['inductor','current'],'inductor',true);
 add('ind-layered','inductor','贴片叠层电感','multilayer','层内导体与连接孔形成线圈','紧凑高频/信号用途，依系列',[['安装/结构','贴片是安装形式；这里展示叠层结构'],['L/Q/SRF','按频率曲线核对'],['电流/DCR','不把额定值脱离测试条件比较']],['导体图形分布在多层本体内，用连接孔组成线圈。','绕线、一体成型也可贴片；叠层与绕线的频率特性不同。'],['使用频率、所需Q与SRF？','尺寸、DCR与电流限制？'],['“贴片”就代表没有绕组吗？',['是','不是，贴片不等于叠层','贴片一定是一体成型'],1,'安装形式和内部结构是两个分类维度。'],['inductor'],'reactance');
 add('ind-molded','inductor','一体成型电感','molded','磁性材料包覆铜线圈','功率转换、大电流储能',[['Isat/L下降','核对跌落判据与峰值电流'],['Irms/DCR','热条件、铜损与磁芯损耗'],['频率/尺寸','高度与屏蔽也要确认']],['线圈被磁粉/黏结体系包覆成型。','电流过大会影响电感量，不能只凭“一体成型”认为永不饱和。'],['峰值电流及允许L下降？','温升、频率、DCR、尺寸和散热？'],['一体成型是否代表不会饱和？',['是','不是，仍要读L-I曲线与Isat','只要外壳没有发热就安全'],1,'材料与磁路决定电感随电流的变化。'],['current'],'inductor');
 add('ind-common','inductor','共模电感','choke','两绕组共用磁芯抑制共模噪声','电源/信号线EMI滤波',[['共模阻抗','必须带频率'],['绕组/额定电流','绝缘与应用要求'],['差模漏感','不等于完全无差模影响']],['正确绕向下，共模电流磁通叠加，理想等大反向差模磁通抵消。','实际还有漏感、寄生电容和损耗，不能把普通单绕组电感直接替代。'],['共模还是差模噪声、频率？','电流、绝缘、接口与安装空间？'],['共模电感里的两绕组直接短接吗？',['是','不是，它们共享磁路但电路独立','只有一个绕组'],1,'共享磁芯不等于共享导线。'],['choke'],'common');
 add('xtal-passive','crystal','无源晶体谐振器','crystal','晶体本身不独立输出时钟','配合MCU/振荡放大器',[['频率/CL','负载电容与电路匹配'],['ESR/驱动电平','启动和过驱动风险'],['频差/温稳/老化','不是同一项ppm'],['焊盘','两焊盘/四焊盘都可能是无源']],['石英压电谐振提供频率选择，振荡放大器提供维持能量。','外部负载与寄生电容影响匹配，不能只按同频率替代。'],['芯片所需频率、CL、ESR及驱动要求？','温度范围、频差、尺寸与焊盘定义？'],['四个焊盘就一定是有源晶振吗？',['是','不是，要看是否集成振荡电路及针脚功能','只能看封装颜色'],1,'四焊盘无源晶体可能包含外壳接地脚。'],['crystal','crystaltech'],'loadcap');
 add('xtal-active','crystal','有源晶振XO','oscillator','供电后由模块输出时钟','MCU外部时钟、数字系统',[['VDD/电流','模块需要电源'],['输出制式','CMOS/LVDS等不可直接互换'],['频率/稳定度','带温度与电压条件'],['OE/启动/抖动','功能与时间条件须确认']],['石英谐振单元与振荡/输出电路集成在封装内。','OUT送时钟，VDD/GND供能；不是把无源晶体直接换到OUT焊盘。'],['工作电源、输出制式及接收芯片？','频率、总误差、抖动、OE与启动时间？'],['XO能不供电就持续输出时钟吗？',['能','不能，它内置的振荡电路需要供电','只要频率相同就能代替无源晶体'],1,'有源晶振与无源晶体的接口与驱动方式不同。'],['crystal'],'clock');
 add('xtal-tcxo','crystal','温补晶振TCXO','oscillator','补偿温度引起的频率变化','通信、定位、精密时钟',[['温稳/总误差','补偿不等于零误差'],['VDD/输出','核对接口与负载'],['老化/抖动','不由温稳指标单独保证']],['振荡模块加入温度检测/补偿，降低温度变化造成的频偏。','补偿后的精度仍有规定温度与供电范围，老化另外核对。'],['目标温度范围和频率误差预算？','供电、输出、老化与相位噪声？'],['TCXO表示任何温度下都完全不偏吗？',['是','不是，只在规定条件下满足相应指标','它不需要供电'],1,'温度补偿不代表无限精度，也不免除工作条件。'],['crystal'],'ppm');
 add('xtal-vcxo','crystal','压控晶振VCXO','oscillator','控制电压调节输出频率','锁相/同步与频率微调',[['牵引范围','ppm及控制电压范围'],['中心频率/线性','调节规律依系列'],['VDD/输出/抖动','需要完整接口条件']],['控制端改变振荡器的调谐条件，使输出在有限范围内偏移。','VCXO不是任意可编程频率发生器，也不自动等于温补。'],['中心频率、牵引范围、控制电压？','调谐方向、线性、供电与输出类型？'],['VCXO能按需要调到任意频率吗？',['能','不能，调节有牵引范围','有控制脚就一定是TCXO'],1,'压控调谐与温度补偿是不同功能。'],['crystal'],'pull');
 add('mos-n','mos','N沟道MOS','mos','以相对源极的正VGS驱动','常见低边开关与功率转换',[['VDS/ID/SOA','温度、时间和安全工作区'],['RDS(on)','带VGS和结温条件'],['VGS(th)','仅为规定小电流下的阈值，不等于充分导通'],['Qg/体二极管','切换损耗与驱动能力']],['绝缘栅极通过电场形成导电沟道；开关时须给栅电容充放电。','不是基极持续驱动电流；G/S/D不可套用B/C/E针脚。'],['驱动相对源极能给多少VGS？','电压/电流、频率、散热、RDS(on)条件？'],['VGS刚超过阈值，就保证低RDS(on)吗？',['保证','不保证，要看指定VGS下的RDS(on)','只看ID最大值'],1,'阈值测试通常不是大电流充分导通条件。'],['mos','mosdrive'],'mos');
 add('mos-p','mos','P沟道MOS','mos','栅极低于源极时形成负VGS','常见高边供电开关',[['负VGS','关注源极电位，不只看对地栅压'],['RDS(on)/VDS','带极性及测试条件'],['驱动与保护','栅源极限、体二极管与SOA']],['增强型P沟道器件以相对源极的负栅压驱动。','电源高边源极电位较高，要看VGS差值；不把N沟道接法直接照搬。'],['源极电压与可用栅驱动？','反接保护、负载、电压/散热与封装？'],['源极12 V、栅极12 V，此时VGS是多少？',['12 V','0 V','−12 V'],1,'VGS＝VG−VS，不是VG对地电压。'],['mos','mosdrive'],'mos');
 add('mos-dual','mos','双MOS','dualmos','两个MOS单元集成在同一封装','电池保护、互补驱动等，依组合',[['组合与互连','双N、双P或N+P等'],['每颗参数','RDS(on)、VDS、VGS与热耦合'],['针脚/体二极管','不能默认并联或共源']],['内部包含两个MOS单元，互连方式必须读电路图。','封装集成可节省空间，但不代表两颗参数一致或能任意接线。'],['需要何种沟道组合与内部连接？','分别承担的电压/电流、RDS(on)与散热？'],['双MOS可以一律当成两颗并联吗？',['可以','不可以，先看内部组合及互连','只看封装针脚数'],1,'共源、共漏、独立或互补组合的用途不同。'],['mos','mosdrive'],'dualmos');
 add('dio-switch','diode','开关二极管','pn','关注切换速度与小信号','信号导通/隔离、快速切换',[['trr/结电容','带测试条件'],['Vf/If/耐压','不要只看速度'],['漏电/极性','封装标记须核对']],['PN结正向导通、反向阻断；真实有恢复过程及漏电。','电路的速度还受结电容及负载影响。'],['切换频率、信号幅度、电流？','trr、结电容、耐压和极性？'],['二极管反向就绝对零电流吗？',['是','不是，存在漏电与动态过程','只有外观决定漏电'],1,'反向漏电和恢复条件需分别核对。'],['diode'],'diode',true);
 add('dio-rectifier','diode','整流二极管','pn','把交流的指定半周送给负载','交流整流、电源通路',[['电流/浪涌','连续、平均与浪涌条件不同'],['VRRM/Vf','最大反向与导通损耗'],['恢复/温度','高频用途需确认恢复特性']],['按方向放行半周，未经滤波的输出仍是脉动。','不能把整流后的波形直接说成平稳直流；滤波与稳压是其他环节。'],['输入频率与反向峰值？','负载平均/峰值、浪涌、恢复和散热？'],['单颗二极管整流后一定得到平稳直流吗？',['一定','不一定，未经滤波仍会脉动','二极管可以代替稳压器'],1,'整流、滤波与稳压的作用不同。'],['diode'],'rectify');
 add('dio-schottky','diode','肖特基二极管','schottky','金属—半导体势垒','低压整流、续流等，依系列',[['Vf与漏电','在相同If/温度下比较'],['反向耐压/结电容','硅与SiC系列须区别'],['热与动态','不把“快”理解成无损耗']],['金属与半导体形成整流势垒，不画成普通PN结。','较低Vf的器件可能有不同漏电/耐压权衡，要在真实工作点比较。'],['同工作点下Vf、漏电与温度？','反向耐压、结电容和开关条件？'],['肖特基结构是普通PN结吗？',['是','不是，本课为金属—半导体势垒','所有二极管都没有结电容'],1,'材料/势垒结构不同，不能套用同一内部材料图。'],['schottky'],'vf');
 add('dio-zener','diode','稳压二极管','pn','利用规定反向工作区稳压','参考、电压钳位',[['Vz/Iz','稳压值必须带测试电流'],['功耗/动态电阻','热与电压变化'],['限流','不能忽略串联限流与负载电流']],['在合适反向电流区建立近似稳压电压。','输入和负载变化会改变稳压管电流；输入不足时不能维持目标电压。'],['Vz与测试电流、负载范围？','限流、功率、温度和允许电压误差？'],['稳压管不需要任何限流吗？',['不需要','需要检查限流与功耗','接反任何普通二极管都一样'],1,'稳压是有条件的反向工作，不是无功耗的理想电压源。'],['diode'],'zener');
 add('dio-tvs','diode','TVS瞬态抑制二极管','pn','在脉冲条件下限制过压','接口、电源瞬态保护',[['VRWM/VBR/VC','三项电压不要混用'],['Ipp/脉冲波形','峰值指标必须带波形'],['单/双向/电容','正常信号兼容性']],['过压脉冲使TVS导通，电流经保护支路分流。','钳位电压高于正常工作保持电压，不能把VRWM当成保护后的输出电压。'],['正常最高电压、芯片允许电压？','浪涌波形、源阻抗、Ipp及单/双向？'],['VRWM＝5 V就保证脉冲钳位在5 V吗？',['保证','不保证，要看VC@Ipp和波形','TVS可无限期稳压'],1,'TVS不是无限期工作的稳压电源。'],['tvs'],'tvs');
 add('dio-led','diode','发光二极管LED','led','电流产生光，也产生热','指示、照明、光电应用',[['颜色/光参数','波长、亮度与角度'],['If/Vf','同条件比较'],['热/限流','不能只按Vf直连电源']],['载流子在发光区复合，部分电能变成光。','本图为蓝光GaN/InGaN示例，不代表白光荧光层或所有颜色材料。'],['颜色、亮度、驱动电流与光学要求？','散热、限流、封装与寿命条件？'],['LED可以因为会发光而不产生热吗？',['可以','不可以，仍有热损耗','只要颜色相同就同样Vf'],1,'光输出、效率与热管理共同影响使用。'],['diode'],'led');
 add('bjt-npn','transistor','NPN三极管','bjt','基流控制、常见低边应用','放大或开关，依工作区',[['VCEO/IC/SOA','还要确认热条件'],['hFE','带IC/VCE/温度条件'],['VCE(sat)','带IC及IB条件'],['B/C/E','与MOS端子和驱动方式不同']],['N-P-N三个区组成耦合结构，基流参与控制集电极电流。','开关应用需确认基流与饱和条件，不能用放大区hFE简单保证饱和。'],['负载电流与可用基流？','饱和压降、频率、散热与针脚？'],['NPN能按MOS的绝缘栅驱动方式使用吗？',['能','不能，BJT需要基流条件','B/C/E和G/S/D一一等同'],1,'双极型基流控制与MOS栅电场控制不同。'],['bjt'],'bjt');
 add('bjt-pnp','transistor','PNP三极管','bjt','与NPN相反的极性条件','高边开关或互补放大',[['极性/电位','看VB相对VE'],['IC/IB/VCE(sat)','带极性与测试条件'],['B/C/E与热','不能仅按外观猜针脚']],['P-N-P结构中，正常导通时基极电位相对发射极较低。','PNP常用于高边场景，NPN接法不能无修改直接搬用。'],['发射极电位与控制端能否拉低？','负载、基流、饱和和封装条件？'],['PNP基极驱动应只看对地电压吗？',['是','不是，要看相对发射极的电位','PNP不需要任何驱动'],1,'相对电位与极性决定工作条件。'],['bjt'],'bjt');
 add('bjt-darlington','transistor','达林顿三极管','darlington','两级BJT联合放大','较大驱动增益的负载控制',[['电流增益','实际范围带条件'],['饱和压降/发热','常高于普通单管，依型号'],['输入/速度','VBE和关断时间须确认']],['第一级发射极连接第二级基极，两级协同工作。','高增益不等于低压降或低发热；关断速度也需检查。'],['需要的增益与输入驱动？','负载、压降损耗、速度和散热？'],['达林顿增益高，就一定导通损耗更低吗？',['一定','不一定，还要看VCE(sat)与电流','它就是两颗MOS'],1,'增益、压降与速度是不同指标。'],['bjt'],'darlington');
 add('bjt-digital','transistor','带阻数字三极管','digital','把偏置电阻集成在器件内','逻辑信号控制的小负载',[['R1/R2','仅R1、仅R2或两者均有'],['输入/输出条件','不能只比较IC最大值'],['NPN/PNP/针脚','完整组合须确认']],['内置R1可限制输入基流，R2可连接基极与发射极。','仍是BJT；不同R1/R2和输入电压改变可用基流。'],['输入高/低电平与负载要求？','R1/R2、极性、输出压降和针脚？'],['“带阻”就可以不看输入条件吗？',['可以','不可以，还要核对R1/R2及负载','它没有基极电流'],1,'内置电阻方便使用，不等于任意逻辑电平都能保证开关。'],['digital'],'digital');
 function lesson(id){if(!Object.hasOwn(lessons,id))throw new RangeError('Unknown training subtype');return lessons[id];}
 function children(family){if(!families.some(f=>f.id===family))throw new RangeError('Unknown training family');return Object.values(lessons).filter(p=>p.family===family);}
 const api={families,lessons:Object.values(lessons),lesson,children};frozen(api);
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingCatalog=api;
})(typeof globalThis!=='undefined'?globalThis:this);
