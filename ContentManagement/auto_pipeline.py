"""
考公每日学 — 纯爬虫内容管线 (零 API 费用)

流程: 爬取文章 → 规则提取 → 生成每日内容包
用法: python auto_pipeline.py --date 2026-06-03
"""

import json, os, re, sys, argparse
from datetime import datetime, timedelta
from typing import List


# ============================================================
# 规则引擎 — 从文章中提取内容 (替代 LLM)
# ============================================================

def extract_political_sentences(articles: List[dict]) -> List[dict]:
    """从文章中提取符合国考真题风格的政治陈述句"""
    cards = []
    patterns = [
        # 重要会议相关
        r'(党的[^，。]{2,10}全会[^。]{10,60}[。])',
        # 领导人讲话金句
        r'((?:指出|强调|要求)[^。]{15,60}[。])',
        # 政策规范性表述
        r'((?:中国式现代化|共同富裕|高质量发展|新质生产力|改革开放|依法治国|生态文明)[^。]{10,50}[。])',
        # 引号内的核心陈述
        r'[「""]([^「」""]{10,50})[」""]',
        # 数字+成就 (可作论据)
        r'(\d{4}年[^。]{10,60}突破[^。]+[。])',
        # 宪法法律相关
        r'((?:宪法|法律规定|依法)[^。]{15,50}[。])',
    ]

    seen = set()
    for art in articles:
        text = art.get('content', '')
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                s = m if isinstance(m, str) else m[0]
                s = re.sub(r'<[^>]+>', '', s).strip()
                if 15 <= len(s) <= 80 and s not in seen:
                    seen.add(s)
                    # Generate wrong options (simple: swap key terms)
                    wrong = generate_wrong_options(s)
                    cards.append({
                        "statement": s,
                        "wrongOptions": wrong,
                        "tags": infer_tags(s),
                    })
                    if len(cards) >= 7:
                        break
            if len(cards) >= 7:
                break
        if len(cards) >= 7:
            break

    # Fill to 7 if short
    while len(cards) < 2:
        cards.append({
            "statement": "改革开放是决定当代中国命运的关键一招。",
            "wrongOptions": ["改革开放只是经济领域的短期政策。","改革开放主要依靠外部力量推动。","改革开放已不再适应当前发展阶段。"],
            "tags": ["改革开放"],
        })
    return cards[:7]


def generate_wrong_options(correct: str) -> List[str]:
    """简单规则生成干扰项: 替换关键词、反向表达"""
    swaps = [
        ("全体人民", "部分群体"), ("共同富裕", "同步富裕"),
        ("依法治国", "以德治国"), ("高质量发展", "高速增长"),
        ("市场", "政府"), ("必须", "可以不必"),
        ("全面", "部分"), ("坚持", "放弃"),
        ("促进", "限制"), ("保障", "削弱"),
        ("推进", "停止"), ("加强", "减少"),
        ("深化", "放缓"), ("完善", "简化"),
    ]
    wrong = []
    for old, new in swaps:
        if old in correct:
            wrong.append(correct.replace(old, new, 1))
            if len(wrong) >= 3:
                break
    while len(wrong) < 3:
        wrong.append(f"与上述观点相反的表述：{correct[:20]}...并非必要。")
    return wrong[:3]


def infer_tags(text: str) -> List[str]:
    """根据文本内容推断标签"""
    tags = []
    mapping = {
        "中国式现代化": "中国式现代化", "共同富裕": "共同富裕",
        "改革": "改革开放", "开放": "改革开放",
        "二十大": "二十大", "三中全会": "二十届三中全会",
        "宪法": "宪法法律", "依法": "依法治国",
        "新质生产力": "新质生产力", "高质量": "高质量发展",
        "生态": "生态文明", "绿色": "绿色发展",
        "文化": "文化自信", "安全": "国家安全",
        "党": "党的建设",
    }
    for keyword, tag in mapping.items():
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags[:2] or ["时政"]


