# FACT 开发日志（Development Log）

本文档用于记录 FACT（网络舆情风险预警与谣言治理系统）的阶段目标、关键决策、已完成事项与下一步计划，便于论文撰写与阶段验收。

**与 README 的分工**：对外的**版本能力总览与推荐阅读顺序**以根目录 **`README.md` 中按 v1.0.0 → v1.4.x 编排的小节**为准；**`docs/README.md`** 为文档索引入口。本文件侧重开发过程、排障与决策细节。

## 2026-04-24

### 阶段 1：工程骨架与项目规范（已完成）

- **目标**：建立单仓多模块的最小工程结构与开发规范，不引入复杂业务代码。
- **已完成**
  - **仓库结构**：创建 `fact_backend/`、`fact_model_service/`、`fact_frontend/`、`fact_crawler/`、`datasets/`、`experiments/`、`docs/` 等目录
  - **规范文件**：创建 `.cursor/rules/fact-project.mdc`，明确模块职责边界与 MVP 原则
  - **说明文件**：完善根 `README.md` 与各子模块 `README.md`
  - **忽略规则**：创建 `.gitignore`（过滤虚拟环境、构建产物、数据缓存、模型权重等）

### 阶段 2：`fact_model_service`（FastAPI 推理服务）最小可运行版本（已完成并通过测试）

- **目标**：不加载真实模型，用 mock 规则稳定输出固定 JSON，供后续 Django 调用。
- **实现要点**
  - **FastAPI**：提供健康检查与 3 组推理接口（谣言、情感、综合）
  - **Pydantic**：请求/响应体结构化定义，确保字段稳定
  - **mock 规则**：关键词命中→概率→风险等级（`low/medium/high`）
- **接口**
  - `GET /health`
  - `POST /predict/rumor`
  - `POST /predict/sentiment`
  - `POST /predict/full`
- **状态**
  - `/health` 与 `/predict/full` 已在本地测试可正常返回

### 阶段 3：`fact_backend`（Django + DRF 业务后台）最小可运行版本（进行中）

- **目标**：搭建 Django + DRF 可启动工程，SQLite 可迁移，提供基础只读 API，并预留模型服务调用能力。
- **已完成**
  - **项目骨架**：`manage.py`、`config/`（settings/urls/api_urls/views/asgi/wsgi）
  - **依赖清单**：`fact_backend/requirements.txt`（Django、DRF、requests）
  - **服务占位**：`services/model_client.py`（预留调用 `http://127.0.0.1:8001/predict/full`，失败降级不阻塞）
  - **opinions app**
    - `OpinionData` 模型
    - API：`GET/POST /api/opinions/`、`GET /api/opinions/{id}/`
  - **analysis/warnings/governance/crawler_tasks/model_versions app**
    - 模型、序列化、只读 ViewSet、路由注册（列表/详情）
  - **dashboard**
    - `GET /api/dashboard/summary/`：返回总数、已分析/预警/高风险统计，以及最近舆情/预警列表
- **下一步（建议）**
  - 完成 `users` app 的最小骨架（不做复杂认证）
  - 执行迁移并跑通所有 `/api/*` 路由的连通性测试
  - 在后续阶段补充“舆情 → 调用模型服务 → 写入 analysis → 生成 warning”的最小业务链路

## 约定（持续更新）

- 对外**版本能力总览**以根目录 **`README.md`（v1.0.0 → v1.4.x 按序编排）** 为准；本日志补充过程、排障与论文级决策。
- 每次迭代至少记录：
  - 本阶段目标
  - 新增/修改的核心模块
  - 新增 API 或数据结构变化
  - 关键决策与原因（便于论文描述）

## 2026-04-25 Django 后端基础接口测试通过

### 一、开发阶段

本阶段完成 FACT 后端基础接口的启动与测试，验证 Django + DRF 后端服务、SQLite 数据库迁移、舆情数据新增接口和 dashboard 汇总接口是否能够正常运行。

### 二、完成内容

