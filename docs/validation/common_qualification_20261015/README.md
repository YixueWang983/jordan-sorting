# 共同输入资格与协议冻结（2026-10-15）

本目录先提交规则、工具和针对性测试，再运行实际资格；运行结果另行提交。
生产源码不变。冻结规则见 [协议](../../development/matched_protocol_20261015.md)
和 `preselected_rules.json`。代码、输入、配置和环境均记录在实际归档中。

本轮只执行资格验证，无warmup、calibration或正式计时；不授予高效后端最低交付验收。
140/380是覆盖目标；实际数量、缺口、错误和资源状态必须依据原始记录。

工具入口：

```sh
python experiments/qualify_common_inputs.py --output NEW_DIRECTORY
python experiments/validate_common_qualification.py NEW_DIRECTORY
```

实际运行前工作区必须干净。归档检查器独立重建选择、逐例结果和汇总，
但重用固定生成函数、oracle及几何分类器；它不是第二个排序实现。
资格通过说明选中的两个后端在绑定版本/配置上分别通过检查，不能证明所有输入。

新增9项针对性测试包括：完整候选分层、一次真实两后端checked/minimal、
错误count与输出拒绝、机械资格重建、失败后保留全选集、重新封装篡改拒绝、
实际进程终止后恢复、优化模式拒绝。机械替身记录不是算法资格。
