# multimodal-playground

音频呼叫中心分析 POC：从 S3 摄取录音，以 Lance blob v2 存储音频，使用 SenseVoice 转写，使用 DeepSeek 分析，追加声学嵌入，并支持标量过滤或最近邻查询。

同时包含一套独立的图像分析流程（人脸存在性 + 清晰度检测），与音频流程完全隔离——详见下方的 [图像流程](#图像流程)。

> 提示：本文档中的命令均假设当前工作目录为 `multimodal-poc/` 子项目目录。

## 架构概览

媒体相关的分析逻辑位于各媒体包内（`audio/workflow/` 和 `image/workflow/`）。顶层 `workflow/` 负责与媒体无关的 Lance 表操作，例如创建索引和保留期管理。S3 / Ray 的共享配置放在 `multimodal_x/config.py`；媒体相关的设置与 schema 分别位于 `audio/config.py`、`image/config.py`、`audio/schema.py` 和 `image/schema.py`。

音频流程先执行分析，然后将音频 blob 与分析元数据共同写入 Lance 资产表。

## 工作流数据流

```
Manifest (parquet / jsonl / csv)
  doc_id, s3_url
       │
       ▼  Stage 1 — audio/workflow/analyze.py
       │  Daft: 读取 manifest → 下载音频字节 → 时长过滤
       │        → SenseVoice ASR（转写 + acoustic_emotion）
       │        → PII 脱敏（身份证、手机号）
       │        → DeepSeek LLM（downgrade_related、bad_tone、emotion_score …）
       │        → [可选 --embed] audio_embedding（128 维）
       │
       ├──（无 --embed）→ JSONL 输出到 S3
       └──（带 --embed）→ Lance 临时表写到 S3
                │
                ▼  Stage 2 — audio/workflow/ingest.py
                │  Daft: 读取 JSONL 或 Lance 临时表
                │        → 从 s3_url 下载音频 blob
                │        → 打上 ingest_time
                │        → write_lance（blob v2，append）
                │        → 校验 blob v2
                │
                ▼  Lance 资产表（blob v2，本地或 S3）
                │  列：doc_id、s3_url、audio_blob、
                │      transcript、acoustic_emotion、
                │      downgrade_related、primary_reason、
                │      secondary_reason、summary、confidence、
                │      text_emotion、bad_tone、emotion_score、
                │      [audio_embedding]、ingest_time
                │
                ▼  Stage 3 — workflow/index.py
                │  lance_ray  : 在 audio_embedding 上创建 IVF_PQ 索引
                │  pylance    : 在 ingest_time 上创建 ZONEMAP 索引
                │
                ├──▶  Stage 4 — audio/workflow/query.py
                │     Daft SQL（daft.sql()） : --sql（标量 / 聚合）
                │     Daft scanner pushdown  : --where（标量过滤）
                │     Daft scanner nearest   : --vector-from（ANN，IVF 索引）
                │
                └──▶  Stage 5 — workflow/manage.py
                      pylance ds.delete()        : --before / --after
                      lance_ray.compact_files    : 删除后自动执行
```

### 引擎分工

| 引擎 | 用途 | 原因 |
|----------------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| **Daft** | manifest 读取、S3 下载、ASR/LLM 流程、Lance 写入（Stage 1 & 2）、标量与 ANN 查询 | 主执行引擎；API 稳定 |
| **lance_ray** | IVF_PQ 向量索引创建、`compact_files` | Lance 表管理首选；分布式 Ray worker |
| **pylance** | ZONEMAP 标量索引、行删除、`cleanup_old_versions` | ZONEMAP：lance_ray 需要未发布代码；删除：仅该 API 支持 |
| **daft_lance** | 若 lance_ray 不可用，作为 `compact_files` 的兜底 | 不用于索引；仅数据处理走 Daft-first |

## 环境准备

```sh
uv sync --upgrade
```

创建 `.env` 文件（或直接导出变量）：

```sh
# S3 / MinIO
MINIO_ENDPOINT=http://127.0.0.1:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_REGION=us-east-1

# LLM — 留空则跳过 DeepSeek 分析（相关字段为 null）
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# ASR 设备
ASR_DEVICE=cpu          # 或 cuda

# Stage 1 应用的时长过滤
MIN_DURATION_S=0
MAX_DURATION_S=1800

# Stage 1 --embed 使用的嵌入后端
EMBED_BACKEND=signal    # signal（128 维 RMS+ZCR）或 wav2vec2

# Daft 执行器
USE_RAY=0               # 设为 1 则在 Daft 步骤中使用 Ray
RAY_ADDRESS=            # 留空则启动/加入本地 Ray
```

## 用法 — 音频流程管道

manifest 必须是 parquet、jsonl 或 csv，且至少包含 `doc_id` 和 `s3_url` 两列。  
`--lance-uri` 同时支持本地路径和 `s3://` URI。

### Stage 1 — analyze

从 S3 下载音频，执行 ASR 与 LLM 分析，将结果写到 S3。

```sh
# 输出：JSONL（无嵌入）
python -m multimodal_x.audio.workflow.analyze \
  --manifest s3://bucket/audio/manifest.parquet \
  --out      s3://bucket/audio/analysis.jsonl

# 输出：Lance 临时表（含 audio_embedding；后续 ANN 搜索必需）
python -m multimodal_x.audio.workflow.analyze \
  --manifest s3://bucket/audio/manifest.parquet \
  --out      s3://bucket/audio/staging.lance \
  --embed
```

### Stage 2 — ingest

读取 Stage 1 的输出，下载音频 blob，并将分析元数据一并追加到 Lance 资产表。

```sh
python -m multimodal_x.audio.workflow.ingest \
  --analysis  s3://bucket/audio/analysis.jsonl \
  --lance-uri s3://bucket/audio/calls.lance
```

如果 Stage 1 使用了 `--embed`，则将 `--analysis` 传为 `.lance` URI。

### Stage 3 — index

构建索引以加速查询。表中需要有足够多的行后再运行（IVF_PQ 至少需要 `num_partitions × 256` 行；小表可使用 `--num-partitions 1`）。

```sh
# 同时构建两种索引（默认）
python -m multimodal_x.workflow.index \
  --lance-uri s3://bucket/audio/calls.lance

# 仅构建向量索引
python -m multimodal_x.workflow.index \
  --lance-uri s3://bucket/audio/calls.lance \
  --no-time

# 为小表调整分区数
python -m multimodal_x.workflow.index \
  --lance-uri s3://bucket/audio/calls.lance \
  --num-partitions 1 --num-sub-vectors 8
```

### Stage 4 — query

```sh
# 标量过滤（Daft 通过 read_lance default_scan_options 下推）
python -m multimodal_x.audio.workflow.query \
  --lance-uri s3://bucket/audio/calls.lance \
  --where "bad_tone = true OR downgrade_related = true" \
  --top-k 20

# 完整 Daft SQL SELECT（SQL 作用域中的表名为 calls）
python -m multimodal_x.audio.workflow.query \
  --lance-uri s3://bucket/audio/calls.lance \
  --sql "SELECT primary_reason, COUNT(*) AS cnt FROM calls GROUP BY primary_reason ORDER BY cnt DESC"

# 通过 Daft SQL 进行标量过滤与投影
python -m multimodal_x.audio.workflow.query \
  --lance-uri s3://bucket/audio/calls.lance \
  --sql "SELECT doc_id, emotion_score, primary_reason FROM calls WHERE bad_tone = true AND emotion_score > 0.5 ORDER BY emotion_score DESC" \
  --top-k 20

# 通过 Daft Lance scanner 执行 ANN 向量搜索（使用 IVF 索引）
python -m multimodal_x.audio.workflow.query \
  --lance-uri s3://bucket/audio/calls.lance \
  --vector-from call_001.mp3 \
  --top-k 10

# 组合：ANN + 标量预过滤
python -m multimodal_x.audio.workflow.query \
  --lance-uri s3://bucket/audio/calls.lance \
  --vector-from call_001.mp3 \
  --where "downgrade_related = true" \
  --distance-min 0.0 \
  --distance-max 1.0 \
  --top-k 10
```

### Stage 5 — manage

按入库日期删除行并压缩表：

```sh
# 删除某日期之前入库的行
python -m multimodal_x.workflow.manage \
  --lance-uri s3://bucket/audio/calls.lance \
  --before 2025-01-01

# 删除日期窗口之外的行
python -m multimodal_x.workflow.manage \
  --lance-uri s3://bucket/audio/calls.lance \
  --after 2024-06-01 --before 2024-12-31
```

删除后会自动运行压缩与版本清理。

## 图像流程

图像分析位于 `multimodal_x/image/`，与音频流程完全隔离（独立的 workflow 入口、独立的 Lance 资产表），因此两者可以独立演进。Stage 3（索引）和 Stage 5（管理）是与媒体无关的共享入口。

v1 检测全部在本地运行（无需 VLM/API）：

| 检测项 | 方法 | 输出列 |
|-----------|--------|----------------|
| 人脸存在性 | InsightFace SCRFD（`buffalo_l`，仅检测模块，CPU） | `face_count`、`face_score`、`face_area_ratio`、`has_face` |
| 清晰度 / 模糊 | 图像缩放至 `IMAGE_LONG_EDGE` 后，OpenCV Laplacian 方差（全图 + 最大人脸裁剪） | `blur_score`、`face_blur_score`、`is_blurry`、`is_face_blurry` |
| 图文相似度 | ChineseCLIP（`OFA-Sys/chinese-clip-vit-base-patch16`） | `image_embedding` |

所有与人脸相关的指标（`face_score`、`face_area_ratio`、`face_blur_score`）均来自同一个人脸——即最大的人脸——因此规则引擎的 AND 条件始终针对单一人脸进行判断，而不会混合不同检测框的指标。

布尔结论由阈值规则引擎（`image/rules.py`）根据原始分数推导得出；原始分数与结论都会持久化，因此可以通过 SQL 重新调整阈值，而无需重新跑模型。可重调的下限是检测器自身的粗过滤阈值 `FACE_DET_THRESH`（默认 0.3）——低于该阈值的人脸不会进入表中。

每条 manifest 记录恰好产生一行输出。失败的记录会保留，并带有 `status` 列（`ok` / `download_failed` / `decode_failed`），分数为 null，结论为 null——这样 "未知" 可以与 "判定为否" 区分，无法读取的图像本身也是一种可报告的合规信号。

环境变量（全部可选）：

```sh
INSIGHTFACE_MODEL=buffalo_l   # insightface 模型包
INSIGHTFACE_ROOT=             # 离线/容器使用的预置模型目录（"" 表示 ~/.insightface）
FACE_DET_SIZE=640             # SCRFD 检测输入尺寸
FACE_DET_THRESH=0.3           # SCRFD 粗过滤阈值；应远低于 FACE_DET_SCORE_MIN
IMAGE_LONG_EDGE=1024          # 检测/模糊处理前缩放长边（不会放大）
FACE_DET_SCORE_MIN=0.5        # has_face 要求的最大人脸检测分数下限
MIN_FACE_RATIO=0.01           # has_face 要求的人脸面积 / 图像面积下限
BLUR_THRESHOLD=100.0          # blur_score 低于此值 → is_blurry
FACE_BLUR_THRESHOLD=80.0      # face_blur_score 低于此值 → is_face_blurry
IMAGE_EMBED_MODEL=OFA-Sys/chinese-clip-vit-base-patch16
IMAGE_EMBED_DEVICE=cpu
IMAGE_EMBED_DIM=512
```

首次运行检测时会下载 SCRFD 模型包（约 280 MB）到 `~/.insightface`；可设置 `INSIGHTFACE_ROOT` 指向预填充目录以跳过下载。首次使用 `--embed` 时会通过 Transformers 缓存下载 ChineseCLIP 模型。

```sh
# 准备图像并生成 manifest
python scripts/init_s3.py --media image --data-dir data/images \
  --raw-prefix raw/images --manifest-key image_poc/manifest.parquet

# Stage 1 — analyze（人脸存在性 + 清晰度分数 + 规则结论 → JSONL）
python -m multimodal_x.image.workflow.analyze \
  --manifest s3://contacts/image_poc/manifest.parquet \
  --out      s3://contacts/image_poc/analysis.jsonl

# Stage 1 带嵌入 — 图文搜索与以图搜图必需
python -m multimodal_x.image.workflow.analyze \
  --manifest s3://contacts/image_poc/manifest.parquet \
  --out      s3://contacts/image_poc/staging.lance \
  --embed

# Stage 2 — ingest（图像 blob + 分析元数据 → Lance 图像资产表）
python -m multimodal_x.image.workflow.ingest \
  --analysis  s3://contacts/image_poc/staging.lance \
  --lance-uri s3://contacts/image_poc/assets.lance

# 如果 Stage 1 没有使用 --embed，则传入 analysis.jsonl。

# Stage 3 — 为图文/以图搜图创建索引
python -m multimodal_x.workflow.index \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --embedding-column image_embedding

# Stage 4 — query（SQL 作用域中的表名为 images）
python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --where "has_face = true AND is_blurry = false"

python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --sql "SELECT doc_id, blur_score, face_count FROM images ORDER BY blur_score ASC"

# 文本搜图
python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --text "头像" \
  --where "status = 'ok'"

# 以图搜图（本地文件或表中已有行）
python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --image-path ./query.jpg

python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --image-from face_001.jpg

# 将描述表（doc_id → description）联入相似度结果。
# 描述表可以是普通 parquet/jsonl/csv 文件，无需 ingest：
#
#   import pyarrow as pa, pyarrow.parquet as pq
#   pq.write_table(pa.table({
#       "doc_id": ["face_001.jpg", "group_photo.jpg"],
#       "description": ["清晰正面人像", "两人合影"],
#   }), "descriptions.parquet")
#
# 结果会增加 `description` 列（左连接：没有描述的图像仍会保留在结果中，description = null）。
python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --text "合影" \
  --desc-table descriptions.parquet

# 使用 --sql 时，描述表会注册为 `descriptions`：
python -m multimodal_x.image.workflow.query \
  --lance-uri s3://contacts/image_poc/assets.lance \
  --sql "SELECT i.doc_id, d.description FROM images i LEFT JOIN descriptions d ON i.doc_id = d.doc_id WHERE i.has_face = true" \
  --desc-table descriptions.parquet

# Stage 5 — manage（共享入口）
python -m multimodal_x.workflow.manage \
  --lance-uri s3://contacts/image_poc/assets.lance --before 2025-01-01
```

## 已验证版本

| 组件 | 版本 | 说明 |
|-----------|---------|-------|
| Daft | 0.7.15 | 主执行引擎 |
| daft-lance | 0.4.0 | `read_lance`、`write_lance`、`take_blobs`、`create_scalar_index`、`compact_files` |
| pylance | 7.0.0 | Lance dataset、blob v2、ANN scanner、delete、cleanup |
| lance-ray | 0.4.2 | 向量索引创建；写回路径延后 |
| Ray | 2.55.1 | 由 lance-ray 引入；Daft 默认使用 native runner，除非 `USE_RAY=1` |

Daft 默认执行器：`native`（本地多线程）。设置 `USE_RAY=1` 可在 Daft 步骤中切换到 Ray。Stage 3（lance_ray 索引）和 Stage 4 ANN（pylance scanner）始终本地运行，不受 `USE_RAY` 影响。

## 注意事项与已知限制

**工作流管道中音频会被下载两次。**  
Stage 1 为了 ASR 和嵌入下载音频字节；Stage 2 为了存成 Lance blob 再次下载相同文件。这是有意为之——分析输出（JSONL）不跨阶段携带原始字节。请据此规划带宽成本，或在阶段之间将文件缓存到本地。

**Stage 1 必须使用 `--embed` 才能进行 ANN 搜索。**  
如果 Stage 1 没有使用 `--embed`，Lance 资产表将没有 `audio_embedding` 列。Stage 3 会报错，Stage 4 的 `--vector-from` 也将无向量可搜。需要重新以 `--embed` 运行 Stage 1 并重新 ingest。
对于图像表，同一 Lance 表的所有批次应保持一致：要么所有 Stage 1 都使用 `--embed`，要么都不使用。图像 ingest 步骤会拒绝将带 `image_embedding` 的批次追加到无该列的表，反之亦然。

**IVF_PQ 最小行数。**  
默认 `--num-partitions 16` 至少需要 4096 行。对于行数较少的表，请传入 `--num-partitions 1`（或跳过 `--embedding`，仅依赖标量查询）。

**缺少 DeepSeek 密钥 → LLM 列为 null。**  
如果未设置 `DEEPSEEK_API_KEY`，则 `downgrade_related`、`bad_tone`、`primary_reason`、`summary`、`confidence`、`text_emotion`、`emotion_score` 全部为 null。ASR 和声学嵌入仍会正常运行。

**每次 ingest 后都会校验 blob v2。**  
`validate_blob_v2` 会在 Lance 静默将 `audio_blob` 降级为 `large_binary` 时立即抛出。测试新版本库时请勿跳过此检查。

**本地 Lance URI 已经过端到端验证。**  
S3 Lance 表的读写由底层库覆盖，但应作为本 POC 的单独验证项对待。

**blob v2 资产表的压缩暂时禁用。**  
当前 `lance-ray 0.4.2` 的向量索引创建可与 pylance 7.x 配合工作，而 pylance 8.0.0 修复了 blob v2 压缩，但修改了 `lance-ray 0.4.2` 仍在调用的分布式索引提交 API。本项目暂时锁定 `pylance<8.0.0`，且 Stage 5 在删除行后跳过压缩。待升级到 pylance 8.x 及兼容的 lance-ray 版本后再启用 blob v2 压缩。