1. 执行 `python manage.py check`，系统检查通过。
2. 执行 `python manage.py makemigrations`，成功生成各 app 的初始迁移文件。
3. 执行 `python manage.py migrate`，成功创建数据库表。
4. 启动 Django 后端服务，运行地址为 `http://127.0.0.1:8000/`。
5. 通过 `POST /api/opinions/` 新增一条舆情测试数据。
6. 通过 `GET /api/opinions/1/` 成功查询新增数据。
7. 通过 `GET /api/dashboard/summary/` 验证统计结果更新，`total_opinions` 从 0 变为 1。

### 三、测试结果

后端服务启动正常，舆情数据成功写入数据库。`GET /api/opinions/1/` 返回状态码 200，能够正确显示标题、正文、来源、类别和状态等字段。`GET /api/dashboard/summary/` 返回状态码 200，统计字段 `total_opinions` 正确更新为 1。

### 四、遇到问题

- 使用 PowerShell 的 `curl.exe` 直接传递 JSON 时出现 JSON 解析错误，接口返回 400。
- 后续改用 `Invoke-RestMethod` 构造请求体后，接口成功写入数据。
- PowerShell 输出中文存在乱码，但浏览器接口返回中文正常，说明数据本身未乱码。

### 五、阶段总结

本阶段验证了 FACT 后端基础 API 与数据库存储能力，说明 Django 后端已经具备舆情数据录入、查询和统计展示的基本能力，为下一步打通“舆情数据 → 模型服务 → 分析结果 → 风险预警”的业务闭环奠定了基础。

### 六、下一步计划

下一步将实现 `POST /api/opinions/{id}/analyze/` 接口，由 Django 后端根据舆情数据调用 FastAPI 模型推理服务，保存分析结果并生成风险预警记录。


## 2026-04-25 后端最小业务闭环测试通过

本阶段完成 FACT 后端核心链路测试。系统已支持舆情数据录入、模型分析触发、分析结果保存、风险预警生成和 dashboard 汇总统计。测试结果显示，`/api/opinions/1/analyze/` 能够成功调用 FastAPI 模型服务，并将返回结果保存至 `AnalysisResult`，同时根据风险评分生成 `RiskWarning`。`/api/dashboard/summary/` 中 `analyzed_count`、`warning_count` 和 `high_risk_count` 均能正确更新，说明后端最小业务闭环已经打通。

测试过程中发现，使用 PowerShell 直接提交中文 JSON 可能导致中文乱码。后续中文测试数据将优先通过 DRF Browsable API 或 UTF-8 JSON 文件方式提交，以避免编码问题。

同时已在 `docs/backend-api.md` 整理并固化当前后端 MVP API 文档，包括接口总览、字段说明、示例请求/响应，以及 `POST /api/opinions/{id}/analyze/` 的业务流程与幂等逻辑说明，便于前端对接与论文撰写引用。

## 2026-04-25 舆情关键词字段与前端展示优化

本阶段为舆情数据入库补充 `OpinionData.keywords` 字段（JSON 数组），用于记录人工/前端自动提取的舆情关键词，与模型分析结果 `AnalysisResult.keywords` 区分开来。同时前端优化舆情录入表单：完善原始标签（raw_label）中文含义与提示说明，新增关键词手动输入与一键自动提取，并在 Dashboard/舆情列表/详情中以标签形式展示关键词与状态中文标签，提升演示可读性。

## 2026-04-25 关键词展示统一与历史数据同步

为解决 Dashboard（读 `OpinionData.keywords`）与 Analysis（读 `AnalysisResult.keywords`）在旧数据场景下展示不一致的问题，本阶段对 dashboard `latest_opinions` 增加 `display_keywords` 字段：合并入库关键词与最新分析关键词用于统一展示；同时在 `POST /api/opinions/{id}/analyze/` 中支持将分析关键词回写到空的 `OpinionData.keywords`，并提供管理命令 `python manage.py sync_opinion_keywords` 用于一次性补齐历史数据。

## 2026-04-25 FACT v1.0.0 手动录入型 MVP 完成

FACT 手动录入型 MVP 已完成并通过联调测试：前端可录入舆情、提取/编辑关键词、触发分析并查看分析结果与风险预警；后端可落库并提供 dashboard 汇总统计；模型服务以 mock 推理稳定输出固定 JSON 结构。已在 `docs/releases/v1.0.0.md` 固化本版本功能清单、限制与下一步计划。

