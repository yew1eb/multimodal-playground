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
