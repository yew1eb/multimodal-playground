# Gravitino + Daft 接入评估

本文档记录在 `gravitino-daft` 子项目中的实验结论，用于指导后续 `multimodal-poc` 是否以及如何接入 Gravitino。

## 1. 实验环境

- 部署：[gravitino-playground](https://github.com/apache/gravitino-playground)（本地完整环境，已启动）
- Daft 版本：`daft[gravitino]` 解析到 `daft==0.7.19`
- Gravitino Python client：`apache-gravitino==1.3.0`
- 认证方式：simple（无密码）
- S3/MinIO 后端： playground 内置 MinIO，S3 API 暴露于 http://localhost:9000

## 2. 已验证能力

### 2.1 本地 fileset backend

- [x] 创建 fileset catalog（location: `file:///tmp/gravitino/...`）
- [x] 创建 schema 与 MANAGED fileset
- [x] 使用 `apache-gravitino` GVFS Python client 上传文件
- [x] 使用 Daft `read_parquet(gvfs://...)` 读取
- [x] 使用 Daft `write_parquet(gvfs://...)` 写入

### 2.2 S3-backed fileset backend（MinIO）

- [x] 创建/复用带 S3 属性的 fileset catalog（`catalog_s3`，`s3a://gravitino-bucket/fileset/`）
- [x] 创建 schema 与 MANAGED fileset
- [x] 使用 `apache-gravitino` GVFS Python client 向 S3-backed fileset 上传文件
- [x] 使用 Daft `GravitinoConfig` + `gvfs://` 路径读写 S3-backed fileset（需宿主机 `minio -> 127.0.0.1`）
- [x] 使用 Daft `S3Config` 直连 MinIO 读写底层 S3 对象

> **注意**：默认情况下 playground 里 `catalog_s3` 的 `s3-endpoint` 属性是 Docker 内部地址 `http://minio:9000`。在宿主机访问时，需要把 `minio` 解析到 `127.0.0.1`（例如 `echo "127.0.0.1 minio" >> /etc/hosts`），Daft 的 `gvfs://` 路径才能正常工作。

## 3. 当前限制

1. **Daft GVFS 写入限制**：Daft 文档写明 GVFS write 当前主要支持 S3-backed fileset，其他后端可能尚未完全支持。
2. **认证**：playground 默认 simple auth，生产环境需考虑 OAuth2。
3. **Lance 格式**：Gravitino fileset 本质上是文件集合，不感知 Lance 语义；Lance 表的写入仍需通过 Daft/lance 完成，只是路径变为 `gvfs://` 或底层 `s3://`。
4. **版本兼容性**：`apache-gravitino` Python client API 在不同版本间可能有变化，建议优先使用 REST API 做元数据管理。
5. **S3 端点差异**：同一 catalog 在 Docker 内部与宿主机访问需要不同的 S3 endpoint，多环境部署时需要妥善管理。

## 4. 对 multimodal-poc 的接入建议

### 4.1 适合 Gravitino 管理的数据

| 数据 | 是否适合 | 说明 |
|------|----------|------|
| Manifest（parquet/jsonl/csv） | ✅ 适合 | 通过 fileset 统一管理，路径用 `gvfs://` 或底层 `s3://` |
| 原始音频/图片二进制 | ✅ 适合 | 作为文件集合管理 |
| Stage 1 分析结果 JSONL | ✅ 适合 | 文件形式存储 |
| Lance 资产表 | ⚠️ 需验证 | Lance 是目录结构，需验证 GVFS/S3 是否支持目录写入 |
| 向量索引 / 标量索引 | ❌ 不适合 | 由 Lance 内部管理，不应通过 fileset 暴露 |

### 4.2 推荐 backend

- **学习/本地开发**：local backend（`file://`）最轻量。
- **与 multimodal-poc 对齐**：S3-backed fileset（MinIO），因为现有项目已基于 MinIO。

### 4.3 改造点预估

1. 依赖：`multimodal-poc/pyproject.toml` 增加 `daft[gravitino]`。
2. 配置：`multimodal_x/config.py` 增加 Gravitino 连接参数；保留现有 MinIO/S3 配置作为 fallback。
3. IO 工具：`multimodal_x/storage/io.py` 增加 `gravitino_io_config()`、`s3_io_config()` 与 `gvfs_path()`；manifest/分析结果读取优先支持 `gvfs://` 与 `s3://`。
4. 引导脚本：新增 `scripts/init_gravitino.py` 创建 catalog/schema/fileset。
5. 双轨运行：CLI 同时支持 `s3://` 与 `gvfs://` URI，确保 Gravitino 不可用时仍能直连 S3。

## 5. 下一步建议

1. 验证 Lance 表能否通过 `gvfs://` 或 `s3://` 路径写入并读取（这是接入 `multimodal-poc` 的关键）。
2. 若需要在宿主机侧纯用 `gvfs://` 路径访问 S3-backed fileset，可再创建一个 endpoint 为 `http://localhost:9000` 的 catalog。
3. 根据验证结果，制定 `multimodal-poc` 具体改造计划。
