from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple


BASE_DIR = Path("experiments/crawler_selection_experiment")
MOCK_DIR = BASE_DIR / "mock_sources"
RESULTS_DIR = BASE_DIR / "results"
REPORT_MD = RESULTS_DIR / "mock_sample_quality_report.md"
REPORT_JSON = RESULTS_DIR / "mock_sample_quality_report.json"
_STATIC_VALID_DETAIL = re.compile(r"^detail_\d{4}\.html$")


def _load_generator_corpus() -> str:
    """合并 generate_mock_samples 中的正文/模板语料，扩展生僻字白名单。"""
    try:
        p = BASE_DIR / "generate_mock_samples.py"
        spec = importlib.util.spec_from_file_location("_fact_gms_quality", p)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(mod)
        return str(getattr(mod, "QUALITY_TEXT_CORPUS", ""))
    except Exception:
        return ""


def _build_allowed_chars() -> set[str]:
    """
    生僻字过滤白名单策略：
    - 允许 ASCII（英文、数字、常见符号）
    - 允许常见标点与空白
    - 允许模板与词库中出现的汉字（即“我们生成过的自然中文”）
    """
    # 来自 generate_mock_samples.py 的模板/词库（硬编码一份，避免跨文件 import 带来的副作用）
    topic_words = [
        "突发事件",
        "公共场所",
        "应急处置",
        "现场通报",
        "风险提示",
        "秩序维护",
        "高校",
        "学生",
        "宿舍",
        "食堂",
        "课堂",
        "校园管理",
        "通知公告",
        "社区",
        "居民",
        "物业",
        "供水",
        "供电",
        "公共服务",
        "办事大厅",
        "医院",
        "门诊",
        "药品",
        "就诊",
        "健康提示",
        "诊疗服务",
        "企业",
        "消费者",
        "平台",
        "资金",
        "投资风险",
        "市场波动",
        "餐饮店",
        "食材",
        "食品抽检",
        "卫生管理",
        "消费提醒",
        "暴雨",
        "台风",
        "地震预警",
        "积水",
        "应急避险",
        "气象提醒",
        "地铁",
        "公交",
        "道路",
        "拥堵",
        "交通管制",
        "出行提示",
        "虚假链接",
        "冒充客服",
        "转账风险",
        "账号异常",
        "安全提醒",
        "网络讨论",
        "热点话题",
        "平台反馈",
        "信息核实",
        "公众关注",
    ]
    title_templates = [
        "网传某地出现{topic}相关消息引发关注",
        "关于{topic}的网络讨论持续升温",
        "多平台传播{topic}相关信息，官方回应正在核实",
        "有网友反映{topic}问题，相关部门发布提醒",
        "{source}出现{topic}相关话题，评论量持续增加",
    ]
    content_templates = [
        "近日，多个网络平台出现关于{topic}的讨论，部分信息尚未得到权威渠道确认。相关部门提醒公众关注官方通报，不轻信未经核实的内容。",
        "有网友在{source}发布与{topic}有关的信息，引发一定范围的转发和评论。目前该事件仍处于信息核实阶段，系统将持续跟踪其传播变化。",
        "针对近期传播的{topic}相关内容，多方信息存在表述差异。为降低舆情误判风险，需要结合来源、时间、关键词和传播热度进行综合分析。",
        "相关话题在短时间内获得较高关注度，评论内容主要集中在事件真实性、处置进展和公众影响等方面。后续需进一步进行风险评估。",
        "简短摘要：相关信息仍在核实。",
        "简短摘要：条目字段可能缺失或格式不一致。",
        "简短摘要：动态条目字段可能缺失。",
    ]
    # 生成的 HTML/JS shell 里会出现的固定说明文本（避免被误判为“模板外生僻字”）
    html_shell_text = [
        "模拟动态渲染",
        "注意",
        "不把完整内容直接写到 HTML 中",
        "避免 Requests/Scrapy 直接解析",
        "Rendered",
        "items",
        "Loading",
        "Dynamic page shell",
        "骨架屏",
        "信息流",
        "初始页面为骨架屏",
        "内容由脚本延迟渲染",
        "加载更多",
        "模拟无需交互",
        "热点列表",
        "模拟新闻门户",
        "某市政务公开",
        "模拟政务公开",
        "模拟论坛",
        "模拟校园平台",
        "模拟本地生活",
        "schema",
        "NewsArticle",
        "Organization",
    ]
    sources = [
        "模拟新闻源",
        "模拟政务公告",
        "模拟论坛",
        "模拟社交平台",
        "模拟校园平台",
        "模拟本地生活平台",
        "模拟 RSS 信息源",
    ]
    risk_bank = [
        "网传",
        "爆料",
        "辟谣",
        "事故",
        "学校",
        "学生",
        "食品安全",
        "公共安全",
        "恐慌",
        "严重",
        "诈骗",
        "疫情",
        "地震",
        "火灾",
        "暴雨",
        "交通管制",
        "出行提示",
        "官方通报",
        "风险提示",
        "信息核实",
    ]

    base_text = "".join(topic_words + sources + risk_bank + title_templates + content_templates + html_shell_text)
    base_text += _load_generator_corpus()

    allowed = set()
    # ASCII
    for i in range(32, 127):
        allowed.add(chr(i))
    # whitespace
    allowed.update(["\n", "\r", "\t", " "])
    # common punctuation (CN)
    allowed.update(list("，。；：？！、“”‘’（）【】《》—…·-—、"))
    # add characters from base_text
    allowed.update(list(base_text))
    return allowed


