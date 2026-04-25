# 第二阶段：少量公开可访问源真实验证（框架）

本目录用于在第一阶段“本地 mock_sources 受控实验”之后，进行第二阶段“少量公开可访问源的真实验证”。

## 设计原则（重要）

- 默认 **不访问外网**：脚本默认读取 `validation_sources.local.json`，若不存在则直接提示并退出。
- 仅运行 `enabled=true` 的数据源。
- 必须进行合规检查提示与 `robots.txt` 检查。
- 控制访问频率：每次请求间随机 sleep 1~3 秒。
- 不做登录、验证码、反爬绕过；不采集个人隐私数据。

## 如何准备配置

1. 复制模板：

```bash
cp experiments/crawler_selection_experiment/real_world_validation/validation_sources.example.json \
   experiments/crawler_selection_experiment/real_world_validation/validation_sources.local.json
```

2. 编辑 `validation_sources.local.json`，填入**公开可访问** URL，并将要验证的源 `enabled` 设为 `true`。

## 如何运行

在仓库根目录执行：

```bash
python experiments/crawler_selection_experiment/real_world_validation/run_real_validation.py
```

运行后生成：

- `experiments/crawler_selection_experiment/results/real_validation_result.csv`
- `experiments/crawler_selection_experiment/results/real_validation_result.json`

