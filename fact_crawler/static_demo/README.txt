本地静态演示（scrapy_static，与根 README v1.4.x 一致）

1. 在本目录启动 HTTP 服务：
   python -m http.server 8765

2. 使用种子源（推荐）：
   执行 python manage.py seed_crawler_sources 后，存在稳定编码：
   source_code = local_static_demo
   base_url 默认 http://127.0.0.1:8765/list.html
   adapter_name = scrapy_static
   robots_required = False（本地演示不做 robots 检查）

   联调示例（仓库根）：
   python scripts/test_create_chinese_crawler_task.py --mode static --source-code local_static_demo --no-keyword-filter --max-items 2

3. 创建任务绑定该源后：
   POST /api/crawler/tasks/{id}/run-now/

4. 公开源静态验证可使用种子中的 gov_zhengce_static（https://www.gov.cn/zhengce/）；列表/详情行为见根 README「v1.4.2 / v1.4.3」。

技术说明：
- Scrapy allowed_domains 不能写带端口主机名；适配器已将 127.0.0.1:8765 规范为 127.0.0.1，否则易出现 run-now 成功但 total_fetched=0。
- HTML 须 UTF-8（本目录页面已带 meta charset）。http.server 常返回无 charset 的 text/html，蜘蛛对本机强制 UTF-8 解码。
- 中文 API 测试请用 Python requests 脚本，避免 PowerShell 裸发 JSON 乱码。
