# FACT：网络舆情风险预警与谣言治理系统

FACT（Full name: **F**alsehood & **A**larm **C**ontrol for public **T**rends）是一个面向网络舆情场景的毕业设计项目，目标是将“舆情数据管理 + 模型分析 + 风险预警 + 前端可视化”串成一条可运行的最小链路，并在此基础上逐步完善治理流程与系统能力。

## 技术架构（分层解耦）

- **fact_backend（Django + Django REST Framework）**  
  业务后台与数据管理：用户管理、舆情数据管理、分析结果管理、风险预警管理、治理响应管理等。  
  仅做业务与数据编排，不直接加载深度学习模型。

- **fact_model_service（FastAPI + PyTorch + Transformers）**  
  模型推理服务：谣言识别、情感分析、关键词提取、风险辅助判断等。  
  仅做推理 API，不承担复杂业务数据库逻辑。

- **fact_frontend（Vue3 + Vite + Element Plus + ECharts）**  
  前端可视化展示：数据大屏、舆情列表、识别结果、风险预警、趋势图表等。  
  通过 Axios 调用 Django 后端接口（不直接调用模型服务）。

- **fact_crawler（Scrapy / Requests）**  
  公开舆情/新闻/辟谣平台数据采集。采集数据优先通过 Django API 入库。

## 模块划分（目录说明）

本仓库采用单仓多模块结构：

- `fact_backend/`：Django + DRF 业务后台（**已完成 MVP 可运行与最小闭环接口**）。
- `fact_model_service/`：FastAPI 模型推理服务（**已完成 mock 推理服务，可稳定返回固定 JSON**）。
- `fact_frontend/`：Vue3 前端工程（后续提供最小页面与接口调用）。
- `fact_crawler/`：采集模块（后续提供最小可运行的采集脚手架与入库方式）。
- `datasets/`：公开数据集与自采集数据存放区。
- `experiments/`：训练/评估/基线实验代码（与在线推理解耦）。
- `docs/`：论文材料、接口文档、系统设计文档。

## 第一阶段开发目标（最小可运行版本 MVP）

严格聚焦最小链路，不做复杂业务：

1. **导入舆情数据**（先人工导入/CSV 导入/最小采集均可，最终落库由 Django 管理）
2. **Django 调用模型服务**（HTTP 调用 FastAPI）
3. **得到谣言识别结果**（先可用 mock 结果占位，后续再接真实模型）
4. **生成风险等级**（规则可先简单：基于模型置信度/情感倾向等）
5. **前端展示**（舆情列表 + 单条分析结果/风险等级展示）

## 开发原则（必须遵守）

- Django 只负责业务后台，不直接加载深度学习模型。
- FastAPI 只负责模型推理服务，不处理复杂业务数据库逻辑。
- Vue3 只负责前端展示，通过 Axios 调用 Django 后端接口。
- Django 调用 FastAPI 获取模型分析结果。
- 采集数据优先通过 Django API 入库。
- 不编造未要求的功能（如管理员端、区块链、全网实时监测等）。

## 当前状态

截至目前（**v1.0.0 手动录入型 MVP 已完成并通过测试**）：

- **fact_model_service（已完成并通过测试）**
  - 可用接口：`GET /health`、`POST /predict/rumor`、`POST /predict/sentiment`、`POST /predict/full`
  - 当前为 mock 逻辑，不加载真实模型权重

- **fact_backend（已完成并通过测试）**
  - SQLite 迁移可用，Django + DRF 可启动
  - 已实现最小业务闭环：**新增舆情 → 触发分析 → 保存分析结果 → 生成风险预警 → dashboard 汇总统计**
  - `POST /api/opinions/{id}/analyze/` 已加入**幂等逻辑**：重复调用不会重复创建 `AnalysisResult` 与 `RiskWarning`

## v1.1.0：第一阶段 mock 爬虫技术选型实验（已完成）

目标：在本地 `mock_sources/` 上完成受控对比实验，为三类采集场景确定唯一技术路线（不访问外网）。

- static_news（静态新闻/公告网页）→ **Scrapy**
- rss_api（RSS/API 结构化信息源）→ **Requests + feedparser**
- dynamic_page（动态渲染页面）→ **Scrapy + Playwright**

产出：`experiments/crawler_selection_experiment/results/` 下的对比结果 CSV/JSON、结论 markdown 与论文插图。

## v1.2.0：第二阶段国内真实公开源验证（已完成）

目标：在**国内公开源**上做小规模验证，确认第一阶段选型在真实环境中的可落地性（合规优先，不做大规模采集）。

- robots 合规检查 + 可访问性验证 + 字段抽取完整性验证
- 输出汇总与明细：
  - `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.csv|json`
  - `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_items.csv|json`

## v1.3.0：爬虫任务控制中心 + RSS 自动采集闭环（开发中）

