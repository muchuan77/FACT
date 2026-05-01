# fact_crawler（Scrapy / Requests）

本模块用于 **公开数据采集**：新闻、舆情、辟谣平台等公开来源的数据抓取与清洗。

## 边界与约束

- 优先通过 `fact_backend` 的 API 入库（后续实现），避免直接与前端耦合。
- 第一阶段不追求全网实时监测，仅做最小可用的数据采集/导入能力。

## 第一阶段（MVP）最小目标

- 提供最小采集脚手架或数据导入脚本入口（后续实现）。

## v1.3.0（落地实验结论）的范围

本版本将实验结论落地到工程框架：

- static_news → **Scrapy**（v1.4.0 实现 adapter）
- rss_api → **Requests + feedparser**（v1.3.0 真实实现 adapter）
- dynamic_page → **Scrapy + Playwright**（v1.5.0 实现 adapter）

本轮仅实现：

- 多适配器框架（Adapter 接口 + runner 自动选择）
- RSS adapter（`rss_feedparser`）真实可用
- 关键词过滤与轻量关键词抽取（用于 monitor/search 任务）

## 目录结构

```text
fact_crawler/
├── README.md
├── requirements.txt
└── crawler/
    ├── __init__.py
    ├── models.py
    ├── base_adapter.py
    ├── rss_feedparser_adapter.py
    ├── scrapy_static_adapter.py
    ├── scrapy_playwright_dynamic_adapter.py
    ├── keyword_extractor.py
    ├── normalizer.py
    ├── backend_client.py
    └── runner.py
```

## 本地依赖

```bash
python -m pip install -r fact_crawler/requirements.txt
```

## 与后端联动（run-now）

后端 `POST /api/crawler/tasks/{id}/run-now/` 会在 v1.3.0 中同步执行 RSS adapter，并将结果写入：

- `OpinionData`（舆情入库）
- `CrawlerRun` / `CrawledItem`（运行与明细追踪）

