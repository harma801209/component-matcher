# 搜索结果旁的型号命名对照

在“规格条件”和“料号片段反推规格”标题旁提供“型号命名对照”按钮。
点击后使用当前页原生 popover，不打开新标签、不导航、不上传文件。
按最终可见匹配结果的品牌＋系列分组，并在组内选择实际出现的型号。
没有用一套通用字母表套用所有厂家，也不生成未出现在结果中的示例型号。

已接入分段结构：富捷部分 FR／FP 系列、光颉 AR、国巨 RT、村田 GR 系列、
信昌 FV／FM／FS／FP／FN／MT／MG、三星 CL、TDK C、AMOTECH 标准 AC 系列。
某系列未接入时仍可选择，明确提示逐码规则尚未核验；如显示库内参数，
会标明这些参数不是已知的代码位置映射。未核验的尾码使用不同颜色和文字提示。

范围不是上述厂家的全系列全尾码。例如信昌 FH／FK 的电压位涉及冲击电压，
不套用 FV 的直流额定电压规则；富捷 FRT 的 X／V 温漂码也不直接套给 FTH。
显示订货代码含义不证明该组合可订购、仍在产、已认证或可直接替代。

## 依据和已复核的示例

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
