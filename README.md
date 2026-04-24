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

