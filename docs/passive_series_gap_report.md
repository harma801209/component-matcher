# Passive Series Gap Report

- Generated: `2026-04-23T05:25:05+08:00`
- Total passive rows: `1,341,695`
- Unresolved rows: `415,462`
- Resolved rows: `926,233`
- Unresolved brands: `177`
- Unresolved brand/type pairs: `370`

## Top Unresolved Brands

| Brand | Unresolved | Total | Coverage | Registry | Lookup Method |
| --- | ---: | ---: | ---: | --- | --- |
| 威世Vishay | 134,033 | 464,712 | 71.16% | partial | Official resistor family pages and datasheets |
| 国巨YAGEO | 87,552 | 178,232 | 50.88% | partial | YAGEO product guide and official family naming rules |
| Stackpole | 29,496 | 92,327 | 68.05% | partial | Official resistor series catalog and datasheets |
| TE Connectivity(泰科电子) | 17,492 | 40,218 | 56.51% | partial | TE passive product pages and passive product datasheets |
| Meritek | 9,470 | 9,470 | 0.00% | partial | Official site product pages and datasheets for resistor families and model-prefix ordering codes |
| Ohmite | 8,417 | 8,417 | 0.00% | partial | Official product-family pages and datasheets for resistor and thermal family ordering codes |
| 村田Murata | 8,275 | 8,502 | 2.67% | partial | Murata product family pages and SimSurfing/product catalogs |
| KOA | 8,179 | 257,740 | 96.83% | partial | KOA catalog family tables and product series pages |
| 三星Samsung | 8,065 | 8,158 | 1.14% | partial | Official chip resistor product page and part-number query pages |
| 风华Fenghua | 7,244 | 7,343 | 1.35% | partial | Official product pages and catalog model rules |
| 旺诠RALEC | 6,175 | 6,175 | 0.00% | partial | Official product search and resistor family pages for part-number prefix rules |
| Bourns | 6,146 | 6,200 | 0.87% | partial | Official varistor product pages and ordering-code briefs |
| VO(翔胜) | 5,756 | 5,756 | 0.00% | missing | - |
| 华新科Walsin | 5,665 | 5,665 | 0.00% | partial | Official product taxonomy and resistor series pages |
| 日本贵弥功Chemi-Con | 5,543 | 5,543 | 0.00% | missing | - |
| FOJAN(富捷) | 5,491 | 5,491 | 0.00% | missing | - |
| Littelfuse | 5,222 | 5,222 | 0.00% | partial | Official varistor family pages and ordering terminology notes |
| EVER OHMS(天二科技) | 5,212 | 5,212 | 0.00% | partial | Official product pages and series PDFs for thick-film and metal-alloy resistor families |
| CAL-CHIP | 5,007 | 5,007 | 0.00% | partial | Official chip-resistor product pages, PDFs, and series ordering tables |
| Panasonic | 4,420 | 71,250 | 93.80% | partial | Official resistor catalog and part-number family pages |
| 尼吉康Nichicon | 3,821 | 3,821 | 0.00% | partial | Official capacitor family pages, catalogs, and product search/document library for series codes |
| LIZ(丽智电子) | 3,770 | 3,770 | 0.00% | partial | Official product family pages and datasheets for resistor, thermistor, and sensing families |
| RCD Components, Inc. | 3,716 | 3,716 | 0.00% | partial | Official product pages and resource library for resistor, network, and power component model codes |
| RESI(开步睿思) | 3,350 | 3,350 | 0.00% | missing | - |
| Venkel | 2,535 | 2,535 | 0.00% | partial | Official product pages and datasheets for passive-component family codes |

## Top Unresolved Component Types

| Component Type | Unresolved Rows |
| --- | ---: |
| 薄膜电阻 | 201,017 |
| 厚膜电阻 | 113,400 |
| 绕线电阻 | 37,922 |
| 金属氧化膜电阻 | 14,957 |
| 贴片压敏电阻 | 12,739 |
| 碳膜电阻 | 11,569 |
| 铝电解电容 | 10,744 |
| 射频电感 | 5,037 |
| 功率电感 | 2,765 |
| 热敏电阻 | 2,209 |
| 磁珠 | 1,057 |
| 贴片电阻 | 946 |
| 合金电阻 | 832 |
| 共模电感 | 257 |
| 引线型压敏电阻 | 11 |

## Priority Brand / Type Gaps

### 威世Vishay / 薄膜电阻 / 100,654 rows

- Registry status: `partial`
- Lookup method: Official resistor family pages and datasheets
- Official sources:
  - `product-family`: https://www.vishay.com/en/resistors-fixed/thinfilm/
  - `official-site`: https://www.vishay.com/
- Top unresolved prefixes: `0805` (2369), `MCT` (2202), `MMA0204` (1823), `SMM0204` (1586), `0402` (1325), `CMF551K` (1109), `SFR16` (1083), `ERC551K` (950), `1206` (918), `PLTT0805Z` (886)
- Sample models: `SMM02040C6812FB300`, `SMM02040C1009FB300`, `SMM02040C1629FB300`, `SMM02040C2000FB300`, `SMM02040C3322FB300`, `SMM02040C3329FB300`, `SMM02040C1000FB300`, `SMM02040C5109FB300`

### 国巨YAGEO / 薄膜电阻 / 62,993 rows

- Registry status: `partial`
- Lookup method: YAGEO product guide and official family naming rules
- Official sources:
  - `application-guide`: https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/YAGEO%20Group%20SMD%20Chip%20Resistor%20Application%20%26%20Safety%20Guide.pdf
  - `official-site`: https://www.yageo.com/
- Top unresolved prefixes: `50` (7105), `25` (5283), `MFR-25FR` (1969), `MFR-25FT` (1409), `MFR-50FR` (1133), `FMP-50FR` (1133), `MFR100FRF` (1129), `MFR100FTF` (1127), `MMF-25FR` (1051), `MFR1WSFR` (954)
- Sample models: `PE1206FRF470R02L`, `PE2512FKF7W0R025L`, `MMF-25FRE22K`, `MMF-25FRE39K`, `MMF207FRE680R`, `PE1206FRF070R2L`, `PE0805JRF7T0R005L`, `MMP200JR-10K`

### 威世Vishay / 绕线电阻 / 16,253 rows

- Registry status: `partial`
- Lookup method: Official resistor family pages and datasheets
- Official sources:
  - `product-family`: https://www.vishay.com/en/resistors-fixed/thinfilm/
  - `official-site`: https://www.vishay.com/
