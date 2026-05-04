本地静态演示（v1.4.0 scrapy_static）

1. 在本目录执行:
     python -m http.server 8765

2. 在 Django 中启用 CrawlerSource「本地静态演示列表」或自建源:
     source_type=static
     adapter_name=scrapy_static
     base_url=http://127.0.0.1:8765/list.html
     robots_required=false（本地无 robots.txt 时可关）

3. 创建任务绑定该源后 POST /api/crawler/tasks/{id}/run-now/

公开源验证可使用 seed 中的「中国政府网政策（静态列表+详情）」。

说明：Scrapy 的 allowed_domains 不能写「带端口」主机名；适配器已把 127.0.0.1:8765 规范为 127.0.0.1，否则会出现 run-now 成功但 total_fetched=0。

编码：HTML 须为 UTF-8（本仓库已统一）。python -m http.server 常返回无 charset 的 text/html，Scrapy 易误判为 latin-1；蜘蛛对本机地址强制 UTF-8 解码。若仍见乱码，先执行 reset_demo_data --yes 再 seed，并用 Python 脚本测 API（勿用 PowerShell 裸发中文 JSON）。
