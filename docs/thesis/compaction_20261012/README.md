# 10-12 论文章节精简合并与构建

已将用户提供的两个章节替换稿合入 `71e3e71b52b0bb057713ff7aeb1599ae24baede3` 之后的本地版本。原包基线为 `2be212a`，但两章、`main.tex` 及审计附录的基线 blob 与应用前仓库一致；只读 patch 准备检查及 `git apply --check` 均通过。完整原包保存在 [supplied_bundle.zip](supplied_bundle.zip)，原作者的预算另存为 [supplied_page_budget.md](supplied_page_budget.md)，它是预算及当时的审阅边界，不代表本次实测或学校规则核定。

## 实测结果

| 对象 | 旧版 | 本次 |
| --- | ---: | ---: |
| 整份 PDF 物理页 | 76 | **68** |
| 实现章 | 10 | 6（物理页 35–40） |
| 实验方法章 | 10 | 6（物理页 41–46） |
| 八个正文章节的物理区间 | 58 | 50（物理页 13–62） |
| 前置部分 | 12 | 12 |
| 附录与参考文献 | 6 | 6 |
| 空白页（已含在以上区间） | 8 | 6 |

净减少 8 页，使用原字号、行距、页边距和右页开章规则；没有手工删空白页。当前总页数落在用户提出的 50–70 页区间，但不是对学校正式计页规则的确认，也不是原包中 65 页参考预算已经完成。真实后端和新匹配实验的新增内容仍须控制篇幅。

最终 PDF 的文件名、SHA256、完整源码哈希与构建环境见 [build_record.json](build_record.json)。实际页界、页码标签与目录见 [page_inventory.json](page_inventory.json)。PDF 另存为 `Jordan_Sorting_精简稿_2026-10-12.pdf`；不覆盖 10-11 的历史 PDF，生成文件不纳入 Git。

## 与原包的有限合并调整

原包没有包含刚完成的共享核心适配，因此实现章补充 `71e3e71` 来源，并同步以下事实：核心已使用访问接口，普通表示及 membership 扫描保留在后端；阶段状态与可关闭的后端计数分开；replay 新建相同后端类型和配置的状态，检查身份与快照；核心累计后端报告的逻辑计数，不推算树的复制量。没有将接口进展写成高效后端已经实现。

编译另发现方法章的 `time.perf_counter_ns()` 超出行宽，改用可换行的标识符排版，含义不变。历史版本、60 输入/3,600 测量、资格检查、不同调用范围、计时边界、统计单位、失败语义及二次复制下界均保留。

## 检查与可复现边界

- 原包 ZIP 完整性与 SHA256SUMS 通过；原始检查报告保存在 [preparation_report.json](preparation_report.json)。
- 两章分别保留 20、18 个原有标签，未删除标签；合并标签仍可解析，不代表继承旧章节审计的 PASS。
- 在单独的干净源码副本中运行 LuaLaTeX、Biber、Latexmk，最终 [main.log](main.log) 和 [main.blg](main.blg) 无 warning、error、未定义引用/引文或 overfull/underfull box；控制台记录见 [build_console.log](build_console.log)。
- 全稿缩略页检查及改动章节物理页 35–46 的细查完成；空白页为 2、4、10、12、34、66。没有发现文字溢出、重叠或图表裁切。
- 生产源码、测试、算法章、附录、实验与历史数据未改。本轮不复跑排序回归或原包辅助脚本 fixture 测试；原包的六项测试结果仍仅是原作者的记录。

本地使用既有 TeX Live 2026 和原生 arm64 Biber。可在已配置依赖的论文目录运行：

```sh
mkdir -p build/texmf-var build/texmf-cache
TEXMFVAR=build/texmf-var TEXMFCACHE=build/texmf-cache latexmk -lualatex main.tex
```

本轮完成的是有界精简、共享核心措辞同步和排版核验。没有新增树后端、资格、性能结果或完整复杂度证明；后端开发仍沿原主线推进。
