# 公开版稳定性规则

## 这条规则的目标

目标不是“每次都多改一点”，而是：

- 不让正式版因为顺手改动而坏掉
- 不让实验性逻辑直接进入公开入口
- 不让发布脚本和代理壳页被无意改坏

## 公开版的定义

公开版只指：

- [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)

任何会改变这个地址可见行为的改动，都算公开版改动。

## 默认原则

以后只要不是明确写了“正式版修复 / 正式版发布 / 公开入口改动”，就默认遵守下面这条：

**不要主动修改会影响公开版入口、代理、发布流程或运行时配置的文件。**

拓库和普通功能修复，优先改：

- 源数据
- 运行库
- 搜索/匹配业务逻辑里最小必要的部分

不要把调试逻辑、临时绕路方案、试验性回退，长期留在正式入口里。

## 受保护边界

下面这些文件属于高风险正式版边界，改之前必须明确是正式版任务：

- `streamlit_app.py`
- `component_matcher.py`
- `build_streamlit_cloud_bundle.py`
- `sync_local_and_public.py`
- `sync_local_and_public.ps1`
- `publish_public.ps1`
- `publish_public.cmd`
- `deploy_cloudflare_pages_proxy.ps1`
- `deploy_cloudflare_pages_proxy.cmd`
- `cloudflare-pages-proxy/dist/_worker.js`
- `cloudflare-pages-proxy/wrangler.jsonc`
- `requirements.txt`
- `runtime.txt`

唯一例外是：如果只是在 `streamlit_app.py` 里更新 `PUBLIC_RELEASE_STAMP` 这种纯发布触发标记，而且不改任何行为逻辑，那它属于允许的无行为变化触发，不算业务改动。

## 必须遵守的动作

1. 先把改动拆到最小
2. 先本地验证
3. 只在确实要改正式版入口时，才允许 `--allow-public-runtime-change`
4. 发布后必须用真实浏览器验证公开版
5. 如果这次改了 BOM 或页面布局，再补测对应场景

## 禁止项

- 不在没有验证时宣布正式版已修好
- 不把临时调试路径当成正式方案
- 不让公开版入口带着未确认的实验逻辑上线
## 公开版 bundle 规则

- 公开版默认只打包搜索侧资产，不打包 `components.db`
- 公开版启动只允许依赖 `cache/components_search.sqlite`、`cache/components_prepared_v5.parquet` 和少量小缓存
- 任何把 `components.db` 加回公开 bundle 的改动，都必须视为正式版高风险改动
- 只有明确要恢复“全量维护模式”时，才允许重新引入全量库
- 公开版在信任 `prepared_cache_is_current()` 之前，必须先检查公开 bundle 是否仍然最新；只要 bundle 需要刷新，就不能直接继续使用现成 prepared cache
- 公开版如果发现 `streamlit_cloud_bundle.zip` 还是旧版本，必须先用 `.part` 文件重建压缩包，再继续解包搜索侧资产，不能让旧 zip 一直留在运行环境里
- `sync_local_and_public.py` 会在公开 bundle 重新生成时自动刷新 `streamlit_app.py` 里的 `PUBLIC_RELEASE_STAMP`，这只是为了让 Streamlit Cloud 重新检查 checkout，不算业务逻辑改动
- `component_matcher.py` 里的 `PUBLIC_CODE_STAMP` 现在也参与公开版查询/会话缓存 key；它变更时，旧的搜索结果缓存要当成过期状态处理
