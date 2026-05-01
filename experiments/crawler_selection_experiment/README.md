# 自动化舆情采集技术对比与选型实验（FACT）

本实验用于在 FACT 系统中**按采集场景**对比不同爬虫/采集技术，并在每类典型场景中选出**唯一最适合**的技术方案，其余方案给出明确淘汰原因。

> 约束：仅使用本地 `mock_sources/`，不访问外部真实网站；不涉及登录/验证码/反爬绕过；不采集隐私数据。

## 场景与候选技术

- **场景 A：静态新闻/公告网页**
  - Requests + BeautifulSoup
  - aiohttp + BeautifulSoup
  - Scrapy
  - 预期结论：**Scrapy 胜出**

- **场景 B：RSS/API 结构化信息源**
  - Requests
  - Requests + feedparser
  - Scrapy
  - 预期结论：**Requests + feedparser 胜出**

- **场景 C：动态渲染页面（正式主实验）**
  - Requests + XHR/API replay（直接复现/读取 `dynamic_payload.json`）
  - Scrapy + Playwright（工程化调度 + 渲染）
  - Playwright（浏览器自动化直采）
  - 预实验负例（不纳入正式排名）：普通 Requests + BeautifulSoup、普通 Scrapy（不执行 JS，壳页解析失败）
  - 预期结论：**Scrapy + Playwright** 作为系统级动态主方案（由 `final_score` 与 rubric 共同体现；纯 Playwright 兜底、XHR 复现为轻量优化路径）

## 如何运行

在仓库根目录执行：

```bash
python experiments/crawler_selection_experiment/generate_mock_samples.py --per-scenario 1000 --noise-ratio 0.15 --seed 20260425

python experiments/crawler_selection_experiment/check_mock_sample_quality.py

python experiments/crawler_selection_experiment/run_experiment.py --repeat 3

python experiments/crawler_selection_experiment/generate_figures.py
```

## 输出文件

运行后会生成：

- `results/crawler_selection_result.csv`
- `results/crawler_selection_result.json`
- `results/selection_conclusion.md`
- `results/figures/*.png`（论文插图，需运行 `generate_figures.py`）

## 第一阶段（正式大样本）mock 数据生成

第一阶段正式实验建议使用**每场景 1000 条有效样本 + 15% 异常样本**（总计约 3450 条）：

```bash
python experiments/crawler_selection_experiment/generate_mock_samples.py --per-scenario 1000 --noise-ratio 0.15 --seed 20260425
```

说明：

- 固定 seed 保证可复现
- 文本采用“主题词库 + 模板句”生成，不使用随机 Unicode 汉字
- **每次运行生成脚本会先清理对应 `mock_sources/` 子目录下的旧 HTML/XML/JSON**，避免缩小样本量或改版后旧文件残留导致统计与解析实验失真
- 静态详情页按五类接近真实站点结构轮换生成：新闻门户、政务通报、论坛帖子、校园公告、本地生活流；正文约 **300～600 字**、多段落
- RSS `description` 为 **150～300 字摘要**，全文在 `content:encoded`；`sample_api.json` 含 `summary`、`engagement_count`、`risk_hint` 等字段便于 API 场景对齐
- 动态页 `dynamic_sample.html` 为骨架屏 + 脚本延迟拉取 `dynamic_payload.json` 再渲染卡片；正式主实验对比 **XHR/API 复现**、**Scrapy+Playwright** 与 **Playwright** 三种可行动态路径（均从 payload 取得与渲染后等价的数据）；普通 Requests+BS4 与普通 Scrapy 仅作文档中的预实验负例
- 噪声样本用于模拟缺字段、重复 link、时间格式差异、HTML 结构缺失等真实噪声（但不生成乱码）

## 样本质量检查（强烈建议）

生成大样本后，先跑质量检查，避免出现乱码字符 `�`、生僻字堆砌或无意义连续字符：

```bash
python experiments/crawler_selection_experiment/check_mock_sample_quality.py
```

输出：

- `results/mock_sample_quality_report.md`
- `results/mock_sample_quality_report.json`

## 第一阶段重复运行

为降低偶然波动，支持对每个场景每种技术重复运行 N 次（默认 1 次）：

```bash
python experiments/crawler_selection_experiment/run_experiment.py --repeat 3
```

以及论文实验报告模板：

- `report.md`