本版本用于将实验结论落地到工程框架中（不再做实验对比）：

- static_news → Scrapy（v1.4.0 适配器实现）
- rss_api → Requests + feedparser（v1.3.0 优先落地）
- dynamic_page → Scrapy + Playwright（v1.5.0 适配器实现）

后端新增 `/api/crawler/*` 任务控制中心，支持 sources/topics/tasks/runs/items 与 `run-now`（v1.3.0 同步执行 RSS），采集结果写入 `OpinionData` 并可选自动触发分析，从而让 Dashboard/Warnings/Analysis 看到自动采集后的数据。

## v1.4.0：静态页 Scrapy 采集（static_demo / gov.cn）

- `scrapy_static` 在子进程中跑 Scrapy，避免与 Django 同进程 Twisted reactor 冲突。
- **本地 `python -m http.server` 页面**：响应头常缺少 `charset`，`response.text`/`response.css` 会按错误 encoding 解码；蜘蛛对 `127.0.0.1` / `localhost` 等使用 **`response.body.decode("utf-8", strict")` + `parsel.Selector`** 再抽取；子进程 JSON 使用 **`ensure_ascii=True`** 写 stdout，避免管道编码破坏中文。
- **中国政府网政策 `https://www.gov.cn/zhengce/`**：列表链接规则已放宽（不强制 `content_`；gov.cn + `/zhengce/` + `.htm/.html/.shtml`；排除 index/list 等）；列表诊断与详情抽取失败信息打印到 **stderr**，`run-now` 子进程 stderr 由 adapter 回显到 Django 终端。
- 演示页位于 `fact_crawler/static_demo/`（UTF-8 + `<meta charset="UTF-8">`）。清理旧测试数据：`cd fact_backend && python manage.py reset_demo_data --yes && python manage.py seed_crawler_sources`。

## v1.4.1：采集源 `source_code`（稳定业务键）

- `CrawlerSource` 增加 **`source_code`**（`SlugField`，唯一），种子源固定：`chinanews_society_rss`、`china_daily_rss`、`gov_zhengce_static`、`local_static_demo`。
- **`GET /api/crawler/sources/`** 默认按 **`id` 升序**（与上述种子写入顺序一致）；仍支持 **`?source_code=`** 筛选。
- **`local_static_demo`** 默认 **`robots_required=False`**（本地 `http.server` 演示，不做 robots 检查）。
- **`seed_crawler_sources`** 按 **`source_code` 幂等 upsert**（存在则更新字段，不存在则创建）；**勿在脚本里写死** 数据库自增 **`id`**（`reset_demo_data` 后 id 会变）。
- 联调推荐：`python scripts/test_create_chinese_crawler_task.py --mode static --source-code local_static_demo --no-keyword-filter`
- 开发可选：`python manage.py reset_demo_data --yes --reset-sequences`（**SQLite** 下重置相关表 `sqlite_sequence`；其他引擎见命令提示与 `docs/backend-api.md`）。

## 文档入口

- 后端 API 文档：`docs/backend-api.md`
- 开发日志：`DEVLOG.md`
- 发布说明：`docs/releases/v1.0.0.md`

## 本地启动（开发）

> 说明：以下为开发启动方式，依赖安装请按各模块 `requirements.txt` 自行处理。

### 启动模型推理服务（FastAPI）

在 `fact_model_service/` 目录：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

测试：

- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/docs`

### 启动业务后台（Django + DRF）

在 `fact_backend/` 目录：

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

测试（浏览器/DRF 可浏览接口）：

- `http://127.0.0.1:8000/api/`
- `http://127.0.0.1:8000/api/dashboard/summary/`
- `http://127.0.0.1:8000/api/opinions/`

## Windows 中文请求注意事项（开发环境）

- 在 Windows PowerShell 中，直接用 `Invoke-RestMethod`/`curl.exe` 发送中文 JSON **可能出现乱码入库**（与终端编码/JSON 序列化相关）。
- 推荐使用 Python `requests.post(..., json=payload)` 方式测试中文任务与关键词（见 `scripts/test_create_chinese_crawler_task.py`）。
- **推荐** `--source-code <slug>` 指定采集源；`--source-id` 仅临时调试（清库后 id 会变）。
- `scripts/test_create_chinese_crawler_task.py --no-keyword-filter`：用于验证**中文采集闭环**（不做关键词过滤，直接采集前 N 条）。
- `scripts/test_create_chinese_crawler_task.py --keyword 社会`：用于验证**主动搜索过滤能力**（关键词命中才入库）。
- 开发阶段若数据库已出现历史乱码/测试数据，可执行：
  - `python manage.py reset_demo_data --yes`（可选 `--reset-sequences`，见 `docs/backend-api.md`）
  - `python manage.py migrate && python manage.py seed_crawler_sources`

