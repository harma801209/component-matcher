# 富临通元器件匹配系统

这是当前项目的工作说明。现在这套系统已经统一按**公网正式版**维护，不再把“局域网版”和“公网版”当成两套产品长期并行维护。

## 当前正式入口

- 正式对外网址：[https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)
- 这条网址跑在 `Cloudflare Pages + Streamlit Community Cloud` 上
- 日常使用时，不需要在本地电脑上手动启动 Streamlit
- 电脑关机后，公网网址仍然可以访问

## 我们现在的工作方式

以后所有这类修改，都以公网正式版为准：

- 命名规则
- 数据库扩库
- 页面显示
- 搜索与 BOM 匹配逻辑

本地环境的作用改成：

- 调试
- 构建数据包
- 发布更新

而不是作为另一套长期对外使用的系统。

## 现在最常用的文件

- 正式公网入口说明：[PUBLIC_ACCESS.md](C:/Users/zjh/Desktop/data/PUBLIC_ACCESS.md)
- 一键同步发布：
  - [sync_local_and_public.cmd](C:/Users/zjh/Desktop/data/sync_local_and_public.cmd)
  - [sync_local_and_public.ps1](C:/Users/zjh/Desktop/data/sync_local_and_public.ps1)
- Cloudflare Pages 代理部署：
  - [deploy_cloudflare_pages_proxy.cmd](C:/Users/zjh/Desktop/data/deploy_cloudflare_pages_proxy.cmd)
  - [deploy_cloudflare_pages_proxy.ps1](C:/Users/zjh/Desktop/data/deploy_cloudflare_pages_proxy.ps1)

## 推荐发布流程

当我在本地改完规则、数据库或页面后，推荐直接走这一套：

```powershell
.\sync_local_and_public.ps1
```

它会负责：

1. 重建 `streamlit_cloud_bundle.zip`
2. 校验关键 Python 文件
3. 提交发布所需文件
4. 推送到 GitHub
5. 触发 Streamlit Community Cloud 自动更新

如果这次改动涉及 `Cloudflare Pages` 代理本身，再额外执行：

```powershell
.\deploy_cloudflare_pages_proxy.ps1
```

## 兼容启动器说明

下面这两个旧文件现在只保留做兼容入口，避免以后误会成“正式运行方式”：

- [start_lan.cmd](C:/Users/zjh/Desktop/data/start_lan.cmd)
- [start_public_fixed.cmd](C:/Users/zjh/Desktop/data/start_public_fixed.cmd)

它们现在会引导到正式公网入口，不再作为推荐的长期使用方式。

## 备注

- `streamlit_cloud_bundle.zip` 使用 Git LFS 管理
- 正式用户统一使用 `pages.dev` 入口
- 后续如果租正式域名，只需要把公网入口再绑定到新域名上，不需要改产品架构
