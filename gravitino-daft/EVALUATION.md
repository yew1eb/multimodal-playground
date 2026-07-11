# Gravitino + Daft 接入评估

本文档记录在 `gravitino-daft` 子项目中的实验结论，用于指导后续 `multimodal-poc` 是否以及如何接入 Gravitino。

## 1. 实验环境

- 计划部署：[gravitino-playground](https://github.com/apache/gravitino-playground)（官方完整环境）
- 备选部署：轻量级 `apache/gravitino:latest` 容器，或本地二进制包 `gravitino-1.3.0-bin.tar.gz`
- Daft 版本：`daft[gravitino]` 解析到 `daft==0.7.19`
- Gravitino Python client：`apache-gravitino==1.3.0`
- 认证方式：simple（无密码）

### 部署现状

> 当前运行环境的出站网络对 Docker Hub / GitHub / Apache CDN 大文件下载极慢或不可达：
> - `docker pull apache/gravitino:latest` 长时间无响应；
> - `gravitino-playground` 多个大镜像下载 20 分钟仍远未完成；
> - GitHub release tarball 与 Apache CDN 均连接超时。
>
> 因此**尚未完成真实 Gravitino 服务的本地部署**，但已准备好所有部署脚本与接入代码。
> 子项目中的 `bootstrap_gravitino.py` 已通过自研 mock 服务器验证 REST 路径与幂等逻辑。

## 2. 已验证能力

### 2.1 本地 fileset backend

- [x] 创建 fileset catalog（location: `file:///tmp/gravitino/...`）— 脚本与 REST 路径已验证（mock）
- [x] 创建 schema 与 MANAGED fileset — 脚本与 REST 路径已验证（mock）
- [ ] 使用 `apache-gravitino` GVFS Python client 上传文件 — 待真实 Gravitino 服务部署后验证
- [ ] 使用 Daft `read_parquet(gvfs://...)` 读取 — 待真实 Gravitino 服务部署后验证
- [ ] 使用 Daft `write_parquet(gvfs://...)` 写入 — 待真实 Gravitino 服务部署后验证

> 当前因网络限制无法下载 Gravitino 镜像/二进制包，GVFS 真实读写尚未验证。

### 2.2 S3-backed fileset backend（可选）

- [ ] 创建带 S3 属性的 fileset catalog
- [ ] Daft GVFS 读写 S3-backed fileset

> 待补充。

## 3. 当前限制

根据官方文档与实验观察：

1. **Daft GVFS 写入限制**：Daft 文档写明 GVFS write 当前主要支持 S3-backed fileset，其他后端可能尚未完全支持。
2. **认证**：playground 默认 simple auth，生产环境需考虑 OAuth2。
3. **Lance 格式**：Gravitino fileset 本质上是文件集合，不感知 Lance 语义；Lance 表的写入仍需通过 Daft/lance 完成，只是路径变为 `gvfs://`。
4. **版本兼容性**：`apache-gravitino` Python client API 在不同版本间可能有变化，建议优先使用 REST API 做元数据管理。

## 4. 对 multimodal-poc 的接入建议

### 4.1 适合 Gravitino 管理的数据

| 数据 | 是否适合 | 说明 |
|------|----------|------|
| Manifest（parquet/jsonl/csv） | ✅ 适合 | 通过 fileset 统一管理，路径用 `gvfs://` |
| 原始音频/图片二进制 | ✅ 适合 | 作为文件集合管理 |
| Stage 1 分析结果 JSONL | ✅ 适合 | 文件形式存储 |
| Lance 资产表 | ⚠️ 需验证 | Lance 是目录结构，需验证 GVFS 是否支持目录写入 |
| 向量索引 / 标量索引 | ❌ 不适合 | 由 Lance 内部管理，不应通过 fileset 暴露 |

### 4.2 推荐 backend

- **学习/本地开发**：local backend（`file://`）最轻量。
- **与 multimodal-poc 对齐**：S3-backed fileset（MinIO），因为现有项目已基于 MinIO。

### 4.3 改造点预估

1. 依赖：`multimodal-poc/pyproject.toml` 增加 `daft[gravitino]`。
2. 配置：`multimodal_x/config.py` 增加 Gravitino 连接参数；保留现有 MinIO/S3 配置作为 fallback。
3. IO 工具：`multimodal_x/storage/io.py` 增加 `gravitino_io_config()` 与 `gvfs_path()`；manifest/分析结果读取优先支持 `gvfs://`。
4. 引导脚本：新增 `scripts/init_gravitino.py` 创建 catalog/schema/fileset。
5. 双轨运行：CLI 同时支持 `s3://` 与 `gvfs://` URI，确保 Gravitino 不可用时仍能直连 S3。

## 5. 下一步建议

1. 完成本评估表中所有复选框的验证。
2. 若 local backend 写入不顺利，立即切换到 S3-backed fileset 验证。
3. 验证 Lance 表能否通过 `gvfs://` 路径写入并读取（这是接入 `multimodal-poc` 的关键）。
4. 根据验证结果，制定 `multimodal-poc` 具体改造计划。
