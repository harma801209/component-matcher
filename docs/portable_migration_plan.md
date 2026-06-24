# 系统移动硬盘无痛迁移清单

更新时间：2026-06-24

目标：把当前元器件匹配系统复制到移动硬盘后，在其他 Windows 电脑上也能继续运行、修改、拓库、同步和部署。

## 结论

当前系统的运行路径基本是可迁移的：主程序使用 `BASE_DIR = component_matcher.py` 所在目录来定位数据库、缓存、价格表、会员库和回报库。因此只要整套 `data` 工作目录和外部原厂资料目录一起带走，就不会被 `C:\Users\zjh\Desktop\data` 这个旧路径绑死。

不要只依赖 GitHub clone。`.gitignore` 会排除数据库、cache、会员库、回报库、浏览器登录态、token 和日志；从 GitHub 单独拉代码时会少掉很多运行资料。仓库里还使用 Git LFS 管理 `components.db`、`cache/components_search.sqlite`、`cache/components_prepared_v5.parquet`，新电脑如果重新 clone 也必须安装 Git LFS。

## 必须迁移

复制整个工作目录：

```text
C:\Users\zjh\Desktop\data
```

其中最关键的运行文件是：

- `component_matcher.py`、`streamlit_app.py`、`requirements.txt`、`runtime.txt`
- `components.db`
- `cache/components_search.sqlite`
- `cache/components_prepared_v5.parquet`
- `cache/components_prepared_v5_meta.json`
- `cache/member_auth.sqlite`
- `cache/no_match_reports.sqlite`
- `cache/manual_correction_rules.csv`
- `cache/resistor_library_cache.csv`
- `cache/mlcc_lcsc_dimension_cache.json`
- `cache/mlcc_official_dimension_cache.json`
- `cache/samsung_all_statuses_base.json`
- `cache/samsung_package_cache.json`
- `pricing/fojan_resistor_series_pricing.csv`
- `Capacitor/`、`Resistor/`、`Inductor/`、`Crystal‌/`
- `rules/`、`references/`、`reports/`、`docs/`、`templates/`
- `regression_cases.csv`
- `logo.png`
- `start_streamlit.ps1`、`sync_local_and_public.ps1`、`publish_public.ps1`、`deploy_cloudflare_pages_proxy.ps1`
- `cloudflare-pages-proxy/`，如果之后还要维护 Cloudflare 入口
- `streamlit_cloud_bundle.zip.part01`、`streamlit_cloud_bundle.zip.part02`、`streamlit_cloud_bundle.manifest.json`，如果之后还要本地生成或更新 Streamlit Cloud 数据包

复制外部原厂资料目录：

```text
C:\Users\zjh\Desktop\被动产品线资料
```

这个目录目前约 0.43GB，包含信昌 PDC、富捷 FOJAN、江海、Epson 等原厂 PDF/报价资料。它不在 `data` Git 工作区里，但以后继续拓库、核对规格书、导入 NTC/电阻/电容资料会用到。

## 建议不迁移

这些文件不影响系统核心运行，建议不要放进日常工作副本：

- `.venv/`：新电脑重新建立虚拟环境即可。
- `__pycache__/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`。
- `*.log`、`*.pid`、`tmp_*`、`_tmp_*`、`*.tmp`。
- `components.db.*.bak`、`components.db.off`、`streamlit_cloud_bundle.zip.off`：历史备份非常大，只在需要回滚旧库时单独归档。
- `chrome_*_profile/`、`streamlit_cloud_profile/`、`scratch_loginsetting*/`：浏览器登录态和 Cookie，体积大且敏感，跨电脑也不一定稳定。
- `_cloud_sim/`、`local_8532_test_*/`、`website_test_*/`、`sort_fix_*/`、`mlcc_edit_work/`：测试或临时工作目录。
- 操作截图：例如 `cache/*.png` 里的调试截图；当前已清理掉发现的旧截图。

## 敏感资料

这些资料如果要复制，建议单独加密保存或到新电脑重新登录/重新生成：

- `cloudflare_account_api_token.txt`
- `.streamlit/secrets.toml`，如果存在
- `.streamlit/config.toml`，里面包含 Streamlit cookie 配置；自己电脑迁移可以复制，给别人时应重新生成
- `cache/member_auth.sqlite`：会员账号、状态、注册/登录时间和加盐哈希密码
- `cache/no_match_reports.sqlite`：前台回报无匹配资料
- `streamlit_cloud_profile/`、`chrome_*_profile/`：浏览器 Cookie 和登录态

## 新电脑恢复步骤

1. 安装 Git、Git LFS、Python 3.12。
2. 把移动硬盘里的 `data` 目录复制到新电脑任意位置，例如：

```text
E:\component-matcher\data
```

3. 进入目录并建立虚拟环境：

```powershell
cd E:\component-matcher\data
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. 启动本机系统：

```powershell
.\start_streamlit.ps1 -Port 8501
```

5. 打开：

```text
http://127.0.0.1:8501
```

6. 验证：

```powershell
.\.venv\Scripts\python.exe -m py_compile component_matcher.py streamlit_app.py
```

7. 试搜一个已知料号、一个规格参数、上传一个 BOM，确认会员登录、后台、回报无匹配和 BOM 导出都正常。

## 推荐迁移方式

日常推荐：

```powershell
.\tools\create_portable_bundle.ps1 -Destination "E:\component-matcher\data" -IncludeExternalDocs
```

这会复制可运行工作副本，并把外部原厂资料复制到：

```text
E:\component-matcher\被动产品线资料
```

如果想把 Git 历史也带走：

```powershell
.\tools\create_portable_bundle.ps1 -Destination "E:\component-matcher\data" -IncludeGit -IncludeExternalDocs
```

注意：当前 `.git` 约 37.6GB，其中 LFS 对象约 16.4GB。带完整 Git 历史最稳，但移动硬盘占用会明显增加。

如果只是换电脑继续维护代码，更轻的做法是：新电脑从 GitHub clone，再从移动硬盘复制 `components.db`、`cache/` 里的关键运行数据、外部原厂资料目录。

## 后续优化建议

- 保持所有新脚本都用 `component_matcher.py` 所在目录或 `$PSScriptRoot` 定位文件，不写死 `C:\Users\zjh\Desktop\data`。
- 把新导入的原厂 PDF、报价表都放进 `C:\Users\zjh\Desktop\被动产品线资料` 或迁移盘同名目录，避免散落在下载目录。
- 数据库大改前只保留最近 1 到 2 个 `.bak`，其余旧备份移到单独归档盘。
- 移动硬盘里建议分成：

```text
component-matcher/
  data/                 # 系统工作目录
  被动产品线资料/        # 原厂规格书和报价源文件
  secrets-private/      # token、登录资料，单独加密或不复制
  db-backups/           # 历史大备份，可选
```
