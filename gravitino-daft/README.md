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
git clone git@github.com:apache/gravitino-playground.git
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

## 文档与参考资料

- [Apache Gravitino Playground](https://github.com/apache/gravitino-playground)
- [Daft Gravitino Connector](https://docs.daft.ai/en/stable/connectors/gravitino/)
- [EVALUATION.md](./EVALUATION.md) — 针对 `multimodal-poc` 的接入评估
- [Metadata as the Control Plane: The Foundation of an… | Junping (JP) Du (Datastrato) | OpenXdata 2026](https://www.youtube.com/watch?v=DDelVhL7l74) — Gravitino 相关演讲
- [Apache Gravitino Playground and Web UI Demo](https://www.youtube.com/watch?v=EjLtHSmbVh4) — Playground 与 Web UI 演示
- [Building a Next-gen Multimodal Data Lakehouse using Gravitino, Daft and Lance](https://www.youtube.com/watch?v=iMxde1GmI1Y) — Gravitino + Daft + Lance 多模态数据湖演讲