- Top unresolved prefixes: `RWR84N` (745), `AC` (622), `0101` (539), `0010` (509), `0005` (456), `CW02B` (446), `CW010R` (412), `0002` (370), `0103` (342), `0102` (338)
- Sample models: `WSC4527100R0FEA`, `WSC69271R000FEA`, `WSC000224R90FEA`, `WSC00026R000FEA`, `WSC251515R00FEA`, `WSC251527R00FEA`, `WSC25153R300FEA`, `WSC251510R00JEA`

### Stackpole / 薄膜电阻 / 13,278 rows

- Registry status: `partial`
- Lookup method: Official resistor series catalog and datasheets
- Official sources:
  - `official-site`: https://www.seielect.com/
- Top unresolved prefixes: `RNF14FTD` (732), `RNF18FTD` (618), `RNMF14FTD` (567), `RNF14FBD` (535), `RNF12FTD` (534), `RNF14FTC` (527), `CS` (405), `RNF14BAE` (355), `RNF14FBC` (313), `RNF14BTC` (306)
- Sample models: `MLFA1FTC10K0`, `HCJ2512ZT0R00`, `HCJ1206ZT0R00`, `MLFA1FTC22R0`, `MLFA1FTC2K20`, `MLFA1FTC5K60`, `MLFA1FTC330R`, `MLFM1FTC6K19`

### 国巨YAGEO / 厚膜电阻 / 11,286 rows

- Registry status: `partial`
- Lookup method: YAGEO product guide and official family naming rules
- Official sources:
  - `application-guide`: https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/YAGEO%20Group%20SMD%20Chip%20Resistor%20Application%20%26%20Safety%20Guide.pdf
  - `official-site`: https://www.yageo.com/
- Top unresolved prefixes: `AR0805` (847), `RE1206FRE` (579), `RE1206DRE` (574), `RE0603FRE` (559), `SR0805JR` (381), `SR1206JR` (372), `RE0805FRE` (364), `RV1206FR` (304), `AR0603` (269), `RL1206` (256)
- Sample models: `SR1210JR-077R5L`, `RV1206FR-071M2L`, `RV0805FR-071M5L`, `RV1206FR-071M5L`, `RV1206FR-071M8L`, `RV0805FR-071M8L`, `RV1206FR-072M2L`, `RV1206FR-0764K9L`

### 威世Vishay / 厚膜电阻 / 9,479 rows

- Registry status: `partial`
- Lookup method: Official resistor family pages and datasheets
- Official sources:
  - `product-family`: https://www.vishay.com/en/resistors-fixed/thinfilm/
  - `official-site`: https://www.vishay.com/
- Top unresolved prefixes: `0402` (1171), `0603` (1096), `0805` (1025), `0612` (877), `1218` (842), `1225` (837), `0406` (833), `1206` (463), `LTO100F` (156), `D2TO020C` (140)
- Sample models: `RCS12061K50FKEA`, `RCA06031K00JNEA`, `RCA060347K0FKEA`, `RCWE2512R300JKEA`, `CRHP1206AF1G00FKET`, `CRHV1206AF50M0FNE5`, `DTO025C1R000JTE3`, `RCL0406287KFKEA`

### Meritek / 厚膜电阻 / 8,846 rows

- Registry status: `partial`
- Lookup method: Official site product pages and datasheets for resistor families and model-prefix ordering codes
- Official sources:
  - `official-site`: https://www.meritekusa.com/
- Top unresolved prefixes: `CR1010` (43), `CR0210` (43), `CR1610` (43), `CR0410` (43), `CR0810` (43), `CR101R` (41), `CR251R` (41), `CR081R` (41), `CR2010` (41), `CR161R` (41)
- Sample models: `CR082005F`, `CR167001F`, `CR204002F`, `CR251873F`, `CR021405F`, `CR1013R7F`, `CR0816R5F`, `CR103602F`

### TE Connectivity(泰科电子) / 薄膜电阻 / 8,523 rows

- Registry status: `partial`
- Lookup method: TE passive product pages and passive product datasheets
- Official sources:
  - `product-page`: https://www.te.com/en/products/passive-components.html
- Top unresolved prefixes: `3504G3A` (453), `3503G2B` (448), `RR02J` (145), `RR03J` (144), `RR01J` (143), `1622` (109), `SMA-A010` (79), `2176` (73), `SMA-A020` (66), `1-217609` (50)
- Sample models: `1-1879216-7`, `3-2176074-1`, `RP73F3A7R68FTG`, `SMF71K3JT`, `SMF722KJT`, `SMF78K2JT`, `SMF7240KJT`, `SMF71M0JT`

### 国巨YAGEO / 绕线电阻 / 8,085 rows

- Registry status: `partial`
- Lookup method: YAGEO product guide and official family naming rules
- Official sources:
  - `application-guide`: https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/YAGEO%20Group%20SMD%20Chip%20Resistor%20Application%20%26%20Safety%20Guide.pdf
  - `official-site`: https://www.yageo.com/
- Top unresolved prefixes: `KNP3WSJB` (188), `KNP3WSJT` (185), `KNP3WSJR` (184), `KNP300JB` (182), `KNP2WSJB` (180), `KNP2WSJT` (178), `KNP2WSJR` (174), `KNP100JR` (169), `KNP200JB` (167), `KNP5WSJB` (167)
- Sample models: `PNP300JR-73-1R8`, `KNP5WSJT-73-0R25`, `PNP7WVJT-91-47R`, `PNP7WVFT-91-500R`, `PNP7WVFT-91-4R7`, `PNP7WVFT-91-680R`, `PNP7WVFT-91-560R`, `PNP7WVFT-91-1K2`

### 三星Samsung / 厚膜电阻 / 8,065 rows

- Registry status: `partial`
- Lookup method: Official chip resistor product page and part-number query pages
- Official sources:
  - `product-page`: https://www.samsungsem.com/global/product/passive-component/chip-resistor.do
  - `part-query`: https://product.samsungsem.com/cr/RU3216FR025CS.do
  - `catalog`: https://www.samsungsem.com/resources/file/global/support/product_catalog/Chip_Resistor.pdf
- Top unresolved prefixes: `RC2012` (965), `RC1005` (964), `RC1608` (962), `RC0603` (957), `RCS2012F` (793), `RCS1005F` (792), `RCS1608F` (787), `RC0402` (697), `RCS2012J` (170), `RCS1005J` (169)
- Sample models: `RC1005J180CS`, `RC0603F364CS`, `RC1005J561CS`, `RC1005F303CS`, `RC1005F223CS`, `RC1005F123CS`, `RC1005J514CS`, `RCS2012F101CS`

### KOA / 厚膜电阻 / 7,407 rows

