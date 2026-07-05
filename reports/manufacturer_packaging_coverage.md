# 原厂标准包装数量覆盖报告

- 核验日期：2026-07-04
- 定义：系统 `MOQ` 优先使用当前启用成本清单中的采购 MOQ；采购 MOQ 为空时，才回退显示原厂标准包装数量。
- 边界：原厂标准包装数量不是经销商拆包 MOQ，也不是商务合同中的最低订购量。

## 第一批覆盖

| 器件/系列 | 原厂证据 | 已覆盖型号行数 | 规则 |
|---|---|---:|---|
| Panasonic ERJ/ERA 贴片电阻 | [Surface Mount Resistors Packaging Method](https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL26.pdf) | 65,820 | 按原厂料号家族和 EIA 尺寸匹配标准每卷数量 |
| YAGEO RC 厚膜贴片电阻 | [RC_L Series Table 4](https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L) | 15,032 | 同时校验型号中的尺寸、包装代码和 7 英寸卷盘代码 |
| TDK C1608 MLCC | [TDK C1608 型号页](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608C0G2E182J080AA) | 847 | 仅覆盖型号明确含 `C1608 / 080 / A` 的 0.80mm、180mm 纸带卷盘产品 |
| Vishay NTCS0402E | [官方规格书](https://www.vishay.com/docs/29003/ntcs0402e3t.pdf) | 22 | 10,000 pcs/卷 |
| Vishay NTCS0603E | [官方规格书](https://www.vishay.com/docs/29056/ntcs0603e3t.pdf) | 34 | 4,000 pcs/卷 |
| Vishay NTCS0805E | [官方规格书](https://www.vishay.com/docs/29044/ntcs0805e3t.pdf) | 41 | 4,000 pcs/卷 |

合计覆盖：`81,796` 条型号记录。

## 第二批覆盖

| 器件/系列 | 原厂证据 | 已覆盖型号行数 | 规则 |
|---|---|---:|---|
| Murata GRM MLCC | [村田型号包装页](https://www.murata.com/en-us/products/productdetail?partno=GRM155R71E472KA01%23) | 8,633 | 同时校验系列、EIA 尺寸和型号末位包装代码 |
| Murata GCM MLCC | [村田型号包装页](https://www.murata.com/products/productdetail?partno=GCM188R71H103KA37%23) | 6,228 | 同时校验系列、EIA 尺寸和型号末位包装代码 |
| Murata GCJ MLCC | [村田型号包装页](https://www.murata.com/en-us/products/productdetail?partno=GCJ21BR71H104KA01%23) | 1,063 | 仅覆盖已确认的 0603/0805 纸带或压纹带包装代码 |
| YAGEO CC MLCC | [0201 R 包装页](https://yageogroup.com/products/Capacitors/part/CC0201KRX5R7BB104)、[0603 P 包装页](https://yageogroup.com/products/Capacitors/part/CC0603KPX7R7BB104) | 3,534 | 覆盖 0201/0402/0603 中数量可由包装代码唯一确定的 R/P 型号 |
| TDK C 系列 MLCC | [C0603 型号页](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C0603C0G1E100D030BA)、[C2012 060 型号页](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G2W221J060AE)、[C2012 125 型号页](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012X5R1V226M125AC) | 2,239 | 按公制尺寸码、厚度码和卷盘代码组合匹配；包含第一批 C1608 的 847 条 |
| TDK NTCG 贴片热敏电阻 | [NTCG063 型号页](https://product.tdk.com/en/search/sensor/ntc/chip-ntc-thermistor/info?part_no=NTCG063JF103FTDS) | 158 | 覆盖 0201/0402/0603 三种尺寸 |
| Samsung CL MLCC | [三星 2025 MLCC 原厂目录](https://m.samsungsem.com/resources/file/global/support/product_catalog/MLCC_2512.pdf) | 3,020 | 只覆盖末位 `C` 的 7 英寸卷盘，并按尺寸与厚度区分纸带/压纹带数量 |

第二批净新增：`24,028` 条型号记录；两批去重后合计覆盖：`105,824` 条。

## 第三批覆盖

| 器件/系列 | 原厂证据 | 已覆盖型号行数 | 规则 |
|---|---|---:|---|
| Samsung RC/RCS 贴片电阻 | [三星 Chip Resistor 原厂目录](https://www.samsungsem.com/resources/file/global/support/product_catalog/Chip_Resistor.pdf) | 7,609 | 型号必须以 `RC/RCS + 公制尺寸码` 开头并以 7 英寸包装码 `CS` 结尾；数量按公制尺寸码确定 |
| Walsin WR 贴片电阻 | [华新科 WR 2025 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/chipR/ASC_WR.pdf) | 5,050 | 从型号中的 WR 尺寸码、包装码和终端码组合确定卷盘数量；散装及非标准后缀不回填 |
| Walsin 常规/NP0 MLCC | [华新科 General Purpose MLCC 2026 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_General_Purpose.pdf) | 9,957 | 仅覆盖包装末位 `T` 的 7 英寸卷盘，并同时校验 EIA 尺寸和厚度 |

第三批净新增：`22,616` 条型号记录；三批去重后合计覆盖：`128,440` 条。

## 第四批覆盖

| 器件/系列 | 原厂证据 | 已覆盖型号行数 | 规则 |
|---|---|---:|---|
| Samsung RU/RUK/RUT/RJ 电阻 | [三星 Chip Resistor 原厂目录](https://www.samsungsem.com/resources/file/global/support/product_catalog/Chip_Resistor.pdf) | 455 | 仅覆盖后缀 `CS` 的 7 英寸包装；RU/RUK/RUT 按公制尺寸码，RJ 同时处理 1220 低至 2mΩ 的压纹带特例 |
| Walsin SH 软端 MLCC | [SH 2026 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Soft_term_SH.pdf) | 484 | 校验 SH 尺寸码、EIA 尺寸、厚度和 `CT` 包装 |
| Walsin RF 微波 MLCC | [RF 2026 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Microwave_RF.pdf) | 569 | 校验 RF 尺寸码、EIA 尺寸、厚度和 `CT` 包装 |
| Walsin HH 高 Q/低 ESR MLCC | [HH 2026 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_HQ_Low_ESR_HH.pdf) | 434 | 校验 HH 尺寸码、EIA 尺寸、厚度和 `CT` 包装 |
| Walsin MT 车规 MLCC | [MT 2026 原厂规格书](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Automotive_MT.pdf) | 73 | 校验 MT 尺寸码、EIA 尺寸、厚度和 `CT` 包装 |

第四批净新增：`2,015` 条型号记录；四批去重后合计覆盖：`130,455` 条。

## 规格参数抽查

- `RC0603FR-0710KL`：0603、10KΩ、±1%，与 YAGEO RC_L 型号规则一致；标准 7 英寸纸带卷盘为 5,000 pcs。
- `ERJ6GEYJ103V`：0805、10KΩ、±5%，与 Panasonic ERJ 料号规则一致；标准卷盘为 5,000 pcs。
- `NTCS0603E3222JMT`：2.2KΩ、±5%、B25/85=3520K，与 Vishay 29056 规格书一致；4,000 pcs/卷。
- `NTCS0402E3104FHT`：100KΩ、±1%、B25/85=3950K，与 Vishay 29003 规格书一致；10,000 pcs/卷。
- `NTCS0805E3223FHT`：22KΩ、±1%、B25/85=3800K，与 Vishay 29044 规格书一致；4,000 pcs/卷。
- `C1608C0G2E182J080AA`：0603、C0G、1.8nF、±5%、250V、厚度 0.80mm，与 TDK 型号页一致；4,000 pcs/卷。

## 仍需原厂资料的参数缺口

- 铝电解电容：ESR、纹波电流、寿命仍有明显空缺，必须按系列规格书和壳号补充。
- 压敏电阻：无法由标准型号编码可靠解出的标称压敏电压继续留空。
- 共模电感：部分系列缺阻抗/电感、额定电流、DCR、回路数或尺寸。
- 晶振：部分系列行只有频率范围，没有唯一负载电容，不能补成单一值。
- MLCC：包装数量通常同时取决于尺寸、厚度和载带/卷盘代码，不能仅按 0402/0603 等尺寸统一填值。
- Samsung CL：末位非 `C` 的型号可能是 10/13 英寸卷盘、定向包装或数量选项，未唯一确认前不补。
- YAGEO CC 0805 及更大尺寸：相同包装字母仍可能因具体料号而有不同数量，不能套用单一尺寸规则。
- Murata LQW 等电感：库中大量型号以 `#` 代替实际包装后缀；原厂同一基础型号可同时有散装和多种卷盘数量，因此继续留空。
- Walsin 常规 1812：库内主要记录为 3.20mm 厚，但 2026 原厂包装表只列到 2.80mm；这 1,298 条继续留空。
- Samsung RC：部分库记录的 `尺寸（inch）` 实际存放公制代码；本轮 MOQ 从已校验的型号公制尺寸码解析，不把该字段当成包装依据。
- Samsung RUW：库内仅 1 条，当前原厂包装表未明确列入 RUW，继续留空。
- Walsin SH/RF/MT：部分库内厚度不在对应系列当前原厂表中，例如 SH 1812 的 3.20mm、RF 0805 的 1.25mm 和多条 MT 的 0.85mm；不跨系列套用数量。

## 写入原则

- 成本清单 MOQ 优先于原厂标准包装数量。
- 只有品牌、系列、尺寸和包装代码全部满足原厂规则时才显示回退 MOQ。
- 无法唯一确认的型号保持空白，列入最终例外清单；只有取得可唯一定位的包装代码或原厂型号页后才补充。

## 2026-07-05 全库最终审计

- 全库记录：`1,676,716` 条。
- 原厂标准包装数量可可靠回退：`452,883` 条，占全库 `27.01%`。
- 本次一次性净新增：`322,428` 条，覆盖从 `130,455` 条提高到 `452,883` 条。
- 新增范围：KOA RN73H/RN73R、RS73、RK73、SG73、HV73、WK73 等明确 `TP/TD/TE` 包装码系列；YAGEO RT/AC/AA/AT/RE/PT/AR/RL/RP；Vishay CRCW 0201、无铅/含铅包装码及 TNPW 明确包装码。
- 原厂依据：[KOA Appendix C](https://www.koaglobal.com/-/media/Files/KOA_Global/EN/product/commonpdf/chip_taping.pdf)、[YAGEO RT](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L)、[YAGEO AC](https://www.yageogroup.com/content/datasheet/asset/file/PYU-AC_51_ROHS_L)、[Vishay CRCW e3](https://www.vishay.com/docs/20035/dcrcwe3.pdf)、[Vishay CRCW 含铅版](https://www.vishay.com/doc?20008=)、[Vishay TNPW e3](https://www.vishay.com/docs/28758/tnpw_e3.pdf)。

### 最终例外边界

- 轴向、军规和通孔电阻常同时提供散装、编带、弹药盒或不同卷盘，型号未带包装后缀时不能唯一确定数量；主要包括 Vishay RNC/CMF/RLR/RN、YAGEO MF/FMP、Stackpole RNCF/RNF 等。
- KOA 旧版 RN73 共 `47,096` 条未出现在当前 Appendix C 的系列清单中，不把新版 RN73H/RN73R 数量反向套给旧料号。
- PSA FAF-MH 等系列虽数量大，但当前料号未提供可由原厂表唯一解出的包装代码，继续留空。
- Vishay CRCW 的 `EB`、TNPW 的 `EN` 等旧/特殊包装代码未被当前原厂表定义，继续留空。
- YAGEO AF 0201/0402 的相同 `07` 代码对应 10,000/20,000 两种每卷数量，料号无法唯一分辨时不回填。
- MLCC、电感和热敏器件仍需同时校验厚度、载带材料、卷径及完整包装后缀；缺一项不按尺寸猜测。
- 验证：发布安全门 14/14 系统回归通过；真实会员、成本清单和未匹配数据库及事务文件指纹保持不变。
