from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path("experiments/crawler_selection_experiment")


TOPICS: List[Tuple[str, List[str]]] = [
    ("公共安全", ["突发事件", "公共场所", "应急处置", "现场通报", "风险提示", "秩序维护"]),
    ("校园舆情", ["高校", "学生", "宿舍", "食堂", "课堂", "校园管理", "通知公告"]),
    ("社会民生", ["社区", "居民", "物业", "供水", "供电", "公共服务", "办事大厅"]),
    ("医疗健康", ["医院", "门诊", "药品", "就诊", "健康提示", "诊疗服务"]),
    ("经济金融", ["企业", "消费者", "平台", "资金", "投资风险", "市场波动"]),
    ("食品安全", ["餐饮店", "食材", "食品抽检", "卫生管理", "消费提醒"]),
    ("自然灾害", ["暴雨", "台风", "地震预警", "积水", "应急避险", "气象提醒"]),
    ("交通出行", ["地铁", "公交", "道路", "拥堵", "交通管制", "出行提示"]),
    ("网络诈骗", ["虚假链接", "冒充客服", "转账风险", "账号异常", "安全提醒"]),
    ("其他", ["网络讨论", "热点话题", "平台反馈", "信息核实", "公众关注"]),
]

SOURCES = [
    "模拟新闻源",
    "模拟政务公告",
    "模拟论坛",
    "模拟社交平台",
    "模拟校园平台",
    "模拟本地生活平台",
    "模拟 RSS 信息源",
]

TITLE_TEMPLATES = [
    "网传某地出现{topic}相关消息引发关注",
    "关于{topic}的网络讨论持续升温",
    "多平台传播{topic}相关信息，官方回应正在核实",
    "有网友反映{topic}问题，相关部门发布提醒",
    "{source}出现{topic}相关话题，评论量持续增加",
]

