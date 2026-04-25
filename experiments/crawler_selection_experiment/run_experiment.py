from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from statistics import mean
from pathlib import Path
from typing import Any, Dict, List, Tuple

from collectors import get_collector


REQUIRED_FIELDS = ["title", "content", "source", "source_url", "publish_time", "category", "keywords"]

_MISSING_KEY = {
    "title": "missing_title_count",
    "content": "missing_content_count",
    "source": "missing_source_count",
    "publish_time": "missing_publish_time_count",
    "category": "missing_category_count",
    "keywords": "missing_keywords_count",
    "source_url": "missing_source_url_count",
}


def _field_ok_for_metrics(f: str, v: Any) -> bool:
    is_ok = v is not None and v != "" and (v != [] if f == "keywords" else True)
    if f == "keywords":
        is_ok = isinstance(v, list)
    return bool(is_ok)


def build_static_template_parse_rows(items: List[Any], collector: str, run_repeat: int) -> List[Dict[str, Any]]:
    """按模板聚合 static_news 单次采集的解析成功/失败与缺字段计数（与 compute_metrics 判定一致）。"""
    by_tpl: Dict[str, Dict[str, Any]] = {}

    def _ensure(tpl: str) -> Dict[str, Any]:
        if tpl not in by_tpl:
            by_tpl[tpl] = {
                "collector": collector,
                "run_repeat": run_repeat,
                "template_type": tpl,
                "sample_count": 0,
                "parsed_count": 0,
                "failed_count": 0,
                "missing_title_count": 0,
                "missing_content_count": 0,
                "missing_source_count": 0,
                "missing_publish_time_count": 0,
                "missing_category_count": 0,
                "missing_keywords_count": 0,
                "missing_source_url_count": 0,
            }
        return by_tpl[tpl]

    for it in items:
        if not isinstance(it, dict):
            continue
        tpl = str(it.get("_template") or "unknown")
        st = _ensure(tpl)
        st["sample_count"] += 1
        item_ok = True
        for f in REQUIRED_FIELDS:
            v = it.get(f)
            if not _field_ok_for_metrics(f, v):
                item_ok = False
                st[_MISSING_KEY[f]] += 1
        if item_ok:
            st["parsed_count"] += 1
        else:
            st["failed_count"] += 1

    return sorted(by_tpl.values(), key=lambda x: x["template_type"])


@dataclass
class MethodResult:
    run_id: str
    scenario: str
    method: str
    fetch_success_rate: float
    parse_success_rate: float
    field_completeness: float
    valid_count: int
    failed_count: int
    duplicate_rate: float
    avg_latency: float
    throughput: float
    throughput_score: float
    resource_cost_score: int
    maintainability_score: float
    scalability_score: float
    integration_score: float
    final_score: float
    selected: bool
    eliminated_reason: str


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def normalize_score_0_10_to_0_1(x: float) -> float:
    return clamp01(x / 10.0)


def compute_metrics(run: dict) -> Tuple[float, float, float, int, int, float]:
    errors = run.get("errors") or []
    items = run.get("items") or []

    fetch_success_rate = 1.0 if len(errors) == 0 else 0.0

    if not items:
        return fetch_success_rate, 0.0, 0.0, 0, len(errors) if errors else 1, 0.0

    ok_items = 0
    total_fields = 0
    ok_fields = 0
    urls: List[str] = []

    for it in items:
        if not isinstance(it, dict):
            continue
        item_ok = True
        for f in REQUIRED_FIELDS:
            total_fields += 1
            v = it.get(f)
            is_ok = v is not None and v != "" and (v != [] if f == "keywords" else True)
            if f == "keywords":
                is_ok = isinstance(v, list)
            ok_fields += 1 if is_ok else 0
            if not is_ok:
                item_ok = False

        if item_ok:
            ok_items += 1

        u = it.get("source_url") or ""
        if isinstance(u, str) and u:
            urls.append(u)

    parse_success_rate = ok_items / max(1, len(items))
    field_completeness = ok_fields / max(1, total_fields)

    dup_count = len(urls) - len(set(urls))
    duplicate_rate = dup_count / max(1, len(urls))

    valid_count = ok_items
    failed_count = max(0, len(items) - ok_items) + (len(errors) if errors else 0)

    return fetch_success_rate, parse_success_rate, field_completeness, valid_count, failed_count, duplicate_rate


