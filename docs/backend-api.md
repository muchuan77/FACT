# FACT 后端 API 文档（MVP）

本文档整理当前 FACT `fact_backend`（Django + DRF）已实现的 MVP 接口，用于前端对接与论文材料沉淀。

**文档导航**：索引见 **[README.md](README.md)**；版本总览见根目录 **[../README.md](../README.md)**。

## 基础信息

- **服务地址（开发）**：`http://127.0.0.1:8000`
- **API 前缀**：`/api/`
- **数据格式**：JSON
- **认证**：MVP 阶段不启用复杂认证（后续扩展）

## Windows 中文请求注意事项（开发环境）

- Windows PowerShell 直接发送中文 JSON 可能导致入库字段乱码（与终端编码/JSON 序列化相关）。
- 推荐用 Python `requests.post(..., json=payload)` 测试中文任务与关键词：
  - `python scripts/test_create_chinese_crawler_task.py`（`--mode rss` / `--mode static` / **`--mode dynamic`**）
- `run-now` 若含静态/动态源，请在 Django 解释器环境中安装与 `fact_backend/requirements.txt` 一致的依赖（含 **Scrapy**；动态源另需 **`scrapy-playwright`**、**`playwright`** 并执行 **`python -m playwright install chromium`**）
- 若出现历史乱码/测试数据，可在开发环境清理：
  - `python manage.py reset_demo_data --yes`（可选 `--reset-sequences` 见下文）
  - `python manage.py seed_crawler_sources`

## 1. 接口总览表

| 模块 | 接口 | 方法 | 功能 | 状态 |
|---|---|---:|---|---|
| users | `/api/users/status/` | GET | users 模块探活 | 已完成（MVP） |
| opinions | `/api/opinions/` | GET | 舆情列表 | 已完成（MVP） |
| opinions | `/api/opinions/` | POST | 新增舆情 | 已完成（MVP） |
| opinions | `/api/opinions/{id}/` | GET | 舆情详情 | 已完成（MVP） |
| opinions | `/api/opinions/{id}/analyze/` | POST | 触发分析并生成预警（最小闭环） | 已完成（MVP） |
| analysis | `/api/analysis/` | GET | 分析结果列表（含 `opinion_title`） | 已完成（MVP） |
| analysis | `/api/analysis/{id}/` | GET | 分析结果详情（含 `opinion_title`） | 已完成（MVP） |
| warnings | `/api/warnings/` | GET | 预警列表（含 `opinion_title`） | 已完成（MVP） |
| warnings | `/api/warnings/{id}/` | GET | 预警详情（含 `opinion_title`） | 已完成（MVP） |
| governance | `/api/governance/` | GET | 治理记录列表 | MVP（只读） |
| governance | `/api/governance/{id}/` | GET | 治理记录详情 | MVP（只读） |
| crawler_tasks | `/api/crawler-tasks/` | GET | 爬虫任务列表 | MVP（只读，不接入真实爬虫） |
| crawler_tasks | `/api/crawler-tasks/{id}/` | GET | 爬虫任务详情 | MVP（只读） |
| crawler_control | `/api/crawler/sources/` | GET/POST | 采集源管理（含 `source_code` 稳定键） | v1.4.1 |
| crawler_control | `/api/crawler/topics/` | GET/POST | 监控主题管理 | v1.3.0 |
| crawler_control | `/api/crawler/tasks/` | GET/POST | 任务管理（monitor/search） | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/` | GET | 任务详情 | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/start/` | POST | 启动任务（状态变更） | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/pause/` | POST | 暂停任务（状态变更） | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/resume/` | POST | 恢复任务（状态变更） | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/stop/` | POST | 停止任务（状态变更） | v1.3.0 |
| crawler_control | `/api/crawler/tasks/{id}/run-now/` | POST | 立即执行一次（同步 RSS + 静态 Scrapy + 动态 Playwright） | v1.5.0 |
| crawler_control | `/api/crawler/tasks/{id}/runs/` | GET | 查看任务运行历史 | v1.3.0 |
| crawler_control | `/api/crawler/runs/{id}/items/` | GET | 查看某次运行的明细条目 | v1.3.0 |
| model_versions | `/api/model-versions/` | GET | 模型版本列表 | MVP（只读） |
| model_versions | `/api/model-versions/{id}/` | GET | 模型版本详情 | MVP（只读） |
| dashboard | `/api/dashboard/summary/` | GET | 数据大屏统计摘要 | 已完成（MVP） |

## 2. users

### 2.1 GET `/api/users/status/`

- **功能**：确认 users app 已启用（探活/信息）
- **请求参数**：无
- **响应字段**
  - `status`：固定 `ok`
  - `app`：固定 `users`
- **示例请求**

```bash
curl http://127.0.0.1:8000/api/users/status/
```

- **示例响应**

```json
{ "status": "ok", "app": "users" }
```

- **状态**：已完成（MVP）

## 3. opinions（舆情数据）

### 3.1 GET `/api/opinions/`

- **功能**：舆情列表（按创建时间倒序）
- **请求参数**：无（后续扩展：分页/筛选）
- **响应字段**：`OpinionData` 列表，字段见 3.3
- **状态**：已完成（MVP）

### 3.2 POST `/api/opinions/`

- **功能**：新增一条舆情
- **请求体字段**
  - `title`（必填）：舆情标题
  - `content`（必填）：舆情正文
  - `source`：来源平台（可空）
  - `source_url`：原文链接（可空）
  - `publish_time`：发布时间（可空，ISO8601）
  - `crawl_time`：采集时间（可空，ISO8601）
  - `category`：主题类别（可空）
  - `raw_label`：原始标签（可空）
  - `keywords`：舆情关键词（可空，JSON 数组；表示人工/自动提取的入库关键词）
  - `status`：处理状态（可选；默认 `new`）
- **示例请求（PowerShell 推荐）**

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/opinions/" -ContentType "application/json" -Body (@{
  title="测试舆情"
  content="网传某地发生严重事故，引发大量关注。"
  source="test"
  category="test"
} | ConvertTo-Json)
```