RISK_BANK = [
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

# 每类 2 段“事件背景/场景切入”，约 100～140 字
INTROS_BY_CAT: Dict[str, List[str]] = {
    "公共安全": [
        "事件背景方面，某地公共场所与秩序管理相关的网络讨论近期增多，部分网民在{source}转发与「{topic}」有关的信息，并称现场情况与网传描述存在差异。由于关键要素尚未经权威渠道逐项核对，本阶段仅将其作为舆情监测样本，不代表事件已被证实。",
        "从传播路径看，与「{topic}」相关的图文信息在多个平台被二次编辑后扩散，标题措辞趋于夸张，容易引发误解。相关部门已提示公众以官方通报为准，避免在事实不清的情况下扩散不确定信息。",
    ],
    "校园舆情": [
        "校园场景方面，某高校周边及校内论坛出现与「{topic}」相关的讨论，学生与家长群体关注度上升。信息来源包括{source}转载、截图拼接与评论区的补充叙述，部分内容与学校正式通知并不一致，需要进一步核实。",
        "学生与家长的关注点主要集中在管理措施、沟通渠道与后续安排等方面。校方如已发布通知公告，应以校内平台为准；若仍处于核实阶段，则应避免将个人猜测当作确定结论对外传播。",
    ],
    "社会民生": [
        "社会民生领域，社区居民在{source}集中讨论与「{topic}」相关的服务体验与诉求表达。讨论中常见“听说”“有人反映”等表述，信息碎片化明显，且不同帖子对时间、地点与责任主体的描述并不一致。",
        "从公共服务角度看，民生类舆情往往涉及多方协同处置。当前样本仅用于测试采集字段解析能力，强调对来源、时间与关键词的结构化抽取，而非对具体纠纷作出判断。",
    ],
    "医疗健康": [
        "医疗健康话题具有较高敏感性。近期在{source}出现与「{topic}」相关的讨论，部分信息引用旧闻或断章取义，容易造成误读。本样本强调“信息核实状态”字段，用于模拟真实采集中对权威发布渠道的依赖。",
        "公众关注点集中在就诊提示、药品说明与健康科普的可信度等方面。样本正文不包含任何可识别个人信息，也不给出未经证实的诊疗结论，仅用于舆情字段抽取实验。",
    ],
    "经济金融": [
        "经济金融类信息在{source}传播时，常伴随“高收益”“紧急处理”等刺激性措辞。与「{topic}」相关的讨论中，部分帖子引用匿名截图或二手转发，真实性难以判断，需要结合平台公告与监管提示综合研判。",
        "消费者与投资者关注点集中在风险提示、平台规则与资金安全等方面。本样本用于模拟结构化字段采集，不提供任何投资建议，也不描述具体违法操作细节。",
    ],
    "食品安全": [
        "食品安全类舆情多与餐饮服务、食材管理与抽检通报相关。{source}出现与「{topic}」相关的讨论后，评论区出现大量情绪化表达，但关键事实仍需以监管部门的公开信息为准。",
        "消费者反馈往往集中在就餐体验、卫生观感与信息来源可信度等方面。样本正文强调“监管核查与消费提醒”，用于测试长文本下的关键词与类别字段抽取稳定性。",
    ],
    "自然灾害": [
        "气象与应急背景下，与「{topic}」相关的提醒信息在{source}快速扩散。部分转发内容夹杂旧图或外地场景，容易误导公众判断，因此需要标注信息核实状态与发布时间。",
        "交通与居民影响方面，讨论集中在出行安排、避险提示与公共服务响应等话题。样本仅模拟舆情文本结构，不包含灾害现场的血腥或刺激性细节描述。",
    ],
    "交通出行": [
        "交通出行类信息常与拥堵、管制与线路调整相关。{source}出现与「{topic}」相关的讨论后，转发链中出现时间表述不一致的情况，需要通过权威渠道交叉验证。",
        "公众关注点集中在通勤影响、绕行建议与官方提示的可获得性等方面。本样本用于测试页面中时间字段、来源字段与正文段落的解析鲁棒性。",
    ],
    "网络诈骗": [
        "网络诈骗类舆情常见套路包括虚假链接、冒充客服与诱导转账等。{source}出现与「{topic}」相关的提醒帖后，评论区出现大量“我也遇到过”的叙述，但其中部分内容无法核验。",
        "平台侧通常会发布安全提醒与账号异常处置指引。样本正文强调防范建议与信息核实，不包含任何可用于实施诈骗的操作细节或个人隐私信息。",
    ],
    "其他": [
        "热点话题在{source}扩散时，往往伴随标签化表达与情绪强化。与「{topic}」相关的讨论中，不同用户对同一事件的描述存在差异，需要结合传播链路进行综合分析。",
        "平台反馈与公众关注叠加后，信息核实压力上升。本样本强调“后续跟踪与风险提示”，用于模拟真实舆情文本中多段落、多信息点的结构。",
    ],
}

# 通用段落：传播 / 核实 / 关注点 / 风险 / 跟踪（每条约 95～130 字）
COMMON_BLOCKS: List[str] = [
    "网络传播情况显示，相关话题在数小时内出现多轮转发，部分账号以截图、拼接长图等方式扩大影响范围。由于转发链中信息被不断改写，原始出处变得模糊，给事实核查带来额外成本。",
    "信息核实状态方面，目前可确认的是：权威部门尚未发布与该话题一一对应的最终结论，部分平台已提示“内容可能存在争议”。因此本系统样本将核实状态标记为待核验，并建议后续持续跟踪官方通报。",
    "公众关注点主要集中在事件真实性、处置进展与对日常生活的影响等方面。评论区亦出现对信息来源可靠性的质疑，以及对谣言治理与平台责任的讨论，体现出舆情热度与观点分化并存。",
    "风险提示方面，建议公众对来源不明、时间不清、要素缺失的帖子保持警惕，不轻信“内部消息”“独家爆料”等话术，更不要基于未经证实的内容做出恐慌性传播或不当行为。",
    "后续跟踪建议以权威发布为准，并结合关键词、发布时间、传播热度与账号行为特征进行综合分析。对于重复出现的相似表述，应关注是否为模板化搬运或营销炒作。",
    "从舆情治理角度看，平台侧可通过公告、置顶说明与举报入口引导用户理性讨论。样本正文仅用于模拟字段抽取场景，不代表对具体事件作出认定。",
    "在数据采集测试中，解析器需要同时处理标题、正文、时间、来源与关键词等字段，并对缺失字段与异常格式保持鲁棒。本段落用于增加正文长度与句子结构多样性。",
    "为降低误判风险，建议将“来源可信度”“时间一致性”“要素完整性”作为基础筛选项。样本数据为受控生成，不指向任何真实个人或具体地址。",
    "部分转发内容存在标题与正文不一致、配图与文字不匹配等问题，属于典型噪声形态。实验用样本通过结构变化模拟此类情况，以检验解析规则的稳定性。",
    "在舆情预警场景中，系统更关注结构化字段是否可稳定抽取，以及异常样本是否可被识别为低可信度。本段落用于补充正文信息量并模拟真实长文本排版。",
    "当多平台同时出现相似关键词时，需要区分“同源扩散”与“独立讨论”。本样本通过固定模板生成可控文本，便于实验复现与结果对比。",
    "对于涉及公共安全的讨论，建议优先引用应急管理与权威媒体的公开信息，并对极端情绪化表达保持审慎。样本不包含血腥、露骨或违法细节化内容。",
    "在信息传播过程中，建议对“独家爆料”“内部流传”等话术保持冷静判断，优先参考权威媒体的详细报道与辟谣说明，避免被情绪化标题误导。",
    "对于涉及救援处置与现场秩序的话题，公众更关注官方通报是否及时、措施是否到位。本样本不包含血腥细节，仅用于字段解析与舆情结构研究。",
]

SHORT_SNIPPETS = [
    "简短摘要：相关信息仍在核实。",
    "简短摘要：条目字段可能缺失或格式不一致。",
    "简短摘要：动态条目字段可能缺失。",
]

RISK_HINT_POOL = [
    "请以权威发布为准，谨慎转发与评论。",
    "警惕标题夸张、来源不明的截图拼接与二次剪辑。",
    "涉及资金与账号操作时，务必通过官方渠道核实，勿轻信诱导链接。",
    "关注官方通报与气象、交通等部门的提示信息，避免误传旧闻。",
    "对“内部消息”“独家爆料”等话术保持审慎，优先核验时间与出处。",
]


def _hx(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _unique_id(i: int, width: int = 4) -> str:
    return str(i).zfill(width)


def _uniq_limit(words: List[str], limit: int) -> List[str]:
    out: List[str] = []
    for w in words:
        w = (w or "").strip()
        if not w:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


def _extract_keywords_from_text(topic_words: List[str], title: str, content: str, limit: int = 8) -> List[str]:
    text = f"{title} {content}"
    hits = [w for w in RISK_BANK if w in text]
    base = topic_words + hits
    return _uniq_limit(base, limit)


def _publish_time_formats(dt: datetime) -> List[str]:
    return [
        dt.strftime("%Y-%m-%d %H:%M"),
        dt.strftime("%Y/%m/%d %H:%M"),
        dt.strftime("%Y-%m-%d %H:%M:%S"),
    ]


def _build_long_body(cat: str, topic: str, source: str, rng: random.Random) -> str:
    intros = INTROS_BY_CAT.get(cat) or INTROS_BY_CAT["其他"]
    paras: List[str] = [rng.choice(intros).format(topic=topic, source=source, cat=cat)]
    n_extra = rng.randint(3, 4)
    paras.extend(rng.sample(COMMON_BLOCKS, k=min(n_extra, len(COMMON_BLOCKS))))
    body = "\n\n".join(paras)
    safety = 0
    while len(body) < 300 and safety < 20:
        paras.append(rng.choice(COMMON_BLOCKS).format(topic=topic, source=source, cat=cat))
        body = "\n\n".join(paras)
        safety += 1
    safety = 0
    while len(body) > 600 and len(paras) > 3 and safety < 30:
        paras = paras[:-1]
        body = "\n\n".join(paras)
        safety += 1
    if len(body) < 300:
        paras.append(rng.choice(COMMON_BLOCKS).format(topic=topic, source=source, cat=cat))
        body = "\n\n".join(paras)
    return body


def _build_summary(body: str, rng: random.Random) -> str:
    if len(body) <= 280:
        s = body.strip()
    else:
        cut = min(260, len(body))
        chunk = body[:cut]
        last = max(chunk.rfind("。"), chunk.rfind("！"), chunk.rfind("？"))
        if last > 120:
            chunk = chunk[: last + 1]
        s = chunk.strip() + "……"
    if len(s) < 150:
        s = s + "后续仍建议持续关注权威发布渠道，并结合关键词与来源进行交叉核验。"
    if len(s) > 300:
        s = s[:297].rstrip() + "……"
    return s


def _body_to_ps_html(body: str) -> str:
    parts = [p.strip() for p in body.split("\n\n") if p.strip()]
    return "\n".join(f"<p>{_hx(p)}</p>" for p in parts)


def _json_ld_news(title: str, iso_time: str, source: str, summary: str) -> str:
    obj = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "datePublished": iso_time,
        "publisher": {"@type": "Organization", "name": source},
        "description": summary[:220],
    }
    return json.dumps(obj, ensure_ascii=False)


def _template_news_portal(
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
    rng: random.Random,
) -> str:
    body_ps = _body_to_ps_html(body)
    kws = "，".join(keywords)
    json_ld = _json_ld_news(title, iso_time, source, summary)
    hot = rng.randint(3, 12)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{_hx(title)} - 模拟新闻源</title>
  <meta name="description" content="{_hx(summary)}" />
  <meta name="keywords" content="{_hx(kws)}" />
  <link rel="canonical" href="{_hx(canonical)}" />
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>
  <header class="site-header"><div class="logo">模拟新闻门户</div><nav class="top-nav">首页 | 国内 | 社会 | 辟谣</nav></header>
  <nav class="breadcrumb">首页 &gt; {_hx(cat)} &gt; 正文</nav>
  <main class="page-main">
    <article class="article">
      <h1 class="article-title">{_hx(title)}</h1>
      <div class="article-meta">
        <span class="source">{_hx(source)}</span>
        <time class="publish-time" datetime="{_hx(iso_time)}">{_hx(display_time)}</time>
        <span class="category">{_hx(cat)}</span>
      </div>
      <section class="article-content">
{body_ps}
      </section>
      <footer class="article-footer">关键词：{_hx(kws)}。原文链接：<a class="permalink" href="{_hx(canonical)}">查看链接</a>。</footer>
    </article>
  </main>
  <aside class="side-rail">热门榜单（模拟）：今日话题 {hot} 条更新</aside>
  <div class="source-url" style="display:none">{_hx(canonical)}</div>
</body>
</html>
"""


def _template_gov_notice(
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
) -> str:
    body_ps = _body_to_ps_html(body)
    kws = "，".join(keywords)
    json_ld = _json_ld_news(title, iso_time, source, summary)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{_hx(title)} - 模拟政务公开</title>
  <meta name="description" content="{_hx(summary)}" />
  <meta name="keywords" content="{_hx(kws)}" />
  <link rel="canonical" href="{_hx(canonical)}" />
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>
  <header class="gov-header"><div class="gov-brand">某市政务公开（模拟）</div></header>
  <main class="page-main">
    <h1 class="notice-title">{_hx(title)}</h1>
    <div class="notice-info">
      <span class="source">信息来源：{_hx(source)}</span>
      <span class="notice-time"><time class="publish-time notice-time" datetime="{_hx(iso_time)}">{_hx(display_time)}</time></span>
      <span class="category">{_hx(cat)}</span>
      <span>责任编辑：模拟编辑组</span>
    </div>
    <div class="notice-body">
{body_ps}
    </div>
    <footer class="article-footer">关键词：{_hx(kws)}。<a class="permalink" href="{_hx(canonical)}">原文链接</a></footer>
  </main>
  <div class="source-url" style="display:none">{_hx(canonical)}</div>
</body>
</html>
"""


def _template_forum_post(
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
    rng: random.Random,
) -> str:
    body_ps = _body_to_ps_html(body)
    kws = "，".join(keywords)
    views = rng.randint(800, 88000)
    comments = rng.randint(0, 3200)
    shares = rng.randint(0, 9000)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{_hx(title)} - 模拟论坛</title>
  <meta name="description" content="{_hx(summary)}" />
  <meta name="keywords" content="{_hx(kws)}" />
  <link rel="canonical" href="{_hx(canonical)}" />
</head>
<body>
  <div class="forum-wrap">
    <div class="post-title">{_hx(title)}</div>
    <div class="post-meta">
      <span class="source">来源：{_hx(source)}</span>
      <time class="publish-time post-time" datetime="{_hx(iso_time)}">{_hx(display_time)}</time>
      <span class="category">{_hx(cat)}</span>
      <span>浏览量：{views}</span><span>评论量：{comments}</span><span>转发量：{shares}</span>
    </div>
    <div class="post-body">
{body_ps}
    </div>
    <div class="post-footer">关键词：{_hx(kws)}。<a class="permalink" href="{_hx(canonical)}">打开原帖</a></div>
  </div>
  <div class="source-url" style="display:none">{_hx(canonical)}</div>
</body>
</html>
"""


def _template_campus(
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
) -> str:
    body_ps = _body_to_ps_html(body)
    kws = "，".join(keywords)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{_hx(title)} - 模拟校园平台</title>
  <meta name="description" content="{_hx(summary)}" />
  <meta name="keywords" content="{_hx(kws)}" />
  <link rel="canonical" href="{_hx(canonical)}" />
</head>
<body>
  <div class="campus-news">
    <h1 class="campus-title">{_hx(title)}</h1>
    <div class="campus-meta">
      <span class="source">{_hx(source)}</span>
      <time class="publish-time campus-time" datetime="{_hx(iso_time)}">{_hx(display_time)}</time>
      <span class="category">{_hx(cat)}</span>
    </div>
    <div class="campus-content">
{body_ps}
    </div>
    <div class="campus-footer">关键词：{_hx(kws)}。<a class="permalink" href="{_hx(canonical)}">公告原文</a></div>
  </div>
  <div class="source-url" style="display:none">{_hx(canonical)}</div>
</body>
</html>
"""


def _template_local_feed(
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
) -> str:
    body_ps = _body_to_ps_html(body)
    kws = "，".join(keywords)
    sum_line = summary.split("。")[0] + "。" if "。" in summary else summary[:80]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{_hx(title)} - 模拟本地生活</title>
  <meta name="description" content="{_hx(summary)}" />
  <meta name="keywords" content="{_hx(kws)}" />
  <link rel="canonical" href="{_hx(canonical)}" />
</head>
<body>
  <div class="local-feed">
    <h2 class="feed-title">{_hx(title)}</h2>
    <div class="feed-summary">{_hx(sum_line)}</div>
    <div class="feed-meta">
      <span class="source">{_hx(source)}</span>
      <time class="publish-time feed-time" datetime="{_hx(iso_time)}">{_hx(display_time)}</time>
      <span class="category">{_hx(cat)}</span>
    </div>
    <div class="feed-content">
{body_ps}
    </div>
    <div class="feed-actions">关键词：{_hx(kws)}。<a class="permalink" href="{_hx(canonical)}">查看详情</a></div>
  </div>
  <div class="source-url" style="display:none">{_hx(canonical)}</div>
</body>
</html>
"""


def _render_static_valid(
    tpl: str,
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    cat: str,
    iso_time: str,
    display_time: str,
    keywords: List[str],
    canonical: str,
    rng: random.Random,
) -> str:
    if tpl == "A":
        return _template_news_portal(
            title=title,
            summary=summary,
            body=body,
            source=source,
            cat=cat,
            iso_time=iso_time,
            display_time=display_time,
            keywords=keywords,
            canonical=canonical,
            rng=rng,
        )
    if tpl == "B":
        return _template_gov_notice(
            title=title,
            summary=summary,
            body=body,
            source=source,
            cat=cat,
            iso_time=iso_time,
            display_time=display_time,
            keywords=keywords,
            canonical=canonical,
        )
    if tpl == "C":
        return _template_forum_post(
            title=title,
            summary=summary,
            body=body,
            source=source,
            cat=cat,
            iso_time=iso_time,
            display_time=display_time,
            keywords=keywords,
            canonical=canonical,
            rng=rng,
        )
    if tpl == "D":
        return _template_campus(
            title=title,
            summary=summary,
            body=body,
            source=source,
            cat=cat,
            iso_time=iso_time,
            display_time=display_time,
            keywords=keywords,
            canonical=canonical,
        )
    return _template_local_feed(
        title=title,
        summary=summary,
        body=body,
        source=source,
        cat=cat,
        iso_time=iso_time,
        display_time=display_time,
        keywords=keywords,
        canonical=canonical,
    )


def _noise_static_html(
    noise_kind: str,
    *,
    title: str,
    content: str,
    source: str,
    cat: str,
    pub: str,
    kw: List[str],
    canonical: str,
) -> str:
    kws = "，".join(kw)
    if noise_kind == "missing_class":
        return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8" /><title>{_hx(title or "噪声")}</title>
<meta name="source" content="{_hx(source)}" /><meta name="publish_time" content="{_hx(pub)}" />
<meta name="category" content="{_hx(cat)}" /><meta name="keywords" content="{_hx(kws)}" /></head>
<body><h1>{_hx(title or "（标题缺失）")}</h1><div class="unknown-body">{_hx(content)}</div>
<div class="source-url">{_hx(canonical)}</div></body></html>"""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8" /><title>{_hx(title or "噪声")}</title>
<meta name="source" content="{_hx(source)}" /><meta name="publish_time" content="{_hx(pub)}" />
<meta name="category" content="{_hx(cat)}" /><meta name="keywords" content="{_hx(kws)}" /></head>
<body><article><h1>{_hx(title or "（标题缺失）")}</h1><div class="article-content">{_hx(content)}</div>
<div class="source-url">{_hx(canonical)}</div></article></body></html>"""


def generate_static_news(per: int, noise_ratio: float, rng: random.Random) -> None:
    out_dir = BASE_DIR / "mock_sources" / "static_news"
    out_dir.mkdir(parents=True, exist_ok=True)
    # 避免与历史生成文件混杂（例如缩小 per-scenario 后旧 detail 页残留）
    for pattern in ("detail_*.html", "list_page_*.html", "list.html"):
        for f in out_dir.glob(pattern):
            try:
                f.unlink()
            except OSError:
                pass

    noise_n = int(per * noise_ratio)
    total_lists = 50
    per_list = max(1, round(per / total_lists))

    base_time = datetime(2026, 4, 1, 8, 0, 0)
    tpl_cycle = ["A", "B", "C", "D", "E"]

    for i in range(1, per + 1):
        cat, words = rng.choice(TOPICS)
        source = rng.choice(SOURCES)
        dt = base_time + timedelta(minutes=i * rng.randint(1, 5))
        pub = rng.choice(_publish_time_formats(dt))
        iso_time = dt.strftime("%Y-%m-%dT%H:%M:%S")
        topic = rng.choice(words)
        title = rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)
        body = _build_long_body(cat, topic, source, rng)
        summary = _build_summary(body, rng)
        kw = _extract_keywords_from_text(words, title, body, limit=8)
        tpl = tpl_cycle[(i - 1) % 5]
        canonical = f"https://example.local/static/{_unique_id(i)}"
        html = _render_static_valid(
            tpl,
            title=title,
            summary=summary,
            body=body,
            source=source,
            cat=cat,
            iso_time=iso_time,
            display_time=pub,
            keywords=kw,
            canonical=canonical,
            rng=rng,
        )
        (out_dir / f"detail_{_unique_id(i)}.html").write_text(html, encoding="utf-8")

    for i in range(1, noise_n + 1):
        idx = _unique_id(i)
        noise_kind = rng.choice(
            [
                "missing_title",
                "missing_content",
                "missing_category",
                "missing_keywords",
                "short_content",
                "missing_class",
            ]
        )
        cat, words = rng.choice(TOPICS)
        source = rng.choice(SOURCES)
        dt = base_time + timedelta(minutes=10_000 + i)
        pub = rng.choice(_publish_time_formats(dt))
        topic = rng.choice(words)
        title = "" if noise_kind == "missing_title" else rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)
        content = "" if noise_kind == "missing_content" else _build_long_body(cat, topic, source, rng)
        if noise_kind == "short_content":
            content = rng.choice(SHORT_SNIPPETS)
        kw = [] if noise_kind == "missing_keywords" else _extract_keywords_from_text(words, title, content, limit=8)
        category = "" if noise_kind == "missing_category" else cat
        canonical = f"https://example.local/static/noise/{idx}"
        meta_cat = category
        nk = "missing_class" if noise_kind == "missing_class" else "normal"
        html = _noise_static_html(
            nk,
            title=title,
            content=content,
            source=source,
            cat=meta_cat,
            pub=pub,
            kw=kw,
            canonical=canonical,
        )
        (out_dir / f"detail_noise_{idx}.html").write_text(html, encoding="utf-8")

    detail_ids = [f"detail_{_unique_id(i)}.html" for i in range(1, per + 1)]
    rng.shuffle(detail_ids)
    for p in range(1, total_lists + 1):
        page_items = detail_ids[(p - 1) * per_list : p * per_list]
        if not page_items:
            break
        lis = "\n".join([f'      <li><a href="{x}">{x}</a></li>' for x in page_items])
        list_html = f"""<!doctype html>
<html lang="zh-CN">
  <head><meta charset="UTF-8" /><title>列表第{p}页 - 模拟新闻源</title></head>
  <body>
    <header class="list-header"><h1>热点列表（模拟）</h1></header>
    <ul class="news-list">
{lis}
    </ul>
  </body>
</html>
"""
        (out_dir / f"list_page_{_unique_id(p, 3)}.html").write_text(list_html, encoding="utf-8")


def _rss_item_xml(
    *,
    title: str,
    link: str,
    pub: str,
    cat: str,
    summary: str,
    body_html: str,
    keywords: List[str],
    include_category: bool = True,
) -> str:
    kws = ",".join(keywords)
    cat_line = f"      <category><![CDATA[{cat}]]></category>\n" if include_category and cat else ""
    return f"""    <item>
      <title><![CDATA[{title}]]></title>
      <link>{_hx(link)}</link>
      <pubDate>{_hx(pub)}</pubDate>
{cat_line}      <keywords><![CDATA[{kws}]]></keywords>
      <description><![CDATA[{summary}]]></description>
      <content:encoded><![CDATA[{body_html}]]></content:encoded>
    </item>"""


def generate_rss_api(per: int, noise_ratio: float, rng: random.Random) -> None:
    out_dir = BASE_DIR / "mock_sources" / "rss_api"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("sample_feed.xml", "sample_api.json"):
        p = out_dir / name
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    noise_n = int(per * noise_ratio)

    base_time = datetime(2026, 4, 1, 9, 0, 0)

    items_xml: List[str] = []
    records_json: List[dict] = []
    seen_links: List[str] = []

    for i in range(1, per + 1):
        cat, words = rng.choice(TOPICS)
        dt = base_time + timedelta(minutes=i)
        pub_variants = [
            dt.strftime("%a, %d %b %Y %H:%M:%S +0800"),
            dt.strftime("%Y-%m-%d %H:%M"),
            dt.strftime("%Y/%m/%d %H:%M"),
        ]
        topic = rng.choice(words)
        source = rng.choice(SOURCES)
        title = rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)
        body = _build_long_body(cat, topic, source, rng)
        summary = _build_summary(body, rng)
        link = f"https://example.local/rss/{i}"
        seen_links.append(link)
        missing_desc = rng.random() < 0.05
        missing_cat = rng.random() < 0.05
        kw = _extract_keywords_from_text(words, title, body, limit=8)
        body_html = _body_to_ps_html(body)
        pub = rng.choice(pub_variants)

        item_xml = _rss_item_xml(
            title=title,
            link=link,
            pub=pub,
            cat=cat,
            summary="" if missing_desc else summary,
            body_html=body_html,
            keywords=kw,
            include_category=not missing_cat,
        )
        items_xml.append(item_xml)

        engagement = rng.randint(200, 120000)
        risk_hint = rng.choice(RISK_HINT_POOL)
        records_json.append(
            {
                "title": title,
                "summary": "" if missing_desc else summary,
                "content": body,
                "source": "模拟 RSS 信息源",
                "source_url": link,
                "publish_time": pub,
                "category": "" if missing_cat else cat,
                "keywords": kw,
                "engagement_count": engagement,
                "risk_hint": risk_hint,
            }
        )

    for i in range(1, noise_n + 1):
        cat, words = rng.choice(TOPICS)
        source = rng.choice(SOURCES)
        topic = rng.choice(words)
        title = "" if rng.random() < 0.2 else f"（噪声）{rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)}"
        body = "" if rng.random() < 0.5 else _build_long_body(cat, topic, source, rng)
        summary = rng.choice(SHORT_SNIPPETS) if not body else _build_summary(body, rng)
        link = "" if rng.random() < 0.4 else rng.choice(seen_links)
        pub = rng.choice(["", "not-a-date", "2026-13-40 99:99"])
        kw: List[str] = []
        body_html = _body_to_ps_html(body) if body else ""
        item_xml = f"""    <item>
      <title><![CDATA[{title}]]></title>
      {'<link>'+_hx(link)+'</link>' if link else ''}
      <pubDate>{_hx(pub)}</pubDate>
      {'<category><![CDATA['+cat+']]></category>' if rng.random() > 0.5 else ''}
      <keywords><![CDATA[]]></keywords>
      <description><![CDATA[{summary}]]></description>
      <content:encoded><![CDATA[{body_html}]]></content:encoded>
    </item>"""
        items_xml.append(item_xml)
        records_json.append(
            {
                "title": title,
                "summary": summary,
                "content": body,
                "source": "模拟 RSS 信息源",
                "source_url": link,
                "publish_time": pub,
                "category": cat if rng.random() > 0.5 else "",
                "keywords": kw,
                "engagement_count": rng.randint(0, 5000),
                "risk_hint": rng.choice(RISK_HINT_POOL),
            }
        )

    feed = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Mock RSS Feed (FACT crawler experiment)</title>
    <link>https://example.local/rss</link>
    <description>受控 RSS mock：含 description 摘要与 content:encoded 全文</description>
{items}
  </channel>
</rss>
""".format(items="\n".join(items_xml))
    (out_dir / "sample_feed.xml").write_text(feed, encoding="utf-8")

    api_obj = {"records": records_json}
    (out_dir / "sample_api.json").write_text(json.dumps(api_obj, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_dynamic_page(per: int, noise_ratio: float, rng: random.Random) -> None:
    out_dir = BASE_DIR / "mock_sources" / "dynamic_page"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("dynamic_payload.json", "dynamic_sample.html"):
        p = out_dir / name
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    noise_n = int(per * noise_ratio)

    base_time = datetime(2026, 4, 1, 10, 0, 0)
    items: List[dict] = []

    for i in range(1, per + 1):
        cat, words = rng.choice(TOPICS)
        dt = base_time + timedelta(minutes=i * 2)
        source = rng.choice(SOURCES)
        topic = rng.choice(words)
        title = rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)
        body = _build_long_body(cat, topic, source, rng)
        summary = _build_summary(body, rng)
        items.append(
            {
                "title": title,
                "summary": summary,
                "content": body,
                "source": source,
                "source_url": f"https://example.local/dynamic/{i}",
                "publish_time": dt.strftime("%Y-%m-%d %H:%M"),
                "category": cat,
                "keywords": _extract_keywords_from_text(words, title, body, limit=8),
                "engagement_count": rng.randint(300, 99000),
                "risk_hint": rng.choice(RISK_HINT_POOL),
            }
        )

    for i in range(1, noise_n + 1):
        cat, words = rng.choice(TOPICS)
        source = rng.choice(SOURCES)
        topic = rng.choice(words)
        body = "" if rng.random() < 0.7 else _build_long_body(cat, topic, source, rng)
        summary = rng.choice(SHORT_SNIPPETS) if not body else _build_summary(body, rng)
        items.append(
            {
                "title": "" if rng.random() < 0.2 else f"（噪声）{rng.choice(TITLE_TEMPLATES).format(topic=topic, source=source)}",
                "summary": summary,
                "content": body,
                "source": source,
                "source_url": "" if rng.random() < 0.7 else f"https://example.local/dynamic/noise/{i}",
                "publish_time": "" if rng.random() < 0.7 else "not-a-date",
                "category": "" if rng.random() < 0.7 else cat,
                "keywords": [] if rng.random() < 0.7 else _extract_keywords_from_text(words, "噪声", summary, limit=5),
                "engagement_count": rng.randint(0, 8000),
                "risk_hint": rng.choice(RISK_HINT_POOL),
            }
        )

    payload = {"items": items}
    (out_dir / "dynamic_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>模拟动态信息流 - FACT</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    .skeleton-line {{ height:12px; background:#eee; margin:8px 0; border-radius:4px; }}
    .card {{ border:1px solid #e5e5e5; border-radius:8px; padding:12px; margin-bottom:12px; }}
    .hidden {{ display:none; }}
    .kw {{ color:#666; font-size:12px; margin-top:6px; }}
  </style>
</head>
<body>
  <header><h1>信息流（模拟）</h1><p class="sub">初始页面为骨架屏，内容由脚本延迟渲染</p></header>
  <div id="skeleton">
    <div class="skeleton-line" style="width:70%"></div>
    <div class="skeleton-line" style="width:90%"></div>
    <div class="skeleton-line" style="width:55%"></div>
  </div>
  <main id="feed-root" class="hidden"></main>
  <section id="load-more" class="hidden">
    <button type="button" disabled>加载更多（模拟，无需交互）</button>
  </section>
  <script>
    function esc(s) {{
      const d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }}
    setTimeout(function() {{
      fetch('./dynamic_payload.json')
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
          var root = document.getElementById('feed-root');
          var sk = document.getElementById('skeleton');
          sk.classList.add('hidden');
          root.classList.remove('hidden');
          var items = (data && data.items) ? data.items : [];
          items.slice(0, 12).forEach(function(it) {{
            var el = document.createElement('article');
            el.className = 'card article-card';
            el.setAttribute('data-id', it.source_url || '');
            var kws = (it.keywords || []).join('，');
            el.innerHTML =
              '<h2 class="card-title">' + esc(it.title || '') + '</h2>' +
              '<div class="card-meta"><span class="src">' + esc(it.source || '') + '</span> · ' +
              '<time>' + esc(it.publish_time || '') + '</time> · <span class="cat">' + esc(it.category || '') + '</span></div>' +
              '<p class="card-summary">' + esc(it.summary || '') + '</p>' +
              '<div class="kw">关键词：' + esc(kws) + '</div>';
            root.appendChild(el);
          }});
          document.getElementById('load-more').classList.remove('hidden');
        }})
        .catch(function() {{
          document.getElementById('skeleton').innerHTML = '<p>加载失败（模拟）</p>';
        }});
    }}, 450);
  </script>
</body>
</html>
"""
    (out_dir / "dynamic_sample.html").write_text(html, encoding="utf-8")


def _quality_corpus_text() -> str:
    chunks: List[str] = []
    chunks.extend(TITLE_TEMPLATES)
    chunks.extend(SOURCES)
    chunks.extend(RISK_BANK)
    for _, ws in TOPICS:
        chunks.extend(ws)
    for lst in INTROS_BY_CAT.values():
        chunks.extend(lst)
    chunks.extend(COMMON_BLOCKS)
    chunks.extend(SHORT_SNIPPETS)
    chunks.extend(RISK_HINT_POOL)
    chunks.append(
        "模拟新闻门户模拟政务公开某市政务公开模拟论坛模拟校园平台模拟本地生活模拟动态信息流骨架屏加载更多"
    )
    return "".join(chunks)


QUALITY_TEXT_CORPUS = _quality_corpus_text()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-scenario", type=int, default=1000)
    ap.add_argument("--noise-ratio", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=20260425)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    generate_static_news(args.per_scenario, args.noise_ratio, rng)
    generate_rss_api(args.per_scenario, args.noise_ratio, rng)
    generate_dynamic_page(args.per_scenario, args.noise_ratio, rng)

    print("[OK] mock samples generated")
    print(f" - static_news: {args.per_scenario} valid + {int(args.per_scenario * args.noise_ratio)} noise")
    print(f" - rss_api: {args.per_scenario} valid + {int(args.per_scenario * args.noise_ratio)} noise")
    print(f" - dynamic_page: {args.per_scenario} valid + {int(args.per_scenario * args.noise_ratio)} noise")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
