# 公开版发布运行手册

公开版只指这个地址：

- [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)

## 先看规则

先读这份规则，再决定要不要改公开版入口：

- [docs/public_stability_rule.md](C:/Users/zjh/Desktop/data/docs/public_stability_rule.md)

核心原则只有一句话：

**默认只做“不会伤到正式版”的改动；只要会碰到公开入口、代理、发布脚本或运行时配置，就必须先确认这是正式版任务。**

## 默认发布路径

平时只要是常规修复、拓库、数据刷新、页面文案调整，优先走这一条：

```powershell
.\publish_public.ps1 -CommitMessage "修复说明"
```

它会自动做这些事：

1. 重建 `streamlit_cloud_bundle.zip`
2. 校验关键 Python 文件
3. 提交并推送到 GitHub
4. 触发 Streamlit Community Cloud 更新
5. 如果检测到 Cloudflare Pages 代理文件变动，再补发代理壳

## 什么情况下要额外小心

只要这次改动碰到了下面这些东西，就先当成“正式版边界改动”：

- `streamlit_app.py`
- `component_matcher.py`
- `build_streamlit_cloud_bundle.py`
- `sync_local_and_public.py`
- `publish_public.ps1`
- `deploy_cloudflare_pages_proxy.ps1`
- `cloudflare-pages-proxy/dist/_worker.js`
- `cloudflare-pages-proxy/wrangler.jsonc`
- `requirements.txt`
- `runtime.txt`

如果是这种改动，发布时要显式加：

```powershell
.\publish_public.ps1 -CommitMessage "正式版修复说明" -AllowPublicRuntimeChange
```

这个参数只给真正要改正式版入口和运行逻辑的任务用，平时不要随手加。

### 1.1 如果这次改动后公开版没有立刻刷新
如果这次改动会影响 `component_matcher.py`、拓库数据，或者其他公开版可见结果，`sync_local_and_public.py` 会在公开 bundle 重新生成时自动刷新一次 `streamlit_app.py` 里的 `PUBLIC_RELEASE_STAMP`。

如果浏览器里还是旧状态，再手动更新一次这个 stamp 作为补充 nudge。

如果还是旧状态，并且需要更强的 app-code 触发，再补一次 `component_matcher.py` 顶部的 `PUBLIC_CODE_STAMP`。这个标记会一起刷新公开版查询缓存 key，所以很适合用来打掉同一个浏览器会话里残留的旧搜索结果。

这个动作只是部署触发，不改业务逻辑，但它能让 Streamlit Cloud 重新检查 checkout。

## 拓库怎么发

如果这次是拓库，顺序固定是：

1. 先补源数据
2. 再刷新运行库
3. 再做公开发布

一句话记法：

**源数据先补，运行库再刷，最后才发布。**

如果只是少量新增，优先做增量刷新，不要一上来就全量重建。

## 发布后固定验证

发布完成后只做这几步：

1. 打开公开版页面
2. 搜一个真实料号，优先搜这次刚补的型号
3. 如果这次改了 BOM，再测一条 BOM
4. 如果这次改了公开壳页，再确认页面没有空白、转圈或报错

只要浏览器里真实通过，这次发布才算完成。
## 公开版打包默认值

- 默认只打公开版搜索侧资产，不把 `components.db` 放进云端 bundle
- 如果公开版又出现空白或启动失败，先确认 bundle 里是否混入了全量库，再看搜索侧缓存是否完好
- 如果公开版已经存在旧的 `streamlit_cloud_bundle.zip`，但 `.part` 或 manifest 已更新，先强制重建 zip 再启动，不要让旧压缩包继续复用