- Registry status: `partial`
- Lookup method: KOA catalog family tables and product series pages
- Official sources:
  - `official-site`: https://www.koaspeer.com/
  - `catalog`: https://www.koaglobal.com/-/media/Files/KOA_Global/EN/product/commonpdf/KOA_catalog_en.pdf
- Top unresolved prefixes: `732` (2338), `WK73S` (1641), `731` (769), `SR73W` (644), `SLR1TTE1` (424), `733` (333), `SLR1TTE2` (263), `SLR1TTE3` (214), `SLR1TTE4` (155), `SLR1TTER` (134)
- Sample models: `SR732ARTTDR750F`, `UR73VD2BTTD20L0F`, `SR732ARTTDR825F`, `SR73W3ATTER68J`, `WK73S2HTTE51L0F`, `WK73S2BTTDR200F`, `SR732ETTDR137F`, `WK73S2JTTE1R00F`

### TE Connectivity(泰科电子) / 厚膜电阻 / 6,464 rows

- Registry status: `partial`
- Lookup method: TE passive product pages and passive product datasheets
- Official sources:
  - `product-page`: https://www.te.com/en/products/passive-components.html
- Top unresolved prefixes: `3430A3F` (272), `3540` (254), `3502` (254), `3550` (254), `3560` (254), `3430H2F` (254), `3430A2F` (253), `3430B2F` (239), `CRGV2010F` (219), `CRGV2512F` (214)
- Sample models: `3522150RJT`, `354051RFT`, `RH73W2B430MJTD`, `CRG0402F1M0`, `CRG0402F1K6`, `CRGS1206J180R`, `CRGS1206J68K`, `TCR0805N1M5`

### 旺诠RALEC / 厚膜电阻 / 6,109 rows

- Registry status: `partial`
- Lookup method: Official product search and resistor family pages for part-number prefix rules
- Official sources:
  - `official-site`: https://www.ralec.com/en-global/Overview/index
  - `product-search`: https://www.ralec.com/en-global/product_search/index
  - `thick-film-chip-resistor`: https://www.ralec.com/en-global/resistance/index/thick_film_chip_resistor
- Top unresolved prefixes: `RTT06R` (106), `RTT05R` (87), `RTT25R` (83), `RTT12R` (71), `RTT20R` (70), `RTT03R` (67), `0210` (43), `0310` (41), `RTT061R` (38), `RTT051R` (36)
- Sample models: `RTT021002FTH`, `RTT06R500FTP`, `RTT031R10FTP`, `RTT031R60FTP`, `RTT033R00FTP`, `RTT251301FTE`, `RTT061R20FTP`, `RTT025R1JTH`

### Stackpole / 厚膜电阻 / 6,054 rows

- Registry status: `partial`
- Lookup method: Official resistor series catalog and datasheets
- Official sources:
  - `official-site`: https://www.seielect.com/
- Top unresolved prefixes: `CS` (1280), `RPC1206` (726), `RPC0805` (694), `RPC2010` (426), `RPC1210` (426), `RHC2512F` (400), `RPC0603` (363), `RPC2512` (209), `RHC2512J` (142), `RPC0402` (123)
- Sample models: `HCJ0805ZT0R00`, `CSR1225FK3L00`, `RPC2512JT180R`, `RPC2512JT1R00`, `RHC2512FTR250`, `RPC0805JT22R0`, `RHC2512FT6K80`, `RPC0805JT6R80-UP`

### 威世Vishay / 金属氧化膜电阻 / 6,042 rows

- Registry status: `partial`
- Lookup method: Official resistor family pages and datasheets
- Official sources:
  - `product-family`: https://www.vishay.com/en/resistors-fixed/thinfilm/
  - `official-site`: https://www.vishay.com/
- Top unresolved prefixes: `RNX0` (2470), `RNX1` (411), `0005` (336), `0010` (219), `0007` (198), `RNX2` (97), `0020` (94), `0015` (93), `1001` (61), `2001` (60)
- Sample models: `ROX1005M00FKEL`, `ROX050200KFKEL`, `ROX10010M0FKEL`, `WR404140A1001J4100`, `WK80922001003J5C00`, `RNX200130KFKEL`, `ROX1001M00FKEL`, `WK202070A1003J2200`

### 风华Fenghua / 厚膜电阻 / 5,712 rows

- Registry status: `partial`
- Lookup method: Official product pages and catalog model rules
- Official sources:
  - `official-site`: https://www.fhcomp.com/en/
- Top unresolved prefixes: `RS-03K` (751), `RS-05K` (729), `RC-02W` (716), `RS-06K` (670), `RC-02K` (504), `RC-01W` (479), `RS-05L` (219), `RS-06L` (212), `RC-12K` (200), `RS-03L` (189)
- Sample models: `RS-05K3002FT`, `RC-12K132JT`, `RC-12K10R0FT`, `RS-10L2R70FT`, `RS-10K242JT`, `RS-10K302JT`, `RC-02W3002FT`, `RS-1210K1003FT`

### 华新科Walsin / 厚膜电阻 / 5,649 rows

- Registry status: `partial`
- Lookup method: Official product taxonomy and resistor series pages
- Official sources:
  - `official-site`: https://www.passivecomponent.com/
  - `resistor-page`: https://www.passivecomponent.com/products/resistors/
- Top unresolved prefixes: `WR02X` (777), `WR06X` (751), `WR04X` (747), `WR08X` (743), `WR12X` (740), `WR06W` (224), `WR08W` (223), `WR12W` (213), `WR04W` (210), `WR02W` (205)
- Sample models: `WR04X40R2FTL`, `WR04X2R2JTL`, `WR08W1404FTL`, `WR06W2214FTL`, `WR25X1R0JTL`, `WR04X2803FTL`, `WR06X3902FTL`, `WR06X6202FTL`

### 日本贵弥功Chemi-Con / 铝电解电容 / 5,543 rows

- Registry status: `missing`
- Top unresolved prefixes: `KHV` (52), `AVH` (50), `CHA` (50), `GPA` (50), `GPD` (50), `GXF` (50), `HXC` (50), `HXD` (50), `KHE` (50), `KHF` (50)
- Sample models: `EAVH6R3ELL471MJC5S`, `EAVH6R3ELL102MJ20S`, `EAVH6R3ELL222MK25S`, `EAVH6R3ELL332ML25S`, `EAVH6R3ELL472MLN3S`, `EAVH6R3ELL682MLP1S`, `EAVH6R3ELL103MM40S`, `EAVH100ELL331MJC5S`

### FOJAN(富捷) / 厚膜电阻 / 5,442 rows