## 2026-04-30 FACT v1.1.0 第一阶段 mock 爬虫技术选型实验完成

本阶段目标：在本地 `mock_sources/` 上进行受控对比实验，形成“按场景唯一选型 + 淘汰原因”的论文级结论。

- 场景与结论：
  - static_news → **Scrapy**
  - rss_api → **Requests + feedparser**
  - dynamic_page → **Scrapy + Playwright**
- 产出：
  - `results/crawler_selection_result.csv|json`
  - `results/selection_conclusion.md`
  - `results/figures/*.png`（论文插图）

## 2026-05-01 FACT v1.2.0 第二阶段国内真实公开源验证完成

本阶段目标：对第一阶段选型进行国内公开源小规模验证，强调合规与可诊断性，不追求大规模采集。

- 合规策略：robots 明确禁止则 skipped；robots 不可确认则 robots_unknown，不强采集、不绕过 SSL/验证码/反爬。
- 推荐验证源：
  - static_news：`china_gov_policy_static`
  - rss_api：`china_daily_china_rss`（主）+ `chinanews_society_rss`（备用）
  - dynamic_page：`nbs_data_dynamic`（国家统计局国家数据平台，JavaScript 渲染）
- 产出（stage2 统一目录）：
  - `results/stage2_real_world/real_validation_result.csv|json`（汇总）
  - `results/stage2_real_world/real_validation_items.csv|json`（抽取明细）

## 2026-05-01 FACT v1.3.0 爬虫任务控制中心（已完成）

本阶段目标：将 v1.1/v1.2 实验结论落地到系统工程中，优先打通 **RSS 自动采集入库闭环**，并建立可扩展的多适配器爬虫框架。

- 后端新增：`/api/crawler/*` 任务控制中心（sources/topics/tasks/runs/items + start/pause/resume/stop/run-now）
- 数据模型：CrawlerSource / TopicProfile / CrawlerTask / CrawlerRun / CrawledItem
- fact_crawler：Adapter 接口 + runner；RSS（Requests + feedparser）adapter 真实实现；static 由 **v1.4.0+ `scrapy_static`** 落地，dynamic 仍预留 **v1.5.0**
- run-now：同步执行 RSS（及后续并入的 static 源），写入 OpinionData，并可选触发 analyze 生成 Analysis/Warnings/Dashboard 可见数据

### Windows 中文测试备注

- PowerShell 直接发送中文 JSON 可能导致入库字段乱码（如 task_name/keywords/source.name）。
- 建议使用 Python requests 脚本测试中文：`scripts/test_create_chinese_crawler_task.py`
- `--no-keyword-filter`：用于验证中文采集闭环（不做关键词过滤，直接采集前 N 条）
- `--keyword`：用于验证主动搜索过滤能力（关键词命中才入库）
- 若历史测试数据已产生乱码，可先清理再 seed：
  - `python manage.py reset_demo_data --yes`
  - `python manage.py seed_crawler_sources`

## 2026-05-04 v1.4.0 static_demo 中文编码修复

- **根因**：`http.server` 返回的 `text/html` 常无 `charset`，Scrapy 将正文按 **latin-1** 解码，UTF-8 中文入库后表现为 `ï¿½`、`Ä³` 等；PowerShell 展示 API 时还会叠加终端编码问题。
- **处理**：`static_demo` 三页统一 **UTF-8** 与 `<meta charset="UTF-8">`；蜘蛛在 `parse_list`/`parse_detail` 记录 `encoding`/`Content-Type`/URL，对本机地址 **强制 `response.replace(encoding="utf-8")`**；`normalizer.looks_like_mojibake` + 适配器跳过疑似乱码条；详情页增加 `article-source`、`meta keywords` 供 `source`/关键词合并。
- **验证**：`scripts/test_create_chinese_crawler_task.py` 在 `total_inserted>0` 时自动拉取 `runs/{id}/items` 并打印前 2 条摘要，检测乱码则 `[WARN] mojibake detected`。
- **清库**：`reset_demo_data --yes` 会删除含 `CrawlerSource`/`OpinionData`/`CrawledItem` 等演示数据，需重新 `seed_crawler_sources`。

