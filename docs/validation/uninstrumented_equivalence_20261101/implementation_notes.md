# 无插桩配置实现核对说明

## 已完成的实现

1. `instrumented=True` 保持为默认值，旧 backend identity 与后端元组未改。
2. 无插桩配置保留同一个公开 backend 类型，以免破坏 `SiblingBackendSpec`
   对确切类型的检查；构造时绑定生成的方法。每次实例的初始化和绑定仍计时。
3. `src/uninstrumented_finger.py` 从两个规范源码模块的 AST 生成私有类族。
   算法方法没有第二份手工实现；构造器和 isinstance 检查解析到同一类族，
   包括 RootedPiece 和 FingerPiece。普通记录基类仅保留 `_ledger` slot，
   不继承 `_Tracked`，有效 getattribute/setattr 均为 object 的实现。
4. 投影删除 57 条纯计数语句、7 个 phase 上下文、21 个 observed 和
   11 个 phase 装饰器，并将 11 处构造器 ledger 参数替换为 None。
   不删除算法分支、必要检查、shared core 的计数语义或实际数据更新。
   若未识别的 ledger 访问残留，或计数参数中含算法调用，则拒绝生成。
5. 类与方法生成按进程缓存；backend_spec 在 batch 计时开始前显式准备。
6. 单独的资格验证/计时 schema 使用新后端元组，旧协议仍走原默认路径。
   AC Power 和 lowpowermode 0 在 campaign 开始及每个输入前后检查，
   保存原始 pmset 输出。电源门槛失败停止，先前记录保留。
7. 正式执行入口只读取作者事先创建的 receipt，不代填或创建 approval；
   common 成功后直接运行 targeted，任何失败阻止后续 campaign。

## 已完成的测试

全量 824 项测试通过，用时 185.306 秒。新增测试包括禁止调用 WorkLedger
和 _Tracked 时完成三类切分排序、checked/计数启用 trace 对照、配置隔离、
单输入资格验证档案复核、模拟时钟的配对次序、缺少 receipt 时拒绝执行、
电源改变时停止并保留记录、独立统计定义与作者执行入口的停止规则。
模拟时钟和临时 TEST STUB 均只属于测试，不是正式实验或作者批准。

实现提交：`3bfc839fae8da3061938f48f490e936deb0c002e`。
协议提交：`4aaf0022603e1abd9550b956c51da98ae89c29cf`。

192 输入等价性、两组资格验证与校准的实际结果另行追加。

## 完成的实际验证与校准

- 等价性 192/192 全部通过，并独立复核；每种树配置核对 50,626 个完成
  前缀，192 份旧 trace 保持一致；固定一例开启详细计数的对照通过。
- common 140/140、targeted split 12/12 的资格检查均通过并独立复核。
  common 每后端核对 27,566 个前缀，targeted 每后端 1,518 个前缀。
- 两组校准均全部通过并独立复核。common 的 B 分布为
  1:24、2:13、4:27、8:28、16:26、32:22；targeted 的 12 个输入均为 B=8。
- 四个 qualification/calibration 档案的完整绑定源码摘要完全一致。
  校准记录的环境为 Apple M4、CPython 3.12.14、macOS 27.2、AC Power、
  lowpowermode 0。没有并行运行测试、编译或其他实验。
- 尚未启动真实正式采样，尚未创建作者批准收据；校准数据不作性能结论。
