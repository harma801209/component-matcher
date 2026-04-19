# 公开版发布后检查清单

每次发完公开版，只看这 4 项：

1. 打开 [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)
2. 搜一个真实料号，优先搜这次刚补的型号，确认能返回结果
3. 如果这次改了 BOM，再测一条 BOM，确认流程跑完
4. 如果这次改了公开壳页，再确认页面没有空白、转圈或报错
5. 如果这次改了 `component_matcher.py` 或拓库数据，但页面还是旧状态，确认 `streamlit_app.py` 里的 `PUBLIC_RELEASE_STAMP` 已更新

如果这次是拓库，额外看一眼刚补的相近替代料有没有出现在候选里。

4 项都通过，这次公开版发布就算完成。
## 额外确认

- 公开 bundle 里没有 `components.db`
- 首屏能正常打开
- 搜索和 BOM 都还能跑