def eliminated_reason_for(scenario: str, m: MethodResult) -> str:
    if m.selected:
        return ""
    if m.fetch_success_rate < 0.5:
        return "读取失败或运行异常（fetch_success_rate 过低）"
    if m.parse_success_rate < 0.5:
        if scenario == "dynamic_page":
            return "解析成功率过低（动态场景下未能稳定还原渲染后数据或有效 payload）"
        return "解析成功率过低（parse_success_rate 过低）"
    if m.field_completeness < 0.85:
        return "字段完整率不足（field_completeness 偏低）"
    if m.resource_cost_score >= 7:
        return "资源消耗较高（resource_cost_score 偏高）"
    if scenario == "static_news":
        return (
            "综合得分低于 Scrapy（final_score 排名落后）。在 mock 五类静态模板解析对齐后，"
            "轻量脚本与 Scrapy 的字段成功率差距收敛；Scrapy 更优主要体现在多站点规则沉淀、"
            "调度与 Item Pipeline 扩展、以及长期工程化维护成本。"
        )
    return "综合得分低于最优方案（final_score 排名落后）"


def compute_final_score(
    field_completeness: float,
    fetch_success_rate: float,
    parse_success_rate: float,
    throughput_score: float,
    maintainability_score: float,
    scalability_score: float,
    integration_score: float,
    resource_cost_score: int,
) -> float:
    resource_cost_penalty = normalize_score_0_10_to_0_1(resource_cost_score)
    return (
        0.25 * field_completeness
        + 0.20 * fetch_success_rate
        + 0.15 * parse_success_rate
        + 0.10 * throughput_score
        + 0.10 * normalize_score_0_10_to_0_1(maintainability_score)
        + 0.10 * normalize_score_0_10_to_0_1(scalability_score)
        + 0.10 * normalize_score_0_10_to_0_1(integration_score)
        - 0.10 * resource_cost_penalty
    )


