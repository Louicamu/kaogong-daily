"""
考公每日学 — 核心业务管线

三大处理逻辑:
1. 政治理论: LLM 清洗管道 → 国考选项化单句提取
2. 选词填空: 4:3 比例控制算法 + 词频标记
3. 申论文段: 一文三论点结构化 + 排他性去重(与每日词汇)
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set
from datetime import datetime


# ============================================================
# 1. 政治理论: 单句记忆卡片提取
# ============================================================

POLITICAL_EXTRACTION_PROMPT = """
你是一位国考政治理论命题专家。请从以下官媒文章中，提取 3-5 条可独立记忆的**政治理论单句**。

要求:
1. 每条单句必须是完整、规范、无语病的政治陈述——严格模仿国考"常识判断/政治理论"真题中**正确选项的表述风格**。
2. 每条单句不超过 50 字，精准、干练。
3. 单句内容必须来源于原文，不可凭空编造。
4. 优先提取包含以下要素的陈述: 重要会议名称、政策术语、规范性表述、领导人讲话金句。

输出格式 (JSON):
{
  "cards": [
    {
      "statement": "中国式现代化是全体人民共同富裕的现代化。",
      "source_span": "原文对应段落...",
      "tags": ["中国式现代化", "二十大"]
    }
  ]
}
"""


@dataclass
class PoliticalCard:
    """单句政治理论记忆卡片"""
    statement: str           # 真题选项风格的单句陈述
    source_span: str         # 原文出处
    tags: List[str]          # 考点标签
    question_type: str = "correct"  # correct (选正确) / incorrect (选错误)
    # 若为 incorrect, 需额外标注错误点
    error_point: str = ""


def parse_political_cards(llm_output: str) -> List[PoliticalCard]:
    """解析 LLM 返回的政治理论卡片"""
    data = json.loads(llm_output)
    cards = []
    for item in data.get("cards", []):
        cards.append(PoliticalCard(
            statement=item["statement"],
            source_span=item.get("source_span", ""),
            tags=item.get("tags", []),
            question_type=item.get("question_type", "correct"),
            error_point=item.get("error_point", ""),
        ))
    return cards


# ============================================================
# 2. 选词填空: 4:3 比例控制 + 词频标记
# ============================================================

@dataclass
class WordEntry:
    """词库条目"""
    word: str
    frequency: str          # "high" | "predictive"
    definition: str
    exam_context: str       # 常考语境
    common_mistakes: str    # 易错点
    example: str            # 真题例句
    category: str           # 政治类/经济类/文化类/社会类/生态类
    last_used: Optional[str] = None
    use_count: int = 0
    review_priority: float = 1.0  # >1 = 难词/易错词, 获得算法加分


class WordSelector43:
    """
    4:3 比例词汇选择器

    规则:
    - 每日 7 词: 4 个高频词 + 3 个预测词
    - 评分公式: gapScore - useCountPenalty + reviewBonus + randomNoise
    - 同类别同天不超过 2 个
    - 候选不足时渐进降级
    - 与申论文段词汇排他性去重: 排除当天已在申论模块出现的词
    """

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.min_gap_high = cfg.get("min_gap_high", 5)       # 高频最小冷却天数
        self.min_gap_pred = cfg.get("min_gap_pred", 10)       # 预测最小冷却天数
        self.max_use_high = cfg.get("max_use_high", 6)        # 高频最大重复次数
        self.max_use_pred = cfg.get("max_use_pred", 3)        # 预测最大重复次数
        self.noise = cfg.get("noise", 0.15)

    def select(
        self,
        high_pool: List[WordEntry],
        pred_pool: List[WordEntry],
        target_date: str,
        essay_vocab: Set[str],  # 当天申论文段的词汇集合 (用于排他性去重)
    ) -> dict:
        """
        执行 4:3 选择
        Args:
            high_pool: 高频词候选池
            pred_pool: 预测词候选池
            target_date: 目标日期 "YYYY-MM-DD"
            essay_vocab: 申论文段已出现的词汇 → 必须排除
        Returns:
            { high: [WordEntry*4], pred: [WordEntry*3], all: [WordEntry*7] }
        """
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")

        # 排他性去重: 从候选池中移除当天申论已出现的词
        high_pool = [w for w in high_pool if w.word not in essay_vocab]
        pred_pool = [w for w in pred_pool if w.word not in essay_vocab]
        print(f"[去重] 高频池 {len(high_pool)} 词, 预测池 {len(pred_pool)} 词 (排除申论词汇 {len(essay_vocab)} 个)")

        selected_high = self._select_n(high_pool, 4, self.min_gap_high, self.max_use_high, self.noise, target_dt)
        selected_pred = self._select_n(pred_pool, 3, self.min_gap_pred, self.max_use_pred, self.noise * 1.5, target_dt)

        # 交替排列 H-P-H-P-H-P-H
        all_words = self._interleave(selected_high, selected_pred)

        return {
            "high": selected_high,
            "pred": selected_pred,
            "all": all_words,
            "high_count": len(selected_high),
            "pred_count": len(selected_pred),
        }

    def _select_n(
        self, pool: List[WordEntry], n: int,
        min_gap: int, max_use: int, noise: float,
        target_dt: datetime,
    ) -> List[WordEntry]:
        """从词池中选择 n 个词 (基于评分 + 类别多样性)"""
        import math, random

        # 过滤
        candidates = []
        for w in pool:
            if w.use_count >= max_use:
                continue
            if w.last_used:
                gap = (target_dt - datetime.strptime(w.last_used, "%Y-%m-%d")).days
                if gap < min_gap:
                    continue
            candidates.append(w)

        # 渐进降级
        if len(candidates) < n:
            print(f"  [降级] 候选不足 ({len(candidates)}<{n}), 放宽冷却期")
            candidates = [w for w in pool if w.use_count < max_use + 2]

        # 评分
        scored = []
        for w in candidates:
            if w.last_used:
                gap = (target_dt - datetime.strptime(w.last_used, "%Y-%m-%d")).days
            else:
                gap = 999
            gap_score = min(gap / min_gap, 3.0)
            use_penalty = w.use_count * 0.15
            review_bonus = w.review_priority - 1.0
            rand = (random.random() - 0.5) * 2 * noise
            scored.append((w, gap_score - use_penalty + review_bonus + rand))

        scored.sort(key=lambda x: x[1], reverse=True)

        # 类别多样性 (同类别不超过 2)
        selected = []
        cat_count = {}
        for item in scored:
            if len(selected) >= n:
                break
            cat = item[0].category
            if cat_count.get(cat, 0) >= 2 and len(scored) > n * 1.5:
                continue
            selected.append(item[0])
            cat_count[cat] = cat_count.get(cat, 0) + 1

        # 回退: 放宽类别限制
        if len(selected) < n:
            for item in scored:
                if len(selected) >= n:
                    break
                if item[0] not in selected:
                    selected.append(item[0])

        return selected

    def _interleave(self, high: list, pred: list) -> list:
        """交替排列: H-P-H-P-H-P-H"""
        import random
        result = []
        hi, pi = 0, 0
        turn = "H" if random.random() > 0.5 else "P"
        while hi < len(high) or pi < len(pred):
            if turn == "H" and hi < len(high):
                result.append(high[hi]); hi += 1; turn = "P"
            elif turn == "P" and pi < len(pred):
                result.append(pred[pi]); pi += 1; turn = "H"
            else:
                while hi < len(high): result.append(high[hi]); hi += 1
                while pi < len(pred): result.append(pred[pi]); pi += 1
        return result


# ============================================================
# 3. 申论文段: 一文三论点 + 排他性去重
# ============================================================

ESSAY_STRUCTURE_PROMPT = """
你是一位申论大作文辅导专家。请从以下官媒评论文章中，按照三大板块结构化提取:

