# 第二阶段：少量公开可访问源真实验证（框架）

在第一阶段「本地 `mock_sources` 受控实验」之后，对少量公开源做**可诊断、合规优先**的真实抓取验证（与生产 **`scrapy_static` / RSS** 代码路径独立）。

## 设计原则

- 默认**不访问外网**：若未配置本地 `validation_sources.local.json`，脚本应提示并退出（以实际脚本为准）。
- 仅运行 `enabled=true` 的数据源；遵守 `robots.txt`；请求间隔受控。
- 不做登录、验证码、反爬绕过；不采集个人隐私数据。

## 准备配置

复制模板并编辑（路径以仓库根为当前目录）：

```bash
cp experiments/crawler_selection_experiment/real_world_validation/validation_sources.example.json \
   experiments/crawler_selection_experiment/real_world_validation/validation_sources.local.json
```

将需验证的源设为 `enabled: true` 并填写公开 URL。

## 运行

```bash
python experiments/crawler_selection_experiment/real_world_validation/run_real_validation.py
```

## 输出位置（与 `run_real_validation.py` 一致）

结果写入（CSV / JSON）：

- `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.csv`
- `experiments/crawler_selection_experiment/results/stage2_real_world/real_validation_result.json`
- 明细（若脚本生成）：同目录下 `real_validation_items.csv` / `real_validation_items.json`

> 若文档中曾出现 `results/real_validation_result.*`（无 `stage2_real_world`）为旧路径，以本说明为准。

## 更多说明

完整阶段说明、依赖与图表生成见上级目录：**[../README.md](../README.md)**。
