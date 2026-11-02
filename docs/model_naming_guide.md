# 搜索结果旁的型号命名对照

在“规格条件”和“料号片段反推规格”标题旁提供“型号命名对照”按钮。
点击后使用当前页原生 popover，不打开新标签、不导航、不上传文件。
按最终可见匹配结果的品牌＋系列分组，并在组内选择实际出现的型号。
没有用一套通用字母表套用所有厂家，也不生成未出现在结果中的示例型号。
标题和按钮按内容宽度紧邻排列，不再使用固定3:2栏位留白；窄屏自动换行。
不支持横向容器的旧版保留可访问的上下排列，不影响打开命名对照。

已接入分段结构：富捷部分 FR／FP 系列、光颉 AR／CR、国巨 RT／RC、华新科 WR／WF（H／U）、
信昌 FCF 排阻、村田 GR 系列、
信昌 FV／FM／FS／FP／FN／MT／MG、三星 CL、TDK C、AMOTECH 标准 AC 系列。
某系列未接入时仍可选择，明确提示逐码规则尚未核验；如显示库内参数，
会标明这些参数不是已知的代码位置映射。未核验的尾码使用不同颜色和文字提示。

范围不是上述厂家的全系列全尾码。例如信昌 FH／FK 的电压位涉及冲击电压，
不套用 FV 的直流额定电压规则；富捷 FRT 的 X／V 温漂码也不直接套给 FTH。
显示订货代码含义不证明该组合可订购、仍在产、已认证或可直接替代。

## 依据和已复核的示例

### 2026-11-02 原厂资料补充

上一版已能选择结果中的所有品牌，但 WR／RC 等系列没有分段处理器，因此只显示
库内参数。这是本系统的接入缺口，不代表厂家没有命名规则。

本轮逐页查看原厂署名 PDF 的命名表及表头，按品牌、系列、子类型分别接入：

