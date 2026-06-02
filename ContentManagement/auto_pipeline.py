"""
考公每日学 — 全自动内容生成管线

双引擎:
  - DeepSeek API (默认, 免费500万tokens, OpenAI兼容)
  - Ollama 本地 (离线备用)

用法:
  python auto_pipeline.py --date 2026-06-03            # 生成一天
  python auto_pipeline.py --batch 30                   # 批量生成30天
  python auto_pipeline.py --date 2026-06-03 --ollama   # 用本地Ollama
"""

import json, os, re, sys, time, argparse, hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from urllib.request import Request, urlopen


# ============================================================
# 双引擎 LLM 客户端
# ============================================================

class LLM:
    """统一 LLM 接口: DeepSeek API / Ollama 本地"""

    def __init__(self, engine: str = "deepseek"):
        self.engine = engine

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        if self.engine == "ollama":
            return self._ollama(prompt, temperature, max_tokens)
        return self._deepseek(prompt, temperature, max_tokens)

    def _deepseek(self, prompt: str, temperature: float, max_tokens: int) -> str:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY 未设置")

        body = json.dumps({
            "model": "deepseek-v4-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")

        req = Request("https://api.deepseek.com/v1/chat/completions", data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })
        resp = json.loads(urlopen(req, timeout=120).read())
        return resp["choices"][0]["message"]["content"]

    def _ollama(self, prompt: str, temperature: float, max_tokens: int) -> str:
        body = json.dumps({
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }).encode("utf-8")
        req = Request("http://localhost:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urlopen(req, timeout=300).read())
        return resp.get("response", "")


# ============================================================
# 统一提示词 — 一次调用产出全部模块
# ============================================================

UNIFIED_PROMPT = """你是国考备考内容专家。从以下当日新闻文章中，一次性生成三个模块的学习内容。

===== 文章 =====
{articles}

===== 模块一：政治理论选择题 (7题，全部来源于当日文章) =====

严格参照国考"常识判断-政治理论"和各省省考"政治理论"板块的命题规律：
  ① 题型: 单选题，判断"以下说法正确/错误的是"，每题4选项(A/B/C/D)
  ② 来源: 每题的正确答案必须能从当日文章中直接找到依据
  ③ 干扰项设计 (核心——达到国考真题难度，每个干扰项独立看都应"好像是对的"):
             严格禁止: 以下词汇在干扰项中绝对不能出现——
             "唯一""只""只有""只能""全部""所有""完全""彻底""全面取消"
             "无关""不重要""次要""不必""无需""不必考虑""可忽略""无足轻重"
             这些词汇会让考生一眼排除干扰项，破坏真题难度。

             正确做法: 用"半真半假"替代"绝对化"——
             错误示范: "法治是民营企业的唯一保障" (一眼假)
             正确示范: "法治对民营企业的作用主要体现在事后纠纷解决，事前预防不是法治的重点"
             → 这句话听起来是合理的——法治确实在纠纷解决中很重要，只是悄悄把"事前预防"也排除了

             错误示范: "所有生态补偿资金全部来自中央" (一眼假)
             正确示范: "生态补偿资金以中央财政转移支付为主体，地方配套资金为辅"
             → 听起来像是一句真实的政策描述，只把"以...为主体，...为辅"的关系悄悄拔高成"只靠中央"

             技法一：半真半假与概念偷换 (最隐蔽)
             前半句是官方原话、政治正确，后半句在"路径、手段、方向"上微调偷换。
             真题示例: "推动优质文化资源向沿海发达地区集中，促进公共文化服务差异化发展"
             → 用"差异化"这种看似高端的词汇，偷换了"补短板、均等化"的真实政策导向。

             技法二：主体错位与张冠李戴
             把"市场"的职责安给"政府"，或把"理论创新"和"实践创新"的引领关系倒置。
             真题示例: "充分发挥政府在资源配置中的决定性作用"
             → 正确表述是市场起决定性作用，政府更好发挥作用。

             技法三：一以贯之的宏观概念错位 (历史跨度陷阱)
             利用跨越几十年的宏观概念进行混淆，欺骗对历史节点不敏感的考生。
             真题示例: "从第一个五年计划到当前五年规划，一以贯之的主题是把我国建设成为社会主义现代化国家"
             → 实际上不同时期主题有演变，并非一成不变。

             技法四：绝对化表述与手段唯一化
             在政策实施路径中使用"唯一途径""彻底解决""全面取代"等词汇，
             违背政治理论中"统筹兼顾、循序渐进"的辩证法原则。
  ④ 覆盖面: 7题应尽量覆盖以下方向 (每方向0-2题):
     - 重要会议精神 (二十大/二十届三中全会等)
     - 习近平新时代中国特色社会主义思想
     - 党史重大事件与经验
     - 宪法法律基本知识
     - 宏观经济政策 (高质量发展/新质生产力/共同富裕)
     - 文化自信与社会治理
     - 生态文明与绿色发展

规则:
1. correctStatement: 从文章中摘录或精准改写，一句完整规范的政治陈述，≤50字
2. wrongOptions: 3个干扰项，与正确选项句式、长度高度一致，内容看似有理实则有误
3. tags: 标注考点方向，如 ["二十大", "共同富裕"]
4. 必须在文章中找到对应依据，不得凭空编造
5. 输出前逐项自检: 每个干扰项是否包含禁止词汇？是否\"半真半假\"而非绝对化？独立读一遍是否像真话？
6. 自检标准: 合格的干扰项应让考生\"知道它可能是对的，但不能确定它一定对\"
7. 如果干扰项仍出现\"唯一\"\"只\"\"全部\"\"完全\"\"所有\"等词，必须重新生成

===== 模块二：选词填空 (15词，严格10:5比例) =====
词形限制:
  - 四字成语: 擘画、踔厉奋发、行稳致远、守正创新、疏堵结合
  - 两字词语: 赋能、闭环、对标、赛道、韧性
  - 三字比喻词: 牛鼻子、试验田、硬骨头、先手棋、最后一公里
  禁止: 超过4个字的长句、含数字的政策条文、非词语的短语解释

高频词(10个, isHighFreq=true):
  历年国考真题中反复出现的成语/词语/比喻词，考生必须掌握。
  例如: 擘画、踔厉奋发、行稳致远、新质生产力、闭环、对标、牛鼻子、硬骨头

预测词(5个, isHighFreq=false):
  近期官方文章中出现的生僻/冷门但规范的词语，未来可能出现在考题中。
  例如: 沙盒监管、全链条、制度型开放、先立后破、微治理
  特征: 使用频率低于高频词，考生容易忽视，但规范性和精准度高

每个词必须包含: word, pinyin, definition(简洁释义), examContext(国考中怎么考), commonMistakes(考生易犯错误), category(政治类/经济类/文化类/社会类/生态类)
重要: 三个模块之间词汇不得重复

===== 间隔重复复习 =====
- 在 dailyWords 中, 纳⼊ 2-3 个国考长期高频词汇作为自然复习 (如"中国式现代化""新质生产力""共同富裕"等)
- 这些词应与前几日词汇表有重叠, 以帮助考生通过间隔重复加深记忆
- 标记方式: 在相应词条中添加 "isReview": true 字段
- 其余 13-14 个词照常生成, 保持 10:5 比例

===== 模块三：申论文段结构化 (1篇) =====
规则:
1. vocabulary(3-5个): 文章中的规范政治用语，附原文语境和加分原因
2. arguments(约3个): 核心论点≤15字 + 展开论述50-80字 + 适用话题
3. evidence(2-3条): 数据/案例/引言，标注evidenceType

===== 返回格式 (纯JSON，不要markdown) =====
{{
  "politicalTheories": [
    {{
      "correctStatement": "正确陈述",
      "wrongOptions": ["干扰项1","干扰项2","干扰项3"],
      "tags": ["考点标签"]
    }}
  ],
  "dailyWords": [
    {{"word":"擘画","pinyin":"bò huà","definition":"筹划、安排","examContext":"常与'蓝图'搭配, 用于宏观规划类选项","commonMistakes":"易误读为bì, 正确读音bò","category":"政治类","isHighFreq":true,"isReview":false}},
    ...共15个: 10个isHighFreq=true(高频), 5个isHighFreq=false(预测); 其中2-3个词设置isReview=true
  ],
  "essayPassage": {{
    "title": "文章标题",
    "source": "来源",
    "vocabulary": [{{"word":"词","context":"原文语境","note":"加分原因"}}],
    "arguments": [{{"point":"论点","elaboration":"展开50-80字","usage":"适用话题"}}],
    "evidence": [{{"evidenceType":"data|case|quote","content":"...","source":"出处"}}]
  }}
}}

请严格遵守10:5比例(10个高频+5个预测=15个词)，确保isHighFreq字段准确"""


def build_unified_prompt(articles: List[dict]) -> str:
    """拼接多篇文章到一个 prompt"""
    parts = []
    for i, art in enumerate(articles[:3]):
        parts.append(f"[文章{i+1}] 来源:{art.get('source','')} 标题:{art.get('title','')}\n{art.get('content','')[:2000]}")
    return UNIFIED_PROMPT.replace("{articles}", "\n\n".join(parts))


# ============================================================
# 文章来源 (四大官媒爬虫 + 种子降级)
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

    # 最终降级: 种子文章 (保证管线不断)
    print("  [降级] 使用种子文章")
    return [{
        "title": "在进一步全面深化改革中推进中国式现代化",
        "content": """
        党的二十届三中全会对进一步全面深化改革、推进中国式现代化作出战略部署。
        中国式现代化是全体人民共同富裕的现代化，是物质文明和精神文明相协调的现代化。
        发展新质生产力是推动高质量发展的内在要求和重要着力点。
        改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。
        2025年我国GDP突破130万亿元，经济实力实现历史性跃升。
        """,
        "source": "人民日报",
        "url": "",
    }]


# ============================================================
# JSON 解析器
# ============================================================

def parse_json(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {}


# ============================================================
# 主管线
# ============================================================

def generate_daily(target_date: str, llm: LLM, output_dir: str = "output") -> dict:
    """统一管线: 一次LLM调用产出政治题 + 15词(10:5) + 申论文段"""
    print(f"\n{'='*60}")
    print(f"  [{target_date}] 生成中...")
    print(f"{'='*60}")

    # 1. 抓取文章
    print("[1/2] 抓取文章...")
    articles = fetch_articles()
    print(f"  获取 {len(articles)} 篇文章")

    # 2. 统一 LLM 调用
    print("[2/2] LLM 生成 (政治题 + 15词 + 申论)...")
    prompt = build_unified_prompt(articles)
    try:
        raw = llm.generate(prompt, temperature=0.3, max_tokens=4096)
        data = parse_json(raw)
    except Exception as e:
        print(f"  [LLM失败] {e}")
        data = {}

    # 解析政治理论
    all_cards = []
    for c in data.get("politicalTheories", []):
        all_cards.append({
            "statement": c.get("correctStatement", ""),
            "wrongOptions": c.get("wrongOptions", []),
            "tags": c.get("tags", []),
        })
    print(f"  政治题: {len(all_cards)} 道")

    # 解析每日词汇 (10:5)
    daily_words = data.get("dailyWords", [])
    high_count = sum(1 for w in daily_words if w.get("isHighFreq"))
    pred_count = sum(1 for w in daily_words if not w.get("isHighFreq"))
    print(f"  词汇: {len(daily_words)} 个 (高频{high_count} + 预测{pred_count})")
    if high_count != 10 or pred_count != 5:
        print(f"  ⚠ 10:5 比例偏离! 实际 {high_count}:{pred_count}，进行修正...")
        daily_words = _enforce_ratio(daily_words, 10, 5)

    # 解析申论文段
    essay = data.get("essayPassage", {})
    print(f"  申论: {len(essay.get('vocabulary',[]))}词 {len(essay.get('arguments',[]))}论点 {len(essay.get('evidence',[]))}论据")

    # 排他性去重: 申论词汇 vs 选词填空词汇
    daily_word_set = {w["word"] for w in daily_words}
    essay_vocab = essay.get("vocabulary", [])
    conflicts = [v for v in essay_vocab if v.get("word") in daily_word_set]
    if conflicts:
        print(f"  [去重] 申论移除 {len(conflicts)} 个重复词: {[c['word'] for c in conflicts]}")
        essay["vocabulary"] = [v for v in essay_vocab if v["word"] not in daily_word_set]

    # 组装
    main_art = articles[0] if articles else {"title":"", "source":"", "content":""}
    package = {
        "date": target_date,
        "generatedAt": datetime.now().isoformat(),
        "engine": "deepseek" if os.environ.get("DEEPSEEK_API_KEY") else "fallback",
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
                "analysis": "选项A的陈述准确反映了原文精神。",
                "tags": c.get("tags", []),
                "source": main_art["source"],
                "date": target_date,
            }
            for i, c in enumerate(all_cards)
        ],
        "dailyWords": daily_words,
        "essayPassage": {
            "title": main_art["title"],
            "source": main_art["source"],
            "sourcePublishDate": target_date,
            "originalExcerpt": main_art.get("content", "")[:500],
            "sections": [
                {"type": "vocabulary", "title": "词汇积累", "items": essay.get("vocabulary", [])},
                {"type": "argument", "title": "论点积累", "items": essay.get("arguments", [])},
                {"type": "evidence", "title": "论据积累", "items": essay.get("evidence", [])},
            ],
            "tags": [t for c in all_cards for t in c.get("tags", [])],
            "readingTimeMinutes": 8,
        },
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{target_date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    print(f"  → {out_path}")
    return package


def _enforce_ratio(words: list, target_high: int, target_pred: int) -> list:
    """强制修正10:5比例: 不足则标记预测词为高频, 超出则降级"""
    high = [w for w in words if w.get("isHighFreq")]
    pred = [w for w in words if not w.get("isHighFreq")]
    # 高频不够 → 从预测词中升级
    while len(high) < target_high and pred:
        w = pred.pop(0); w["isHighFreq"] = True; high.append(w)
    # 高频过多 → 降级到预测
    while len(high) > target_high:
        w = high.pop(); w["isHighFreq"] = False; pred.insert(0, w)
    # 预测不够 → 补充
    while len(pred) < target_pred:
        pred.append({"word": f"储备词{len(pred)+1}", "isHighFreq": False, "pinyin": "", "definition": "待补充", "examContext": "", "commonMistakes": "", "category": "政治类"})
    # 预测过多 → 截断
    pred = pred[:target_pred]
    return high + pred


def batch_generate(start_date: str, days: int, llm: LLM):
    """批量生成多天"""
    d = datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(days):
        date_str = (d + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            generate_daily(date_str, llm)
        except Exception as e:
            print(f"  [ERROR] {date_str}: {e}")
        time.sleep(1)  # API 限速


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="考公每日学 — 自动内容生成")
    parser.add_argument("--date", type=str, default=None, help="日期 YYYY-MM-DD")
    parser.add_argument("--batch", type=int, default=0, help="批量生成N天")
    parser.add_argument("--ollama", action="store_true", help="使用本地Ollama")
    parser.add_argument("--output", type=str, default="output", help="输出目录")
    args = parser.parse_args()

    engine = "ollama" if args.ollama else "deepseek"
    llm = LLM(engine=engine)

    if args.batch > 0:
        start = args.date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        batch_generate(start, args.batch, llm)
    else:
        target = args.date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        generate_daily(target, llm, output_dir=args.output)


if __name__ == "__main__":
    main()