def extract_daily_words(articles: List[dict]) -> List[dict]:
    """从文章中提取高频词和预测词 (10:5)"""
    # 高频词库 — 国考真题常见词
    high_freq_bank = [
        {"word": "擘画", "pinyin": "bò huà", "definition": "筹划、安排，常指宏观规划",
         "examContext": "常搭配'蓝图'，用于申论大作文宏观论述",
         "commonMistakes": "易误读为bì，正确读音bò", "category": "政治类"},
        {"word": "踔厉奋发", "pinyin": "chuō lì fèn fā", "definition": "精神振奋、斗志昂扬",
         "examContext": "新时代精神状态的标准表述", "commonMistakes": "踔易误写为卓或焯", "category": "政治类"},
        {"word": "行稳致远", "pinyin": "xíng wěn zhì yuǎn", "definition": "稳步前进才能到达远方",
         "examContext": "经济政策常用表述", "commonMistakes": "'致'不可写作'至'", "category": "经济类"},
        {"word": "新质生产力", "pinyin": "xīn zhì shēng chǎn lì", "definition": "以科技创新为主导的先进生产力",
         "examContext": "经济板块必考概念", "commonMistakes": "不可简单等同高科技产业", "category": "经济类"},
        {"word": "守正创新", "pinyin": "shǒu zhèng chuàng xīn", "definition": "坚持正道又勇于创新",
         "examContext": "二十大关键词", "commonMistakes": "需理解'正'与'新'的辩证关系", "category": "文化类"},
        {"word": "赋能", "pinyin": "fù néng", "definition": "赋予能力或能量",
         "examContext": "数字经济热词", "commonMistakes": "不可滥用", "category": "经济类"},
        {"word": "闭环", "pinyin": "bì huán", "definition": "管理流程形成完整回路",
         "examContext": "社会治理常用", "commonMistakes": "注意搭配", "category": "社会类"},
        {"word": "对标", "pinyin": "duì biāo", "definition": "对照标准进行比较改进",
         "examContext": "经济改革常用", "commonMistakes": "与'对比'区分", "category": "经济类"},
        {"word": "牛鼻子", "pinyin": "niú bí zi", "definition": "比喻事物的关键或主要矛盾",
         "examContext": "改革话题常用比喻", "commonMistakes": "非正式书面语慎用", "category": "政治类"},
        {"word": "硬骨头", "pinyin": "yìng gǔ tou", "definition": "比喻艰巨的任务或顽固的问题",
         "examContext": "改革攻坚常用", "commonMistakes": "搭配注意", "category": "政治类"},
    ]

    # 从文章中提取文本
    all_text = " ".join([a.get('content', '') for a in articles[:3]])

    # 检查哪些高频词出现在文章中
    found_high = []
    for w in high_freq_bank:
        if w['word'] in all_text:
            # 提取包含该词的原文句子
            sentences = re.findall(rf'[^。]*{w["word"]}[^。]*[。]', all_text)
            w['sourceSentence'] = sentences[0][:120] if sentences else f'文章中包含"{w["word"]}"'
            w['sourceArticle'] = articles[0].get('source', '人民日报') if articles else '人民日报'
            w['sourceDate'] = datetime.now().strftime('%Y-%m-%d')
            w['isHighFreq'] = True
            found_high.append(w)

    # 预测词: 从文章提取2-4字的高频中文词 (过滤垃圾)
    stop_words = {'可以','通过','进行','一个','这一','这个','不是','已经','没有','目前','同时','此外','因此','所以','而且','但是','然而','如果','虽然','因为','或者','以及','对于','关于','根据','按照','经过','为了','由于','随着','这些','那些','什么','怎么','怎样','如何','其他','其中','主要','重要','必须','需要','应该','能够','可以','可能','一定','一直','已经','正在','将会','更加','比较','非常','特别','十分','尤其','全部','所有','每个','任何','一些','很多','少数','大量','各种','不同','相同','一样','类似','相关','有关','相应','直接','间接','全面','系统','深入','广泛','积极','主动','有效','有力','有序','明显','显著','突出','基本','根本','关键','核心','重点','中心','基础','前提','条件','保障','支撑','推动','促进','加强','加快','加大','提高','提升','增强','完善','健全','建立','构建','推进','深化','落实','贯彻','执行','实施','坚持','持续','不断','逐步','稳步','积极','主动','着力','大力','切实','扎实','深入','全面','统筹','协调','融合','协同','联动','互动','对接','衔接','配套','互补','优化','调整','转变','转型','升级','创新','突破','跨越','赶超','引领','带动','辐射','示范','覆盖','延伸','扩展','扩大','开拓','开辟','打造','培育','壮大','做强','做优','做大','做好','做实','做细','做深','做透',}
    word_freq = {}
    for art in articles[:3]:
        text = art.get('content', '')
        words = re.findall(r'[一-鿿]{2,4}', text)
        for w in words:
            if w not in stop_words and w not in [h['word'] for h in high_freq_bank]:
                word_freq[w] = word_freq.get(w, 0) + 1

    # 选取出现次数>2, 字数=2-4, 不含标点数字的词
    sorted_pred = sorted(word_freq.items(), key=lambda x: -x[1])
    pred_words = []
    for word, count in sorted_pred:
        if len(pred_words) >= 5:
            break
        if count >= 3 and len(word) >= 2 and re.match(r'^[一-鿿]+$', word):
            sentences = re.findall(rf'[^。]*{word}[^。]*[。]', all_text)
            pred_words.append({
                "word": word, "pinyin": "", "definition": f'文中出现{count}次',
                "examContext": "来源于当日文章，预测可能成为考点",
                "commonMistakes": "",
                "sourceSentence": sentences[0][:120] if sentences else f'"{word}"在文章中出现',
                "sourceArticle": articles[0].get('source', '人民日报') if articles else '人民日报',
                "sourceDate": datetime.now().strftime('%Y-%m-%d'),
                "category": "综合", "isHighFreq": False,
            })

    # 补足到10:5比例 (标记为复习词)
    while len(found_high) < 10 and len(found_high) < len(high_freq_bank):
        w = dict(high_freq_bank[len(found_high)])
        w.update({"isHighFreq": True, "sourceSentence": "复习词汇，今日文章中未出现",
            "sourceArticle": "考公词库", "sourceDate": datetime.now().strftime('%Y-%m-%d')})
        found_high.append(w)
    while len(pred_words) < 5:
        pred_words.append({"word": f"储备词{len(pred_words)+1}", "pinyin": "", "definition": "待补充",
            "examContext": "", "commonMistakes": "", "category": "综合", "isHighFreq": False,
            "sourceSentence": "", "sourceArticle": "", "sourceDate": datetime.now().strftime('%Y-%m-%d')})

    return found_high[:10] + pred_words[:5]


