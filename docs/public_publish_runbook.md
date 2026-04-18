# 公开版发布规则

这里的“公开版”只指 [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)。

## 默认发布方式

平时只要改的是公开版相关内容，优先直接跑：

```powershell
.\publish_public.ps1 -CommitMessage "修复说明"
```

这个命令会自动做这几件事：

1. 检查是否需要重建 bundle
2. 校验关键 Python 文件
3. 提交并推送到 GitHub
4. 触发 Streamlit Community Cloud 更新
5. 如果检测到 Cloudflare Pages 代理文件变动，再顺手补发代理壳

## 什么时候只发一部分

- 只改本地应用内容时，正常跑 `publish_public.ps1` 就行。
- 只改 Cloudflare Pages 代理壳时，直接跑 `deploy_cloudflare_pages_proxy.ps1`。
- 只想先本地准备、不真正发布时，跑 `publish_public.ps1 -SkipPush`。

## 以后新增发布产物时的规则

以后如果又增加新的公开版产物，记住两步：

1. 先把它加入 `sync_local_and_public.py` 的发布清单
2. 再确认 `publish_public.ps1` 会自动包含它，避免“本地改了，但公开版没发出去”

## 发布后固定验证

发布完成后，固定只做这三件事：

1. 打开公开版页面
2. 用一个真实料号做搜索
3. 如果这次改了 BOM 或壳页，再补测对应页面

只要浏览器里实际通过，这次发布就算完成。
