# 自动化舆情采集技术对比与选型实验报告（模板）

> 项目：FACT（网络舆情风险预警与谣言治理系统）  
> 实验主题：自动化舆情采集技术对比与选型  
> 数据源：本地 mock_sources（不访问外网）

## 1. 实验目的

为 FACT 系统后续“真实自采集数据”确定技术路线。本实验针对不同采集场景（静态网页、RSS/API、动态页面）分别对比 2~3 种候选采集技术，使用统一指标与评分模型量化评估，并在每个场景中选出**唯一最佳技术**，其余技术给出淘汰原因，形成可写入论文的选型结论。

## 2. 典型采集场景设计

- 场景 A：静态新闻/公告网页（列表页 + 详情页）
- 场景 B：RSS/API 结构化信息源（RSS feed）
- 场景 C：动态渲染页面（内容由 JS 渲染/内嵌数据）

### 2.1 动态页面：预实验负例与正式主实验设计

**动态页面预实验说明。** 普通 Requests + BeautifulSoup 与普通 Scrapy 无法执行 JavaScript，在「初始 HTML 不包含完整舆情数据、需由脚本拉取 `dynamic_payload.json` 再渲染」的页面中，只能读到骨架壳页，因而在初始实验中表现为 `parse_success_rate` 与 `field_completeness` 接近 0。该结论符合技术事实，但作为论文主实验的对比组过于极端。正式主实验因此**不再**将上述二者纳入动态场景的正式排名，仅在本文档中保留为预实验负例说明。

**动态页面正式实验设计。** 正式候选技术改为三类「至少具备动态内容处理能力」的方案，并在同一评分模型下对比：

1. **Requests + XHR/API replay**：模拟通过浏览器 Network 发现 XHR/API 后直接请求 JSON（本地 mock 为读取 `dynamic_payload.json`），代表轻量接口复现路径。
2. **Scrapy + Playwright**：模拟在 Scrapy 调度体系中接入 Playwright 渲染（本地 mock 仍从 `dynamic_payload.json` 取得与渲染后等价的数据），代表工程化动态采集路径。
3. **Playwright**：模拟浏览器自动化直采、等待渲染后抽取（本地 mock 同上），代表强动态兜底路径。

**动态页面最终选型逻辑。** 若综合得分表明 **Scrapy + Playwright** 胜出，则论文中应强调：它通常不是资源最省、也不是配置最简单的路径，但最契合 FACT 一类**长期、可编排**的舆情采集系统——需要任务调度、失败重试、去重、Pipeline 入库与规则沉淀；Scrapy + Playwright 同时保留 Scrapy 的工程化链路与 Playwright 的 JS 渲染能力。Requests + XHR/API replay 适合接口稳定、可维护复现的页面优化；纯 Playwright 适合复杂交互与强动态页面的兜底；普通 Requests + BS4 与普通 Scrapy 仅作预实验负例，不纳入正式动态主实验排名。

## 3. 候选技术说明

- Requests + BeautifulSoup：简单、轻量、适合规则明确的页面
- aiohttp + BeautifulSoup：异步并发，吞吐更好但工程复杂度更高
- Scrapy：工程化框架，适合大规模、多站点采集与可扩展 pipeline
- Requests：结构化 API/RSS 直接请求，集成成本低
- Requests + feedparser：专用于 RSS/Feed 的字段解析，稳定且维护性好
- Requests + XHR/API replay：在可定位接口时直接复现 JSON，吞吐高、资源低，但依赖接口发现与参数/token 维护
- Scrapy + Playwright：在 Scrapy 工程化链路中接入浏览器渲染，适合系统级长期动态采集
- Playwright：浏览器自动化直采，交互与渲染稳定性强，全量使用则资源与运维成本偏高

## 4. 评价指标与评分模型

### 4.1 指标

每个场景分别统计：

1. fetch_success_rate：采集请求成功率
2. parse_success_rate：字段解析成功率
3. field_completeness：字段完整率
4. valid_count：有效数据数量
5. failed_count：失败数量
6. duplicate_rate：重复率
7. avg_latency：平均耗时
8. throughput：单位时间采集量
9. resource_cost_score：资源消耗（越低越好）
10. maintainability_score：维护性
11. scalability_score：扩展性
12. integration_score：与 FACT 后端集成便利性
13. final_score：综合得分
14. selected：是否选用
15. eliminated_reason：淘汰原因

### 4.2 综合评分模型

\[
final\_score =
0.25 \cdot field\_completeness
+ 0.20 \cdot fetch\_success\_rate
+ 0.15 \cdot parse\_success\_rate
+ 0.10 \cdot throughput\_score
+ 0.10 \cdot maintainability\_score
+ 0.10 \cdot scalability\_score
+ 0.10 \cdot integration\_score
- 0.10 \cdot resource\_cost\_penalty
\]

其中 `throughput_score`、`resource_cost_penalty` 做归一化处理。

## 5. 分场景实验结果

运行脚本生成：