- **示例响应**：201，返回创建后的 `OpinionData`
- **状态**：已完成（MVP）

### 3.3 GET `/api/opinions/{id}/`

- **功能**：舆情详情
- **路径参数**
  - `id`：舆情 ID
- **响应字段（OpinionData）**
  - `id`
  - `title`
  - `content`
  - `source`
  - `source_url`
  - `publish_time`
  - `crawl_time`
  - `category`
  - `raw_label`
  - `keywords`：舆情关键词数组（入库关键词，**不等同于**模型分析结果关键词）
  - `status`：`new / analyzed / warned / closed`
  - `created_at`
  - `updated_at`
- **状态**：已完成（MVP）

## 4. 最小业务闭环：analyze

### 4.1 POST `/api/opinions/{id}/analyze/`

- **功能**：对指定舆情触发模型分析，将结果保存为 `AnalysisResult` 并生成 `RiskWarning`，同时更新 `OpinionData.status`。
- **路径参数**
  - `id`：舆情 ID
- **请求体**：无（可传 `{}`）
- **响应结构**
  - `opinion`：舆情对象（同 3.3）
  - `analysis_result`：分析结果对象（见 5.1）
  - `risk_warning`：风险预警对象（见 6.1）
  - `note`：当走幂等分支/补偿分支时返回说明（可选）

#### 4.1.1 业务流程（MVP）

1. 通过 `id` 查询 `OpinionData`（不存在返回 404）
2. 读取 `OpinionData.content` 作为输入文本（为空返回 400）
3. 调用模型推理服务客户端：`services/model_client.py -> predict_full(text)`
   - 目标接口：`http://127.0.0.1:8001/predict/full`
4. 将返回的字段写入 `AnalysisResult`：
   - `rumor_label`、`rumor_probability`、`sentiment_label`、`sentiment_probability`、`keywords`、`model_name`
5. 计算 `risk_score` 并生成 `RiskWarning`
6. 更新 `OpinionData.status`
7. 返回 `{ opinion, analysis_result, risk_warning }`

#### 4.1.2 幂等逻辑说明

为避免重复插入，接口具备幂等行为：

- 若该 `OpinionData` **已存在** `AnalysisResult` 且 **已存在** `RiskWarning`：
  - **不会**重复创建
  - 直接返回已有记录，并返回 `note="already analyzed; returned existing records"`
- 若该 `OpinionData` **已存在** `AnalysisResult` 但 **缺少** `RiskWarning`：
  - **不会**重复创建分析结果
  - 只补齐创建 `RiskWarning`，并返回 `note="analysis existed; created missing warning"`

> 后续扩展建议：可加入“强制重跑”参数（如 `?force=1`）或记录模型版本变更导致的重算策略，但 MVP 阶段不实现。

#### 4.1.3 风险评分与分级规则（MVP）

- **风险评分公式**

