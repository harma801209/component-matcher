# 本机 Excel 只读打开

匹配结果保留“下载 Excel”，原“在线打开”替换为“本机 Excel（只读）”。
使用微软 Office URI `ms-excel:ofv|u|https://…/BOM.xlsx`，不是下载按钮改名，也不在服务器启动 Excel。
电脑需要安装并注册 Excel，浏览器第一次可能要求确认打开应用。手机或未安装 Excel 时可下载。
用户不用先手动保存；Excel 仍会经网络读取，并可能在本机产生临时缓存/受保护视图。

## 文件与访问边界

- 和下载使用同一份完整 XLSX 字节，包含所有导出工作表，不是筛选后的复核页面。
- 登录会话验证通过后，后端使用现有服务密钥创建临时入口。成员登录令牌不进入文件 URL。
- URL 是 256 位随机的短期读取凭据：持有者在有效期内可以读取，因此不要分享。服务端只保存其 SHA256。
- 有效期 300 秒；支持 GET、HEAD、单段 Range 和 OPTIONS，拒绝 PUT/POST 写回。到期返回404，页面禁用打开链接；刷新页面可生成新入口。下载不依赖此入口。
- 换/删除 BOM、重新匹配、切换客户或成本时间、退出登录时撤销旧会话入口；不同登录会话独立。撤销失败明确警告最迟5分钟过期，不假报成功。
- 已被 Excel 读取、缓存或另存的文件不能远程收回；“只读”并不禁止用户另存副本。
- 最大8MiB；临时服务故障、容量不足或超过限制时仍可下载完整原始导出，不截断、不上传到第三方在线 Office。

## 服务端实现

Cloudflare Worker 在 Streamlit 引导之前处理 `/api/bom-excel` 与 `/x/<随机凭据>/BOM.xlsx`。
管理接口仅允许持现有服务密钥的后端创建/按会话撤销。owner 是服务密钥与登录令牌的 HMAC，不是会员ID或登录令牌。
现有 D1 绑定中新增独立 `bom_excel_tickets`、`bom_excel_chunks` 表及索引，不改动成员、成本、快照表。
工作簿以 AES-GCM 密文分段保存，解密密钥由未保存的随机凭据派生，元数据纳入认证。
全局临时文件总量最多64MiB、128个入口，每段256KiB，HTTP请求体和单文件另有限制。
过期在每次读取时强制验证；密文在到期访问或下次创建/撤销请求时惰性清理，没有永久公开文件。
响应设 private/no-store、nosniff、no-referrer、noindex，日志不写文件内容、凭据或管理密钥。
后端请求使用明确的服务 User-Agent；默认 Python 请求标识在正式安全网关会被403拦截。
公网关闭了 Streamlit 文件监视，故业务层也按源文件时间戳重载这个无状态传输模块，不能仅依赖入口脚本重新编译。

## 验证和回退

- Python：`tests.test_bom_native_excel`、`tests.test_bom_excel_preview`、`tests.test_bom_save_as` 纳入完整安全门禁。
- Worker真实隔离D1：`node tests/test_bom_native_excel.mjs`（MINIFLARE_MODULE可指定已有miniflare安装路径，不使用远程数据库）。
- Chrome桌面/手机布局、定时失效后下载字节不变：`python tools/check_bom_native_excel.py [--phone]`。
- 正式验收用合成BOM，通过正常会员登录；核对 native URI、HTTPS文件全部工作表和下载字节，移除/注销后的404，以及本机安装的Excel只读读取。
- 不更改系统协议注册、浏览器确认策略、Excel信任中心或受保护视图。
- 回退可恢复上一版结果操作控件；新增表不必删除，短期入口自然到期。不要替换任何会员/成本数据库或运行快照。

参考：[微软 Office URI 规范](https://learn.microsoft.com/en-us/office/client-developer/office-uri-schemes)。