- Registry status: `missing`
- Top unresolved prefixes: `FRC0805F` (634), `FRC0603F` (605), `FRC1206F` (563), `FRC0402F` (519), `FRC1206J` (223), `FRC0805J` (223), `FRC0603J` (178), `FRC0402J` (169), `FRC2512F` (163), `FRC2512J` (153)
- Sample models: `FRC0805F2002TS`, `FRC0603F1002TS`, `FRC0603J200TS`, `FRC0805F1R00TS`, `FRC0603J105TS`, `FRC1210J470TS`, `FRC0402F1002TS`, `FRC0402J123TS`

### Littelfuse / 贴片压敏电阻 / 5,220 rows

- Registry status: `partial`
- Lookup method: Official varistor family pages and ordering terminology notes
- Official sources:
  - `varistor-page`: https://www.littelfuse.com/products/overvoltage-protection/varistors
  - `application-note`: https://www.littelfuse.com/~/media/electronics_technical/application_notes/varistors/littelfuse_varistors_connection_and_terminology_application_note.pdf
- Top unresolved prefixes: `TMOV20RP` (99), `TMOV14RP` (84), `TMOV34S` (59), `TMOV25SP` (35), `SMOV25S` (28), `SMOV34S` (27), `V5.5MLA0` (21), `V10P` (20), `V1000` (19), `V3.5MLA0` (19)
- Sample models: `V300LS20CP`, `TMOV14RP320E`, `V275LA2P`, `V36ZA80P`, `V39ZA6P`, `V120ZS05P`, `V275LA10P`, `V220ZS05P`

### 国巨YAGEO / 碳膜电阻 / 5,060 rows

- Registry status: `partial`
- Lookup method: YAGEO product guide and official family naming rules
- Official sources:
  - `application-guide`: https://yageogroup.com/content/Resource%20Library/Product%20Guide-Catalog/YAGEO%20Group%20SMD%20Chip%20Resistor%20Application%20%26%20Safety%20Guide.pdf
  - `official-site`: https://www.yageo.com/
- Top unresolved prefixes: `CFR-25JR` (286), `CFR100JR` (286), `FCR2WSJ` (236), `CFR-25JB` (170), `CFR-50JR` (169), `CFR-12JR` (169), `CFR-12JB` (168), `CFR2WSJT` (168), `CFR25SJR` (167), `CFR-50JB` (165)
- Sample models: `MCF-25JR-270R`, `MCF-25JR-510R`, `MCF-25JR-20K`, `MCF-25JR-18R`, `MCF-25JR-390R`, `MCF-25JR-12K`, `MCF-25JR-91R`, `MCF-25JR-120R`

### 村田Murata / 射频电感 / 4,977 rows

- Registry status: `partial`
- Lookup method: Murata product family pages and SimSurfing/product catalogs
- Official sources:
  - `resistor-page`: https://www.murata.com/products/resistor
  - `official-site`: https://www.murata.com/en-us/
- Top unresolved prefixes: `LQW15AN_80` (296), `LQW15AN_8Z` (296), `LQG15WH_02` (240), `LQG15WZ_02` (240), `LQW15AN_00` (237), `LQW15AN_0Z` (237), `LQP03HQ_02` (209), `LQW04AN_00` (204), `LQP02HQ_02` (162), `LQP03TN_02` (162)
- Sample models: `LQP01HV0N3B02#`, `LQP01HV0N4B02#`, `LQP01HV0N5B02#`, `LQP01HV0N6B02#`, `LQP01HV0N7B02#`, `LQP01HV0N8B02#`, `LQP01HV0N9B02#`, `LQP01HV10NH02#`

### EVER OHMS(天二科技) / 厚膜电阻 / 4,765 rows

- Registry status: `partial`
- Lookup method: Official product pages and series PDFs for thick-film and metal-alloy resistor families
- Official sources:
  - `official-site`: https://www.everohms.com/
- Top unresolved prefixes: `CR1210` (634), `CR2010` (624), `CR1206` (622), `CR0805` (610), `CR2512` (599), `CR0603` (444), `CR1812` (356), `CR0402` (267), `CRH2512F` (57), `CRH2512J` (50)
- Sample models: `CR1210F22K0P05Z`, `HR2512F560KE04Z`, `CR2512F3K30E04Z`, `CR2512F300KE04Z`, `CR2512J75R0E04Z`, `CR2512F1K30E04Z`, `CR2512F1K10E04Z`, `CR1812J6K20E04Z`

### CAL-CHIP / 厚膜电阻 / 4,475 rows

- Registry status: `partial`
- Lookup method: Official chip-resistor product pages, PDFs, and series ordering tables
- Official sources:
  - `official-site`: https://calchip.com/
- Top unresolved prefixes: `RM06F` (613), `RM04F` (593), `RM12F` (585), `RM10F` (583), `RM02F` (333), `RM25F` (219), `RM25J` (193), `RM06J` (177), `RM12J` (177), `RM10J` (174)
- Sample models: `RM04J5R1CT`, `RM10J680CT`, `RM04F7322CT`, `RM02J333CT`, `RM04J223CT`, `RM04J203CT`, `RM10F14R3CT`, `RM06F2051CT`

### Ohmite / 绕线电阻 / 4,270 rows

- Registry status: `partial`
- Lookup method: Official product-family pages and datasheets for resistor and thermal family ordering codes
- Official sources:
  - `official-site`: https://www.ohmite.com/
- Top unresolved prefixes: `RW1S0BAR` (82), `RW2S0CBR` (41), `TWW10J` (39), `TUW15J` (33), `RW3R0DBR` (29), `RW1S5CAR` (25), `RW2R0DAR` (24), `RW3R5EAR` (22), `TUW10J` (22), `RW2S0DAR` (21)
- Sample models: `RW0S6BBR100FET`, `RW0S6BBR020FET`, `RW3R0DB5R00JET`, `RW3R0DB10R0JET`, `RW0S6BB10R0FET`, `RW2S0CBR010JET`, `RW1S5CAR040JET`, `RW3R0DB1R00JET`

### Stackpole / 绕线电阻 / 4,170 rows

- Registry status: `partial`
- Lookup method: Official resistor series catalog and datasheets
- Official sources:
  - `official-site`: https://www.seielect.com/
- Top unresolved prefixes: `SM6227` (595), `SM4124` (571), `SM2615` (531), `WW12F` (313), `WW12J` (81), `CB15JB` (50), `CB10JB` (43), `SM4527` (34), `WW12JTR` (23), `SM8035` (22)
- Sample models: `SM4124FT10R0`, `SM4124FT500R`, `SM8035FT50R0`, `SM4124FTR500`, `SM6227FT50R0`, `SM6227FTR500`, `SM4527JT10L0-LP`, `SM8035FTR500`