\[
risk\_score = \frac{rumor\_probability + sentiment\_probability}{2}
\]

- **风险等级**
  - `risk_score >= 0.75`：`high`
  - `0.45 <= risk_score < 0.75`：`medium`
  - `risk_score < 0.45`：`low`

- **OpinionData.status 更新**
  - 若 `risk_level` 为 `high` 或 `medium` → `warned`
  - 否则 → `analyzed`

#### 4.1.4 异常返回（MVP）

- `OpinionData` 不存在：**404**
- `content` 为空：**400**，`detail` 提示不可分析
- 模型服务不可用/调用失败：**503**，返回 `model_service_error`
- 模型响应字段解析失败：**502**，返回 `raw` 便于排查

#### 4.1.5 示例请求

```bash
curl -X POST "http://127.0.0.1:8000/api/opinions/1/analyze/" -H "Content-Type: application/json" -d "{}"
```

#### 4.1.6 示例响应（成功）

```json
{
  "opinion": { "id": 1, "title": "测试舆情", "content": "…", "status": "warned", "created_at": "…", "updated_at": "…" },
  "analysis_result": {
    "id": 1,
    "opinion": 1,
    "opinion_title": "测试舆情",
    "rumor_label": "rumor",
    "rumor_probability": 0.86,
    "sentiment_label": "negative",
    "sentiment_probability": 0.79,
    "keywords": ["事故", "网传", "关注"],
    "model_name": "mock-full-analysis-model",
    "analyzed_at": "…"
  },
  "risk_warning": {
    "id": 1,
    "opinion": 1,
    "opinion_title": "测试舆情",
    "analysis_result": 1,
    "risk_score": 0.825,
    "risk_level": "high",
    "warning_reason": "risk_score=0.83, rumor=0.86, sentiment=0.79",
    "status": "open",
    "created_at": "…"
  }
}
```

- **状态**：已完成（MVP）

## 5. analysis（分析结果）

### 5.1 GET `/api/analysis/` / GET `/api/analysis/{id}/`

- **功能**：查看分析结果（只读）
- **响应字段（AnalysisResult）**
  - `id`
  - `opinion`：舆情 ID
  - `opinion_title`：舆情标题（便于前端直接展示）
  - `rumor_label`
  - `rumor_probability`
  - `sentiment_label`
  - `sentiment_probability`
  - `keywords`：关键词数组（JSON）
  - `model_name`
  - `analyzed_at`
- **状态**：已完成（MVP）

## 6. warnings（风险预警）

### 6.1 GET `/api/warnings/` / GET `/api/warnings/{id}/`

- **功能**：查看风险预警（只读）
- **响应字段（RiskWarning）**
  - `id`
  - `opinion`：舆情 ID
  - `opinion_title`：舆情标题（便于前端直接展示）
  - `analysis_result`：分析结果 ID
  - `risk_score`：风险得分
  - `risk_level`：`low / medium / high`
  - `warning_reason`：预警原因（MVP 以风险评分摘要为主）
  - `status`：`open / processing / closed`
  - `created_at`
- **状态**：已完成（MVP）

## 7. dashboard

### 7.1 GET `/api/dashboard/summary/`

- **功能**：数据大屏统计摘要（MVP）
- **响应字段含义**
  - `total_opinions`：舆情总数（`OpinionData` 总记录数）
  - `analyzed_count`：分析结果总数（`AnalysisResult` 总记录数）
  - `warning_count`：预警总数（`RiskWarning` 总记录数）
  - `high_risk_count`：高风险预警数（`risk_level=high`）
  - `latest_opinions`：最近 5 条舆情（用于大屏列表）
    - `keywords`：舆情入库关键词（`OpinionData.keywords`）
    - `display_keywords`：统一展示关键词（推荐前端使用）
      - 生成规则：合并 `OpinionData.keywords` 与该舆情最新 `AnalysisResult.keywords`，去重、保持顺序，最多 8 个；都为空则为空数组
  - `latest_warnings`：最近 5 条预警（包含 `opinion_title`）
- **状态**：已完成（MVP）

## 9. crawler 控制中心（v1.4.0 补充）

### 9.0 采集源稳定标识 `source_code`（v1.4.1）

- **`CrawlerSource.id`**：数据库主键，自增；开发环境执行 `reset_demo_data` 后重新 `seed` 时 **id 可能变化**，**不建议在脚本或集成里写死**。
- **`CrawlerSource.source_code`**：`SlugField`，全表唯一、**稳定业务标识**；默认种子源固定为：
  - `chinanews_society_rss`、`china_daily_rss`、`gov_zhengce_static`、`local_static_demo`、`local_dynamic_demo`（动态演示默认 **enabled=false**）
