# 文档索引（FACT）

本目录存放**对外可读**的接口说明、发布说明与论文相关材料入口。与根目录 **`README.md`**（版本能力总览）、**`DEVLOG.md`**（开发过程与排障）分工如下：

| 文档 | 用途 |
|------|------|
| [../README.md](../README.md) | 项目总览、技术架构、**v1.0.0 → v1.4.x** 按版本编排 |
| [../DEVLOG.md](../DEVLOG.md) | 阶段记录、关键决策、联调备注 |
| [backend-api.md](backend-api.md) | Django / DRF **MVP 接口**说明（含 `/api/crawler/*`） |
| [releases/v1.0.0.md](releases/v1.0.0.md) | v1.0.0 发布级功能清单与限制 |

## 子模块自述

各模块启动方式、边界与目录细节见：

- [../fact_backend/README.md](../fact_backend/README.md)
- [../fact_model_service/README.md](../fact_model_service/README.md)
- [../fact_frontend/README.md](../fact_frontend/README.md)
- [../fact_crawler/README.md](../fact_crawler/README.md)

## 可选扩展目录（按需新建）

以下为建议命名，**未创建时不影响主流程**：

- `docs/design/`：系统设计（模块边界、时序等）
- `docs/thesis/`：论文图表与引用材料
