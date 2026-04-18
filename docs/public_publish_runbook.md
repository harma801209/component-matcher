# 公开版发布规则

这份规则只针对正式公开站 `https://fruition-component.pages.dev/`。

## 先记住一句话

**默认只跑 `publish_public.ps1`。**

它会先把主应用同步到 GitHub / Streamlit，再判断要不要补发 Cloudflare Pages 的代理壳。

## 公开版发布链路

公开版其实有两条链：

1. 主应用链
   - 本地修改
   - `sync_local_and_public.ps1`
   - 重建 `streamlit_cloud_bundle.zip`
   - 提交并推送到 GitHub
   - 触发 Streamlit Community Cloud 自动更新

2. Cloudflare Pages 代理链
   - 本地修改 `cloudflare-pages-proxy/dist/_worker.js` 或 `cloudflare-pages-proxy/wrangler.jsonc`
   - `deploy_cloudflare_pages_proxy.ps1`
   - 让 `fruition-component.pages.dev` 的壳页生效

## 最快的发布方式

以后只要你是在修公开版，优先这样做：

```powershell
.\publish_public.ps1 -CommitMessage "修复说明"
```

这个命令会自动做下面的事：

1. 检查是否需要重建 bundle
2. 校验关键 Python 文件
3. 提交需要发布的文件
4. 推送到 GitHub
5. 触发 Streamlit Community Cloud 更新
6. 如果发现 Cloudflare Pages 代理文件有改动，再自动补发代理壳

## 什么时候只需要主应用同步

只改这些内容时，通常只需要一条命令：

- `component_matcher.py`
- `streamlit_app.py`
- `components.db`
- `cache/*`
- `Inductor/*`
- `Resistor/*`
- `Capacitor/*`
- 普通说明文档

原因是这些内容最终都走主应用链，`publish_public.ps1` 会自动处理。

## 什么时候还要补发 Cloudflare Pages

只要改到这些内容，就一定要让代理壳也发布：

- `cloudflare-pages-proxy/dist/_worker.js`
- `cloudflare-pages-proxy/dist/favicon.png`
- `cloudflare-pages-proxy/wrangler.jsonc`

如果你直接跑的是 `sync_local_and_public.ps1`，那它只会处理主应用链。  
如果你跑的是 `publish_public.ps1`，它会自动判断是否要补发代理壳。

## 发布后必须做的确认

发布完成后，固定做这三步：

1. 打开 `https://fruition-component.pages.dev/`
2. 用一个真实料号做搜索
3. 如果本次改了 BOM 或拓库，再测一条 BOM 行

只有浏览器里实际通过了，才算这次公开版发布完成。

## 例外情况

如果你只想先本地准备，不想真的发布：

```powershell
.\publish_public.ps1 -SkipPush
```

如果你只想单独发 Cloudflare Pages 代理壳，直接跑：

```powershell
.\deploy_cloudflare_pages_proxy.ps1
```

## 以后新增发布文件的规则

如果以后再加新的公开版发布产物，记住两件事：

1. 先把它加入 `sync_local_and_public.py` 的发布清单
2. 再确认 `publish_public.ps1` 会不会自动覆盖到它

这样以后就不会出现“文件改了，但没发到公开版”的情况。
