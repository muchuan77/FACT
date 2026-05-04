# fact_crawler（Scrapy / Requests）

公开数据采集与清洗；**入库**由 `fact_backend` 的 API 触发（`run-now` 内联调用 adapter），不直接与前端耦合。

## 边界与约束

- 遵守 robots 与合规策略；不实现登录、验证码与反爬绕过（工程内明确禁止的路径除外）。
- 第一阶段不追求全网实时监测，以可复现、可诊断的适配器为主。

## 已实现适配器（与根 README 对齐）

| adapter_name | 说明 |
|--------------|------|
| `rss_feedparser` | RSS / Feed，`requests` + `feedparser` |
| `scrapy_static` | 静态列表 + 详情，**子进程** Scrapy（v1.4.0+）；含 **gov.cn `/zhengce/`** 列表/正文增强（v1.4.2 / v1.4.3） |
| `scrapy_playwright_dynamic` | **v1.5.0+** 动态页：Scrapy + Playwright，**子进程**跑浏览器与 reactor |

`runner` 按任务绑定的 `adapter_name` 调度；关键词过滤与轻量关键词抽取见 `keyword_extractor.py`、`normalizer.py`。

## 目录结构（核心）

```text
fact_crawler/
├── README.md
├── requirements.txt
├── static_demo/          # 本地 UTF-8 静态演示（见 static_demo/README.txt）
├── dynamic_demo/         # 本地 UTF-8 动态演示（JS 延迟注入卡片，见 dynamic_demo/README.txt）
└── crawler/
    ├── base_adapter.py
    ├── runner.py
    ├── rss_feedparser_adapter.py
    ├── scrapy_static_adapter.py
    ├── scrapy_playwright_dynamic_adapter.py
    ├── scrapy_static/     # Scrapy 静态工程
    │   ├── spider.py
    │   ├── run_spider.py
    │   └── subprocess_runner.py
    ├── scrapy_playwright_dynamic/
    │   ├── spider.py
    │   ├── run_spider.py
    │   └── subprocess_runner.py
    ├── keyword_extractor.py
    ├── normalizer.py
    └── backend_client.py
```

## 依赖

```bash
python -m pip install -r fact_crawler/requirements.txt
python -m playwright install chromium
```

动态适配器首次运行前必须安装 Chromium 内核；仅 RSS / 静态采集可不执行第二行。

## 与后端联动

后端 **`POST /api/crawler/tasks/{id}/run-now/`** 同步执行已启用且类型匹配的 **RSS、static、dynamic** 源，写入 `OpinionData` 及 `CrawlerRun` / `CrawledItem`。接口说明见 **[../docs/backend-api.md](../docs/backend-api.md)**。

## 进一步阅读

- 版本与 gov.cn 行为：**[../README.md](../README.md)**（v1.4.0–v1.4.3）
- 本地 static 演示：**[static_demo/README.txt](static_demo/README.txt)**
- 本地 dynamic 演示：**[dynamic_demo/README.txt](dynamic_demo/README.txt)**