## 第二阶段：少量公开源真实验证（框架）

第一阶段是受控实验；第二阶段用于验证结论在真实环境的适用性（但不追求大规模采集）。

### 1) 准备真实验证配置

- 复制模板为本地配置（默认不提供，避免误触发外网访问）：

```bash
cp experiments/crawler_selection_experiment/real_world_validation/validation_sources.example.json \
   experiments/crawler_selection_experiment/real_world_validation/validation_sources.local.json
```

- 编辑 `validation_sources.local.json`：
  - 填写公开可访问 URL
  - 将要验证的数据源 `enabled` 设为 `true`

### 2) 运行真实验证

```bash
python experiments/crawler_selection_experiment/real_world_validation/run_real_validation.py
```

输出：

- `results/stage2_real_world/real_validation_result.csv`
- `results/stage2_real_world/real_validation_result.json`

### 3) 合规要求（必须遵守）

- 遵守 `robots.txt`：明确不允许则 skipped；无法确认则 `robots_unknown`，不强行采集
- 请求间隔 1~3 秒
- 不做登录、验证码、反爬绕过
- 不采集个人隐私数据

### 4) 第二阶段最小真实验证（国内公开源 MVP）

本阶段仅用于验证第一阶段选型在国内公开源的**可落地性**（合规/可访问/字段抽取），不做大规模采集，不作为训练数据来源。

当前推荐验证源（国内公开源）：

- **static_news**：`china_gov_policy_static`
- **rss_api**：`china_daily_china_rss`、`chinanews_society_rss`
- **dynamic_page**：`nbs_data_dynamic`（国家统计局国家数据平台，JavaScript 渲染页面，适合作为 Scrapy + Playwright 的动态页面 MVP 验证源）

1. 复制配置文件（默认不提供本地配置，避免误触发外网访问）：

PowerShell:

```powershell
Copy-Item experiments\crawler_selection_experiment\real_world_validation\validation_sources.local.json.example `
  experiments\crawler_selection_experiment\real_world_validation\validation_sources.local.json
```

2. 安装第二阶段依赖（一次即可）：

```bash
python -m pip install -r experiments/crawler_selection_experiment/requirements.txt
python -m playwright install chromium
```

3. 编辑 `validation_sources.local.json`：把 3 个源的 `enabled` 改为 `true`（其余保持默认）。

4. 运行：

```bash
python experiments/crawler_selection_experiment/real_world_validation/run_real_validation.py
```

5. 查看结果：

- `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.csv`

运行策略补充：

- 若 `china_daily_china_rss` 解析失败，可改为启用 `chinanews_society_rss` 作为**备用 RSS 验证源**（不要默认启用）。
- `robots_unknown` **不代表采集技术失败**：表示 robots.txt 获取/解析失败导致无法确认许可；按合规策略不执行正式采集，结果应在论文中解释为“合规检查不确定”，而非技术能力不足。
- 第二阶段真实验证以“**可诊断、可解释**”为目标：不会强行绕过 robots、SSL 异常、验证码或反爬。

## 说明

本实验为“**技术选型实验**”，重心是：

- 同一场景内多方案对比
- 指标量化评分（含资源消耗惩罚）
- 形成“**唯一选型 + 其余淘汰原因**”的结论

## 生成论文用图表（可视化）

在仓库根目录执行：

```bash
python experiments/crawler_selection_experiment/generate_figures.py
```

输出目录：

- `experiments/crawler_selection_experiment/results/figures/`

图表说明：

- `final_score_by_scenario.png`：每个场景内候选技术 final_score 对比，并突出 selected=true
- `static_news_radar.png` / `rss_api_radar.png` / `dynamic_page_radar.png`：分场景雷达图对比核心指标，突出最终选型
- `selection_heatmap.png`：唯一选型热力图（scenario × method，selected=1/0）
- `valid_failed_count_by_scenario.png`、`field_completeness_by_method.png`、`throughput_by_method.png`：有效/失败计数、字段完整率、吞吐（线性轴）
- `score_delta_from_best.png`：各场景相对最优 `final_score` 的差值（selected 为 0），便于论文展示差距
- `throughput_by_method_log.png`、`latency_by_method_log.png`：吞吐与平均延迟的 **log 轴**图（仅可视化；`throughput=0` 或 `avg_latency=0` 在绘图时用极小 epsilon，**不修改 CSV 原始值**）