def extract_essay_passage(articles: List[dict]) -> dict:
    """从文章中提取结构化申论文段"""
    if not articles:
        return None

    art = articles[0]
    text = art.get('content', '')
    title = art.get('title', '')
    source = art.get('source', '')

    # 词汇积累: 提取引号内的规范用语
    quoted = re.findall(r'[「""]([^「」""]{4,20})[」""]', text)[:5]

    # 论点积累: 找包含"是...的"结构的句子
    arguments_raw = re.findall(r'([^。]{10,40}是[^。]{10,40}[。])', text)[:3]

    # 论据积累: 找数据/数字相关的句子
    evidence_data = re.findall(r'(\d{4}年[^。]{10,80}[。])', text)[:2]
    evidence_quote = quoted[:2] if quoted else []

    return {
        "title": title,
        "source": source,
        "sourcePublishDate": datetime.now().strftime('%Y-%m-%d'),
        "originalExcerpt": text[:800],
        "sections": [
            {"type": "vocabulary", "title": "词汇积累", "items": [
                {"word": w, "contextSentence": "", "explanation": "原文中的规范用语"}
                for w in quoted[:5]
            ]},
            {"type": "argument", "title": "论点积累", "items": [
                {"pointTitle": a[:20], "pointContent": a, "usageGuide": "可用于申论论述"}
                for a in arguments_raw[:3]
            ]},
            {"type": "evidence", "title": "论据积累", "items": [
                {"evidenceType": "data", "content": d, "source": source}
                for d in evidence_data[:2]
            ] + [
                {"evidenceType": "quote", "content": q, "source": source}
                for q in evidence_quote[:1]
            ]},
        ],
        "tags": ["时政"],
        "readingTimeMinutes": 8,
    }


