/* Bounded, offline teaching rules. Decoding is not catalog validation. */
(function(root){
 'use strict';
 const tolerance={B:'0.1',C:'0.25',D:'0.5',F:'1',G:'2',J:'5'};
 const sizes={'0201':'0603','0402':'1005','0603':'1608','0805':'2012','1206':'3216','1210':'3225','1812':'4532','2010':'5025','2512':'6432'};
 const sourceFOJAN=['富捷 · 官方产品中心（规则沿用系统已核对资料）','https://www.fojan.cn/product'];
 const examples=['FRC0603J221 TS','FRL1206FR470TS','FRM253WFR120TM','FCM25123WF0M30TM','RC0603FR-0710KL','GRM188R71H104KA93D','1N4148'];
 const field=(code,label,value)=>({code,label,value});
 const result=(status,message,model,fields=[],sources=[])=>({status,message,model,fields,sources});
 function resistance(code){
  if(/^\d{3,4}$/.test(code))return Number(code.slice(0,-1))*10**Number(code.slice(-1));
  if(/^\d*R\d+$/.test(code))return Number(code.replace('R','.'));
  if(/^\d+M\d{2,3}$/.test(code))return Number(code.replace('M','.'))/1000;
  return NaN;
 }
 function ohms(n){if(n===0)return '0 Ω';if(n<1)return Number((n*1000).toPrecision(7))+' mΩ';if(n>=1e6)return Number((n/1e6).toPrecision(7))+' MΩ';if(n>=1e3)return Number((n/1e3).toPrecision(7))+' kΩ';return Number(n.toPrecision(7))+' Ω';}
 function oneEdit(a,b){
  if(a===b||Math.abs(a.length-b.length)>1)return false;
  if(a.length===b.length)return [...a].filter((c,i)=>c!==b[i]).length===1;
  const short=a.length<b.length?a:b,long=a.length>b.length?a:b;let i=0,j=0,skips=0;
  while(i<short.length&&j<long.length){if(short[i]===long[j]){i++;j++;}else{j++;skips++;if(skips>1)return false;}}
  return true;
 }
 function decode(input){
  const raw=String(input||'').trim();
  if(!raw)return result('input','请先输入完整型号。','');
  if(raw.length>96||/[\n\r<>;；Ω%]/.test(raw))return result('input','请确认搜索内容是否正确：这里一次输入一个型号，不要附带规格描述。','');
  const model=raw.toUpperCase().replace(/\s+/g,'');
  // Whitespace is an allowed formatting difference; punctuation is not erased.
  let m=model.match(/^(FRC|FRL)(0201|0402|0603|0805|1206|1210|1812|2010|2512)([BCDFGJ])([0-9R]+)TS$/);
  if(m){
   const [,series,size,tol,value]=m,n=resistance(value),expected=tol==='J'&&series==='FRC'&&!value.includes('R')?3:4;
   if(value.length!==expected||!Number.isFinite(n)||(series==='FRL'&&!(n>0&&n<1))||(series==='FRC'&&n>0&&n<1))return result('suspected','阻值码长度或系列与阻值组合疑似有误，请核对完整型号；不会自动补码。',model);
   return result('decoded','已按编码格式拆解；不代表完整料号已在目录、库存或价格清单中确认。',model,[field(series,'品牌 / 系列',series==='FRC'?'FOJAN(富捷) · 常规厚膜电阻':'FOJAN(富捷) · 低阻电阻'),field(size,'封装代码','英制 '+size+' / 常用公制 '+sizes[size]),field(tol,'精度码','±'+tolerance[tol]+'%'),field(value,'阻值码',ohms(n)),field('T','包装码','7英寸卷带'),field('S','端电极码','锡端电极')],[sourceFOJAN]);
  }
  m=model.match(/^FRM(06|08|12|20|25)(02|05|07|15|[123]W)([DFGJ])(R\d{3,4})T(ML|M|N|K)$/);
  if(m){const [,size,power,tol,value,terminal]=m;return result('decoded','按富捷合金电阻格式拆解；阻值范围、功率组合及端电极适用性仍须核对该系列规格书。',model,[field('FRM','品牌 / 系列','FOJAN(富捷) · 合金低阻贴片电阻'),field(size,'封装代码',{'06':'0603','08':'0805','12':'1206','20':'2010','25':'2512'}[size]+'（英制）'),field(power,'功率码',{'02':'0.25 W','05':'0.5 W','07':'0.75 W','15':'1.5 W'}[power]||power.replace('W',' W')),field(tol,'精度码','±'+tolerance[tol]+'%'),field(value,'阻值码',ohms(resistance(value))),field('T','包装码','卷带'),field(terminal,'端电极 / 特殊码','保留代码 '+terminal+'，须按 FRM 对应版本核对，不套用 FRC 规则')],[sourceFOJAN]);}
  m=model.match(/^FCM(2512|3920|5930)([1-9]\d?W)([DFGJ])(R\d{3,4}|\d+M\d{2,3})([TRB])M$/);
  if(m){const [,size,power,tol,value,pack]=m;return result('decoded','按 FCM 裸片高功率合金电阻格式拆解；编码解释不等于阻值范围、功率组合或价格已确认。',model,[field('FCM','品牌 / 系列','FOJAN(富捷) · 裸片高功率合金电阻'),field(size,'封装代码',size+'（英制代码）'),field(power,'功率码',power.replace('W',' W')),field(tol,'精度码','±'+tolerance[tol]+'%'),field(value,'阻值码',ohms(resistance(value))),field(pack,'包装码',{T:'卷带',R:'卷带（规格须核对）',B:'散装'}[pack]),field('M','端电极码','保留 M，须按 FCM 规格书核对')],[sourceFOJAN]);}
  if(/^FCM(2512|3920|5930)[1-9]\d?W(R\d{3,4}|\d+M\d{2,3})[TRB]M$/.test(model))return result('suspected','型号疑似缺少精度码：功率码后、阻值码前应有精度代码。请核对原始规格书，不会自行补成 F 或其他代码。',model);
  if(model==='RC0603FR-0710KL'||model==='RC0603FR0710KL')return result('example','已核对的国巨具体型号示例；不将这些参数外推到其他 RC 型号。',model,[field('RC','品牌 / 系列','YAGEO(国巨) · 常规厚膜电阻'),field('0603','封装','英制0603 / 公制1608'),field('F','精度','±1%'),field('10K','阻值','10 kΩ'),field('R / 07 / L','订购后缀','完整订购码须保留；不当作电气数值'),field('规格书参数','功率 / 最高连续工作电压','0.1 W（70°C） / 75 V；实际允许电压还受功耗限制')],[['YAGEO · 此完整型号规格书','https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL']]);
  if(model==='GRM188R71H104KA93D'||model==='GRM188R71H104KA93')return result('example',model.endsWith('D')?'已核对的村田具体型号示例；末尾 D 为包装规格码。':'识别到村田电气基础型号；订购前还须核对末尾包装规格码，并非一概判为打错。',model,[field('GRM','品牌 / 系列','Murata(村田) · 通用 MLCC'),field('188','尺寸相关码','此型号英制0603 / 公制1608；含尺寸 / 厚度信息，不仅是长宽'),field('R7','介质特性','X7R'),field('1H','额定电压','50 Vdc'),field('104','容量码','100000 pF = 100 nF = 0.1 µF'),field('K','容量精度','±10%'),field('A93 / D','规格 / 包装后缀','完整代码须保留；工作有效容量须查偏压曲线')],[['Murata · 此型号与包装代码','https://www.murata.com/en-us/products/productdetail?partno=GRM188R71H104KA93%23']]);
  if(model==='1N4148')return result('example','识别到通用二极管型号。仅凭 1N4148 不能确定厂家；以下以 Nexperia 规格书示范，不按字符拆出电气参数。',model,[field('1N4148','类型','小信号开关二极管（厂商须另行确认）'),field('规格书示例','封装','Nexperia 示例为 DO-35'),field('测试条件','正向压降','Vf最大1 V，条件 If=10 mA；不是固定压降')],[['Nexperia · 1N4148 / 1N4448','https://assets.nexperia.com/documents/data-sheet/1N4148_1N4448.pdf']]);
  const hint=examples.map(x=>x.replace(/\s+/g,'')).find(x=>oneEdit(model,x));
  if(hint)return result('suspected','型号疑似漏码或错码：与教学示例 '+hint+' 相差一个字符。请核对，不会自动更改为该示例。',model);
  if(/^(FRC|FRL|FRM|FCM)\d/.test(model))return result('suspected','疑似富捷型号，格式与本课堂已覆盖规则不一致：可能缺码、错码，也可能属于未覆盖订购变体。请确认搜索内容是否正确并核对规格书。',model);
  return result('unsupported','此型号暂未覆盖，不能据此判断型号错误。请确认搜索内容是否正确，并查看对应厂家的完整订购规则；1N 等通用编号不能单独确定品牌。',model);
 }
 const scenarios=[
  {id:'r-power',course:'resistor',title:'电阻 · 功耗与降额',question:'教学任务：1 kΩ 电阻上连续施加10 V，P=0.1 W。要求在本场景温度条件下，功耗不超过降额后允许功率的50%，且器件电压限制不低于10 V。哪份候选资料满足题设？',options:['降额后允许0.125 W；电压上限50 V','降额后允许0.25 W；电压上限50 V','降额后允许0.25 W；电压上限8 V'],answer:1,why:['功耗占允许值80%，不满足题设50%余量。','0.1/0.25=40%，且10 V低于50 V；满足本题两项条件。','功率余量满足，但10 V超过8 V限制。'],explain:'必须同时核对功率与电压。本题的50%是教学设计要求，不是所有电阻的通用厂家规则。'},
  {id:'r-unit',course:'resistor',title:'电阻 · 毫欧与兆欧',question:'客户要求电流检测电阻5 mΩ、±1%，你核对到下列两份资料，其他条件尚未提供。下一步应该怎样处理？',options:['用5 MΩ代替，字母大小写无所谓','先选择标明0.005 Ω、±1%的候选继续核对功率、TCR与电流条件','只要封装一样，任意阻值都可替代'],answer:1,why:['5 mΩ=0.005 Ω，5 MΩ=5000000 Ω，不能混淆。','单位与精度符合；还不能仅凭这两项宣布可以量产替代。','封装相同不等于电气参数相同。'],explain:'m与M是不同前缀。型号、单位和测试条件都要复核。'},
  {id:'c-bias',course:'capacitor',title:'电容 · 有效容量',question:'教学任务：工作点需要有效容量至少8 µF。候选A与B标称均10 µF、耐压均高于工作电压；相应偏压/温度曲线及误差核对后，工作点容量下限分别为5 µF与9 µF。哪一个满足本题容量要求？',options:['A，标称10 µF已经足够','B，工作点下限9 µF达到要求','二者都满足，因为标称相同'],answer:1,why:['A在题设工作点下限5 µF，小于8 µF。','9 µF大于8 µF；实际选型仍需核对阻抗、封装及其他条件。','不能仅用标称容量替代工作有效容量。'],explain:'这些是教学候选条件，不是某厂家真实偏压曲线。'},
  {id:'c-units',course:'capacitor',title:'电容 · 容量码104',question:'在本题采用的三位数字容量码中，前两位为有效数字，第三位为以pF计的十进制倍率。104对应多少容量？',options:['104 pF','100 nF（0.1 µF）','10 µF'],answer:1,why:['104不是直接读成104 pF。','10×10⁴ pF=100000 pF=100 nF=0.1 µF。','10 µF为10000000 pF，不是104。'],explain:'此规则须先确认适用于该厂家系列；容量码之外仍有耐压、介质与精度。'},
  {id:'l-current',course:'inductor',title:'电感 · 峰值与有效值',question:'教学波形已算出峰值2.5 A、有效值1.8 A。按本题规定，需要Isat>2.5 A且Irms>1.8 A；三份资料采用同一温度与跌落判据，哪项通过这两项初筛？',options:['Isat=2 A，Irms=3 A','Isat=3 A，Irms=2.2 A','Isat=3 A，Irms=1.5 A'],answer:1,why:['Isat不满足峰值要求，即使Irms较大。','两项均满足题设；仍须查L下降、损耗与热条件。','Irms低于1.8 A，即使Isat足够。'],explain:'Isat和Irms不能互换；实际判据与温升条件因系列而异。'},
  {id:'l-loss',course:'inductor',title:'电感 · DCR铜损',question:'理想直流教学计算：电流2 A，A的DCR=0.1 Ω，B的DCR=0.05 Ω。仅比较I²×DCR铜损，下列判断正确的是？',options:['A为0.4 W，B为0.2 W；不能由此断言总损耗或温升','A与B相同，因为电感量相同','B必定总损耗减半且温升减半'],answer:0,why:['计算正确；未包括磁芯损耗、交流绕组损耗和散热。','铜损与DCR有关，不能只看电感量。','仅能说明这部分直流铜损，不能外推总损耗与温升。'],explain:'不同器件的总损耗与温升要结合实际频率、纹波和热条件。'},
  {id:'d-vf',course:'diode',title:'二极管 · 读测试条件',question:'资料A的Vf在If=1 mA、25°C测得，资料B在If=100 mA、25°C测得。能否直接按这两个数字大小判断哪颗在100 mA下压降更低？',options:['可以，Vf就是固定常数','不可以，应比较相同电流和温度下的数据','只要封装一样就可以'],answer:1,why:['Vf随电流与温度等条件变化。','需查两颗在100 mA、相同温度下的曲线或规格。','封装相同不能补齐测试条件。'],explain:'还应核对耐压、电流限制、功耗与开关特性。'},
  {id:'d-polarity',course:'diode',title:'二极管 · 极性与通用编号',question:'本题已确认轴向玻璃封装规格书注明黑环为阴极K。仅凭通用型号1N4148，哪种说法正确？',options:['黑环是阳极，且型号只能属于一家品牌','黑环为阴极；厂家与完整订购规格仍须另行核对','反向接法下任何电压都不会有电流'],answer:1,why:['与本题已确认的封装标记相反，通用编号也不唯一指定厂家。','极性依据本题规格书；通用编号不能单独确定品牌。','真实器件存在反向漏电，超额定条件还可能击穿。'],explain:'其他封装的标记应查各自规格书，不可只按外观猜测。'}
 ];
 const ids=['quiz-resistor','quiz-capacitor','quiz-inductor','quiz-diode',...scenarios.map(q=>q.id)];
 function validRecords(data){const clean={};if(!data||typeof data!=='object'||Array.isArray(data))return clean;for(const id of ids){const r=Object.prototype.hasOwnProperty.call(data,id)?data[id]:null;if(r&&typeof r==='object'&&Number.isInteger(r.choice)&&r.choice>=0&&r.choice<3&&typeof r.correct==='boolean'&&Number.isInteger(r.attempts)&&r.attempts>0&&r.attempts<=10000)clean[id]={choice:r.choice,correct:r.correct,attempts:r.attempts};}return clean;}
 function grade(q,choice){if(!q||!Number.isInteger(choice)||choice<0||choice>=q.options.length)throw new RangeError('请选择一个选项');return choice===q.answer;}
 const api=Object.freeze({decode,resistance,oneEdit,examples:Object.freeze(examples),scenarios:Object.freeze(scenarios),validRecords,grade});
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingPractice=api;
})(typeof window==='undefined'?globalThis:window);