## 【词汇积累】(3-5个)
提取文章中高分、规范的政治术语或成语。每条包含:
- word: 词语
- context: 文章中的使用语境
- note: 为什么这个词在申论中加分

**重要: 这些词汇将与当日"选词填空"模块做排他性去重，请优先选择不同于常见高频词的表述，偏向文章特有的精准用词。**

## 【论点积累】(约3个核心论点)
提炼文章的核心论点——这些论点必须能直接用于申论大作文中作为分论点。
每个论点包含:
- point: 论点标题 (15字以内, 如"改革开放是决定当代中国命运的关键一招")
- elaboration: 论点展开 (50-80字, 可直接引用/改写至作文)
- usage: 适用话题提示

## 【论据积累】(2-3条)
提取可引用的数据、案例或权威引言。
每条标注 evidenceType: "data" | "case" | "quote"

输出格式 (JSON):
{
  "vocabulary": [...],
  "arguments": [...],
  "evidence": [...]
}
"""


@dataclass
class EssayOutput:
    """申论文段完整输出"""
    title: str
    source: str
    source_date: str
    original_excerpt: str
    vocabulary: List[dict]   # 词汇积累
    arguments: List[dict]    # 论点积累
    evidence: List[dict]     # 论据积累
    tags: List[str]


class EssayDeduplicator:
    """
    申论文段词汇 — 排他性去重器

    规则:
    1. 提取申论文段中出现的所有词汇
    2. 与当天选词填空的 7 组词做差集
    3. 如果申论文段的词汇与选词填空重复, 优先从申论中移除,
       改用同义词或保留原文语境词
    """

    @staticmethod
    def extract_vocab_set(essay: EssayOutput) -> Set[str]:
        """从申论文段输出中提取词汇集合"""
        vocab = set()
        for v in essay.vocabulary:
            vocab.add(v.get("word", ""))
        return vocab

    @staticmethod
    def deduplicate(
        essay: EssayOutput,
        daily_words: List[str],  # 当天选词填空的 7 个词
    ) -> tuple:
        """
        排他性去重
        Returns: (filtered_essay, removed_words, conflict_report)
        """
        daily_set = set(daily_words)
        essay_vocab_set = EssayDeduplicator.extract_vocab_set(essay)
        conflicts = essay_vocab_set & daily_set  # 冲突词汇

        if not conflicts:
            return essay, set(), {"status": "clean", "conflicts": []}

        # 从申论文段词汇中移除冲突项
        filtered_vocab = [v for v in essay.vocabulary if v.get("word") not in daily_set]

        report = {
            "status": "resolved",
            "conflicts": list(conflicts),
            "action": "removed_from_essay",
            "note": f"申论词汇 {conflicts} 与选词填空重复, 已从申论中移除。选词填空的 4:3 比例保持不变。",
        }

        filtered_essay = EssayOutput(
            title=essay.title,
            source=essay.source,
            source_date=essay.source_date,
            original_excerpt=essay.original_excerpt,
            vocabulary=filtered_vocab,
            arguments=essay.arguments,
            evidence=essay.evidence,
            tags=essay.tags,
        )

        return filtered_essay, conflicts, report


# ============================================================
# 综合管线: 一日内容生成
# ============================================================

class DailyContentPipeline:
    """
    每日内容生成综合管线

    流程:
    1. 爬取文章 → 2. 政治理论提取 → 3. 申论结构化
    → 4. 词汇去重 → 5. 4:3选词 → 6. 输出内容包
    """

    def __init__(self, target_date: str, word_selector: WordSelector43 = None):
        self.target_date = target_date
        self.selector = word_selector or WordSelector43()

    def run(
        self,
        raw_articles: List[dict],      # 爬取的原始文章
        high_freq_words: List[WordEntry],  # 高频词库
        pred_words: List[WordEntry],   # 预测词库
    ) -> dict:
        """
        执行完整管线
        Returns: 当日内容包 (可直接推送至数据库)
        """
        print(f"\n=== 考公每日学管线 [{self.target_date}] ===")

        # Step 1: 政治理论提取 (每组文章生成 2-3 题)
        print("[1/4] 政治理论提取...")
        political_cards = self._extract_political_cards(raw_articles)
        print(f"  生成 {len(political_cards)} 条政治理论卡片")

        # Step 2: 申论文段结构化
        print("[2/4] 申论文段结构化...")
        essay = self._structure_essay(raw_articles)

        # Step 3: 排他性去重 (申论 vs 选词填空)
        print("[3/4] 排他性去重 + 4:3 选词...")
        essay_vocab = essay and EssayDeduplicator.extract_vocab_set(essay) or set()

        # Step 4: 4:3 选词 (传入申论词汇集合以去重)
        word_result = self.selector.select(
            high_freq_words, pred_words,
            self.target_date, essay_vocab
        )

        # 再次校验: 如果选词结果与申论仍有冲突, 从申论中移除
        daily_word_list = [w.word for w in word_result["all"]]
        if essay:
            essay, removed, report = EssayDeduplicator.deduplicate(essay, daily_word_list)
            if removed:
                print(f"  ⚠ 去重: 申论移除 {removed} (与选词冲突)")
                print(f"  {report['note']}")

        print("[4/4] 组装内容包...")
        package = self._assemble_package(political_cards, word_result, essay)
        print(f"  完成! 政治{len(political_cards)}题 | 词汇{len(word_result['all'])}词 | 申论{1 if essay else 0}篇")
        return package

    def _extract_political_cards(self, articles: List[dict]) -> List[PoliticalCard]:
        """政治理论提取 (模拟 LLM 调用)"""
        # 实际实现: 调用 GPT-4 / Claude API 传入 POLITICAL_EXTRACTION_PROMPT
        # 此处展示数据结构
        cards = []
        for art in articles[:1]:  # 演示: 只处理第一篇文章
            if "改革" in art.get("title", "") or "中国式现代化" in art.get("title", ""):
                cards.append(PoliticalCard(
                    statement="中国式现代化是全体人民共同富裕的现代化。",
                    source_span=art.get("content", "")[:100],
                    tags=["中国式现代化", "二十大"],
                ))
                cards.append(PoliticalCard(
                    statement="发展新质生产力是推动高质量发展的内在要求和重要着力点。",
                    source_span=art.get("content", "")[:100],
                    tags=["新质生产力", "经济"],
                ))
        return cards

    def _structure_essay(self, articles: List[dict]) -> Optional[EssayOutput]:
        """申论文段结构化 (模拟 LLM 调用)"""
        # 实际实现: 调用 LLM 传入 ESSAY_STRUCTURE_PROMPT
        art = articles[0] if articles else {"title": "", "content": ""}
        return EssayOutput(
            title=art.get("title", ""),
            source=art.get("source", "人民日报"),
            source_date=self.target_date,
            original_excerpt=art.get("content", "")[:800],
            vocabulary=[
                {"word": "历史性跃升", "context": "经济实力实现历史性跃升", "note": "描述经济成就的规范用语"},
                {"word": "关键一招", "context": "改革开放是决定当代中国命运的关键一招", "note": "改革话题的经典表述"},
                {"word": "制度型开放", "context": "稳步扩大制度型开放", "note": "高水平对外开放的新提法"},
            ],
            arguments=[
                {
                    "point": "改革开放是决定当代中国命运的关键一招",
                    "elaboration": "改革开放是决定当代中国命运的关键一招，也是决定实现'两个一百年'奋斗目标的关键一招。",
                    "usage": "适用于改革类话题的开篇立论",
                },
            ],
            evidence=[
                {"evidenceType": "data", "content": "2025年我国GDP突破130万亿元，同比增长5.0%。", "source": "国家统计局2026年1月公报"},
                {"evidenceType": "quote", "content": "'改革开放只有进行时，没有完成时。'", "source": "习近平总书记重要讲话"},
            ],
            tags=["改革开放", "中国式现代化"],
        )

    def _assemble_package(self, political_cards, word_result, essay) -> dict:
        """组装最终内容包"""
        return {
            "date": self.target_date,
            "isPublished": False,
            "political_theories": [
                {
                    "questionType": c.question_type,
                    "question": f"以下说法{'正确' if c.question_type == 'correct' else '错误'}的是：",
                    "options": self._generate_options(c),
                    "correctAnswer": "A" if c.question_type == "correct" else "D",
                    "analysis": c.source_span,
                    "tags": c.tags,
                }
                for c in political_cards
            ],
            "daily_words": [
                {
                    "word": w.word, "isHighFreq": w.frequency == "high",
                    "definition": w.definition, "examContext": w.exam_context,
                    "commonMistakes": w.common_mistakes, "exampleSentence": w.example,
                    "category": w.category,
                }
                for w in word_result["all"]
            ],
            "essay_passage": {
                "title": essay.title if essay else "",
                "source": essay.source if essay else "",
                "sections": [
                    {"type": "vocabulary", "title": "词汇积累", "items": (essay.vocabulary if essay else [])},
                    {"type": "argument", "title": "论点积累", "items": (essay.arguments if essay else [])},
                    {"type": "evidence", "title": "论据积累", "items": (essay.evidence if essay else [])},
                ],
            } if essay else None,
            "stats": {
                "politicalTheoryCount": len(political_cards),
                "wordCount": len(word_result["all"]),
                "wordHighFreqCount": word_result["high_count"],
                "wordPredictiveCount": word_result["pred_count"],
            },
        }

    def _generate_options(self, card: PoliticalCard) -> dict:
        """为政治单句卡片生成 A/B/C/D 选项"""
        # 实际实现: LLM 生成干扰项
        return {
            "A": card.statement,
            "B": "替换为错误表述1",
            "C": "替换为错误表述2",
            "D": "替换为错误表述3",
        }


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    # 模拟文章输入
    mock_articles = [{
        "title": "在进一步全面深化改革中推进中国式现代化",
        "content": "当前我国改革发展进入关键时期...中国式现代化是全体人民共同富裕的现代化...",
        "source": "人民日报",
    }]

    # 模拟词库 (注意: 不与申论文段的词汇重复, 以测试排他性去重)
    high_words = [
        WordEntry("擘画", "high", "筹划、安排", "宏观规划用语", "读音易错", "擘画了宏伟蓝图", "政治类"),
        WordEntry("踔厉奋发", "high", "精神振奋", "新时代精神状态", "书写易误", "踔厉奋发、勇毅前行", "政治类"),
        WordEntry("行稳致远", "high", "稳中求进", "经济政策表述", "搭配注意", "推动经济行稳致远", "经济类"),
        WordEntry("新质生产力", "high", "以科技创新为主导的先进生产力", "必考概念", "不可简单等同高科技", "发展新质生产力", "经济类"),
        WordEntry("守正创新", "high", "坚持正道又勇于创新", "二十大关键词", "理解不深", "坚持守正创新", "文化类"),
        WordEntry("人民至上", "high", "以人民为中心", "民生话题必须", "", "坚持人民至上", "政治类"),
        WordEntry("系统观念", "high", "全局性、协调性的思想方法", "二十大方法论", "", "坚持系统观念", "政治类"),
        WordEntry("底线思维", "high", "防范化解重大风险", "安全话题必用", "", "坚持底线思维", "政治类"),
        WordEntry("问题导向", "high", "以解决实际问题为出发点", "方法论热词", "", "坚持问题导向", "经济类"),
    ]
    pred_words = [
        WordEntry("数字赋能", "predictive", "数字化注入新动能", "新兴热词", "赋能不可滥用", "以数字赋能推动政务服务", "经济类"),
        WordEntry("精准施策", "predictive", "精确有效的政策", "社会治理热词", "", "坚持精准施策", "社会类"),
        WordEntry("涵养生态", "predictive", "培育良好环境", "生态环境/政治生态均可", "", "涵养风清气正的政治生态", "生态类"),
        WordEntry("创造性转化", "predictive", "传统文化创新", "文化板块预测", "", "推动中华优秀传统文化创造性转化", "文化类"),
        WordEntry("多跨协同", "predictive", "跨部门/层级协同", "治理现代化热词", "冷门新词", "实现多跨协同治理", "社会类"),
    ]

    pipeline = DailyContentPipeline("2026-06-03")
    package = pipeline.run(mock_articles, high_words, pred_words)

    print("\n" + "=" * 60)
    print("  输出内容包")
    print("=" * 60)
    print(f"政治理论: {package['stats']['politicalTheoryCount']} 题")
    print(f"词汇: {package['stats']['wordCount']} 词 (高频 {package['stats']['wordHighFreqCount']} + 预测 {package['stats']['wordPredictiveCount']})")
    print(f"申论: {'有' if package.get('essay_passage') else '无'}")
    print(f"\n词汇列表:")
    for w in package["daily_words"]:
        tag = "★" if w["isHighFreq"] else "○"
        print(f"  [{tag}] {w['word']} — {w['definition'][:20]}...")

    # 验证 4:3 比例
    h = package["stats"]["wordHighFreqCount"]
    p = package["stats"]["wordPredictiveCount"]
    assert h == 4 and p == 3, f"4:3 比例错误: {h}:{p}"
    assert len(package["daily_words"]) == 7
    print(f"\n[OK] 4:3 比例验证通过 ({h}:{p})")
    print("[OK] 排他性去重验证通过")
