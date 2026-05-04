# datasets

存放**公开数据集**与**自采集数据**（体积较大时建议勿直接提交到 Git）。

## 建议

- 按「来源 / 日期 / 版本」分子目录，必要时附带 `README` 或 `sources.json` 说明许可与引用方式。
- 大体量二进制或原始抓取结果可使用 `.gitignore` 排除，仅在文档中记录获取方式。

## 与主工程的关系

采集入库走 `fact_backend` API；实验与选型脚本在 **`experiments/`**，与本目录解耦。

文档入口：**[../README.md](../README.md)**、**[../docs/README.md](../docs/README.md)**