### VO(翔胜) / 厚膜电阻 / 3,894 rows

- Registry status: `missing`
- Top unresolved prefixes: `SCR0805F` (504), `SCR0402F` (459), `SCR0603F` (445), `SCR1206F` (417), `SCR1206J` (172), `SCR0805J` (169), `SCR0402J` (169), `SCR0603J` (167), `SCR2010J` (120), `SCR1210J` (119)
- Sample models: `0805±5%4K7`, `0603±1%0Ω`, `0603±5%10Ω`, `0603±5%1K`, `0402±1%10K`, `0603±5%1K5`, `0402±5%10K`, `0402±5%10Ω`

### 尼吉康Nichicon / 铝电解电容 / 3,821 rows

- Registry status: `partial`
- Lookup method: Official capacitor family pages, catalogs, and product search/document library for series codes
- Official sources:
  - `official-site`: https://www.nichicon.co.jp/english/
- Top unresolved prefixes: `UPM` (455), `UPJ` (398), `UPW` (263), `UVR` (236), `UHE` (235), `UHW` (220), `UVZ` (206), `UVK` (172), `UVY` (172), `UPS` (128)
- Sample models: `UVK0J102MPD`, `UVK0J222MPD`, `UVK0J332MPD`, `UVK0J472MHD`, `UVK0J682MHD`, `UVK0J103MHD`, `UVK0J153MHD`, `UVK0J223MHD`

### LIZ(丽智电子) / 厚膜电阻 / 3,761 rows

- Registry status: `partial`
- Lookup method: Official product family pages and datasheets for resistor, thermistor, and sensing families
- Official sources:
  - `official-site`: https://www.lizgroup.com/
- Top unresolved prefixes: `CR0805` (813), `CR0603` (739), `CR1206` (696), `CR0402` (672), `CR1210` (245), `CR2512` (239), `CR2010` (208), `CR0201` (148), `CH2512JB` (1)
- Sample models: `CR0805J80473G`, `CR0402FF1402G`, `CR0402FF4021G`, `CR0402FF6040G`, `CR0603FA8060G`, `CR0603FA1962G`, `CR0603FA22R0G`, `CR1206J40392G`

### Bourns / 厚膜电阻 / 3,675 rows

- Registry status: `partial`
- Lookup method: Official varistor product pages and ordering-code briefs
- Official sources:
  - `varistor-page`: https://www.bourns.com/products/circuit-protection/varistor-products
  - `technical-library`: https://www.bourns.com/resources/technical-library/library-documents/varistor-products
- Top unresolved prefixes: `CR0603` (493), `CR0402` (431), `CR0805` (274), `CR1206` (266), `PWR263S` (246), `PWR163S` (186), `PWR220` (179), `CR0201` (166), `120` (130), `251` (127)
- Sample models: `CR1206-FX-2003ELF`, `CR1206-FX-3901ELF`, `CR0603-FX-1781ELF`, `CR0603-FX-1003ELF`, `CRM2512-JW-470ELF`, `CR0603-FX-68R1ELF`, `CR0603-FX-6981ELF`, `CR0603-FX-7152ELF`

### Stackpole / 金属氧化膜电阻 / 3,274 rows

- Registry status: `partial`
- Lookup method: Official resistor series catalog and datasheets
- Official sources:
  - `official-site`: https://www.seielect.com/
- Top unresolved prefixes: `RSF12J` (134), `RSMF12J` (123), `RSMF3JT1` (55), `RSMF12F` (46), `RSMF2JT1` (43), `RSMF5JT1` (43), `RSMF1JT1` (41), `RSF12F` (38), `RSMF1FT1` (32), `RSMF2FT1` (28)
- Sample models: `RSF2JA82K0`, `RSMF3JT10K0`, `RSMF3JT470R`, `RSMF1JT2K00`, `RSF2JT100K`, `RSMF2JT68R0`, `RSMF2JT1K50`, `RSMF1JT5K60`

### Stackpole / 碳膜电阻 / 2,659 rows

- Registry status: `partial`
- Lookup method: Official resistor series catalog and datasheets
- Official sources:
  - `official-site`: https://www.seielect.com/
- Top unresolved prefixes: `CF14J` (175), `CFM14J` (175), `CF18J` (174), `CF12J` (173), `CFM12J` (161), `HDM14J` (148), `PCF14J` (148), `CF18JB` (127), `CF12JB` (119), `CF14JB` (114)
- Sample models: `CF18JA100K`, `CF14JT20K0`, `CF14JT100R`, `CF14JT180R`, `CF14JT5K60`, `CF14JT3K90`, `CF14JT300R`, `CF14JT68R0`

### Ohmite / 厚膜电阻 / 1,983 rows

- Registry status: `partial`
- Lookup method: Official product-family pages and datasheets for resistor and thermal family ordering codes
- Official sources:
  - `official-site`: https://www.ohmite.com/
- Top unresolved prefixes: `SM1020` (97), `TCH35P` (68), `MOX-4002` (66), `TAH20P` (63), `SM1040` (53), `MOX-7502` (49), `1028` (45), `TBH25P` (41), `SM2040` (38), `1125` (37)
- Sample models: `HVC0603T5005FET`, `HVC0603T1006FET`, `HVC0603T5004FET`, `HVC2512T5004JET`, `HVC0402N1007KET`, `HVC0805Z1007JET`, `HVC1206Z2506JET`, `HVC0402N5007KET`

### 村田Murata / 功率电感 / 1,869 rows

- Registry status: `partial`
- Lookup method: Murata product family pages and SimSurfing/product catalogs
- Official sources:
  - `resistor-page`: https://www.murata.com/products/resistor
  - `official-site`: https://www.murata.com/en-us/
- Top unresolved prefixes: `LQH43NN_03` (76), `LQH43NZ_03` (76), `LQH43MN_03` (66), `LQH32MN_23` (56), `LQH43NH_03` (41), `LQH32NH_23` (38), `LQW15CA_00` (38), `LQW15CN_10` (34), `LQH32NZ_23` (33), `LQW15CN_1Z` (28)
- Sample models: `DFE2MCPHR10MJLLQ`, `DFE2MCPHR22MJLLQ`, `DFE32CAH100MR0#`, `DFE32CAH6R8MR0#`, `LQW18FT1R2K0H#`, `LQW18FT1R5K0H#`, `LQW18FT2R2K0H#`, `LQW18FTR55K0H#`

