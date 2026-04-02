# 富临通元器件匹配系统

这是一个用于阻容感与铝电解电容料号、规格参数、BOM 上传匹配的 Streamlit 应用。

## 当前部署结构

- 局域网版：直接读取这台电脑上的本地数据库和缓存
- 公网版：部署在 Streamlit Community Cloud，固定地址为 [fruition-componentmatche.streamlit.app](https://fruition-componentmatche.streamlit.app)

两边共用同一套代码，但公网版使用仓库里的发布文件和 `streamlit_cloud_bundle.zip`。

## 一键同步发布

如果你已经在本地改好了规则、数据库、页面或说明文件，推荐直接使用下面这个启动器：

- [sync_local_and_public.cmd](C:/Users/zjh/Desktop/data/sync_local_and_public.cmd)

它会自动完成这几件事：

1. 重新构建 `streamlit_cloud_bundle.zip`
2. 校验关键 Python 文件语法
3. 只暂存发布需要的文件
4. 自动创建 git commit
5. 通过 GitHub SSH 443 推送到远端 `main`
6. 让 Streamlit Community Cloud 自动部署新版本

也可以直接运行 PowerShell 版：

```powershell
.\sync_local_and_public.ps1
```

常用参数：

```powershell
.\sync_local_and_public.ps1 -CommitMessage "更新江海铝电解库"
.\sync_local_and_public.ps1 -SkipBundleRebuild
.\sync_local_and_public.ps1 -SkipPush
```

## Streamlit Community Cloud

云端入口文件：

- `streamlit_app.py`

云端运行依赖：

- `requirements.txt`
- `runtime.txt`
- `.streamlit/config.toml`

云端数据包：

- `streamlit_cloud_bundle.zip`
- `streamlit_cloud_bundle.manifest.json`

应用在云端启动时，如果本地数据库文件不存在，会自动从 `streamlit_cloud_bundle.zip` 解包恢复。

## 本地启动

- 局域网启动：`start_lan.cmd`
- 本地固定公网隧道启动：`start_public_fixed.cmd`

## 说明

- `streamlit_cloud_bundle.zip` 使用 Git LFS 管理
- 公网版和局域网版不会自动双向同步；推荐用一键同步脚本统一发布
- 如果需要访问保护，可以在本地启动器或 Streamlit Cloud secrets 中设置 `app_access_code`