- `results/crawler_selection_result.csv`
- `results/crawler_selection_result.json`
- `results/selection_conclusion.md`

将三类场景的候选技术得分排名、最终选择与淘汰原因粘贴到本节，并补充定性解释。

> 本论文第一阶段正式实验使用**受控大样本**：每场景 1000 条有效样本 + 15% 异常/噪声样本，总量约 3450 条；并对每种技术重复运行 3 次取平均，以降低偶然波动（详见 README 的生成与运行命令）。

## 6. 技术淘汰分析

按场景归纳淘汰原因，例如：

- 动态页面场景下：预实验中不执行 JS 的普通 Requests/Scrapy 在壳页上解析失败；正式主实验在三种可行动态方案之间按 final_score 与定性维度择优
- 静态大规模采集场景下：轻量脚本扩展性不足、工程化能力不足（scalability 低）
- RSS/API 场景下：框架方案相对“过重”，在结构化源上收益不明显（resource_cost 与维护成本偏高）

## 7. 最终系统采集方案（结论）

本实验输出的“唯一选型”应体现为：

1. 静态新闻/公告页面最终选择 **Scrapy**
2. RSS/API 结构化信息源最终选择 **Requests + feedparser**
3. 动态渲染页面正式主实验在 **Requests + XHR/API replay**、**Scrapy + Playwright** 与 **Playwright** 之间择优；若得分支持，推荐系统级主方案为 **Scrapy + Playwright**（兼顾调度/Pipeline 与 JS 渲染），XHR 复现为轻量优化路径，纯 Playwright 为强动态兜底
4. 其余方案在不适合的场景中明确淘汰，并给出原因

## 8. 后续真实数据采集计划

建议写明：

- 数据源清单（新闻站点、辟谣平台、校园公告等）
- 采集频率与调度策略（后续可用 celery/cron）
- 入库方式：优先通过 FACT 后端 API 入库
- 合规与伦理：不采集隐私、遵守 robots 与站点条款、避免攻击性访问

## 9. 第二阶段：真实公开源验证设计（少量验证框架）

### 9.1 设计动机

- **第一阶段（本地 mock 受控实验）**用于保证对比的公平性与可重复性：相同数据源、相同字段要求、同一评分模型下进行量化评估，得到“每场景唯一选型 + 淘汰原因”。
- 但受控实验无法覆盖真实网络环境的全部不确定性（网络波动、robots 约束、页面结构差异等），因此需要：
- **第二阶段（少量公开源真实验证）**用于验证第一阶段选型在真实环境中的可落地性。

### 9.2 验证原则

- 仅选择**少量**公开可访问源（不追求大规模采集）
- 只运行 `enabled=true` 的源；默认不访问外网
- 必须遵守 `robots.txt`：明确不允许则 skipped；无法确认则 `robots_unknown`，不强行采集
- 访问频率限制：请求间 sleep 1~3 秒
- 不做登录、验证码、反爬绕过；不采集个人隐私数据

### 9.3 验证框架与输出

真实验证入口脚本与配置在：

- `experiments/crawler_selection_experiment/real_world_validation/`

输出到：

- `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.csv`
- `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.json`

本阶段只验证：

1. robots 合规检查；
2. 页面/接口是否可访问；
3. 是否能抽取统一字段；
4. 字段完整率是否达到最低要求（`field_completeness >= 0.6`）。

重要约束：

- 本阶段不做大规模数据采集，不作为训练数据来源；
- 第二阶段结果仅作为后续 `fact_crawler` 工程化落地与规则补齐的依据。

论文写作口径建议（避免误判）：

- `robots_unknown` 不应计为采集技术失败：它表示 robots.txt 获取/解析失败导致许可状态无法确认；按合规策略未执行正式采集，应归类为“合规检查阶段不确定性/环境约束”，并在论文中明确说明“不绕过、不强采集”。

动态验证源替换说明（第二阶段 MVP）：

1. 原 `china_gov_policy_library_dynamic` 虽然 robots 与 HTTP 访问通过，但返回内容较短、字段抽取失败，说明该源更适合作为后续“复杂动态/检索型页面”优化对象。
2. 为保证第二阶段 MVP 验证闭环与可解释性，改用 **国家统计局国家数据平台**（`nbs_data_dynamic`）作为更简单、稳定的动态验证源。
3. 国家数据平台需要 JavaScript 渲染，能够体现 **Scrapy + Playwright** 相对普通静态请求的必要性。
4. 该替换不改变第一阶段技术选型结论，仅调整第二阶段真实源验证样本。

### 9.4 结论融合

最终系统采集技术方案以“**本地受控实验结论**”为主，并以“**真实公开源验证结果**”作为可落地性校验：

- 若真实验证出现大面积 `robots` 限制或解析不可用，则需要调整数据源范围或补充适配规则；
- 若真实验证可稳定获取核心字段，则确认第一阶段选型可用于系统实现。

## 10. 可视化结果说明（论文插图）

为便于在论文实验章节直观展示“对比试验 → 得分排名 → 技术淘汰 → 唯一选型”的过程，可使用脚本生成可视化图表：

