# experiments

模型训练、评估、消融与**采集技术选型等**离线实验代码；与在线 **`fact_model_service` 推理解耦**，不混入业务后台。

## 边界

- 不在此目录实现生产爬虫入库逻辑（生产路径见 **`fact_crawler`** + **`fact_backend`** `/api/crawler/*`）。
- 选型实验详见 **`crawler_selection_experiment/`**。

## 当前内容

- **`crawler_selection_experiment/`**  
  - 第一阶段：本地 `mock_sources` 受控对比（见该目录 `README.md`）  
  - 第二阶段：少量公开源真实验证（见 `real_world_validation/README.md`）

## 文档

- 工程版本与采集能力总览：**[../README.md](../README.md)**、**[../DEVLOG.md](../DEVLOG.md)**
