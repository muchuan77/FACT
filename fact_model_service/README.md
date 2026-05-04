# fact_model_service（FastAPI + mock 推理）

本模块为 **FACT 模型推理服务** 的最小可运行版本（MVP 第二阶段）。当前阶段不加载任何真实深度学习模型，仅用规则与 mock 逻辑返回固定格式 JSON，确保后续 Django 可稳定调用与落库。

## 边界与约束

- 仅负责推理 API，不承担复杂业务数据库逻辑
- 不接入真实模型、不训练、不写数据库
- 由 `fact_backend` 通过 HTTP 调用（前端默认不直连本服务）

## 目录结构

```text
fact_model_service/
├─ app/
│  ├─ main.py
│  ├─ schemas/
│  │  └─ prediction.py
│  ├─ services/
│  │  ├─ rumor_service.py
│  │  ├─ sentiment_service.py
│  │  └─ full_analysis_service.py
│  └─ utils/
│     └─ text_utils.py
├─ requirements.txt
└─ README.md
```

## 接口一览

### GET `/health`

健康检查。

返回示例：

```json
{ "status": "ok", "service": "FACT model service" }
```

### POST `/predict/rumor`

谣言识别（mock）。

请求体：

```json
{ "text": "网传某地发生严重事故，引发大量关注。" }
```

返回字段：

- `text`：原始文本
- `rumor_label`：`rumor` / `non_rumor`
- `rumor_probability`：0~1
- `model_name`：当前 mock 模型名

### POST `/predict/sentiment`

情感分析（mock）。

请求体：

```json
{ "text": "网传某地发生严重事故，引发大量关注。" }
```

返回字段：

- `text`：原始文本
- `sentiment_label`：`negative` / `neutral` / `positive`（当前 MVP 主要输出 `negative/neutral`）
- `sentiment_probability`：0~1（表示“负向”概率）
- `model_name`：当前 mock 模型名

### POST `/predict/full`

综合分析（mock）：谣言识别 + 情感分析 + 关键词 + 风险辅助判断。

请求体：

```json
{ "text": "网传某地发生严重事故，引发大量关注。" }
```

返回字段：

- `keywords`：规则命中的关键词数组
- `suggested_risk_level`：`low` / `medium` / `high`
- 其余字段同上

## 本地启动

在 `fact_model_service/` 目录下执行（先自行创建虚拟环境并安装依赖）：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

访问交互文档：

- Swagger UI：`http://127.0.0.1:8001/docs`
- OpenAPI JSON：`http://127.0.0.1:8001/openapi.json`

## 测试示例（curl）

健康检查：

```bash
curl http://127.0.0.1:8001/health
```

谣言识别：

```bash
curl -X POST "http://127.0.0.1:8001/predict/rumor" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"网传某地发生严重事故，引发大量关注。\"}"
```

## 进一步阅读

- 工程版本与联调总览：**[../README.md](../README.md)**
- 文档索引：**[../docs/README.md](../docs/README.md)**
