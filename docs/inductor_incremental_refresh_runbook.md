# 电感拓库增量刷新手册

## 目标

每次新增一个电感品牌或系列时，只刷新这次新增的数据，不再对整套电感库做全量重建。

## 标准流程

1. 先抓取品牌/系列数据，生成独立的品牌快照文件，例如：
   - `Inductor/bourns_power_inductor_expansion.csv`
   - `Inductor/sumida_power_inductor_expansion.csv`
   - `Inductor/tdk_mlg0603p_expansion.csv`

2. 再执行增量刷新脚本：
   - 单品牌：`python .\sync_inductor_incremental_refresh.py <品牌快照CSV>`
   - 多品牌批量：`python .\sync_inductor_incremental_refresh.py <快照1> <快照2> <快照3>`

3. 脚本会自动做三件事：
   - 更新 `components.db`
   - 刷新 `cache/components_search.sqlite`
   - 刷新 `cache/components_prepared_v5.parquet`

4. 完成后立刻抽查 2 到 3 个型号，确认：
   - 数据库里有记录
   - 搜索能直接命中
   - 公开页/本地页不再依赖全量回退

## 使用原则

- 只在需要重建整套底层缓存时，才考虑全量同步脚本。
- 日常拓库默认走增量刷新。
- 新品牌数据先落品牌快照，再进增量刷新，最后再做公开页验证。
- 如果同一轮拓库里有多个品牌已经完成，优先合并成一次增量刷新，减少 parquet 重写次数。