- 生成脚本：`experiments/crawler_selection_experiment/generate_figures.py`
- 输出目录：`experiments/crawler_selection_experiment/results/figures/`

建议在论文中放入：

1. `final_score_by_scenario.png`：展示每个场景下候选技术的 final_score 排名，并突出最终选中技术。
2. 三张雷达图：`static_news_radar.png`、`rss_api_radar.png`、`dynamic_page_radar.png`，展示核心指标的多维对比，说明选中技术的综合优势。
3. `selection_heatmap.png`：展示每类场景“唯一选型”矩阵（selected=1/0），用于强化“非并存方案，而是按场景唯一最佳方案”的结论表达。
4. `valid_failed_count_by_scenario.png`、`field_completeness_by_method.png`、`throughput_by_method.png`：补充有效/失败计数、字段完整率与吞吐对比。
5. **可视化增强（不改变原始评分数值）**：`score_delta_from_best.png` 展示各场景内候选方案与最优 `final_score` 的相对差值（selected 方案差值为 0）；`throughput_by_method_log.png` 与 `latency_by_method_log.png` 对吞吐量与平均延迟采用对数坐标，仅用于凸显数量级差异（图中对 0 值使用极小 epsilon 以免 `log(0)`，CSV 中原始 `throughput`/`avg_latency` 不变）。论文正文仍以线性尺度下的 `final_score` 与原始指标为主，对数图作为可读性辅助。

## 11. 样本质量控制（第一阶段 mock 大样本）

为保证第一阶段受控实验的可信度与可写入论文的严谨性，本实验对 mock 文本与样本结构做了明确的质量控制约束：

1. **不使用随机 Unicode 汉字生成正文**：禁止从 `\u4e00-\u9fff` 这类区间随机取字，避免产生现实语料中极少出现的生僻字和无意义字符拼接。
2. **采用主题词库与模板句生成文本**：标题与正文由“主题类别 + topic_words 词库 + 固定模板句”组合生成，确保表达自然、主题多样、字段规范。
3. **异常样本仅模拟真实采集问题**：噪声样本用于模拟字段缺失（title/content/category/keywords）、链接重复、时间格式差异、HTML 结构缺失等；异常体现在“字段/结构”，而不是“文字乱码”。
4. **统一 UTF-8 编码**：所有文件读写显式使用 UTF-8；HTML 均包含 `<meta charset="UTF-8">`；JSON 写入使用 `ensure_ascii=False`。
5. **质量检查脚本验证**：提供 `check_mock_sample_quality.py` 扫描 `mock_sources/` 下的 HTML/XML/JSON，检查：
   - 是否出现乱码替换字符 `�`
   - 是否出现非白名单汉字（按模板/词库白名单策略判定并记录）
   - 是否存在明显无意义连续字符（同一字符连续重复 >= 6）
   - 统计样本数量、类别分布、空字段数量

质量报告输出到：

- `results/mock_sample_quality_report.md`
- `results/mock_sample_quality_report.json`

## 12. 样本真实性与页面结构设计（第一阶段 mock）

为更贴近真实网络舆情采集环境，本实验在受控前提下提升了 mock 页面与文本的复杂度，使“技术选型实验”不仅测试脚本能否跑通，也测试**多模板 DOM 结构下的字段解析稳定性**：

1. **页面类型**：静态详情页按轮换策略模拟五类常见来源——新闻门户文章、政务通报/公告、论坛帖子、校园平台通知、本地生活信息流；不再使用非标准标签（如 `<headline>`），而采用 `article`、`section`、`time`、`header/nav`、`link rel="canonical"` 以及 `application/ld+json`（NewsArticle）等更接近生产站点习惯的元素。
2. **正文规模**：每条有效样本正文由多段模板化自然中文构成，目标长度约 **300～600 字**，覆盖事件背景、传播情况、核实状态、公众关注点与风险提示/后续跟踪等要素，便于检验长文本下的正文抽取与完整率指标。
3. **RSS/API**：`sample_feed.xml` 中 `description` 承载 **150～300 字摘要**，完整正文置于带命名空间的 **`content:encoded`**；采集侧优先解析正文，再回退到摘要。`sample_api.json` 同步提供 `summary`、`content`、`engagement_count`、`risk_hint` 等字段，便于论文中描述“结构化 API 与 RSS 双形态”的一致性设计。
4. **动态页**：`dynamic_sample.html` 呈现骨架屏与脚本延迟拉取 `dynamic_payload.json` 再渲染列表卡片，**初始 HTML 不内嵌完整舆情正文**；完整条目在 `dynamic_payload.json`（1000 有效 + 15% 噪声）。正式主实验比较 Requests + XHR/API replay、Scrapy + Playwright 与 Playwright；普通 Requests+BS4 与普通 Scrapy 仅作为预实验负例说明。
5. **可复现与防混杂**：生成脚本在写入前会清理本模块 mock 目录中的旧文件，避免历史短样本与新版长样本混在同一目录下干扰质量统计与解析实验。

