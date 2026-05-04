本地动态演示（v1.5.0 scrapy_playwright_dynamic）

1. 安装浏览器内核（在已 pip install playwright 的环境中执行一次）：
   python -m playwright install chromium

2. 在本目录启动 HTTP 服务（端口与种子源一致：8766）：
   python -m http.server 8766

3. 种子源 source_code=local_dynamic_demo 默认 enabled=false。
   启用：在 Django Admin 或 PATCH /api/crawler/sources/{id}/ 将 enabled 设为 true。
   测试脚本在 --mode dynamic 且选用 local_dynamic_demo 时，若仍为 false 会自动 PATCH 为 true 并打印 [INFO]。

4. 联调（仓库根）：
   python scripts/test_create_chinese_crawler_task.py --mode dynamic --source-code local_dynamic_demo --no-keyword-filter --max-items 2

5. 子页面（卡片「原文链接」占位，便于浏览器点开验证）：
   demo-item-1.html、demo-item-2.html（与 index.html 同目录，同端口即可访问）。

说明：初始 HTML 不含卡片正文，卡片由 JS 延迟写入，需 Playwright 渲染后方可被采集。