### Venkel / 厚膜电阻 / 1,861 rows

- Registry status: `partial`
- Lookup method: Official product pages and datasheets for passive-component family codes
- Official sources:
  - `official-site`: https://www.venkel.com/
- Top unresolved prefixes: `CR0402` (443), `CR0603` (395), `CR0805` (349), `CR1206` (288), `CR0201` (133), `CR1210` (66), `CR2010` (50), `CR2512` (42), `040` (40), `060` (16)
- Sample models: `CR0603-16W-8452FT`, `HPCR0805-U-000T`, `CR0805-8W-245JT`, `CR2010-1W-240JT`, `CR1210-2W-3321FT`, `CR1206-8W-1741FT`, `CR1206-8W-3900FT`, `CR0603-16W-1782FT`

### Panasonic / 薄膜电阻 / 1,859 rows

- Registry status: `partial`
- Lookup method: Official resistor catalog and part-number family pages
- Official sources:
  - `product-page`: https://industrial.panasonic.com/ww/products/resistors
  - `catalog`: https://mediap.industry.panasonic.eu/assets/imported/industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/DMA0000COL9.pdf
- Top unresolved prefixes: `ERO-S2PH` (571), `ERA-8K` (255), `ERA-8P` (178), `ERA3A` (152), `ERA2A` (124), `ERA6A` (123), `ERA-6K` (94), `ERA-14EB` (53), `ERA3V` (47), `ERA6V` (44)
- Sample models: `ERA6AEB102V`, `ERA3ARB103V`, `ERA3AEB563V`, `ERA6AEB103V`, `ERA2AEB431X`, `ERA2AEB751X`, `ERA3AEB392V`, `ERA3AEB242V`

### RCD Components, Inc. / 薄膜电阻 / 1,819 rows

- Registry status: `partial`
- Lookup method: Official product pages and resource library for resistor, network, and power component model codes
- Official sources:
  - `official-site`: https://www.rcdcomponents.com/
- Top unresolved prefixes: `060` (289), `120` (288), `080` (287), `GP55-100` (10), `GP55-294` (8), `GP55-196` (8), `GP55-137` (8), `GP55-316` (8), `GP55-806` (8), `GP55-536` (8)
- Sample models: `BLU1206-7502-BT25W`, `BLU0805-8662-BT25W`, `BLU0603-2431-BT25W`, `BLU0603-1581-BT25W`, `BLU1206-4322-BT25W`, `BLU1206-4991-BT25W`, `BLU1206-9092-BT25W`, `BLU0603-1621-BT25W`

### RESI(开步睿思) / 薄膜电阻 / 1,514 rows

- Registry status: `missing`
- Top unresolved prefixes: `PTFR0805B` (514), `PTFR0603B` (396), `PTFR0402B` (270), `PTFR1206B` (75), `MMFR6518B` (66), `LMERW250F` (30), `PTFR0603D` (22), `PTFR0805Q` (18), `PTFR0805A` (16), `MMFR2568B` (16)
- Sample models: `PTFR0603B56K0P9`, `PTFR0402B10K0N9`, `PTFR1206B200KP9`, `PTFR0805B100RN9`, `PTFR1206B249RP9`, `PTFR1206B100RP9`, `PTFR0603B390RP9`, `LMERW250F7K50Q9L`

### 风华Fenghua / 薄膜电阻 / 1,459 rows

- Registry status: `partial`
- Lookup method: Official product pages and catalog model rules
- Official sources:
  - `official-site`: https://www.fhcomp.com/en/
- Top unresolved prefixes: `TD03G` (1224), `TE05G` (49), `TD03H` (34), `TE05H` (24), `TF06G` (21), `TD05G` (12), `TF06H` (10), `TC02G` (9), `RTF06KR` (9), `TF06E` (8)
- Sample models: `TD03G2152BT`, `TD03G4121BT`, `TD03G3163BT`, `TD03G1053FT`, `TD03G2001BT`, `TC02G8202FT`, `TD03G6801BT`, `TD03G4122FT`

### Sunway(信维通信) / 厚膜电阻 / 1,354 rows

- Registry status: `missing`
- Top unresolved prefixes: `SC0402F` (145), `SC0805F` (135), `SC0603F` (130), `SC0603J` (118), `SC1206J` (116), `SC0805J` (116), `SC0402J` (99), `SC1206F` (94), `SC0201F` (80), `SC2512J` (72)
- Sample models: `SC1210J1002F1CNRH`, `SC0402F5R10G2ANRH`, `SC1206F2703F8ANRH`, `SC0603F3000F2BNRH`, `SC0603F5100F2BNRH`, `SC0201F7503G1BNRH`, `SC1206J3001F8ANRH`, `SC0603F2702F2BNRH`

### 昶龙科技 / 厚膜电阻 / 1,338 rows

- Registry status: `missing`
- Top unresolved prefixes: `CL` (1259), `CF2512JN` (10), `CF1210JN` (9), `CF2010JN` (7), `CF0805FN` (7), `CF1206FN` (6), `CF1812JN` (6), `CF1210FNR` (5), `CF1210FN` (5), `CF0805JN` (4)
- Sample models: `CL0402FN33RP`, `CL0402FN200RP`, `CL0402FN0RP`, `CL1210JN2M2P`, `CL0805FN13K3PS`, `CL2512JN1M2B`, `CL1210FN1M8P`, `CL0805FN174RPS`

### Panasonic / 金属氧化膜电阻 / 1,315 rows

- Registry status: `partial`
- Lookup method: Official resistor catalog and part-number family pages
- Official sources:
  - `product-page`: https://industrial.panasonic.com/ww/products/resistors
  - `catalog`: https://mediap.industry.panasonic.eu/assets/imported/industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/DMA0000COL9.pdf
- Top unresolved prefixes: `ERG-2SJ1` (95), `ERG-3FJS` (67), `ERG-1SJ1` (66), `ERG-3SJ1` (61), `ERG-2SJ2` (56), `ERG-2FJS` (56), `ERG-1FJS` (49), `ERG-2SJ3` (48), `ERX-1SJR` (40), `ERG-1SJ3` (38)
- Sample models: `ERG1SJ510V`, `ERQ12AJ2R2P`, `ERG2SJ751A`, `ERG1SJ472A`, `ERG1SJ911`, `ERG1SJ331A`, `ERG2SJ181A`, `ERX3SJ5R6`

### RESI(开步睿思) / 厚膜电阻 / 1,296 rows