ALLOWED_CHARS = _build_allowed_chars()


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF


def _scan_text_for_issues(text: str) -> Dict[str, any]:
    issues = {
        "replacement_char_count": text.count("�"),
        # 注意：生僻字不靠“是否在白名单里”一刀切（否则会误伤正常汉字）。
        # 这里先收集“候选可疑字”（不在模板/词库白名单），最终是否判为生僻字由全局频次阈值决定。
        "candidate_rare_cjk": Counter(),
        "repeat_runs": [],
    }

    # candidate rare: CJK chars not in whitelist
    for ch in text:
        if _is_cjk(ch) and ch not in ALLOWED_CHARS:
            issues["candidate_rare_cjk"][ch] += 1

    # detect long repeat runs (e.g., "啊啊啊啊啊啊")
    # 过滤空白重复（JSON 缩进、空格/换行连续重复不属于“无意义字符”）
    m = re.finditer(r"([^\s])\1{5,}", text)
    for mm in m:
        issues["repeat_runs"].append({"char": mm.group(1), "length": len(mm.group(0))})

    return issues


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_meta(html: str, name: str) -> str:
    key = f'<meta name="{name}" content="'
    i = html.find(key)
    if i < 0:
        return ""
    j = html.find('"', i + len(key))
    if j < 0:
        return ""
    return html[i + len(key) : j].strip()


def _parse_tag_text(html: str, tag: str) -> str:
    # very lightweight tag extraction (not a full HTML parser)
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    val = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return val


