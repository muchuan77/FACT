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
- `fact_frontend/`：Vue3 前端工程（**MVP 已联调**：Dashboard、舆情录入/分析/列表等，见 `fact_frontend/README.md`）。
- `fact_crawler/`：采集模块（**RSS + `scrapy_static` 已接入** `run-now`，见 `fact_crawler/README.md`）。
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

## 当前状态（概览）

项目已迭代至 **v1.4.x**（爬虫控制中心、RSS、`scrapy_static`、gov.cn `/zhengce/` 列表/详情增强、`source_code` 稳定源标识等）。**按版本的交付范围与能力边界**见下文各节；**v1.0.0 发布级清单**见 `docs/releases/v1.0.0.md`。更细的决策与排障过程见 `DEVLOG.md`。

## v1.0.0：手动录入型 MVP（首个可演示版本）

**定位**：不依赖外网自动采集，以前端录入 + 后端编排 + **mock 模型服务**打通「舆情 → 分析 → 预警 → 大屏」最小闭环，作为后续爬虫与真实模型的基线。

- **fact_backend（Django + DRF）**  
  SQLite 可迁移；舆情 `OpinionData` 的增删查改；`POST /api/opinions/{id}/analyze/` 调用模型服务并写入 `AnalysisResult`、生成 `RiskWarning`（**幂等**：重复分析不重复落库）；`GET /api/dashboard/summary/` 汇总统计；analysis / warnings / governance 等只读 API 占位。
- **fact_model_service（FastAPI）**  
  `GET /health`；`POST /predict/rumor`、`/predict/sentiment`、`/predict/full` 等 **mock 固定 JSON**，不加载真实权重。
- **fact_frontend（Vue3）**  
  舆情录入、关键词编辑/自动提取、触发分析、列表与 Dashboard 与后端联调展示。
- **文档**  
  `docs/releases/v1.0.0.md` 固化本版本功能、限制与后续方向。

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

## v1.3.0：爬虫任务控制中心 + RSS 自动采集闭环（已完成）

将 v1.1 / v1.2 实验结论落地到工程（不再在仓库内做 A/B 对比实验）：

- **选型延续**：static_news → Scrapy（**v1.4.0** 起 `scrapy_static` 适配器）；rss_api → Requests + feedparser；dynamic_page → Scrapy + Playwright（**v1.5.0** 规划）。
- **后端**：`/api/crawler/*` — sources / topics / tasks / runs / items，以及 start、pause、resume、stop、**`run-now`**（同步执行已绑定的 **RSS 与 static** 源，结果写入 `OpinionData`，可选 `auto_analyze`）。

## v1.4.0：静态页 Scrapy 采集（`scrapy_static` + static_demo + gov.cn 初版）

- **`scrapy_static`**：默认在**子进程**中跑 Scrapy，避免与 Django `runserver` 同进程 Twisted reactor 冲突。
- **本地 `python -m http.server`（`static_demo`）**：响应头常无 `charset`；对本机使用 **`response.body.decode("utf-8", strict")` + `parsel.Selector`**；子进程 stdout 单行 **`json.dumps(..., ensure_ascii=True)`**，配合 `PYTHONUTF8` 等，减轻 Windows 管道中文损坏。
- **gov.cn `/zhengce/`（初版）**：列表链规则（gov.cn + `/zhengce/` + `.htm/.html/.shtml`、排除 index/list 等）；**`[gov.cn zhengce list diagnostics]`** 等诊断输出到 stderr，adapter 对 gov 子进程 stderr 做回显。
- **演示**：`fact_crawler/static_demo/`（UTF-8 + `<meta charset="UTF-8">`）。清库后重种子：`cd fact_backend && python manage.py reset_demo_data --yes && python manage.py seed_crawler_sources`。

## v1.4.1：采集源 `source_code`（稳定业务键）

- `CrawlerSource` 增加 **`source_code`**（`SlugField`，唯一），种子源固定：`chinanews_society_rss`、`china_daily_rss`、`gov_zhengce_static`、`local_static_demo`。
- **`GET /api/crawler/sources/`** 默认按 **`id` 升序**（与上述种子写入顺序一致）；仍支持 **`?source_code=`** 筛选。
- **`local_static_demo`** 默认 **`robots_required=False`**（本地 `http.server` 演示，不做 robots 检查）。
- **`seed_crawler_sources`** 按 **`source_code` 幂等 upsert**（存在则更新字段，不存在则创建）；**勿在脚本里写死** 数据库自增 **`id`**（`reset_demo_data` 后 id 会变）。
- 联调推荐：`python scripts/test_create_chinese_crawler_task.py --mode static --source-code local_static_demo --no-keyword-filter`
- 开发可选：`python manage.py reset_demo_data --yes --reset-sequences`（**SQLite** 下重置相关表 `sqlite_sequence`；其他引擎见命令提示与 `docs/backend-api.md`）。

## v1.4.2：gov.cn `/zhengce/` 列表与正文抽取增强

- **列表**：在原始 HTML（`utf-8` + `errors="replace"`）上用**正则抽取全部 `href`**，与 CSS 结果合并去重；若页面中段出现假 **`</html>`** 导致 parsel 只见头部，则在检测到尾部仍有 `/zhengce`、`.htm` 等内容时**截断前缀**再解析。
- **链接**：`urljoin`、协议相对 `//` → `https:`；过滤 english / big5 / mail / login / `.js` `.css` `.pdf` `.zip` 等无效链。
- **详情正文**：仅从 **`#UCAP-CONTENT` / `.pages_content` / `.article-content`** 抽文本；启发式判定 **CSS/JS/导航污染** 则 **`reason=polluted:...`** 跳过不入库。
- **诊断**：列表日志增加 `selector_a_href_count`、`regex_href_raw_count` 等与合并 href 统计。

## v1.4.3：gov.cn 详情标题与 `link_text`

- **根因**：详情曾仅用「正文容器切片」后的 HTML 建唯一 `Selector`，**`<title>` / head 内 meta 丢失** → 正文很长但 **title 为空**。
- **做法**：**`full_sel`**（unwrap 后**全文**，抽标题、meta、时间、来源）与 **`content_sel`**（从正文容器起切片，**只抽正文**）分离；标题多级兜底（含 **`Request.meta["link_text"]`** 列表锚文本）；**`_gov_clean_title`** 去掉 `_中国政府网` 等站点后缀。
- **skip 语义**：`[gov.cn zhengce detail skip] reason='title_empty'|'body_too_short'|'polluted:...'`；标题仍空时打印 **`[gov.cn zhengce detail title_empty_debug]`**（各候选 + `body_sample`）。adapter 在 gov 子进程结果缺 `title` 时 stderr 一行提示对照上述日志。

## 文档入口

- **文档索引（推荐先读）**：`docs/README.md`
- 后端 API：`docs/backend-api.md`
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

