# fact_frontend（Vue3 + Vite + TypeScript + Element Plus + ECharts）

本模块用于 **前端可视化展示**：数据大屏、舆情列表、识别结果、风险预警与趋势图表等。

## 边界与约束

- 只做展示与交互。
- 通过 Axios 调用 `fact_backend` 的 REST API。
- 默认不直接调用 `fact_model_service`（由 Django 统一聚合/转发）。

## 前端 MVP（当前阶段）目标

- 使用真实后端接口（`http://127.0.0.1:8000`）完成最小展示闭环：
  - Dashboard：`/api/dashboard/summary/`
  - 舆情：`/api/opinions/` 列表/新增 + `/{id}/` 详情 + `/{id}/analyze/` 分析触发
  - 分析结果：`/api/analysis/`
  - 风险预警：`/api/warnings/`

## 目录结构（核心）

```text
src/
├── api/            # axios 请求封装 + 各业务 API
├── router/         # vue-router
├── stores/         # pinia
├── views/          # 页面
├── components/     # 复用组件
├── types/          # TS 类型
├── App.vue
└── main.ts
```

## 本地启动

先确保后端已启动：`http://127.0.0.1:8000`

在 `fact_frontend/` 目录执行：

```bash
npm install
npm run dev
```

默认前端地址：`http://127.0.0.1:5173`

## 进一步阅读

- 工程版本总览：**[../README.md](../README.md)**
- 文档索引：**[../docs/README.md](../docs/README.md)**

