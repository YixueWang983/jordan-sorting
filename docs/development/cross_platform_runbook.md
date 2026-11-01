# Mac / Windows 测试与环境评估

执行依据：[版本化协议](../plan/cross_platform_evaluation_20261101.md)。算法生产代码不因平台切换而更换。正式论文门槛与用于选测试服务器的环境诊断分别保留。

## 同步和 Python

完整克隆 Git 历史；历史证据验证需要 `git show`，不能 shallow clone。Windows 首次 clone：

```powershell
git -c core.autocrlf=false clone --config core.autocrlf=false --config core.longpaths=true https://github.com/YixueWang983/jordan-sorting.git D:\project
```

已有仓库使用 `git fetch origin` 后检出明确提交，先检查 `git status`，不要覆盖未提交工作。仅设置 autocrlf 不会修复已转换的文件；应在干净副本重新检出并核对 Git blob/源码摘要。源码和 manifest 中的相对路径统一使用 `/`。

评测采用 64 位 CPython 3.12.14。在仓库外建立虚拟环境；Windows 本次为 `D:\project-env\jordan-sorting-py312`。Mac 可使用自己的相同版本解释器。系统上的其他 Python 版本不参与比较。需要图形分析或全量工具测试时，在所选虚拟环境中安装 matplotlib 并将 `python -m pip freeze --all` 保存到环境记录；其余实验核心仅需标准库。Codex 自带 Python/Git 可使用，但应用更新后需重新核对实际版本。

## 测试

macOS，仓库根目录：

```sh
PYTHONPATH=src:experiments:tests python3 -B -m unittest discover -s tests
PYTHONPATH=src:experiments:tests python3 -B -m unittest test_platform_environment test_host_stability
```

Windows PowerShell，仓库根目录：

```powershell
$env:PYTHONPATH = 'src;experiments;tests'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
& 'D:\project-env\jordan-sorting-py312\Scripts\python.exe' -B -m unittest discover -s tests
& 'D:\project-env\jordan-sorting-py312\Scripts\python.exe' -B -m unittest test_platform_environment test_host_stability
```

单独修改一项测试可使用 `模块.测试类.测试方法` 定向执行。需要评测前先完成测试，禁止与计时会话并行运行。

当前跨平台执行入口是下文的 `run_host_stability.py` 和 `run_input_suite.py`。历史 week11/week12 的执行器仍保留原 POSIX load-average 门槛；它们的合成档案测试可在 Windows 上运行，但不会将不存在的 Windows `os.getloadavg` 伪装成系统观测。新实验使用当前入口。

## 环境诊断与迁移决策

开始诊断前提交代码，保持干净工作区。输出放仓库外的新目录；已有目录会被拒绝。默认按预定规则选择五来源各最小/最大 n 的 10 个输入，先做两后端 checked/fresh minimal 正确性检查、单独校准，再执行三会话配对计时。诊断不需要作者数学审阅收据，也不会生成该收据；其结果明确为 `performance_eligible=false`，不能充当论文正式数据。

Windows：

```powershell
& 'D:\project-env\jordan-sorting-py312\Scripts\python.exe' -B experiments/run_host_stability.py --output D:\jordan-evaluation\windows-attempt-001 --conditions D:\project-environment-check\20261101\user-confirmed-conditions.json
& 'D:\project-env\jordan-sorting-py312\Scripts\python.exe' -B experiments/validate_host_stability.py D:\jordan-evaluation\windows-attempt-001 --output D:\jordan-evaluation\windows-analysis-001.json
```

Mac：

```sh
PYTHONPATH=src:experiments python3 -B experiments/run_host_stability.py --output ../mac-stability-attempt-001
PYTHONPATH=src:experiments python3 -B experiments/validate_host_stability.py ../mac-stability-attempt-001 --output ../mac-stability-analysis-001.json
```

可重复 `--case-id` 指定登记清单中的任意输入进行定向诊断。新目录保存独立结果，不将不同输入/源码/主机的旧结果拼接成一次完整会话。默认 900 秒整轮预算、180 秒每输入任务预算；失败立即停止并保存 failure，先检查原因，不自动覆盖或重试。

两台机器都使用同一提交完成诊断后，复制完整、未修改的诊断目录到分析主机（保留所有文件字节；诊断目录没有绝对前置依赖），执行：

```sh
PYTHONPATH=src:experiments python3 -B experiments/validate_host_stability.py ../windows-attempt-001 --compare ../mac-stability-attempt-001 --output ../host-comparison-001.json
```

左侧为 Windows，右侧为 Mac。验证器从原始记录重算每次会话的中位数/IQR，报告 IQR/median、会话中位数的相对跨度以及 Windows 指标较低的输入数。速度与波动分别讨论。要求源码、输入、Python 版本、GC、诊断规则和会话数一致；主机身份和批量 B 可不同。一次诊断只支持初步判断，不把主机差异当操作系统因果结果。需要长期迁移时保留后续日期的独立重复，不只挑最好的一次。

主机条件记录为独立 `conditions.json`。Sherry02 的固定 5.0 GHz 和无竞争负载为作者确认，不当作软件实测。记录当前电源计划/VBS，程序不更改系统电源或安全设置。

## 统一论文评测

新统一入口保留四阶段和 `--source` 选择。Mac 与 Windows 都使用 `run_input_suite.py`，按 equivalence → qualification → calibration → formal 执行；每阶段新目录，各前置档案必须来自同一环境和源码。Windows 参数与 Mac 相同，仅替换解释器、路径及 PYTHONPATH 分隔符。所有阶段通过原始电源证据、完整源文件、Git 对象及原始工作记录验证；正式采样仍需作者已审阅的真实收据。

`--stage formal --source all` 的连续会话规则保持不变。`--case-id` 只属于环境诊断，不用于拼接正式会话。不要把历史 Mac 资格/校准直接迁移成 Windows 前置结果。

历史统一档案使用 `validate_input_suite_run.py ARCHIVE --historical` 只读检查；旧档案的绝对前置引用需按原归档 relocation 说明恢复。新环境诊断没有此绝对前置限制，可按完整目录跨机复制后验证。

平台 API 依据：[Python 文件同步和替换](https://docs.python.org/3.12/library/os.html#os.fsync)、[Windows GetSystemPowerStatus](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getsystempowerstatus)。文件同步在重命名前完成；Windows 的交流供电和节能状态直接取自系统 API。

Windows 原生命令按实际[控制台输出码页](https://learn.microsoft.com/en-us/windows/console/getconsoleoutputcp)解码，无控制台时回退到系统 OEM 码页。不能用 Python UTF-8 模式或 ANSI 码页推断 `powercfg` 的输出编码。