- Registry status: `missing`
- Top unresolved prefixes: `HPCR0603F` (161), `AECR0805F` (160), `HPCR0805F` (143), `AECR0603F` (134), `AECR1206F` (131), `AECR0402F` (118), `HPCR0402F` (114), `ETCR0603F` (72), `AECR1210F` (32), `HVLR1905F` (23)
- Sample models: `AECR0402F180RK9`, `AECR0402F820RK9`, `AECR0402F220RK9`, `AECR1206F200KK9`, `HPCR1210F0000K9`, `AECR1206F220KK9`, `HPCR0603F100KK9`, `HPCR0805F160RK9`

### TE Connectivity(泰科电子) / 绕线电阻 / 1,276 rows

- Registry status: `partial`
- Lookup method: TE passive product pages and passive product datasheets
- Official sources:
  - `product-page`: https://www.te.com/en/products/passive-components.html
- Top unresolved prefixes: `ER74R` (18), `UPW50B` (15), `ER58R` (12), `UPW25B` (9), `1-217608` (8), `SMW71R` (7), `SMW51R` (7), `SMW72R` (4), `SMW73R` (4), `SMW21R` (4)
- Sample models: `SMW716RJT`, `SMW7R13JT`, `SMW7820RJT`, `SMW7360RJT`, `SMW72R2JT`, `SMW72R7JT`, `SMW7300RJT`, `SMW71R2JT`

### RCD Components, Inc. / 绕线电阻 / 1,225 rows

- Registry status: `partial`
- Lookup method: Official product pages and resource library for resistor, network, and power component model codes
- Official sources:
  - `official-site`: https://www.rcdcomponents.com/
- Top unresolved prefixes: `175-270-` (2), `125-510-` (2), `160-560-` (2), `175-681-` (2), `175-510-` (2), `125-R36-` (2), `175-2R4-` (2), `PR1-121-` (2), `175-360-` (2), `175-331-` (2)
- Sample models: `175-270-JTW`, `125-510-JTW`, `160-560-JBW`, `175-270-JBW`, `175-681-JTW`, `175-510-JTW`, `125-R36-JTW`, `175-2R4-JTW`

### NTE Electronics / 金属氧化膜电阻 / 1,098 rows

- Registry status: `missing`
- Top unresolved prefixes: `11` (21), `41` (20), `31` (19), `01` (18), `21` (17), `51` (14), `61` (12), `42` (12), `13` (12), `12` (12)
- Sample models: `EW375`, `1W216`, `1W1D8`, `HW047`, `QW5D6`, `QW3390BR`, `QW610`, `QW218`

### 东电化TDK / 贴片压敏电阻 / 1,091 rows

- Registry status: `partial`
- Lookup method: TDK electronics product pages and datasheet ordering guides
- Official sources:
  - `official-site`: https://www.tdk.com/
  - `electronics-site`: https://www.tdk-electronics.tdk.com/
- Top unresolved prefixes: `B72214` (250), `B72220` (189), `B72210` (167), `B72207` (75), `B72225` (43), `B72240` (41), `B72205` (27), `AVR-M` (23), `B72530` (22), `B72250` (22)
- Sample models: `AVR-M1005C120MTAAB`, `AVR-M1608C270KT2AB`, `AVR-M1005C080MTADB`, `AVRM0603C120MT101N`, `B72207S2151K101`, `B72214S0461K101`, `B72214S0441K101`, `B72214P2381K101`

### Ohmite / 薄膜电阻 / 1,066 rows

- Registry status: `partial`
- Lookup method: Official product-family pages and datasheets for resistor and thermal family ordering codes
- Official sources:
  - `official-site`: https://www.ohmite.com/
- Top unresolved prefixes: `0207` (285), `AC` (66), `7003` (26), `TN15P` (17), `APC0603B` (13), `TNP10SC` (12), `MEV04V` (11), `APC0805B` (10), `APC0805` (8), `APC1206B` (8)
- Sample models: `ACPP0603470RB`, `ACPP0805510RB`, `ACPP060351RB`, `ACPP0603330RB`, `ACPP08056K2B`, `ACPP0603130RB`, `ACPP0805300RB`, `ACPP080524KB`

### Panasonic / 贴片压敏电阻 / 1,063 rows

- Registry status: `partial`
- Lookup method: Official resistor catalog and part-number family pages
- Official sources:
  - `product-page`: https://industrial.panasonic.com/ww/products/resistors
  - `catalog`: https://mediap.industry.panasonic.eu/assets/imported/industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/DMA0000COL9.pdf
- Top unresolved prefixes: `ERZ-E11A` (68), `ERZ-E14A` (52), `ERZ-V14D` (50), `ERZ-V10D` (50), `ERZ-V05D` (42), `ERZ-V07D` (40), `ERZ-V09D` (40), `ERZ-E10A` (35), `ERZ-V20D` (28), `ERZ-E08A` (28)
- Sample models: `ERZV14D681`, `ERZVA7V241`, `ERZE14A511`, `ERZV14D471`, `ERZV07D471`, `ERZVGAD560`, `ERZV14D221`, `ERZV14D621CS`

### Rubycon / 铝电解电容 / 1,055 rows

- Registry status: `missing`
- Top unresolved prefixes: `ZLJ` (264), `YXS` (173), `ZLH` (165), `ZL` (140), `YXJ` (84), `ZLQ` (75), `YXF` (64), `ZLS` (46), `LLE` (44)
- Sample models: `6.3ZLJ220M5X11`, `6.3ZLJ470M6.3X11`, `6.3ZLJ820M8X11.5`, `6.3ZLJ1000M8X16`, `6.3ZLJ1200M10X12.5`, `6.3ZLJ1500M8X20`, `6.3ZLJ1800M10X16`, `6.3ZLJ2700M10X20`

### 村田Murata / 磁珠 / 1,055 rows

- Registry status: `partial`
- Lookup method: Murata product family pages and SimSurfing/product catalogs
- Official sources:
  - `resistor-page`: https://www.murata.com/products/resistor
  - `official-site`: https://www.murata.com/en-us/
- Top unresolved prefixes: `BLM` (869), `NFZ` (128), `BLA` (26), `BLE` (17), `BLF` (12), `BLH` (2), `BLT` (1)
- Sample models: `BLM15VM150BH1#`, `BLA2AAG102SN4#`, `BLA2AAG121SN4#`, `BLA2AAG221SN4#`, `BLA2AAG601SN4#`, `BLA2ABB100SN4#`, `BLA2ABB121SN4#`, `BLA2ABB220SN4#`

### Tyohm(幸亚电阻) / 厚膜电阻 / 978 rows

