# gravitino-daft

Gravitino + Daft 学习与验证沙盒，用于本地部署 [Apache Gravitino Playground](https://github.com/apache/gravitino-playground) 并验证 Daft 通过 GVFS 读写 fileset 的能力。

本子项目独立于 `multimodal-poc/`，不修改其任何代码。

## 环境准备

1. 安装 Docker / Docker Compose。
2. 安装 Python 3.12 与 `uv`（或 `pip`）。
3. 同步依赖：
   ```bash
   uv sync
   ```
4. 复制环境变量示例：
   ```bash
   cp .env.example .env
   ```

## 启动 Gravitino

使用官方 Gravitino Playground 进行本地部署：

### 官方 Gravitino Playground（完整环境）

如果需要体验 Hive、Trino、Spark、Iceberg REST 等完整能力，可在仓库根目录旁克隆官方 playground：

```bash
# 克隆到 ../gravitino-playground（与 gravitino-daft/ 同级）
cd ..
git clone git@github.com:yew1eb/gravitino-playground.git
cd gravitino-playground
./playground.sh start
```

等待 3–5 分钟后验证：

```bash
./playground.sh status
```

打开 Web UI：http://localhost:8090

> 注意：playground 会占用 8090、9001、13306、15432、18080、18888 等端口，请确保无冲突；
> 首次启动需要下载多个大体积 Docker 镜像，耗时可能较长。

## 运行示例

### 1. 创建 fileset catalog / schema / filesets

```bash
uv run python scripts/bootstrap_gravitino.py
```

### 2. 上传示例数据

```bash
uv run python scripts/upload_sample_data.py
```

### 3. 读取 GVFS 数据

```bash
uv run python scripts/read_gvfs.py
```

### 4. 写入 GVFS 数据

```bash
uv run python scripts/write_gvfs.py
```

## 无 Gravitino 环境时测试 bootstrap 脚本

如果暂时无法部署 Gravitino（如下载镜像受网络限制），可以使用项目自带的 mock 服务器验证 `bootstrap_gravitino.py` 的 REST 调用逻辑：

```bash
# 终端 1：启动 mock 服务器
uv run python scripts/mock_gravitino_server.py

# 终端 2：运行 bootstrap（mock 服务器监听 127.0.0.1:8090）
uv run python scripts/bootstrap_gravitino.py
```

> mock 服务器仅用于验证 bootstrap 脚本的 REST 路径与幂等逻辑，不支持 GVFS 文件读写。

## S3/MinIO 示例

`gravitino-playground` 已内置 MinIO 服务（S3 API 暴露在 http://localhost:9000，控制台在 http://localhost:9002），并在启动时自动创建了 `catalog_s3` 这个 S3-backed fileset catalog。下面演示如何把 Gravitino 作为元数据控制平面、把 MinIO 作为存储后端，并用 Daft 通过 `gvfs://` 路径读写底层 S3 对象。

> 前置条件：宿主机需要把 `minio` 解析到 `127.0.0.1`，这样 catalog 里 `s3-endpoint=http://minio:9000` 才能在宿主机正常访问：
> ```bash
> sudo sh -c 'echo "127.0.0.1 minio" >> /etc/hosts'
> ```

### 1. 创建 S3-backed schema / filesets

```bash
uv run python scripts/bootstrap_s3.py
```

### 2. 查看 S3 fileset 元数据

```bash
uv run python scripts/s3_metadata.py
```

### 3. 通过 GVFS 上传示例数据到 S3-backed fileset

```bash
uv run python scripts/upload_s3_fileset.py
```

### 4. 用 Daft + GVFS 读取 S3-backed fileset

```bash
uv run python scripts/read_s3_fileset.py
```

### 5. 用 Daft + GVFS 向 S3-backed fileset 写入数据

```bash
uv run python scripts/write_s3_fileset.py
```

### 6. 直连底层 S3（可选）

如果你希望绕过 GVFS、在客户端自行管理 S3 凭证和端点，可以：

```bash
uv run python scripts/direct_s3_with_daft.py
```

### 7. 在 Jupyter Notebook 中交互式探索

```bash
uv run --with jupyterlab jupyter lab notebooks/gravitino_daft_s3.ipynb
```

## 文档与参考资料

- [Apache Gravitino Playground](https://github.com/apache/gravitino-playground)
- [Daft Gravitino Connector](https://docs.daft.ai/en/stable/connectors/gravitino/)
- [EVALUATION.md](./EVALUATION.md) — 针对 `multimodal-poc` 的接入评估
- [Metadata as the Control Plane: The Foundation of an… | Junping (JP) Du (Datastrato) | OpenXdata 2026](https://www.youtube.com/watch?v=DDelVhL7l74) — Gravitino 相关演讲
- [Apache Gravitino Playground and Web UI Demo](https://www.youtube.com/watch?v=EjLtHSmbVh4) — Playground 与 Web UI 演示
- [Building a Next-gen Multimodal Data Lakehouse using Gravitino, Daft and Lance](https://www.youtube.com/watch?v=iMxde1GmI1Y) — Gravitino + Daft + Lance 多模态数据湖演讲
