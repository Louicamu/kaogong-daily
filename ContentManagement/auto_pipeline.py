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
            "model": "deepseek-chat",
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
# 提示词
# ============================================================

def political_prompt(article_text: str) -> str:
    return f"""你是国考政治理论命题专家。从以下文章提取 2 条政治理论选择题。

规则:
1. 每条题包含1个正确陈述(correctStatement)+ 3个干扰选项(wrongOptions)
2. 正确陈述严格模仿国考"常识判断"正确选项表述, 来源于原文, 不超过50字
3. 干扰项必须看似合理但实际有误——如: 偷换概念、张冠李戴、用词绝对化
4. 必须确保正确陈述和干扰项在句式上风格一致

文章:
{article_text[:2500]}

返回纯JSON (不要markdown):
{{"cards":[
  {{
    "correctStatement": "原文中的正确陈述",
    "wrongOptions": ["错误但看似合理的选项1", "错误选项2", "错误选项3"],
    "tags": ["考点标签"]
  }}
]}}"""


def essay_prompt(article_text: str, existing_words: List[str]) -> str:
    words_str = "、".join(existing_words) if existing_words else "无"
    return f"""你是申论大作文辅导专家。从以下文章提取结构化内容。

文章:
{article_text[:2500]}

规则:
1. 词汇积累(3-5个): 提取高分规范政治用语。**必须排除以下词汇(已在选词填空模块出现): {words_str}**
2. 论点积累(约3个): 核心论点, 每个≤15字, 附带展开论述和适用话题
3. 论据积累(2-3条): 数据/案例/引言, 标注类型

返回纯JSON:
{{"vocabulary":[{{"word":"词","context":"原文语境","note":"加分原因"}}],"arguments":[{{"point":"论点","elaboration":"展开50-80字","usage":"适用话题"}}],"evidence":[{{"evidenceType":"data|case|quote","content":"...","source":"出处"}}]}}"""


# ============================================================
# 文章来源 (免费 RSS / 网页抓取)
# ============================================================

ARTICLE_SOURCES = [
    {
        "name": "人民日报评论",
        "url": "http://opinion.people.com.cn/GB/8213/49160/49219/index.html",
        "selector": "div.hdNews a",  # CSS selector (备用)
    },
]


def fetch_articles() -> List[dict]:
    """抓取当日文章 (降级: 用硬编码的种子文章保证管线不断)"""
    import urllib.request

    articles = []

    # 尝试从人民日报抓取
    try:
        req = urllib.request.Request(
            "http://opinion.people.com.cn/GB/8213/49160/49219/index.html",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        html = urllib.request.urlopen(req, timeout=10).read().decode("gbk", errors="ignore")
        # 简单链接提取
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{15,})</a>', html)
        for url, title in links[:3]:
            if "people.com.cn" in url:
                try:
                    req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    content = urllib.request.urlopen(req2, timeout=10).read().decode("gbk", errors="ignore")
                    text = re.sub(r'<[^>]+>', '', content)
                    text = re.sub(r'\s+', ' ', text)
                    # 取正文 (通常在 div.article 或正文段落中)
                    body_match = re.search(r'(?:<p>|　　)(.{50,})', content)
                    body = body_match.group(1) if body_match else text[:2000]
                    body = re.sub(r'<[^>]+>', '', body)[:2000]
                    articles.append({"title": title, "content": body, "source": "人民日报", "url": url})
                except:
                    pass
    except Exception as e:
        print(f"  [抓取] 人民日报失败: {e}")

    # 降级: 种子文章 (保证每天有内容输出)
    if not articles:
        articles.append({
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
        })

    return articles


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
    """生成一天的内容"""
    print(f"\n{'='*60}")
    print(f"  [{target_date}] 生成中...")
    print(f"{'='*60}")

    # 1. 抓取文章
    print("[1/3] 抓取文章...")
    articles = fetch_articles()
    print(f"  获取 {len(articles)} 篇文章")

    # 2. 政治理论提取
    print("[2/3] 政治理论 + 申论结构化...")
    all_cards = []
    essay_vocab = set()

    for art in articles[:2]:
        try:
            raw = llm.generate(political_prompt(art["content"]), temperature=0.2, max_tokens=1024)
            data = parse_json(raw)
            for c in data.get("cards", []):
                all_cards.append({
                    "statement": c["statement"],
                    "tags": c.get("tags", []),
                    "source": art["source"],
                })
            print(f"  政治卡片: {len(data.get('cards',[]))} 条")
        except Exception as e:
            print(f"  [政治提取失败] {e}")

    # 3. 申论文段结构化 (传入已有词汇做去重)
    main_art = articles[0]
    political_words = []
    for c in all_cards:
        political_words.extend(re.findall(r'[一-鿿]{2,4}', c["statement"]))

    try:
        raw = llm.generate(essay_prompt(main_art["content"], political_words[:20]), temperature=0.3, max_tokens=1536)
        essay = parse_json(raw)
        print(f"  申论: {len(essay.get('vocabulary',[]))}词 {len(essay.get('arguments',[]))}论点 {len(essay.get('evidence',[]))}论据")
    except Exception as e:
        print(f"  [申论结构化失败] {e}")
        essay = {"vocabulary": [], "arguments": [], "evidence": []}

    # 4. 去重检查
    essay_words = {v["word"] for v in essay.get("vocabulary", [])}
    card_words = set()
    for c in all_cards:
        for w in re.findall(r'[一-鿿]{2,}', c["statement"]):
            card_words.add(w)
    conflicts = essay_words & card_words
    if conflicts:
        print(f"  [去重] 移除 {len(conflicts)} 个重复词: {conflicts}")
        essay["vocabulary"] = [v for v in essay.get("vocabulary", []) if v["word"] not in card_words]

    # 5. 组装 (选词填空的词库由词库管理器另外维护)
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
                    "A": c.get("correctStatement", c.get("statement", "")),
                    "B": c.get("wrongOptions", ["混淆概念的错误表述", "绝对化不当的表述", "与原文相悖的表述"])[0],
                    "C": c.get("wrongOptions", ["", "", ""])[1] if len(c.get("wrongOptions", [])) > 1 else "与原文无关的表述",
                    "D": c.get("wrongOptions", ["", "", ""])[2] if len(c.get("wrongOptions", [])) > 2 else "逻辑错误的表述",
                },
                "correctAnswer": "A",
                "analysis": f"选项A的陈述准确反映了原文精神。",
                "tags": c.get("tags", []),
                "source": c.get("source", main_art["source"]),
                "date": target_date,
            }
            for i, c in enumerate(all_cards)
        ],
        "essayPassage": {
            "title": main_art["title"],
            "source": main_art["source"],
            "sourcePublishDate": target_date,
            "originalExcerpt": main_art["content"][:500],
            "sections": [
                {"type": "vocabulary", "title": "词汇积累", "items": essay.get("vocabulary", [])},
                {"type": "argument", "title": "论点积累", "items": essay.get("arguments", [])},
                {"type": "evidence", "title": "论据积累", "items": essay.get("evidence", [])},
            ],
            "tags": [t for c in all_cards for t in c.get("tags", [])],
            "readingTimeMinutes": 8,
        },
    }

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{target_date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    print(f"  → {out_path}")
    return package


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