### 补充（子进程 + 本机 Selector）

- `response.replace(encoding=utf-8)` 仍走 Scrapy 文本层，无法根治 **无 charset 时 latin-1 误读**；本机改为 **`response.body.decode("utf-8", strict")` + `parsel.Selector(text=html)`**，列表/详情抽取一律 `sel.css` / `sel.xpath`，不再用 `response.css`。
- 子进程 **stdout 仅输出一行 `json.dumps(..., ensure_ascii=True)`**，避免 Windows 管道 GBK；父进程设 `PYTHONIOENCODING=utf-8`、`PYTHONUTF8=1`，stdin 配置同用 `ensure_ascii=True`。

### gov.cn `/zhengce/`（v1.4.0 起；列表/详情行为以 README v1.4.2 / v1.4.3 为准）

- **v1.4.0**：列表诊断 **`[gov.cn zhengce list diagnostics]`**、链接规则初版、stderr 回显。
- **v1.4.2**：raw 正则 href、假 `</html>` unwrap、无效链过滤、正文仅容器 + 污染 skip；诊断增加 selector/regex 计数。
- **v1.4.3**：详情 **full_sel / content_sel** 拆标题与正文；`Request.meta["link_text"]`；`reason=title_empty|body_too_short|polluted:*` 与 **`title_empty_debug`**。

## 2026-05-05 v1.4.1 `CrawlerSource.source_code`

- **模型**：`source_code = SlugField(max_length=100, unique=True)`，与自增 `id` 分离；清库重 seed 后 **id 会变，`source_code` 不变**。
- **默认种子**（`seed_crawler_sources`）：`chinanews_society_rss`、`china_daily_rss`、`gov_zhengce_static`、`local_static_demo`；**以 `source_code` 为 upsert 键**，不再用 `base_url`/name 识别。
- **API**：`CrawlerSourceSerializer` 暴露 `source_code`；列表 **`GET /api/crawler/sources/`** 按 **`id` 升序**（避免按 `source_code` 字母序打乱业务顺序）；`?source_code=...` 可筛选。
- **`local_static_demo`**：`robots_required=False`（本地演示源）。

## 2026-05-05 v1.4.2 gov.cn `/zhengce/` 静态增强（仅 spider）

- **列表**：`response.body.decode("utf-8", errors="replace")` 上正则抽取全部 `href`，与 CSS 结果合并去重；假 `</html>` 后仍有正文时截断前缀再 `Selector`；`urljoin` + 扩展无效链（english/big5/mail/login/js/css/pdf/zip 等）过滤。
- **详情**：正文仅从 `#UCAP-CONTENT` / `.pages_content` / `.article-content` 抽文本；污染启发式检测失败则 `[gov.cn zhengce detail skip] polluted=...`；诊断日志保留并增加 `selector_a_href_count` / `regex_href_raw_count`。

## 2026-05-05 v1.4.3 gov.cn 详情标题与 `link_text`

- **根因**：详情曾用「正文容器切片」后的 HTML 建唯一 `Selector`，`<title>`/head 内 meta 丢失 → `title` 空、`body` 仍长。
- **修复**：`_gov_detail_full_and_content_selectors`：`full_sel` = unwrap 后全文；`content_sel` = 从 UCAP/pages_content/article-content 起切片；`_extract_gov` 标题走 **content h1 → full h1 → … → meta → `response.meta["link_text"]`**，并 `_gov_clean_title` 去掉 `_中国政府网` 等后缀；正文仍只从 `content_sel` 三容器抽取。
- **列表**：`_links_gov_policy` 返回 `(url, anchor_text)`，合并去重后 `Request(..., meta={"link_text": ...})`；正则 href 无锚文本则空串。
- **skip 日志**：`reason='title_empty'|'body_too_short'|'polluted:xxx'`；标题空时 **`[gov.cn zhengce detail title_empty_debug]`** 输出候选与 `body_sample`。
- **adapter**：gov+zhengce 子进程结果若存在无 `title` 条，stderr 提示对照上述日志。

