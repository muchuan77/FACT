# fact_backend（Django + DRF）

业务后台：舆情、分析结果、风险预警、治理记录、爬虫任务控制中心等；**不**在进程内加载深度学习模型，通过 HTTP 调用 `fact_model_service` 完成推理。

## 边界与约束

- 仅负责业务编排与 REST API。
- **不得**在 Django 中直接加载/运行深度学习模型权重。
- 采集结果默认经本服务落库（`OpinionData`、`CrawlerRun` / `CrawledItem` 等）。

## 当前能力（与根 README 版本对齐）

- **舆情闭环**：`OpinionData`、`POST /api/opinions/{id}/analyze/`（幂等）、`AnalysisResult`、`RiskWarning`、`GET /api/dashboard/summary/`。
- **爬虫控制中心（v1.3+）**：`/api/crawler/*`（sources / topics / tasks / runs / items；`run-now` 同步执行 **RSS + `scrapy_static`**，可选 `auto_analyze`）。
- **种子与清库**：`python manage.py seed_crawler_sources`（按 `source_code` 幂等）、`python manage.py reset_demo_data --yes`（可选 `--reset-sequences`，见 `docs/backend-api.md`）。

## 本地启动

```bash
cd fact_backend
python manage.py migrate
python manage.py seed_crawler_sources   # 首次或清库后
python manage.py runserver 127.0.0.1:8000
```

## 进一步阅读

- 接口字段与示例：**[../docs/backend-api.md](../docs/backend-api.md)**
- 版本总览：**[../README.md](../README.md)**、**[../DEVLOG.md](../DEVLOG.md)**