| 范围 | 原厂依据 | 本例与重要区别 |
| --- | --- | --- |
| Walsin WR04／06／08／12，X／W | [ASC_WR_V23，2015-04，第 6 页（原厂署名存档）](https://datasheet.lcsc.com/datasheet/pdf/b7fd8449de4a882cd112db0d86c915bb.pdf?productCode=C334789) | `WR|04|X|1602|F|T|L`；04=0402，1602=16kΩ，F=±1%，T=7英寸卷盘，L=Sn基；X/W 是类型，不是温漂。P为跳线，不解释为百分比误差。 |
| Walsin WF04／06／08／12 H | [ASC_WFxxH_V03，2023-05，第 4 页（原厂署名存档）](https://www.melchionielectronics.com/media/72/e4/9c/1759185236/walsin_series_wf04h_wf06h_wf08h_wf12h.pdf?ts=1772123888) | H为高精度厚膜；不把所有 WF 都称为薄膜。B/D为±0.1%/±0.5%。 |
| Walsin WF04／06／08／12 U | [ASC_WFxxU_V16，2012-03，第 6 页（原厂署名存档）](https://www.micros.com.pl/mediaserver/R5SK059.00b_WALSIN_0001.pdf) | U为±25ppm/℃；与WR的类型位不同。本轮只接入该版本明确的尺寸、误差和包装，不推断Q等特殊尾码。 |
| YAGEO RC | [官网 RC_L V.14，2025-11-14，第 2 页](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L) | `RC|0402|F|R|-|07|16K|L`；中间“-”是温漂按规格表，不是RT的D/C温漂表。07是标准功率7英寸卷盘，7W与7D分别涉及功率和装量；L只是订货默认码。 |
| Viking CR | [官网 CR REV.C6，2021-03-10，PDF第 3 页](https://www.viking.com.tw/Templates/att/CR_Series.pdf?lng=en) | `CR-|02|F|L|6|---|16K`；阻值区用“-”补足6位，0A=2010，而不是AR系列的尺寸表。功能P/H不凭空推断固定瓦数。 |
| PSA／PDC FCF ARRAY | [官网 FCF ARRAY Rev.12.0.I48，PDF第 4 页](https://www.pdc.com.tw/storage/architecture/product~~19/product~~105/product~~158/FCF-Array/FCF-Array.pdf) | `FCF|240|F|T|-|163`；240是0402×4凸电极排阻，163=16kΩ。与两位尺寸码的单颗FCF及FCF-E分离，不把四联排阻当成可直接替换的单颗0402。 |

这些是分系列的字段含义表，不是可订购组合生成器。没有因本轮规则说明新增型号、
改变匹配排序／价格／替代判定，也不把旧版订货表当作当前在产证明。
未覆盖的其他子系列及特殊尾码仍会明确待核验，不伪造定义。

### 此前已接入的分系列依据

- [Viking 原厂 AR Series REV.F3](https://www.viking.com.tw/Templates/att/AR_Series.pdf?lng=nl)，
  2022-02-10，Part Numbering（PDF 第 2 页）：
  `AR | 02 | B | T | C | 4703` 对应系列、0402、±0.1%、编带、±25ppm/℃、470kΩ。
- [富捷原厂署名 FRT 规格书（立创存档）](https://atta.szlcsc.com/upload/public/pdf/source/20250928/814D8B9757EBFCCAF3BFA08634B71205.pdf)，
  FJ-JS-3001-V1.0／2021-01-25，第 1 页：包装 T、端电极 S=Sn；
  特殊码 X=25ppm/℃、V=50ppm/℃。这些是该版本 FRT 的字段，不是功率码。
- [YAGEO RT 原厂数据表（存档）](https://images.100y.com.tw/pdf_file/30-YAGEO-RT-Series.pdf) 的 Ordering Information：
  `RT | 0402 | B | R | D | 07 | 470K | L`，温漂 D=25ppm/℃、C=15ppm/℃，
  与 Viking AR 的 C=25ppm/℃区分；L 为订货系统尾码，不作为生产状态或认证证明。
- [PDC 原厂目录（立创存档）](https://datasheet.lcsc.com/datasheet/pdf/3d771c0c586676719f80e96a0f8d9dcd.pdf?productCode=C525198)
  的分系列 Part Number 表。FV 的 202 为 2000V，不等同于 FH／FK 的冲击电压编码。
- AMOTECH 采用已有 `amotech_catalog.py` 的原厂核验表。应用码 A 不直接等于
  通过 AEC-Q200；2B 的 200／250V 双值保留歧义，不擅选更高值。
- 其余分段沿用当前系统已接入的品牌规则，未复核厚度／产品／包装后缀不猜测。

## 行为与安全

只投影品牌、型号、系列及公开规格字段。成本、客户、账号、票据、审计字段
不能进入面板。实际匹配结果、报价及原表均不修改。原生 popover 的开合不提交
搜索，内部选择器使用 Streamlit fragment，切换时不重跑匹配、报价或搜索审计。
旧版本不支持 fragment 时使用无需提交的静态 details 列表。

回归测试覆盖截图型号、跨品牌温漂差异、零欧／毫欧、公英制尺寸、空值、
品牌与器件类型隔离、未知尾码、HTML 转义、公开字段白名单及结果范围。
本地浏览器另用父流程计数器检查：切换品牌和具体型号后仍只执行一次父匹配流程。
本功能不改筛选数据库，但更新了应用代码，仍须重生成版本一致的 `catalog_ready`
清单，确保上一轮筛选提速不会因代码指纹变动退回慢路径。

## 全品牌覆盖扩充（进行中，非全覆盖声明）

用户要求：所有实际匹配品牌及其系列的每个代码都应完整解释，不接受用泛化参数表
冒充命名表，也不能用未公开字段或“可选择该品牌”冒充完整支持。

本轮先审计公开 prepared 目录：1,710,469 条记录，252 个原始品牌标签。
这是指定快照的记录数，不是库存数量、不保证是唯一型号数，也不是完整实时搜索输出。
原始品牌包含别名；原始系列字段中有脏值和具体料号，不能将其分组数量称为真实系列数。
SQLite 查询核心另有更多原始品牌标签，因此该快照的统计不能外推为全系统覆盖率。

### 本轮新增原厂依据

| 品牌／范围 | 原厂命名表 | 分段与边界 |
| --- | --- | --- |
| KOA RN73H、RN73R | [2026 原厂总目录第 32／34 页](https://www.koaspeer.com/pdfs/KOA_2026FullCatalog_Linked.pdf) | 系列、尺寸、端电极、包装、阻值、误差、温漂。RN73R 不套用 RN73H 的金电极；RN73H 新增 1H 不套给旧 RN73。 |
| KOA RN73 旧版 | [原厂 RN73，2022-10-05，第 1 页](https://www.koaspeer.com/pdfs/RN73.pdf) | 旧型号可解释不等于当前在产。含锡铅 L 及 TDD／TED 10 英寸包装；不以 RN73R 的当前表覆盖旧表。 |
| KOA RK73B／H／Z、RS73F／G | [2026 原厂总目录第 21／23／25／36 页](https://www.koaspeer.com/pdfs/KOA_2026FullCatalog_Linked.pdf) | RK73B 三位阻值与 RK73H 四位阻值分离；RK73Z 无阻值／误差字段，不编造尾码；A 耐热冲击与 T 端电极是两个位置。RS73 尺寸功率按本系列表，不套普通 RK73。 |
| Vishay CRCW e3 | [文档 20035，2026-04-14，第 3 页](https://www.vishay.com/docs/20035/dcrcwe3.pdf) | 四字符字母小数阻值；K=100ppm、N=200ppm；Z/0 为跳线；包装按尺寸限定。不是 CRCW-P、0201 或旧版非 e3 全覆盖。 |
| Vishay TNPW e3 | [文档 28758，2026-04-10，第 4 页](https://www.vishay.com/docs/28758/tnpw_e3.pdf) | H/E/X/Y=50/25/15/10ppm；0H=单一批次日期码。不能与 CRCW 的温漂字母表互换。EC 装量限 25/50ppm。 |
| Vishay RNC／RNR | [文档 31025，2025-09-04，第 2 页](https://www.vishay.com/docs/31025/erc.pdf) | 军标外形、温漂、四位阻值、误差、失效率等级、包装、已公开热浸锡选项。失效率 S 不解释成精度或生产状态；其他特殊编号保留未核验。 |
| Vishay CMF50／55／60 Industrial | [文档 31018，2025-02-21，第 2 页](https://www.vishay.com/docs/31018/cmfind.pdf)、[原厂包装文档 31544，2013-02-25，第 1／4 页](https://www.vishay.com/docs/31544/packthre.pdf) | 六字符字母小数阻值、误差、温漂、包装；BF 为含铅散装，EK 为无铅散装。EB 采用 2025 CMF 表的弹药盒定义，不混用 2013 编带定义。军标、阻燃及未知特殊编号不标完整。 |
| PSA／PDC FAF | [FAF Rev.7.0.M46，PDF 第 5 页](https://www.pdc.com.tw/storage/architecture/product~~19/product~~105/product~~160/FAF.pdf)、[2020 原厂目录正文第 75 页](https://www.pdc.com.tw/storage/architecture/product~~19/product~~123/2020_3in1_catalog.pdf) | 尺寸、误差、包装、功率、四位阻值、温漂、已公开 HC／M／MF／MH 订货类型。标准功率与功能功率位置独立；三字符丝印／订货示例存在歧义，暂不猜测。 |
| PSA／PDC FPS／FPF／FWF／单颗 FCF | [2020 原厂目录正文第 62／63／69／70 页](https://www.pdc.com.tw/storage/architecture/product~~19/product~~123/2020_3in1_catalog.pdf) | 各系列分别约束尺寸、功率、温漂与特殊码；普通 FCF 不套排阻和 FCF-E 低阻版本；未编码的标准温漂不虚构代码。FPF 的增强功率 K／包装 Q 不套给 FPS。 |
| Stackpole RNCF | [原厂署名 RNCF，2022-07-08，第 8 页（欧洲存档）](https://stackpole-europe.com/specs/SEI-RNCF.pdf) | 尺寸、误差、包装、温漂、四字符阻值。三个不同位置的 T 分别可能是 ±0.01%、卷盘和 10ppm，不能混用。 |

本轮本地目录审计：完整逐码解释由 65,434 条增加到 488,021 条，
部分解释 47,379 条，其余 1,175,069 条尚未接入；**仍未达到用户要求的全覆盖**。
旧版、特殊后缀、原厂内部编号及其他品牌仍须逐项核验，不删减原匹配结果来提高覆盖率。
面板现在区分“本型号逐码解释完整”和“已核验 X/Y 段，尚未完整”，并为本轮规则附原厂资料入口。

### 可重复的完整度验收

`tools/audit_model_naming_coverage.py` 只读取显式给定的公开 parquet，
不导入应用、不登录、不读取会员／成本／报告库。输出范围说明、源文件校验值、
原始品牌＋系列＋器件类型分组及未完成示例。

使用 `--require-complete` 时，只要存在一个部分解释、无解释或空输入，就不能验收为全覆盖
（非零退出码 2）。该检查与发布回归门禁分离：通过回归测试不代表已完成全品牌内容。
不把实时网络请求放进对照面板，切换命名说明仍不重新查询物料或价格。
