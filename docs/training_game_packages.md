# 游戏器件外观修正

这次只调整30个游戏章节的外观和功能连接。结构探索中的外观/内部材料模型、计算题设、94个关卡、解锁方式、自由实验与当前页面进度不改。

## 一份端子位置驱动模型与连接

`training_game_packages.js`提供独立的游戏封装示例，两个游戏引擎和四个基础器件选择卡共用。引脚、焊盘、导线起点及电流路径使用同一组接触点，移除旧的统一缩放/悬空高度模板。贴片接触脚底面贴住焊盘，径向引线穿过板面；不是把元件塑料本体直接压在PCB上。

| 游戏 | 外观示例与核对资料 |
| --- | --- |
| 厚膜/薄膜/抗硫化电阻 | 两端包覆金属端接、居中印字。薄膜1 kΩ用1001；抗硫化不以蓝色外壳假装通用品类识别。[Vishay电阻](https://www.vishay.com/en/resistors-fixed/)、[耐硫化示例](https://www.vishay.com/docs/20034/rca.pdf) |
| 采样电阻 | 宽端接与合金体，R005/R010/R050随选择变动。[采样电阻示例](https://www.vishay.com/en/product/30183/) |
| MLCC | 封闭陶瓷体和两端包覆电极，不在游戏外观上裸露内部叠层。[Murata陶瓷电容](https://www.murata.com/en-global/products/capacitor/ceramiccapacitor) |
| 铝电解 | 圆柱套管、负极条和减号、顶盖及两个径向引线。防爆纹只是本例外形，不能推为所有尺寸通用。[Chemi-Con极性](https://www.chemi-con.co.jp/en/faq/detail.php?id=alEcapPolarity) |
| 薄膜/安规 | 盒式径向引线示例；不把X/Y类别当作唯一外形或认证保证。[TDK薄膜电容资料](https://www.tdk-electronics.tdk.com/download/537974/76160cdb800cf40be24ef767fe5082bb/pdf-generaltechnicalinformation.pdf) |
| 钽 | 模压贴片及正极条；接反后条纹跟随真实方向转动，板上接法不随角色自动纠正。[AVX资料](https://www.kyocera-avx.com/docs/techinfo/Tantalum-NiobiumCapacitors/Tantalum-Capacitors-Characteristics-and-Component.pdf) |
| 绕线/叠层/一体成型 | 绕线有磁芯及连续铜线；叠层为封闭体；一体成型不裸露绕组。[Coilcraft绕线](https://www.coilcraft.com/en-us/products/rf/ferrite-core-chip-inductors/1812-%284532%29/1812ls/)、[一体成型](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/epl/epl3015/)、[Murata电感](https://www.murata.com/en-global/products/inductor) |
| 共模 | 双绕组与共享磁芯、四个独立端子；1→4、2→3为两条不同线路。移除磁路时铜线仍在。[Coilcraft共模示例](https://www.coilcraft.com/getmedia/38efcbd7-3710-40e5-9e90-1a4381ec2b36/comoee.pdf) |
| 四类晶振 | 四底焊盘分布四角、金属盖和1脚点；无源晶体只有两谐振端，其余为外壳端。[FA-238](https://download.epsondevice.com/td/pdf/brief/FA-238_en.pdf)、[XO](https://download.epsondevice.com/td/pdf/app/SG-210STF_en.pdf)、[TCXO](https://abracon.com/datasheets/ILSI/I538.pdf)、[VCXO](https://abracon.com/Support/PackageDrawing/Oscillators/ASFLV.PDF) |
| N/P MOS | SOT-23两侧2+1，1G/2S/3D；N/P不靠虚构颜色区分。[SOT-23封装](https://assets.nexperia.com/documents/outline-drawing/SOT23.pdf)、[2N7002](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf)、[BSS84](https://assets.nexperia.com/documents/data-sheet/BSS84.pdf) |
| 双MOS | SOT-363两侧3+3；1S1/2G1/3D2/4S2/5G2/6D1，源极在板上连接成教学背靠背路径。[PMGD280UN](https://assets.nexperia.com/documents/data-sheet/PMGD280UN.pdf) |
| NPN/PNP/达林顿/带阻三极管 | SOT-23两侧2+1和1脚点；普通B/E/C，带阻IN/GND/OUT。[NPN](https://assets.nexperia.com/documents/data-sheet/PMBT2222A.pdf)、[PNP](https://assets.nexperia.com/documents/data-sheet/PMBT2907A.pdf)、[达林顿](https://assets.nexperia.com/documents/data-sheet/BCV27.pdf)、[带阻](https://assets.nexperia.com/documents/data-sheet/PDTC114ET.pdf) |
| 开关/稳压二极管 | 轴向玻璃与阴极环；弯脚连接焊盘。[1N4148](https://assets.nexperia.com/documents/data-sheet/1N4148_1N4448.pdf)、[BZX79](https://assets.nexperia.com/documents/data-sheet/BZX79.pdf) |
| 整流/肖特基/TVS | SMA示例和阴极条。整流切换方向可见条纹翻转；TVS题设为单向，不概括双向器件。[SMA阴极条示例](https://www.vishay.com/docs/98678/ss14hm3_bia_ss14-m3ia.pdf) |
| LED | MiniLED示例有K标记与实时发光面；方向切换旋转本体。基础电阻游戏的径向LED补引线、焊盘、阴极平边。[MiniLED资料](https://www.vishay.com/docs/84215/vlmx234.pdf) |

## 边界与验证

模型是放大的教学外形，不是等尺寸厂商CAD。资料用于本例外形和端子参考，不把课程给定Ron、R1/R2、电压或额定条件当作参考料号性能。外形相似并不代表型号/极性/脚位相同，具体型号必须查规格书。板上仅画功能连接，不是可生产布线/真实市电指导。

`tools/check_training_game_packages.py`通过原生界面逐一检查30个真实WebGL模型，读取实际变换后的80个接触网格底面或穿板范围，核对焊盘和导线起点。保存30个默认视角、12个低视角、4组方向变化的截图。`--gallery-only`只把原始截图并排展示，不修改器件图。`--public`检查正式页面。

回归仍需完成`check_training_levels.py`的16关、`check_training_subtype_games.py`的78关、实时亮度/电流/拖放/键盘/暂停检查，及1440/900/390宽度的外层单滚动。自动通关只能证明逻辑不回归，不能证明新手已理解或外观涵盖所有厂商。

## 同轮账号导航

管理后台链接由已验证的管理员角色生成，渲染器也过滤非管理员。后台自身权限检查保留。登录后左下侧栏提供退出登录，手机在导航末尾；复用既有登出请求、会话撤销和浏览器凭证清理，不增加另一套认证，不修改会员/价格数据库结构。

`check_workbench_account_navigation.py`本地使用独立临时数据库验证访客、普通会员及管理员，以及退出、刷新和旧链接重放。正式检查由显式提供的验收账号登录，只读取会员/成本历史并退出本次会话，不创建/修改会员或成本。另运行发布安全门及导航单元测试；受保护业务数据指纹必须保持不变。