- **列表/详情**：`GET/POST /api/crawler/sources/` 的 JSON 中均包含 `source_code`；**列表默认按 `id` 升序**（与种子写入顺序一致）；可按 **`GET /api/crawler/sources/?source_code=local_static_demo`** 精确定位一条源。
- **`local_static_demo`** 种子默认 **`robots_required=false`**（本地 `http.server` 演示）。
- **后续扩展（v1.6.0 规划）**：平台站内/垂直搜索类源将使用 `source_code` 命名（如 `tieba_search`、`bilibili_search`、`weibo_search`、`xiaohongshu_search`）；**v1.5.0 不实现**对应采集器与登录/反爬逻辑。

### 9.1 `POST /api/crawler/tasks/{id}/run-now/` 支持的源

- **RSS**：`source_type=rss` 且 `adapter_name=rss_feedparser`（与 v1.3.0 相同）。
- **静态列表+详情**：`source_type=static` 且 `adapter_name=scrapy_static`；适配器见 `fact_crawler/crawler/scrapy_static_adapter.py`，本地演示见 `fact_crawler/static_demo/README.txt`。
- **动态单页（Playwright）**：`source_type=dynamic` 且 `adapter_name=scrapy_playwright_dynamic`；适配器见 `fact_crawler/crawler/scrapy_playwright_dynamic_adapter.py`，本地演示见 `fact_crawler/dynamic_demo/README.txt`（需 `python -m playwright install chromium` 与本地 `http.server`）。
- 任务可绑定多源；`run-now` 会依次执行所有已启用的 **RSS、static、dynamic** 源，共用同一 `CrawlerRun` 与去重/入库逻辑。

### 9.2 dry_run

- 请求体 JSON：`{"dry_run": true}` 时仍会写入 `CrawlerRun` / `CrawledItem`，但不创建 `OpinionData`，也不会触发 `auto_analyze`。

### 9.3 静态 / 动态采集实现说明（Twisted reactor + 子进程）

- **`scrapy_static`** 与 **`scrapy_playwright_dynamic`** 默认均在**子进程**中跑 Scrapy（动态源另启 Playwright Chromium），避免与 Django `runserver` 同进程内 Twisted / asyncio 冲突（否则可能出现 `ReactorAlreadyRunning` / `ReactorNotRestartable`，且 `str(异常)` 为空导致接口 `error` 字段为空）。
- 调试如需在同进程跑爬虫，可设环境变量 **`FACT_SCRAPY_STATIC_INPROCESS=1`** 或 **`FACT_SCRAPY_PLAYWRIGHT_INPROCESS=1`**（不推荐在生产使用）。
- 动态子进程默认超时（秒）可由环境变量 **`FACT_SCRAPY_PLAYWRIGHT_SUBPROCESS_TIMEOUT`** 覆盖（默认 `480`）。

### 9.4 开发清库与自增主键（`reset_demo_data --reset-sequences`）

- **仅开发环境**：`python manage.py reset_demo_data --yes --reset-sequences`
  - **SQLite**：在删除演示数据后，额外清理 `sqlite_sequence` 中与本次删除相关的表项，使下次插入时主键从 1 起跳。
  - **PostgreSQL / MySQL**：命令会打印说明，需自行用 `sqlsequencereset` / `ALTER SEQUENCE` / `ALTER TABLE ... AUTO_INCREMENT` 处理；生产部署**不依赖**自增 id，请用 **`source_code`** 引用采集源。

## 说明：两类关键词的区别（重要）

- **`OpinionData.keywords`**：舆情入库阶段的关键词（人工/前端自动提取/后续爬虫清洗）
- **`AnalysisResult.keywords`**：模型分析阶段返回的关键词（推理结果）
- **`display_keywords`**：为解决“旧数据入库关键词为空但模型关键词存在”的展示不一致问题，dashboard 提供的**统一展示字段**（前端大屏优先使用）。

## 8. 其它只读模块（MVP 占位）

以下模块当前仅提供只读列表/详情接口，用于占位与后续论文描述：

- `GET /api/governance/`、`GET /api/governance/{id}/`
- `GET /api/crawler-tasks/`、`GET /api/crawler-tasks/{id}/`
- `GET /api/model-versions/`、`GET /api/model-versions/{id}/`

状态：MVP（只读）/ 后续扩展。

