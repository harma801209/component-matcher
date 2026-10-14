# 游戏电源交互与验收

每次进入器件关卡、下一关或自由实验，先断电，不自动播放。唯一供电按钮在同一操作区切换“打开电源 / 关闭电源”，其 `aria-pressed` 与供电状态一致。通电启动观察；普通关卡断电停止观察；已获得的通关记录保留。

游戏不再提供暂停、慢放、播放复位或手动推进时间的工具栏。下一关、器件选项、提示，以及模拟突然用电、接反电源、MOS控制等必要实验动作仍保留。综合小夜灯的电容备用供电步骤例外：关闭外部电源后，储能经负载短暂释放，不能伪造为立即零电流。

低动画偏好下仍从断电开始，明确点击供电才启动本关；偏好改变为减少动画时关闭供电。页面不可见时不推进计时。不支持 WebGL 时观察与数值计时继续工作；不调用业务数据库。

新的统一浏览器验收：

```powershell
python tools/check_training_power.py --full
python tools/check_training_power.py --full --phone
python tools/check_training_power.py --full --fallback
python tools/check_training_power.py --public --full
python tools/check_training_power.py --public --phone
```

`--full` 通过真实按钮完成 94 个器件关卡、14 次换场景验证和受前置器件通关约束的 5 步综合作品；不注入答案、通关或模拟时间。默认模式检查 30 个器件的初始断电、开关电源、动画阶段、结果与通关记录。手机模式为 Chrome 的 iPhone 15 Pro 尺寸及原生触控模拟，不等同真机 Safari。截图与 JSON 验收结果在工作树外的诊断目录。

旧 `check_training_levels.py`、`check_training_subtype_games.py`、`check_training_beginner.py`、`check_training_nightlight.py` 等依赖播放工具按钮或手动推进的历史浏览器脚本，不作为这个交互版本的验收入口；统一使用上面的检查器。模型与进度的单元测试仍在 `tests/test_product_training.py`，发布前仍须执行 `tools/run_release_safety_gate.py`。
