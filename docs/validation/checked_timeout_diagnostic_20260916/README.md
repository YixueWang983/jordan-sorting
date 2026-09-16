# Checked 超时诊断与扩展计时草案

本目录按用户后续授权归档 2026-09-16 已在仓库外完成的单输入诊断。此次提交只发布已有结果和草案，没有重新执行诊断、正确性验证或正式计时。

- [原始诊断报告](report.md)：checked diagnostics 在约 97.365 秒内完成，minimal 输出检查也通过；本次未复现历史超时。
- [原始诊断记录](diagnostic.json)：函数计数、包含时间与排除嵌套调用的时间、前缀进度、环境及源码/输入哈希。
- [扩展计时草案](expanded-timing-proposal.md)：尚未执行、尚未冻结的候选方案；不是新增性能实验结果。
- [诊断脚本](diagnose.py)与[后处理脚本](finish.py)：实际运行时的原始脚本快照，按原字节保存，便于检查记录的产生方式。
- [归档清单](manifest.json)：文件哈希、历史运行基线和发布时静态复核结果。

`report.md` 中“仓库外”“没有 commit、push”以及 `diagnostic.json` 的 Git 状态，描述的是诊断完成当时，而非本目录发布后的状态。诊断基线为 `071973c639a26eb6f08ee5d9f7025e5de97b2a34`；发布前 HEAD 为 `a7028a5d62aa18aabb72c60f30954f1d5767a5b8`。

这些脚本不是通用命令行工具。它们保留当时机器的绝对路径，并向脚本所在目录写入结果；不要直接在本归档目录运行。若需重做，应复制到新的仓库外目录、调整路径，并记录改动后的脚本哈希与独立运行环境。重新运行所得时间不能覆盖本次记录。发布检查只解析脚本语法，没有执行脚本。

计时字段用于诊断资源开销：`elapsed_seconds` 从 oracle 认证之后开始，到完整 checked diagnostics 返回及记录保存附近结束，包含包装器和进度记录开销；不包含随后独立进程中的 minimal 检查。函数 inclusive 时间相互包含，不能相加。该数据不是正式排序 benchmark。

原 `results/validation_runs/ordinary_list_extended_correctness_v1__run001/` 保持 209 PASS、1 TIMEOUT、4 未执行；没有将本次成功诊断回写为原运行的第 210 个 PASS。原正式性能实验仍为 60 cases、3,600 measured rows。1024/1025 未由本次诊断验证。方案中的样本配额及预算均为建议，不代表已经生成或完成。
