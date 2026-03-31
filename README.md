# 富临通元器件匹配系统

这是一个用于阻容感器件料号与规格匹配的 Streamlit 应用。

## Cloud 版本

本仓库已经整理成可部署到 **Streamlit Community Cloud** 的结构：

- 入口文件：`streamlit_app.py`
- 依赖文件：`requirements.txt`
- Python 版本：`runtime.txt`
- Streamlit 配置：`.streamlit/config.toml`
- 云端数据包：`streamlit_cloud_bundle.zip`

Streamlit Community Cloud 会从仓库根目录启动应用，因此请保持这些文件位于仓库根目录。

## 部署方式

1. 将本仓库推送到 GitHub。
2. 在 Streamlit Community Cloud 中创建新应用。
3. 入口文件选择 `streamlit_app.py`。
4. 如需访问码保护，在 Community Cloud 的 Secrets 中添加：

```toml
app_access_code = "你的访问码"
```

## 本地启动

- 局域网启动：`start_lan.cmd`
- 公网固定隧道启动：`start_public_fixed.cmd`

## 说明

- `streamlit_cloud_bundle.zip` 使用 Git LFS 管理，里面包含云端运行所需的数据包。
- 应用启动时会自动解包云端数据包，并在数据库已存在时避免重复全量重建。
- 如果你只想让团队内或局域网使用，可以继续用本地启动脚本。
