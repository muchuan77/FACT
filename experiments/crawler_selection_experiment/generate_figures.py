from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path("experiments/crawler_selection_experiment")
CSV_PATH = BASE_DIR / "results" / "crawler_selection_result.csv"
FIG_DIR = BASE_DIR / "results" / "figures"


REQUIRED_COLUMNS = [
    "scenario",
    "method",
    "final_score",
    "selected",
    "field_completeness",
    "fetch_success_rate",
    "parse_success_rate",
    "throughput_score",
    "maintainability_score",
    "scalability_score",
    "integration_score",
    "valid_count",
    "failed_count",
    "throughput",
    "avg_latency",
]


SCENARIO_ORDER = ["static_news", "rss_api", "dynamic_page"]


def _require_columns(df: pd.DataFrame, cols: List[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns in CSV: {missing}\nCSV path: {CSV_PATH}")


def _to_bool_selected(v) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("true", "1", "yes", "y")


def _normalize_0_10_to_0_1(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x) / 10.0))
    except Exception:
        return 0.0


def _scenario_label(s: str) -> str:
    return {
        "static_news": "Static news",
        "rss_api": "RSS / API",
        "dynamic_page": "Dynamic page",
    }.get(s, s)


def load_results() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise RuntimeError(f"CSV not found: {CSV_PATH}. Run run_experiment.py first.")
    df = pd.read_csv(CSV_PATH)
    _require_columns(df, REQUIRED_COLUMNS)

    # types
    df["selected"] = df["selected"].apply(_to_bool_selected)
    for c in REQUIRED_COLUMNS:
        if c in ("scenario", "method", "selected"):
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def ensure_output_dir() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def plot_final_score_by_scenario(df: pd.DataFrame) -> Path:
    scenarios = [s for s in SCENARIO_ORDER if (df["scenario"] == s).any()]
    n = len(scenarios)
    if n == 0:
        raise RuntimeError("No scenarios found in CSV.")

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.2), dpi=200, sharey=True)
    if n == 1:
        axes = [axes]

    for ax, s in zip(axes, scenarios):
        sub = df[df["scenario"] == s].copy().sort_values("final_score", ascending=False)
        methods = sub["method"].tolist()
        scores = sub["final_score"].tolist()
        selected = sub["selected"].tolist()

        colors = ["#2E86DE" if sel else "#AAB7B8" for sel in selected]
        bars = ax.bar(range(len(methods)), scores, color=colors)

        for i, (b, sel) in enumerate(zip(bars, selected)):
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 0.01,
                f"{scores[i]:.3f}" + (" ★" if sel else ""),
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title(f"Final score by method ({_scenario_label(s)})")
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels(methods, rotation=20, ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("final_score")
        ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    out = FIG_DIR / "final_score_by_scenario.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def _radar_metrics_row(row: pd.Series) -> Dict[str, float]:
    return {
        "field_completeness": float(row["field_completeness"] or 0.0),
        "fetch_success_rate": float(row["fetch_success_rate"] or 0.0),
        "parse_success_rate": float(row["parse_success_rate"] or 0.0),
        "throughput_score": float(row["throughput_score"] or 0.0),
        # 0~10 => 0~1
        "maintainability_score": _normalize_0_10_to_0_1(row["maintainability_score"]),
        "scalability_score": _normalize_0_10_to_0_1(row["scalability_score"]),
        "integration_score": _normalize_0_10_to_0_1(row["integration_score"]),
    }


def plot_radar_for_scenario(df: pd.DataFrame, scenario: str) -> Path:
    sub = df[df["scenario"] == scenario].copy().sort_values("final_score", ascending=False)
    if sub.empty:
        raise RuntimeError(f"No data for scenario: {scenario}")

    metrics = [
        "field_completeness",
        "fetch_success_rate",
        "parse_success_rate",
        "throughput_score",
        "maintainability_score",
        "scalability_score",
        "integration_score",
    ]

    labels = [
        "Completeness",
        "Fetch",
        "Parse",
        "Throughput",
        "Maintain",
        "Scale",
        "Integrate",
    ]

    angles = [i * 2 * math.pi / len(metrics) for i in range(len(metrics))]
    angles += angles[:1]

    fig = plt.figure(figsize=(6.2, 6.2), dpi=200)
    ax = plt.subplot(111, polar=True)
    ax.set_title(f"Radar comparison ({_scenario_label(scenario)})", y=1.08)

    ax.set_thetagrids([a * 180 / math.pi for a in angles[:-1]], labels)
    ax.set_ylim(0, 1.0)

    for _, row in sub.iterrows():
        vals_map = _radar_metrics_row(row)
        vals = [vals_map[m] for m in metrics]
        vals += vals[:1]

        is_selected = bool(row["selected"])
        color = "#E74C3C" if is_selected else "#7F8C8D"
        lw = 2.6 if is_selected else 1.3
        alpha = 0.22 if is_selected else 0.10

        ax.plot(angles, vals, color=color, linewidth=lw, label=row["method"])
        ax.fill(angles, vals, color=color, alpha=alpha)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=1, fontsize=9, frameon=False)
    fig.tight_layout()

    out = FIG_DIR / f"{scenario}_radar.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_selection_heatmap(df: pd.DataFrame) -> Path:
    scenarios = [s for s in SCENARIO_ORDER if (df["scenario"] == s).any()]
    methods = sorted(df["method"].unique().tolist())

    # matrix: scenario x method
    mat = []
    for s in scenarios:
        row = []
        for m in methods:
            sub = df[(df["scenario"] == s) & (df["method"] == m)]
            row.append(1 if (not sub.empty and bool(sub.iloc[0]["selected"])) else 0)
        mat.append(row)

    fig, ax = plt.subplots(figsize=(1.2 * max(4, len(methods)), 2.6), dpi=200)
    im = ax.imshow(mat, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_title("Selection heatmap (selected=1)")

    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels([_scenario_label(s) for s in scenarios])

    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=25, ha="right")

    # annotate cells
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            ax.text(j, i, str(mat[i][j]), ha="center", va="center", fontsize=9, color="black")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["0", "1"])

    fig.tight_layout()
    out = FIG_DIR / "selection_heatmap.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_valid_failed_count_by_scenario(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=200)
    sub = df.copy()
    sub["scenario"] = pd.Categorical(sub["scenario"], categories=SCENARIO_ORDER, ordered=True)
    sub = sub.sort_values(["scenario", "method"])

    grouped = sub.groupby("scenario", observed=True)[["valid_count", "failed_count"]].mean().reset_index()
    x = range(len(grouped))
    ax.bar([i - 0.2 for i in x], grouped["valid_count"], width=0.4, label="valid_count", color="#2ECC71")
    ax.bar([i + 0.2 for i in x], grouped["failed_count"], width=0.4, label="failed_count", color="#E67E22")
    ax.set_xticks(list(x))
    ax.set_xticklabels([_scenario_label(s) for s in grouped["scenario"].tolist()])
    ax.set_title("Valid vs failed count (avg by scenario)")
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "valid_failed_count_by_scenario.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_field_completeness_by_method(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(10.0, 4.6), dpi=200)
    sub = df.copy().sort_values(["scenario", "final_score"], ascending=[True, False])
    sub["label"] = sub["scenario"].map(_scenario_label) + " | " + sub["method"]
    colors = ["#2E86DE" if s else "#AAB7B8" for s in sub["selected"].tolist()]
    ax.bar(sub["label"], sub["field_completeness"], color=colors)
    ax.set_title("Field completeness by method")
    ax.set_ylabel("field_completeness")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "field_completeness_by_method.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_throughput_by_method(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(10.0, 4.6), dpi=200)
    sub = df.copy().sort_values(["scenario", "throughput"], ascending=[True, False])
    sub["label"] = sub["scenario"].map(_scenario_label) + " | " + sub["method"]
    colors = ["#E74C3C" if s else "#AAB7B8" for s in sub["selected"].tolist()]
    ax.bar(sub["label"], sub["throughput"], color=colors)
    ax.set_title("Throughput by method")
    ax.set_ylabel("items / second")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "throughput_by_method.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_score_delta_from_best(df: pd.DataFrame) -> Path:
    """各场景内 best_final_score - final_score；仅增强可读性，不改变原始 final_score。"""
    scenarios = [s for s in SCENARIO_ORDER if (df["scenario"] == s).any()]
    n = len(scenarios)
    if n == 0:
        raise RuntimeError("No scenarios found in CSV.")

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.4), dpi=200, sharey=False)
    if n == 1:
        axes = [axes]

    for ax, s in zip(axes, scenarios):
        sub = df[df["scenario"] == s].copy()
        best = float(sub["final_score"].max())
        sub = sub.assign(score_delta=best - sub["final_score"]).sort_values("score_delta", ascending=True)
        methods = sub["method"].tolist()
        deltas = sub["score_delta"].tolist()
        selected = sub["selected"].tolist()

        colors = ["#27AE60" if sel else "#95A5A6" for sel in selected]
        bars = ax.bar(range(len(methods)), deltas, color=colors)

        for i, b in enumerate(bars):
            h = float(deltas[i])
            ax.text(
                b.get_x() + b.get_width() / 2,
                h + max(deltas) * 0.02 if max(deltas) > 0 else 0.002,
                f"{h:.4f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title(f"Score gap vs best ({_scenario_label(s)})")
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels(methods, rotation=20, ha="right")
        ax.set_ylabel("best_final_score - final_score")
        ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.suptitle("Relative gap from best final_score per scenario (selected has delta=0)", y=1.02, fontsize=11)
    fig.tight_layout()
    out = FIG_DIR / "score_delta_from_best.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_throughput_by_method_log(df: pd.DataFrame) -> Path:
    eps = 1e-6
    fig, ax = plt.subplots(figsize=(10.0, 4.8), dpi=200)
    sub = df.copy().sort_values(["scenario", "throughput"], ascending=[True, False])
    sub["label"] = sub["scenario"].map(_scenario_label) + " | " + sub["method"]
    colors = ["#8E44AD" if s else "#BDC3C7" for s in sub["selected"].tolist()]
    tp = sub["throughput"].astype(float)
    y_plot = tp.where(tp > 0, eps)
    ax.bar(sub["label"], y_plot, color=colors)
    ax.set_yscale("log")
    ax.set_title("Throughput by method (log scale)")
    ax.set_ylabel("items / second (log)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.text(
        0.01,
        0.02,
        f"Note: throughput=0 plotted as {eps:g} for log axis only; CSV unchanged.",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
    )
    fig.tight_layout()
    out = FIG_DIR / "throughput_by_method_log.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_latency_by_method_log(df: pd.DataFrame) -> Path:
    eps = 1e-9
    fig, ax = plt.subplots(figsize=(10.0, 4.8), dpi=200)
    sub = df.copy().sort_values(["scenario", "avg_latency"], ascending=[True, False])
    sub["label"] = sub["scenario"].map(_scenario_label) + " | " + sub["method"]
    colors = ["#16A085" if s else "#BDC3C7" for s in sub["selected"].tolist()]
    lat = sub["avg_latency"].astype(float)
    y_plot = lat.where(lat > 0, eps)
    ax.bar(sub["label"], y_plot, color=colors)
    ax.set_yscale("log")
    ax.set_title("Average latency by method (log scale)")
    ax.set_ylabel("avg_latency (log)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.text(
        0.01,
        0.02,
        f"Note: log scale for readability only; avg_latency=0 shown as {eps:g}. CSV unchanged.",
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
    )
    fig.tight_layout()
    out = FIG_DIR / "latency_by_method_log.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    ensure_output_dir()
    df = load_results()

    a = plot_final_score_by_scenario(df)
    b = plot_radar_for_scenario(df, "static_news")
    c = plot_radar_for_scenario(df, "rss_api")
    d = plot_radar_for_scenario(df, "dynamic_page")
    e = plot_selection_heatmap(df)
    f = plot_valid_failed_count_by_scenario(df)
    g = plot_field_completeness_by_method(df)
    h = plot_throughput_by_method(df)
    i = plot_score_delta_from_best(df)
    j = plot_throughput_by_method_log(df)
    k = plot_latency_by_method_log(df)

    print("[OK] figures generated:")
    for p in (a, b, c, d, e, f, g, h, i, j, k):
        print(f" - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

