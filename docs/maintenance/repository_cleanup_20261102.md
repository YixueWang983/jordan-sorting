# 仓库旧交付文件清理记录

执行日期：2026 年 11 月 2 日。作者选择“先清理旧稿与重复产物”，本轮按此范围整理当前分支；不重写 Git 历史。

## 范围与保留内容

- 删除 15 份已被统一结果稿替代的论文 PDF、4 个旧交付 ZIP，以及 4 个 ZIP 校验值和 3 个交付验证文件，共 26 个文件，40,576,949 字节（约 38.7 MiB）。这些是不同历史版本及其交付副本，不是声称内容逐字节相同。
- 保留最新 80 页统一结果稿、全部 LaTeX 内容和图、源码、测试、输入清单、实验与审阅档案、历史计划和周报。附录 B 暂缓事项不变。
- 更新仓库、文档、论文、计划与图表 README，并新增 output 入口，移除过时“当前版本”和已过期任务安排。历史原记录保持原样。
- 当前 checkout 的体积减少；Git 历史仍含旧文件，因此这不是清空历史或显著缩减完整克隆大小的操作。

## 恢复与历史审计

清理前版本为 [`649e5ebae022704b774cc8958f9d7524a84afc66`](https://github.com/YixueWang983/jordan-sorting/tree/649e5ebae022704b774cc8958f9d7524a84afc66)。所有删除文件都可在该不可变提交中读取或恢复。

例如恢复一个旧稿（在仓库根目录执行）：

```sh
git restore --source=649e5ebae022704b774cc8958f9d7524a84afc66 -- output/pdf/jordan_thesis_supervisor_review_20261020_r2.pdf
```

历史报告的相对路径、清单与哈希没有改写。若历史报告仍引用一个已删除交付文件，使用下表的固定版本链接；需要复现完整历史审计时，使用相应原始版本的 checkout。特别是 `docs/thesis/unified_results_20261101/verify.py` 的保存性检查包括旧 PDF，应在本次清理前的提交运行。当前论文的源文件、最新 PDF 及编译日志仍可直接按 build_report.json 校验。

机器可读的文件大小、SHA-256 及引用档案列表见 [清理清单](repository_cleanup_20261102.json)。

## 删除明细

| 原路径及历史版本链接 | 字节数 | SHA-256 |
| --- | ---: | --- |
| [output/packages/jordan_review_20261016.zip](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_review_20261016.zip) | 10034262 | `a4b057c8f427ef829feabbec1f08489208c7fef260689378e52b881b2e9d69e7` |
| [output/packages/jordan_review_20261016.zip.sha256](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_review_20261016.zip.sha256) | 93 | `6a79da797e03785ec05feb9333a72c48a91e79a4a1c0330befc52d0753113150` |
| [output/packages/jordan_supervisor_review_20261016.verification.json](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261016.verification.json) | 507 | `9eacf6e32f8b23927e1b0e322062babc4ca6104910c9a7b884c01ceae1bbf029` |
| [output/packages/jordan_supervisor_review_20261016.zip](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261016.zip) | 2866160 | `98566c7af89c50d143a290438574c4f49c01dd2ff2f0fb2213dd1285a507f8f2` |
| [output/packages/jordan_supervisor_review_20261016.zip.sha256](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261016.zip.sha256) | 104 | `ccaa0d2f941a14fc2ec93f71993ef84a0212d228203a9927b5b557f670b502f8` |
| [output/packages/jordan_supervisor_review_20261020.verification.json](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020.verification.json) | 360 | `7f6f8b32dd42f83e074b35c84ad42bbb78801701d172e3342a14946d45f07bf9` |
| [output/packages/jordan_supervisor_review_20261020.zip](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020.zip) | 9919613 | `ef28e60fb14e578e43ee9b263ce55b67b34972e17ebcbf97affd6639158338d1` |
| [output/packages/jordan_supervisor_review_20261020.zip.sha256](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020.zip.sha256) | 104 | `3d852d12bdfe0b49ddad43d4c956ccc1128736f7e6cf4da571f9dfd39796ee77` |
| [output/packages/jordan_supervisor_review_20261020_r2.verification.json](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020_r2.verification.json) | 409 | `97204fa63b650ce86f1f2d03205febf06b60f057e199f985656b96ae35360919` |
| [output/packages/jordan_supervisor_review_20261020_r2.zip](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020_r2.zip) | 11866607 | `58dbadce35524aa0b7ae4a9cc3c7462760861a215ca43cbddf9f616074799aaf` |
| [output/packages/jordan_supervisor_review_20261020_r2.zip.sha256](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/packages/jordan_supervisor_review_20261020_r2.zip.sha256) | 107 | `6207b8af1a3b1a5f24a9017a462f02942a38ff4817c542c706df80763448c42c` |
| [output/pdf/Wang_Thesis_Draft_2026-11-02.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/Wang_Thesis_Draft_2026-11-02.pdf) | 403877 | `d662ef5d6e2950dce361c5b092911a343512c92e0b65de3bc725fce48ee7d33f` |
| [output/pdf/jordan_thesis_20261015.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_20261015.pdf) | 498989 | `4a8f2a7ea3210b4ec3ed1b42f1750f8c8711799e2eb420b78ab63110adf586d9` |
| [output/pdf/jordan_thesis_formal_20261016.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_formal_20261016.pdf) | 351025 | `957f38b36ebd8383a914f89459660e24bfc8b12143f66a69e06bbbc422807043` |
| [output/pdf/jordan_thesis_language_revision_20261031.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_language_revision_20261031.pdf) | 386799 | `50262cb9463999a1121f66ae6443983a0cc92a3a5a2d12c6506cab1f3175c2db` |
| [output/pdf/jordan_thesis_review_20261016.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_review_20261016.pdf) | 352046 | `754b3d8e1629248e7b0a057e8c67199b9d5c4b59faa876ddd7ea07e1f59516c0` |
| [output/pdf/jordan_thesis_supervisor_review_20261016.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261016.pdf) | 357005 | `ba77bbec5e8393097347447831dce24bef5456ff447976d52794b898c03ade12` |
| [output/pdf/jordan_thesis_supervisor_review_20261020.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261020.pdf) | 391761 | `a86aa4be9bec3f36d74bfb78403a29250b538384967e9b965528e6a942eeb740` |
| [output/pdf/jordan_thesis_supervisor_review_20261020_r2.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261020_r2.pdf) | 393702 | `bbdd4d49bed6acccb2a7c51960cb2cc8382093164ed63760ba5d682e8a57edc6` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_ai_alignment.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_ai_alignment.pdf) | 394208 | `591068b412e38353449dbf47fec7d2a932c9d50009bbe81b2f851a6ccd117ccf` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_ai_wording.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_ai_wording.pdf) | 394050 | `04cc6c7b1c597345746f56744f87a72840dd682fb17a690e8bd9bd3f9de852d6` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_algorithm_review.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_algorithm_review.pdf) | 392868 | `450c0a3e02c38fa9225844a65c68be36f4d9ea0fbb40acf66e18ad67efc868f7` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_disclosure_scope.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_disclosure_scope.pdf) | 392692 | `7e5c679e0bc956869de1f8d94e3d1f52f2ea752090c529be689f8e0dc62a25cf` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_numeric.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_numeric.pdf) | 393697 | `ed62a74165814671b24a2742eaf37331f994f675c0e3b660871b85c915147902` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_ownership_diagnostic.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_ownership_diagnostic.pdf) | 393273 | `8eabe10ed98712d5762c23fc11986a9c7ce28ee4ea705d658a63fcf1855b733d` |
| [output/pdf/jordan_thesis_supervisor_review_20261022_reflection.pdf](https://github.com/YixueWang983/jordan-sorting/blob/649e5ebae022704b774cc8958f9d7524a84afc66/output/pdf/jordan_thesis_supervisor_review_20261022_reflection.pdf) | 392631 | `98c9e7a04ae0ed50952faab898dbd224bd8874638e8f3e068d5b8d11678347f4` |

## 检查

清理检查记录见 [verification.json](repository_cleanup_20261102_verification.json)。检查仅涉及文件和链接，不运行排序、采样或新的性能实验。