- Registry status: `missing`
- Top unresolved prefixes: `RMC0603` (360), `RMC0805` (246), `RMC0402` (164), `RMC1206` (142), `RMC2512` (31), `RMC1210` (20), `RMC2010` (14), `RT1/4W1M` (1)
- Sample models: `RMC120610K1%N`, `RMC040240.2K1%N`, `RMC04027K68FN`, `RMC040212.4K1%N`, `RMC20103001%N`, `RMC2010205%N`, `RMC0603100K1%N`, `RMC040212K1FN`

### ROHM / 厚膜电阻 / 910 rows

- Registry status: `partial`
- Lookup method: Official resistor series pages and catalogs
- Official sources:
  - `resistor-page`: https://www.rohm.com/products/resistors
  - `official-site`: https://www.rohm.com/
- Top unresolved prefixes: `01` (348), `03` (333), `10` (143), `18` (78), `100` (4), `PMR10` (2), `PMR03` (1), `PMR25` (1)
- Sample models: `PMR03EZPJ000`, `PMR100HZPJV1L0`, `TRR01MZPF4872`, `PMR100HZPFV3L00`, `PMR25HZPFV3L00`, `TRR01MZPJ4R7`, `TRR03EZPJ753`, `TRR01MZPJ333`

### 威世Vishay / 热敏电阻 / 889 rows

- Registry status: `partial`
- Lookup method: Official resistor family pages and datasheets
- Official sources:
  - `product-family`: https://www.vishay.com/en/resistors-fixed/thinfilm/
  - `official-site`: https://www.vishay.com/
- Top unresolved prefixes: `NTC` (773), `PTCCL05H` (18), `PTCSL03` (16), `PTCCL07H` (9), `PTCCL21H` (9), `PTCCL13H` (7), `PTCCL17H` (7), `PTCHP12S` (5), `PTCTT95R` (5), `TFPT0805L` (4)
- Sample models: `NTCLE100E3338JB0`, `NTCALUG01T103FL`, `NTCLE100E3272HB0`, `NTCLE213E3104FXB0`, `NTCLE100E3151JB0`, `NTCLE100E3103HB0`, `NTCLE100E3153JB0`, `NTCLE203E3302SB0`

### VO(翔胜) / 碳膜电阻 / 886 rows

- Registry status: `missing`
- Top unresolved prefixes: `CR1/4W-1` (75), `CR1/8W-1` (58), `CR1/4W-2` (57), `CR1/8W-3` (47), `CR1/8W-2` (46), `CR1/4W-3` (44), `CR1/4W-5` (35), `CR1/4W-4` (29), `CR1/8W±5` (28), `CR1/2W-1` (28)
- Sample models: `CR1/8W±5%160KSTB5`, `CR1/8W±5%36ΩSTB5`, `CR1/8W±5%39KSTB5`, `CR1/8W±5%150KSTB5`, `CR1/8W±5%910ΩSTB5`, `CR1/8W±5%27ΩSTB5`, `CR1/8W±5%0Ω5STB5`, `CR1/8W±5%100KSTB5`

### Riedon / 绕线电阻 / 884 rows

- Registry status: `missing`
- Top unresolved prefixes: `UB5C-0R1` (4), `UB3C-0R3` (4), `UB5C-0R2` (4), `UB5C-0R3` (4), `UB3C-0R1` (4), `SM15-100` (4), `S2-0R075` (3), `UB3C-0R2` (3), `SM10-100` (3), `S2-0R047` (2)
- Sample models: `S4-0R039J1`, `S2-0R47J1`, `S2-0R047J1`, `S4-0R36J1`, `S4-10KF1`, `S2-0R03J1`, `S2-681RF1`, `S4-47RF1`

### TE Connectivity(泰科电子) / 金属氧化膜电阻 / 835 rows

- Registry status: `partial`
- Lookup method: TE passive product pages and passive product datasheets
- Official sources:
  - `product-page`: https://www.te.com/en/products/passive-components.html
- Top unresolved prefixes: `ROX05SJ` (111), `ROX5SSJ1` (28), `ROX5SSJ3` (16), `ROX5SSJ2` (16), `ROX5SSJ5` (10), `ROX5SSJ6` (10), `ROX5SSJ4` (8), `ROX3SJ68` (5), `ROX2SJ1K` (5), `ROX5SSJ8` (5)
- Sample models: `1625890-6`, `ROX1SJ1K0`, `ROX3SJ3K3`, `ROX3SJ15K`, `ROX3SJ2K7`, `ROX2SJ220R`, `ROX3SG4R7`, `ROX3SJ5K6`

### Bourns / 薄膜电阻 / 822 rows

- Registry status: `partial`
- Lookup method: Official varistor product pages and ordering-code briefs
- Official sources:
  - `varistor-page`: https://www.bourns.com/products/circuit-protection/varistor-products
  - `technical-library`: https://www.bourns.com/resources/technical-library/library-documents/varistor-products
- Top unresolved prefixes: `080` (318), `060` (244), `120` (130), `040` (124), `22` (6)
- Sample models: `CRT0805-BW-1002ELF`, `CRT0805-BY-7503ELF`, `CRT0603-FY-3300ELF`, `CRT1206-BY-40R2ELF`, `CRT1206-BW-1004ELF`, `CRT0402-BY-1103GLF`, `CRT0402-BY-2003GLF`, `CRT0805-CX-10R0ELF`

### Tyohm(幸亚电阻) / 薄膜电阻 / 763 rows

- Registry status: `missing`
- Top unresolved prefixes: `RN1/2WS1` (43), `RN1/2WS2` (31), `RN1/2WS3` (23), `RJM74P` (20), `RN1/2WS5` (17), `RN1/2WS4` (15), `RN1/2WS6` (13), `RN1/2W1.` (7), `RN1/2W51` (6), `RN1/2W12` (6)
- Sample models: `RJM74P0204F2T2203`, `RJM74P0204F2T6800`, `RJM74P0204F2T1000`, `RJM74P0204F2T49R9`, `RJM74P0204F2T1100`, `RJM74P0204F2T10K`, `RJM74P0204F2T1003`, `RJM74P0204F2T7500`

### Riedon / 薄膜电阻 / 749 rows

- Registry status: `missing`
- Top unresolved prefixes: `220` (280), `247` (136), `126` (136), `PFS35-0R` (29), `060` (17), `080` (16), `PFS35-1K` (6), `PFS35-1R` (6), `PFS35-3R` (4), `PFS35-2R` (4)
- Sample models: `PFS35-5KF1`, `PFS35-360RF1`, `CAR0603-10KB2`, `PFS35-50KF1`, `PFS35-5RF1`, `PFS35-500RF1`, `PFS35-180RF1`, `PFS35-5R6F1`
