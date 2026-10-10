/* Source-scoped material knowledge shared by both views. */
(function(root){
 'use strict';
 const lessons={
  resistor:{name:'厚膜贴片电阻',scope:'典型厚膜结构，不代表薄膜或金属合金电阻。层厚、修调槽与材料配比依型号变化。',caption:'沿长度剖开，先看电阻膜，再看基板和两端镀层。薄层已放大，方便识别。',
   layers:[
    {id:'substrate',name:'陶瓷基板',brief:'氧化铝 Al₂O₃',composition:'常见为氧化铝（Al₂O₃）陶瓷。',role:'绝缘、支撑电阻膜，并帮助把热量传出。',scope:'陶瓷等级、纯度与添加物需查具体系列。',refs:[0]},
    {id:'film',name:'厚膜电阻膜',brief:'典型：RuO₂＋玻璃相',composition:'钌系陶瓷金属复合材料；RuO₂（二氧化钌）导电相与玻璃相是公开工艺示例。',role:'承担电阻作用；膜的材料、几何尺寸与修调共同决定阻值。',scope:'不同厚膜系列的材料配比可能不同；确认具体成分时，请查该型号的材料声明。',refs:[0,1]},
    {id:'cover',name:'保护层',brief:'玻璃保护层（示例）',composition:'此示例为烧结玻璃保护层。',role:'保护电阻膜，减少环境及加工影响。',scope:'也有不同树脂/复合保护工艺；不把厂家玻璃配方视为统一成分。',refs:[0]},
    {id:'electrode',name:'基础端电极',brief:'导电金属；Ag为工艺示例',composition:'连接膜层的导电金属；银（Ag）基电极见公开厚膜工艺。',role:'把电阻膜两端接到外部端子。',scope:'金属体系按系列确认，不能据此认定每颗电阻都使用银或银钯。',refs:[1]},
    {id:'nickel',name:'阻挡镀层',brief:'镍 Ni',composition:'镍（Ni）阻挡层。',role:'位于基础电极与可焊外层之间。',scope:'镀层厚度与结构依封装/系列；本图为典型层序。',refs:[0]},
    {id:'finish',name:'可焊外层',brief:'可焊镀层；无铅Sn示例',composition:'外部可焊金属镀层；锡（Sn）为无铅外层示例。',role:'用于与PCB焊盘焊接。',scope:'锡、含铅或其他端接版本必须按原厂订货规格确认。',refs:[2]}
   ],sources:[['Vishay · M系列材料与剖面结构','https://www.vishay.com/docs/60031/m.pdf'],['公开厚膜材料工艺 · EP2286420B1','https://patents.google.com/patent/EP2286420B1/en'],['Vishay · D/CRCW e3镍层与锡端接','https://www.vishay.com/docs/20035/dcrcwe3.pdf']]},
  capacitor:{name:'高介电常数MLCC',scope:'这里展示BaTiO₃基、镍内部电极的MLCC示例。不能把C0G或所有陶瓷电容都当作相同配方。',caption:'陶瓷隔开相邻电极；电极交替接左、右端，层层叠加储能。薄层已放大。',
   layers:[
    {id:'dielectric',name:'陶瓷介质',brief:'钛酸钡 BaTiO₃基',composition:'高介电常数MLCC常见为钛酸钡（BaTiO₃）基陶瓷，含按性能设计的添加物。',role:'隔开电极，并在电场中储能。',scope:'X7R/X5R是温度特性分类，不是配方名称；C0G不得照用本例材料。',refs:[0]},
    {id:'internal',name:'内部电极',brief:'镍 Ni（本例）',composition:'本例使用镍（Ni）金属电极。',role:'交替连接两个端子，多层叠加有效电极面积。',scope:'镍属基底金属电极示例；其他电极工艺依产品确认。',refs:[0,1]},
    {id:'base',name:'端电极基础层',brief:'铜 Cu（本例）',composition:'铜（Cu）基础电极层。',role:'收集连接同一端的内部电极。',scope:'本例采用村田公开结构资料的材料层序，不替代其他系列材料声明。',refs:[1]},
    {id:'barrier',name:'端部阻挡层',brief:'镍 Ni',composition:'镍（Ni）镀层，位于铜基础层与锡层之间。',role:'形成端接阻挡层。',scope:'层厚及柔性端接等结构不由本图确定。',refs:[1]},
    {id:'tin',name:'端部可焊层',brief:'锡 Sn',composition:'锡（Sn）外镀层。',role:'提供外部可焊连接表面。',scope:'仅为此结构示例；具体端接版本以料号资料为准。',refs:[1]}
   ],sources:[['Murata · 钛酸钡介质与镍电极','https://article.murata.com/en-global/article/mlcc-for-5g-smartphone-2'],['Murata · MLCC剖面与材料表','https://search.murata.co.jp/Ceramy/image/img/A01X/1R0009A.pdf']]},
  inductor:{name:'绕线铁氧体电感',scope:'此图为绕线铁氧体结构，不代表空气芯、叠层电感或金属粉芯一体成型结构。屏蔽/封装形式也随系列变化。',caption:'穿过绕组的剖面。橙色圆面是铜线被切开的截面，外圈是绝缘膜，不是互不相连的独立小零件。',
   layers:[
    {id:'core',name:'磁芯 / 磁性屏蔽体',brief:'铁氧体：复合金属氧化物',composition:'铁氧体以铁氧化物为主要组成，结合锰、锌或镍等金属氧化物；MnZn、NiZn为材料类别示例。',role:'引导磁通；磁性屏蔽体有助于减少外泄磁场。',scope:'不是纯铁块；配比、气隙、损耗与饱和性能需查具体磁材/系列。',refs:[0,1]},
    {id:'copper',name:'绕组导体',brief:'铜 Cu（本例）',composition:'本例为铜（Cu）绕线。',role:'电流通过绕组建立磁场；导体电阻产生铜损。',scope:'线径、匝数与绕法不按图推算；特殊产品也可能用其他导体。',refs:[2]},
    {id:'insulation',name:'绕线绝缘膜',brief:'聚合物绝缘漆（示例）',composition:'漆包线绝缘膜可采用聚氨酯、聚酯亚胺等聚合物体系。',role:'隔离相邻匝与导体，防止匝间短路。',scope:'这些是漆包线材料例子，具体漆种和耐热等级随型号变化。',refs:[2]},
    {id:'terminal',name:'外部端子',brief:'导电金属 / 可焊表面',composition:'导电金属端子与可焊镀层；具体合金和镀层随型号变化。',role:'连接绕组与PCB焊盘。',scope:'具体金属、镀层及焊接结构应查原厂材料声明。',refs:[1]}
   ],sources:[['TDK · 铁氧体组成与磁性陶瓷','https://www.tdk.com/en/tech-mag/ferrite02/001'],['Coilcraft · 绕组损耗与屏蔽结构说明','https://cps.coilcraft.com/en-us/faq/'],['Elektrisola · 漆包线导体及绝缘材料','https://update.elektrisola.com/ja/Enamelled-Wire/Info']]},
  diode:{name:'硅PN结与玻璃封装',scope:'这是硅PN结和轴向玻璃封装的组合教学示意，1N4148可作为阅读实例；肖特基、LED、SiC等使用不同结构。',caption:'P区和N区都在同一硅芯片里，中间是PN结；不是把两种独立材料拼起来。图为原理示意。',
   layers:[
    {id:'p',name:'P型区',brief:'硅 Si＋受主掺杂',composition:'硅（Si）中加入受主杂质；硼（B）是常见示例。',role:'形成以空穴为多数载流子的区域。',scope:'常见受主元素有硼；具体掺杂浓度取决于产品设计。',refs:[0]},
    {id:'junction',name:'PN结 / 耗尽区',brief:'仍为硅，不是另加一层材料',composition:'仍在硅晶体中，是PN交界附近的电荷分布区域，不是夹入的金属或绝缘薄片。',role:'形成内建电场，随偏置条件改变。',scope:'宽度为定性示意；实际结形状和工艺需查具体设计。',refs:[2]},
    {id:'n',name:'N型区',brief:'硅 Si＋施主掺杂',composition:'硅（Si）中加入施主杂质；磷（P）、砷（As）是常见示例。',role:'形成以电子为多数载流子的区域。',scope:'磷、砷等杂质加入硅中形成N区；具体浓度取决于产品设计。',refs:[0]},
    {id:'glass',name:'玻璃封装',brief:'密封玻璃；配方依封装',composition:'轴向玻璃封装；玻璃成分与配比随封装工艺变化；需要具体成分时，请索取该型号的原厂文件。',role:'保护芯片，黑色环标示阴极侧。',scope:'不能从玻璃外观推断半导体类型、材料比例或真实额定值。',refs:[1]},
    {id:'lead',name:'金属引线 / 连接',brief:'导电金属（具体合金待核对）',composition:'导电金属连接；具体合金与表面镀层应查原厂材料声明。',role:'把阳极、阴极引到外部电路。',scope:'具体芯片连接方式与支撑结构随型号变化。',refs:[1]}
   ],sources:[['BYU洁净室 · 硅晶圆P/N掺杂说明','https://www.cleanroom.byu.edu/EW_wafer_specs'],['Nexperia · 1N4148玻璃封装与平面工艺','https://www.nexperia.com/product/1N4148'],['Toshiba · PN结形成与耗尽区','https://toshiba.semicon-storage.com/us/semiconductor/knowledge/e-learning/discrete/chap1/chap1-6.html']]}
 };
 function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
 freeze(lessons);
 function lesson(course){if(!Object.hasOwn(lessons,course))throw new RangeError('Unknown material lesson');return lessons[course];}
 const api=Object.freeze({lesson});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingMaterialData=api;
})(typeof window==='undefined'?globalThis:window);