# ============================================================
# 文章抓取
# ============================================================

def fetch_articles() -> List[dict]:
    """抓取当日文章, 爬虫失败时降级为种子文章"""
    try:
        from crawler import fetch_all
        articles = fetch_all()
        if articles:
            return articles
    except Exception as e:
        print(f"  [爬虫] 模块加载失败: {e}")

    print("  [降级] 使用种子文章")
    return [{
        "title": "在进一步全面深化改革中推进中国式现代化",
        "content": """
        党的二十届三中全会对进一步全面深化改革、推进中国式现代化作出战略部署。
        中国式现代化是全体人民共同富裕的现代化。
        发展新质生产力是推动高质量发展的内在要求和重要着力点。
        改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。
        2025年我国GDP突破130万亿元，经济实力实现历史性跃升。
        坚持依法治国，建设社会主义法治国家。守正创新，推动中华优秀传统文化创造性转化。
        要牢牢守住安全底线，以全链条治理防范化解重大风险。
        坚持人民至上，让改革发展成果更多更公平惠及全体人民。
        """,
        "source": "人民日报",
        "url": "",
    }]


# ============================================================
# 主管线
# ============================================================

def generate_daily(target_date: str, output_dir: str = "output") -> dict:
    print(f"\n{'='*60}")
    print(f"  考公每日学 [{target_date}] — 纯爬虫模式")
    print(f"{'='*60}")

    print("[1/3] 抓取文章...")
    articles = fetch_articles()
    print(f"  获取 {len(articles)} 篇")

    print("[2/3] 规则提取政治题 + 词汇...")
    political_cards = extract_political_sentences(articles)
    daily_words = extract_daily_words(articles)
    high_count = sum(1 for w in daily_words if w.get('isHighFreq'))
    pred_count = sum(1 for w in daily_words if not w.get('isHighFreq'))
    print(f"  政治题: {len(political_cards)} 道 | 词汇: {len(daily_words)} ({high_count}:{pred_count})")

    print("[3/3] 申论文段 + 组装...")
    essay = extract_essay_passage(articles)

    main_art = articles[0] if articles else {"title":"", "source":"人民日报", "content":""}
    package = {
        "date": target_date,
        "generatedAt": datetime.now().isoformat(),
        "engine": "rules",
        "politicalTheories": [
            {
                "questionId": f"pt_{target_date}_{i:02d}",
                "questionType": "correct",
                "question": "以下说法正确的是：",
                "options": {
                    "A": c["statement"],
                    "B": c.get("wrongOptions", ["","",""])[0] or "混淆概念的错误表述",
                    "C": c.get("wrongOptions", ["","",""])[1] or "与原文相悖的表述",
                    "D": c.get("wrongOptions", ["","",""])[2] or "逻辑错误的表述",
                },
                "correctAnswer": "A",
                "analysis": f"该陈述来源于原文。",
                "tags": c.get("tags", []),
                "source": main_art["source"],
                "date": target_date,
            }
            for i, c in enumerate(political_cards)
        ],
        "dailyWords": daily_words,
        "essayPassage": essay,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{target_date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    print(f"  → {out_path}")
    return package


def main():
    parser = argparse.ArgumentParser(description="考公每日学 — 纯爬虫管线")
    parser.add_argument("--date", type=str, default=None, help="日期 YYYY-MM-DD")
    parser.add_argument("--output", type=str, default="output", help="输出目录")
    args = parser.parse_args()
    target = args.date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    generate_daily(target, output_dir=args.output)


if __name__ == "__main__":
    main()
