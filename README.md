# multimodal-playground

本仓库是多模态数据与 AI 数据治理相关的实验集合，包含两个独立的子项目：

## 子项目

### 1. multimodal-poc

多模态媒体分析 POC：
- 音频呼叫中心分析（SenseVoice 转写 + DeepSeek LLM 分析 + Lance blob v2 存储）
- 图像质量/人脸检测分析（InsightFace + OpenCV + ChineseCLIP）
- 基于 Daft 的数据流处理与 Lance 向量/标量查询

详见 [`multimodal-poc/README.md`](./multimodal-poc/README.md)。

### 2. gravitino-daft

Gravitino + Daft 学习与验证沙盒：
- 本地部署 Apache Gravitino（standalone 或官方 playground）
- 探索 Gravitino 的 metalake / catalog / schema / fileset 元数据管理
- 验证 Daft 通过 GVFS（`gvfs://`）读写 fileset 的能力
- 为后续 `multimodal-poc` 接入统一数据目录做准备

详见 [`gravitino-daft/README.md`](./gravitino-daft/README.md)。

## TODO / 后续引入

以下项目计划后续引入到本仓库进行实验和对比：

- [polars-benchmark](https://github.com/pola-rs/polars-benchmark) — Polars 官方基准测试集，用于对比 Polars 与 Daft 在不同查询场景下的性能。
- [LakeBench](https://github.com/microsoft/LakeBench) — 微软针对数据湖的基准测试，可用于评估多模态/半结构化数据场景。
- [daft-examples](https://github.com/Eventual-Inc/daft-examples) — Daft 官方示例集，用于学习 Daft 在真实场景下的最佳实践。
- [querybench](https://github.com/MrPowers/querybench) — 查询引擎对比工具，用于横向比较不同引擎的查询性能。