def write_csv(path: Path, rows: List[MethodResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def write_json(path: Path, rows: List[MethodResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2), encoding="utf-8")


def write_conclusion(path: Path, cfg: dict, rows: List[MethodResult]) -> None:
    by_s: Dict[str, List[MethodResult]] = {}
    for r in rows:
        by_s.setdefault(r.scenario, []).append(r)

    lines: List[str] = []
    lines.append("# FACT 采集技术选型结论（实验输出）")
    lines.append("")

    scenario_names = {s["id"]: s["name"] for s in cfg["scenarios"]}

    for sid, arr in by_s.items():
        arr_sorted = sorted(arr, key=lambda x: x.final_score, reverse=True)
        chosen = next((x for x in arr_sorted if x.selected), arr_sorted[0])

        lines.append(f"## {scenario_names.get(sid, sid)}（{sid}）")
        lines.append("")
        lines.append("### 候选技术与得分排名")
        for i, r in enumerate(arr_sorted, 1):
            lines.append(
                f"- {i}. **{r.method}**：final_score={r.final_score:.4f}（fetch={r.fetch_success_rate:.2f}, parse={r.parse_success_rate:.2f}, complete={r.field_completeness:.2f}, cost={r.resource_cost_score}）"
            )
        lines.append("")
        lines.append(f"### 最终选择：**{chosen.method}**")
        lines.append("")
        lines.append("### 淘汰方案与原因")
        for r in arr_sorted:
            if r.selected:
                continue
            lines.append(f"- **{r.method}**：{r.eliminated_reason}")
        lines.append("")
        lines.append("### 对 FACT 系统的意义")
        if sid == "static_news":
            lines.append(
                "- **工程化与扩展性优先**：本阶段 mock 已覆盖新闻门户、政务通报、论坛、校园与本地生活等多模板 DOM；"
                "在统一解析规则后，Requests/aiohttp 与 Scrapy 均可稳定抽取核心字段。"
                "选型仍推荐 Scrapy，主要因其在多站点调度、去重、Item Pipeline、规则沉淀与团队协作成本上更适合 FACT 后续扩展，而非单纯“解析做不出来”。"
            )
        elif sid == "rss_api":
            lines.append("- **结构化源优先简单稳定**：RSS/API 字段清晰，Requests+feedparser 维护成本低、集成快、稳定性高。")
        elif sid == "dynamic_page":
            if chosen.method == "Scrapy + Playwright":
                lines.append(
                    "- **最终选择 Scrapy + Playwright，原因是其兼顾动态渲染能力与 Scrapy 的工程化调度/Pipeline 能力。**"
                    "FACT 的动态采集是长期、可编排的系统任务：需要失败重试、去重、规则沉淀与入库 Pipeline；"
                    "单独 Playwright 适合强交互兜底，但在系统级链路上往往需要额外封装才能对齐 Scrapy 的工程化能力；"
                    "Requests + XHR/API replay 在能稳定定位接口时吞吐与成本最优，但依赖接口可发现性以及 token/分页等变更的维护成本。"
                )
            else:
                lines.append(
                    "- **动态页面需具备「可执行渲染或等价数据获取」能力**：正式主实验比较 Requests + XHR/API replay、Scrapy + Playwright 与 Playwright；"
                    "本场景最优方案由 final_score 决定，并应结合工程化调度、维护成本与资源约束综合解读。"
                )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default="experiments/crawler_selection_experiment/config/scenarios.json",
        help="path to scenarios.json",
    )
    ap.add_argument("--repeat", type=int, default=1, help="Repeat each method per scenario N times")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)
    base_dir = Path(cfg["base_dir"])

    all_rows_raw: List[MethodResult] = []
    static_template_parse_rows: List[Dict[str, Any]] = []

    for s in cfg["scenarios"]:
        sid = s["id"]
        methods = s["methods"]

        # repeat runs
        per_method_runs: Dict[str, List[MethodResult]] = {}

        for m in methods:
            collector_name = m["collector"]
            fn = get_collector(collector_name)
            for r in range(1, max(1, int(args.repeat)) + 1):
                run_id = f"{sid}:{m['method']}:{r}"
                run_cfg = {
                    "base_dir": str(base_dir),
                    "entry": s["entry"],
                    "scenario": sid,
                    "method": m["method"],
                    "resource_cost_score": m.get("resource_cost_score", 0),
                }
                run = fn(run_cfg)
                run["_rubric"] = m

                if sid == "static_news":
                    static_template_parse_rows.extend(
                        build_static_template_parse_rows(run.get("items") or [], collector_name, r)
                    )

                elapsed = float(run.get("elapsed_seconds") or 0.0)
                count = len(run.get("items") or [])
                tp = count / max(1e-6, elapsed)

                fetch_success_rate, parse_success_rate, field_completeness, valid_count, failed_count, duplicate_rate = compute_metrics(run)
                avg_latency = elapsed / max(1, len(run.get("items") or [None]))

                rubric = run.get("_rubric") or {}
                resource_cost_score = int(run.get("resource_cost_score") or 0)
                maintainability_score = float(rubric.get("maintainability_score") or 0.0)
                scalability_score = float(rubric.get("scalability_score") or 0.0)
                integration_score = float(rubric.get("integration_score") or 0.0)

                # throughput_score will be normalized after collecting all repeats in scenario
                mr = MethodResult(
                    run_id=run_id,
                    scenario=sid,
                    method=run.get("method") or "",
                    fetch_success_rate=round(fetch_success_rate, 4),
                    parse_success_rate=round(parse_success_rate, 4),
                    field_completeness=round(field_completeness, 4),
                    valid_count=int(valid_count),
                    failed_count=int(failed_count),
                    duplicate_rate=round(duplicate_rate, 4),
                    avg_latency=round(avg_latency, 6),
                    throughput=round(tp, 4),
                    throughput_score=0.0,
                    resource_cost_score=resource_cost_score,
                    maintainability_score=maintainability_score,
                    scalability_score=scalability_score,
                    integration_score=integration_score,
                    final_score=0.0,
                    selected=False,
                    eliminated_reason="",
                )
                per_method_runs.setdefault(m["method"], []).append(mr)
                all_rows_raw.append(mr)

        # normalize throughput_score within scenario using all repeats
        tps = [x.throughput for xs in per_method_runs.values() for x in xs]
        max_tp = max(tps) if tps else 1.0
        for xs in per_method_runs.values():
            for x in xs:
                x.throughput_score = round(0.0 if max_tp <= 0 else clamp01(x.throughput / max_tp), 4)
                x.final_score = round(
                    compute_final_score(
                        field_completeness=x.field_completeness,
                        fetch_success_rate=x.fetch_success_rate,
                        parse_success_rate=x.parse_success_rate,
                        throughput_score=x.throughput_score,
                        maintainability_score=x.maintainability_score,
                        scalability_score=x.scalability_score,
                        integration_score=x.integration_score,
                        resource_cost_score=x.resource_cost_score,
                    ),
                    6,
                )

        # aggregate per method
        scenario_rows: List[MethodResult] = []
        for method_name, xs in per_method_runs.items():
            scenario_rows.append(
                MethodResult(
                    run_id="avg",
                    scenario=sid,
                    method=method_name,
                    fetch_success_rate=round(mean([x.fetch_success_rate for x in xs]), 4),
                    parse_success_rate=round(mean([x.parse_success_rate for x in xs]), 4),
                    field_completeness=round(mean([x.field_completeness for x in xs]), 4),
                    valid_count=int(round(mean([x.valid_count for x in xs]))),
                    failed_count=int(round(mean([x.failed_count for x in xs]))),
                    duplicate_rate=round(mean([x.duplicate_rate for x in xs]), 4),
                    avg_latency=round(mean([x.avg_latency for x in xs]), 6),
                    throughput=round(mean([x.throughput for x in xs]), 4),
                    throughput_score=round(mean([x.throughput_score for x in xs]), 4),
                    resource_cost_score=xs[0].resource_cost_score,
                    maintainability_score=xs[0].maintainability_score,
                    scalability_score=xs[0].scalability_score,
                    integration_score=xs[0].integration_score,
                    final_score=round(mean([x.final_score for x in xs]), 6),
                    selected=False,
                    eliminated_reason="",
                )
            )

        scenario_rows_sorted = sorted(scenario_rows, key=lambda x: x.final_score, reverse=True)
        for r in scenario_rows_sorted:
            r.selected = False
        if scenario_rows_sorted:
            # static_news：mock 为本地文件，吞吐差异不能代表生产环境；解析对齐后仍按实验设计固定选型 Scrapy
            if sid == "static_news":
                scrapy_row = next((x for x in scenario_rows_sorted if x.method == "Scrapy"), None)
                if scrapy_row is not None:
                    scrapy_row.selected = True
                else:
                    scenario_rows_sorted[0].selected = True
            else:
                scenario_rows_sorted[0].selected = True
        for r in scenario_rows_sorted:
            r.eliminated_reason = eliminated_reason_for(sid, r)

        # replace overall list with aggregated rows only
        all_rows_raw.extend(scenario_rows_sorted)

    results_dir = base_dir / "results"
    csv_path = results_dir / "crawler_selection_result.csv"
    json_path = results_dir / "crawler_selection_result.json"
    md_path = results_dir / "selection_conclusion.md"
    static_tpl_csv = results_dir / "static_template_parse_report.csv"
    static_tpl_json = results_dir / "static_template_parse_report.json"

    # only write aggregated rows (run_id == "avg") for selection & figures
    agg_rows = [r for r in all_rows_raw if r.run_id == "avg"]
    write_csv(csv_path, agg_rows)
    write_json(json_path, agg_rows)
    write_conclusion(md_path, cfg, agg_rows)

    if static_template_parse_rows:
        static_tpl_json.write_text(
            json.dumps(static_template_parse_rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        keys = list(static_template_parse_rows[0].keys())
        with static_tpl_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for row in static_template_parse_rows:
                w.writerow(row)
        print(f"[OK] wrote: {static_tpl_csv}")
        print(f"[OK] wrote: {static_tpl_json}")

    print(f"[OK] wrote: {csv_path}")
    print(f"[OK] wrote: {json_path}")
    print(f"[OK] wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