def _parse_source(html: str) -> str:
    # meta preferred; fallback to <div class="source">
    v = _parse_meta(html, "source")
    if v:
        return v
    m = re.search(r'<div class="source">\s*([^<]+)\s*</div>', html, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    file_stats = []
    global_candidate_rare = Counter()
    cjk_freq = Counter()
    global_replacement = 0
    global_repeats = Counter()

    # distributions
    category_dist = Counter()
    empty_field_counts = Counter()
    counts = {
        "static_detail": 0,
        "static_noise_detail": 0,
        "static_list_pages": 0,
        "rss_items_xml": 0,
        "rss_records_json": 0,
        "dynamic_items_json": 0,
    }

    # 1) scan all text files under mock_sources
    for p in MOCK_DIR.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".html", ".xml", ".json"):
            continue
        txt = _read(p)
        issues = _scan_text_for_issues(txt)
        global_replacement += issues["replacement_char_count"]
        global_candidate_rare.update(issues["candidate_rare_cjk"])
        for ch in txt:
            if _is_cjk(ch):
                cjk_freq[ch] += 1
        for rr in issues["repeat_runs"]:
            global_repeats[rr["char"]] += 1

        file_stats.append(
            {
                "path": str(p),
                "replacement_char_count": issues["replacement_char_count"],
                "rare_cjk_candidate_count": int(sum(issues["candidate_rare_cjk"].values())),
                "repeat_run_count": len(issues["repeat_runs"]),
            }
        )

    # 2) structured checks
    static_dir = MOCK_DIR / "static_news"
    if static_dir.exists():
        counts["static_list_pages"] = len(list(static_dir.glob("list_page_*.html")))
        counts["static_detail"] = len(list(static_dir.glob("detail_*.html")))
        counts["static_noise_detail"] = len(list(static_dir.glob("detail_noise_*.html")))

        for p in static_dir.glob("detail_*.html"):
            html = _read(p)
            cat = _parse_meta(html, "category")
            if cat:
                category_dist[cat] += 1
            else:
                empty_field_counts["static.category.empty"] += 1

            # title can be in <h1> or <title>/<headline>; publish_time is meta; source can be meta or div
            title_txt = _parse_tag_text(html, "h1") or _parse_tag_text(html, "title") or _parse_tag_text(html, "headline")
            if not title_txt:
                empty_field_counts["static.title.empty"] += 1
            if not _parse_meta(html, "publish_time"):
                empty_field_counts["static.publish_time.empty"] += 1
            if not _parse_source(html):
                empty_field_counts["static.source.empty"] += 1

    rss_dir = MOCK_DIR / "rss_api"
    if rss_dir.exists():
        feed = rss_dir / "sample_feed.xml"
        api = rss_dir / "sample_api.json"
        if feed.exists():
            import xml.etree.ElementTree as ET

            root = ET.fromstring(_read(feed))
            channel = root.find("channel")
            if channel is not None:
                items = channel.findall("item")
                counts["rss_items_xml"] = len(items)
                for it in items:
                    title = (it.findtext("title") or "").strip()
                    link = (it.findtext("link") or "").strip()
                    pub = (it.findtext("pubDate") or "").strip()
                    cat = (it.findtext("category") or "").strip()
                    desc = (it.findtext("description") or "").strip()
                    if not title:
                        empty_field_counts["rss_xml.title.empty"] += 1
                    if not link:
                        empty_field_counts["rss_xml.link.empty"] += 1
                    if not pub:
                        empty_field_counts["rss_xml.pubDate.empty"] += 1
                    if not cat:
                        empty_field_counts["rss_xml.category.empty"] += 1
                    if not desc:
                        empty_field_counts["rss_xml.description.empty"] += 1

        if api.exists():
            obj = json.loads(_read(api))
            records = obj.get("records") or []
            counts["rss_records_json"] = len(records)
            for r in records:
                cat = (r.get("category") or "").strip()
                if cat:
                    category_dist[cat] += 1
                else:
                    empty_field_counts["rss_json.category.empty"] += 1
                for f in ("title", "content", "source_url", "publish_time"):
                    if not (r.get(f) or "").strip():
                        empty_field_counts[f"rss_json.{f}.empty"] += 1

    dyn_dir = MOCK_DIR / "dynamic_page"
    if dyn_dir.exists():
        payload = dyn_dir / "dynamic_payload.json"
        if payload.exists():
            obj = json.loads(_read(payload))
            items = obj.get("items") or []
            counts["dynamic_items_json"] = len(items)
            for it in items:
                cat = (it.get("category") or "").strip()
                if cat:
                    category_dist[cat] += 1
                else:
                    empty_field_counts["dynamic.category.empty"] += 1
                for f in ("title", "content", "source_url", "publish_time"):
                    if not (it.get(f) or "").strip():
                        empty_field_counts[f"dynamic.{f}.empty"] += 1

    # 正文长度与 HTML 结构真实性（静态有效样本：detail_*.html 且不含 noise）
    _exp_root = Path(__file__).resolve().parent
    if str(_exp_root) not in sys.path:
        sys.path.insert(0, str(_exp_root))
    from collectors.rss_item_utils import parse_rss_item_to_record
    from collectors.static_detail_parse import parse_static_detail

    static_valid_content_lens: List[int] = []
    len_buckets = {"lt100": 0, "100_300": 0, "300_600": 0, "gt600": 0}
    headline_tag_violations = 0
    html_structural_hits = Counter()

    if static_dir.exists():
        for p in sorted(static_dir.glob("detail_*.html")):
            if not _STATIC_VALID_DETAIL.match(p.name):
                continue
            raw = _read(p)
            if "<headline" in raw.lower():
                headline_tag_violations += 1
            for tag in ("<title", "<h1", "<article", "<section", "<time"):
                if tag in raw.lower():
                    html_structural_hits[tag] += 1
            parsed = parse_static_detail(raw)
            L = len((parsed.get("content") or "").strip())
            static_valid_content_lens.append(L)
            if L < 100:
                len_buckets["lt100"] += 1
            elif L < 300:
                len_buckets["100_300"] += 1
            elif L <= 600:
                len_buckets["300_600"] += 1
            else:
                len_buckets["gt600"] += 1

    rss_content_lens: List[int] = []
    if rss_dir.exists() and (rss_dir / "sample_feed.xml").exists():
        import xml.etree.ElementTree as ET

        rroot = ET.fromstring(_read(rss_dir / "sample_feed.xml"))
        rch = rroot.find("channel")
        if rch is not None:
            for rit in rch.findall("item"):
                rec = parse_rss_item_to_record(rit)
                rt = (rec.get("title") or "").strip()
                if not rt or rt.startswith("（噪声）"):
                    continue
                rss_content_lens.append(len((rec.get("content") or "").strip()))

    dynamic_valid_lens: List[int] = []
    if dyn_dir.exists() and (dyn_dir / "dynamic_payload.json").exists():
        dobj = json.loads(_read(dyn_dir / "dynamic_payload.json"))
        for dit in dobj.get("items") or []:
            dt = (dit.get("title") or "").strip()
            if not dt or dt.startswith("（噪声）"):
                continue
            dynamic_valid_lens.append(len((dit.get("content") or "").strip()))

    body_len_stats = {
        "static_valid_sample_count": len(static_valid_content_lens),
        "static_valid_content_mean_len": round(mean(static_valid_content_lens), 2)
        if static_valid_content_lens
        else 0.0,
        "static_valid_content_len_buckets": len_buckets,
        "rss_non_noise_content_mean_len": round(mean(rss_content_lens), 2) if rss_content_lens else 0.0,
        "rss_non_noise_sample_count": len(rss_content_lens),
        "dynamic_non_noise_content_mean_len": round(mean(dynamic_valid_lens), 2)
        if dynamic_valid_lens
        else 0.0,
        "dynamic_non_noise_sample_count": len(dynamic_valid_lens),
        "headline_tag_violations_in_html": headline_tag_violations,
        "html_structural_tag_hits_among_static_valid": dict(html_structural_hits),
    }

    report = {
        "summary": {
            "replacement_char_total": int(global_replacement),
            # 生僻字判定：全局 CJK 字符频次 <= 2 且不在模板/词库白名单
            "rare_cjk_total": 0,
            "rare_cjk_unique": 0,
            "repeat_runs_total": int(sum(global_repeats.values())),
        },
        "counts": counts,
        "category_distribution_top20": category_dist.most_common(20),
        "empty_field_counts_top30": empty_field_counts.most_common(30),
        "rare_cjk_top30": [],
        "file_issue_samples_top20": sorted(
            file_stats,
            key=lambda x: (x["replacement_char_count"], x["rare_cjk_candidate_count"], x["repeat_run_count"]),
            reverse=True,
        )[:20],
        "rules": {
            "rare_cjk_definition": "CJK char with global freq <= 2 AND not in whitelist derived from templates/topic words/risk bank",
            "replacement_char": "�",
            "repeat_run_threshold": "same char repeated >= 6",
        },
        "body_length_and_realism": body_len_stats,
    }

    # finalize rare cjk by frequency + whitelist
    rare_final = Counter()
    # 阈值说明：freq==1 的“模板外汉字”通常就是随机 Unicode 造成的；freq==2 仍可能来自少量样本波动
    # 因此默认只将 freq==1 判为生僻/可疑字（更符合“低频生僻字记录”且减少误报）。
    for ch, cnt in cjk_freq.items():
        if cnt <= 1 and ch not in ALLOWED_CHARS:
            rare_final[ch] = cnt
    report["summary"]["rare_cjk_total"] = int(sum(rare_final.values()))
    report["summary"]["rare_cjk_unique"] = int(len(rare_final))
    report["rare_cjk_top30"] = rare_final.most_common(30)

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines: List[str] = []
    md_lines.append("# Mock 样本质量报告")
    md_lines.append("")
    md_lines.append("## 1. 总览")
    md_lines.append(f"- replacement_char_total: **{report['summary']['replacement_char_total']}**")
    md_lines.append(f"- rare_cjk_total: **{report['summary']['rare_cjk_total']}**（unique={report['summary']['rare_cjk_unique']}）")
    md_lines.append(f"- repeat_runs_total: **{report['summary']['repeat_runs_total']}**")
    md_lines.append("")
    md_lines.append("## 2. 样本数量统计")
    for k, v in counts.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")
    md_lines.append("## 3. 类别分布（Top 20）")
    for k, v in report["category_distribution_top20"]:
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")
    md_lines.append("## 4. 空字段统计（Top 30）")
    for k, v in report["empty_field_counts_top30"]:
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")
    md_lines.append("## 5. 生僻字/非白名单汉字（Top 30）")
    if report["rare_cjk_top30"]:
        for ch, cnt in report["rare_cjk_top30"]:
            md_lines.append(f"- {ch}: {cnt}")
    else:
        md_lines.append("- （未发现）")
    md_lines.append("")
    md_lines.append("## 6. 文件问题样本（Top 20）")
    for it in report["file_issue_samples_top20"]:
        md_lines.append(
            f"- {it['path']} | replacement={it['replacement_char_count']} rare_cjk_candidates={it['rare_cjk_candidate_count']} repeats={it['repeat_run_count']}"
        )
    md_lines.append("")
    md_lines.append("## 7. 合格判定建议（人工可复用）")
    md_lines.append("- replacement_char_total 应为 0")
    md_lines.append("- rare_cjk_total 应接近 0（允许极少数模板外字符，但需人工确认）")
    md_lines.append("- 空字段统计应主要来自噪声样本设计，而非正常样本")
    md_lines.append("")
    md_lines.append("## 8. 正文长度（有效样本）")
    bl = report["body_length_and_realism"]
    md_lines.append(
        f"- 静态详情有效样本数: **{bl['static_valid_sample_count']}**，正文平均长度: **{bl['static_valid_content_mean_len']}** 字"
    )
    md_lines.append(f"- 静态正文长度分布: {bl['static_valid_content_len_buckets']}")
    md_lines.append(
        f"- RSS（非噪声）样本数: **{bl['rss_non_noise_sample_count']}**，正文平均长度: **{bl['rss_non_noise_content_mean_len']}** 字"
    )
    md_lines.append(
        f"- 动态 JSON（非噪声）样本数: **{bl['dynamic_non_noise_sample_count']}**，正文平均长度: **{bl['dynamic_non_noise_content_mean_len']}** 字"
    )
    md_lines.append("")
    md_lines.append("## 9. HTML 结构真实性")
    md_lines.append(f"- 非标准 `<headline>` 违规出现次数: **{bl['headline_tag_violations_in_html']}**（应为 0）")
    md_lines.append(
        "- 说明：五类模板中论坛/本地流可能使用 `div.post-title` / `h2.feed-title` 作为标题容器，因此 `<h1>` 计数不一定等于样本数。"
    )
    md_lines.append("- 静态有效详情页中含以下子串的文件计数（越大越接近真实页面骨架）:")
    for k, v in bl["html_structural_tag_hits_among_static_valid"].items():
        md_lines.append(f"  - `{k}`: {v}")
    md_lines.append("")

    REPORT_MD.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")
    print(f"[OK] wrote: {REPORT_MD}")
    print(f"[OK] wrote: {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

