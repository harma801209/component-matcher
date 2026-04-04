# 公网访问说明

## 正式使用方式

现在系统已经统一按**公网正式版**维护，正式对外入口是：

- [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)

这条网址具备这些特征：

- 免费固定地址
- 不暴露个人 GitHub 用户名
- 用户不需要连你家/公司的局域网
- 你本地电脑关机后仍然可以访问

## 现在的公网架构

当前链路是：

1. `Cloudflare Pages` 作为固定入口
2. `Cloudflare Pages Worker` 负责代理和清理前端旧缓存
3. `Streamlit Community Cloud` 运行应用主体

所以现在的“正式站点”已经不是本地电脑上的临时服务。

## 本地电脑什么时候还需要参与

只有在下面这些场景，本地电脑才需要开着：

- 我们修改命名规则
- 我们扩数据库
- 我们调整页面显示
- 我们重新发布更新

也就是说，本地电脑现在承担的是：

- 开发
- 调试
- 发布

而不是“网站在线运行”。

## 现在最重要的两个脚本

### 1. 一键同步正式发布

```powershell
.\sync_local_and_public.ps1
```

或双击：

- [sync_local_and_public.cmd](C:/Users/zjh/Desktop/data/sync_local_and_public.cmd)

这一步负责把最新代码和数据同步到公网应用链路。

### 2. Cloudflare Pages 代理部署

当修改了 `pages.dev` 入口代理逻辑时，再执行：

```powershell
.\deploy_cloudflare_pages_proxy.ps1
```

或双击：

- [deploy_cloudflare_pages_proxy.cmd](C:/Users/zjh/Desktop/data/deploy_cloudflare_pages_proxy.cmd)

## 旧入口说明

下面这些旧方式现在都不再作为正式入口：

- 局域网直接打开本机服务
- 本地 Cloudflare Tunnel 固定隧道
- `streamlit.app` 原始直链
- 旧的 GitHub Pages 外壳页

如果只是给用户使用，请只发这个：

- [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)

## 兼容启动器

保留的旧启动器只是为了兼容以前的操作习惯：

- [start_lan.cmd](C:/Users/zjh/Desktop/data/start_lan.cmd)
- [start_public_fixed.cmd](C:/Users/zjh/Desktop/data/start_public_fixed.cmd)

它们现在不再代表推荐架构，会提示改用正式公网入口。
