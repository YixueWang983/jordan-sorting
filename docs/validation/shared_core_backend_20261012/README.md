# 10-12 共享核心后端适配验证

基线为 `2be212a11ceee7453d2f8beebc04337d3690d117`，验证对象是其上的本地生产代码变更，**不是该旧提交本身**。[verification.json](verification.json) 记录源码/测试/实验工具 SHA256、Python 环境、完整命令和日志哈希。本归档不宣称真实指尖树已实现或允许计时。

## 实际改变

- `paper_jordan_sort_valid`、`paper_jordan_diagnostics_valid`、certified wrapper、初始化和共享 runner 接收关键字参数 `backend`。默认 `ordinary_list`；不存在的名字明确失败。`SiblingBackendSpec` 保存类与不可变构造参数。
- replay 传递相同 spec/policy，创建独立对象，拒绝复用当前可变后端、构造失败或返回其他后端类型。后端身份包含类、配置和 schema；初始 list ID 不再硬编码为 1/2。
- 核心用必要访问接口检查 liveness、边界 header、owner、child slots 和极端 child；不读取普通列表的 `pair_ids`、eager ownership 或 `get_list`。普通后端保留既有安全检查、扫描和 ownership 维护，没有因此获得高效复杂度。
- `stage_results` 继续控制执行次序，各模式保持一致；可关闭的 `backend_work` 独立存放。split 计数由后端报告，核心不按输入长度自动计复制量。普通四项计数保持旧逻辑大小口径，不是完整实际工作统计。
- `logical_snapshot` 只在审计/replay 路径物化有序 child groups 和 owner；同后端还比较物理快照。same-core replay 不属于独立算法证明。

契约、各 boundary 查询的前提及未闭合项见 [接入与成本表第 0 节](../../development/backend_integration_cost_map_20261011.md)。

## 验证结果与计数

| 运行 | 结果 | 解释 |
| --- | --- | --- |
| [核心回归](regression.log) | 173 项通过，0 跳过 | 原 155 项 + certified wrapper 3 项 + 新生产接入 15 项；不是 173 项真实树测试 |
| [下游回归](consumer_regression.log) | 125 项通过，0 跳过 | paper validator、week7/week11 runner、协议及 week11/week12 validator 的六个测试模块；测试中的微型夹具不属于正式实验 |
| 隐藏普通表示的有界检查 | n=3/4/5/6，分别 6/16/50/144 个 oracle 合法排列 | 合计 216 个，已包含在新增 15 项中的一个测试里，不另加到测试数量；通过 diagnostics/replay，并和外部 `sorted` 比输出 |
| 修改前后对照 | [11 份基线](baseline.json) 全部保持原字段 | [comparison.json](comparison.json)：输出、trace、原指标、processed_count、invariants_valid 相同；新增 backend_identity 字段单独记录 |

两个 unittest 命令共 **298 个不同测试方法**；开发过程中重跑不累计。11 份基线包含镜像及小输入，不作为独立数据集规模。没有复跑原 37 项模型/入口测试，它们的历史结果仍在原归档。

新路由夹具内部仍使用普通列表，但对核心隐藏 eager owner/child 字段，且不提供 `get_list`；因此可以捕获表示读取和硬编码初始化 ID。另一个夹具返回显式标识为 synthetic 的计数，仅用于证明核心采用后端报告值，绝不作为真实成本证据。所有夹具位于测试目录。

验证还覆盖五种 policy、镜像、非零普通 split、输出检查、新实例/相同配置、构造失败不回退、identity/schema 篡改、计数篡改、minimal 禁止完整快照、阶段顺序拒错。已有错误注入及普通 ownership 回归保持通过。

## 仍未完成

真实 heterogeneous 节点/fingers/ribs、插入与 split 重平衡、树的 header/稳定 handle 维护、真实结构不变量与成本账本均未实现。本轮也没有将抽象操作模型接到真实生产树。一般性 locality 论证仍需核对，不能以以上有限测试代替。

没有执行完整仓库测试、大规模 16 例重新资格、140/380 正式批次或论文编译。旧 16 例归档绑定旧源码，不自动取得本次核心资格。已有论文 PDF 保持原版身份，未新增后端完成或性能结论。

下一项生产工作是按已暴露的访问契约实现真实节点、两端 fingers、header 与 make/insert，随后 split/adopt 和完整排序；10-15 的非零真实树 split 检查点不变。
