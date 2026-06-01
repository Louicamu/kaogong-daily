"""
考公每日学 — Ollama 本地 LLM 驱动的内容生成管线

依赖: ollama + qwen2.5:7b (或 14b)
用法: python ollama_pipeline.py --date 2026-06-03
"""

import json
import argparse
import subprocess
import time
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict


# ============================================================
# Ollama 客户端 (零依赖, 直接 HTTP)
# ============================================================

class Ollama:
    """Ollama HTTP 客户端 — 不用任何第三方库"""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base = base_url
        self._ensure_running()

    def _ensure_running(self):
        """检查 Ollama 是否在运行, 没运行则尝试启动"""
        import urllib.request
        try:
            urllib.request.urlopen(f"{self.base}/api/tags", timeout=3)
        except:
            print("[Ollama] 服务未运行, 尝试启动...")
            subprocess.Popen(["ollama", "serve"], creationflags=0x08000000)  # DETACHED_PROCESS
            time.sleep(3)

    def _ensure_model(self):
        """确保模型已下载"""
        import urllib.request
        try:
            req = urllib.request.Request(f"{self.base}/api/tags")
            data = json.loads(urllib.request.urlopen(req, timeout=3).read())
            models = [m["name"] for m in data.get("models", [])]
            if any(self.model in m for m in models):
                return
        except:
            pass
        print(f"[Ollama] 正在下载模型 {self.model}...")
        subprocess.run(["ollama", "pull", self.model], check=True)
        print("[Ollama] 模型就绪")

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """调用 Ollama generate API"""
        self._ensure_model()
        import urllib.request
        req = urllib.request.Request(
            f"{self.base}/api/generate",
            data=json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
        return resp.get("response", "")


# ============================================================
# 提示词模板
# ============================================================

POLITICAL_PROMPT = """你是国考政治理论命题专家。从以下文章提取 3 条政治理论单句记忆卡片。

规则:
1. 每条单句必须模仿国考"常识判断/政治理论"真题的正确选项表述风格
2. 一句完整、规范、无语病的政治陈述, 不超过 50 字
3. 必须来源于原文

文章:
{article}

返回纯 JSON (不要 markdown):
{{
  "cards": [
    {{
      "statement": "...",
      "tags": ["标签1", "标签2"]
    }}
  ]
}}"""


ESSAY_PROMPT = """你是申论大作文辅导专家。从以下官媒文章提取结构化内容。

文章:
{article}

规则:
1. 词汇积累: 提取 3-5 个高分规范政治用语 (优先精准用词, 避免常见成语)
2. 论点积累: 提炼约 3 个核心论点, 每个论点 ≤15 字, 附带展开论述和适用话题
3. 论据积累: 提取 2-3 条数据/案例/引言

返回纯 JSON (不要 markdown):
{{
  "vocabulary": [
    {{"word": "词", "context": "原文语境", "note": "加分原因"}}
  ],
  "arguments": [
    {{"point": "论点标题", "elaboration": "展开论述 50-80字", "usage": "适用话题"}}
  ],
  "evidence": [
    {{"evidenceType": "data|case|quote", "content": "...", "source": "出处"}}
  ]
}}"""


# ============================================================
# 政治理论题目生成器
# ============================================================

@dataclass
class PoliticalCard:
    statement: str
    tags: List[str]
    source: str = ""


class PoliticalExtractor:
    """从文章中提取政治理论记忆卡片"""

    def __init__(self, ollama: Ollama):
        self.ollama = ollama

    def extract(self, article: dict) -> List[PoliticalCard]:
        """提取政治单句卡片，失败时降级到规则引擎"""
        text = f"标题: {article.get('title', '')}\n\n内容: {article.get('content', '')[:2000]}"
        prompt = POLITICAL_PROMPT.format(article=text)

        try:
            resp = self.ollama.generate(prompt, temperature=0.2, max_tokens=1024)
            data = self._parse_json(resp)
            cards = []
            for item in data.get("cards", []):
                cards.append(PoliticalCard(
                    statement=item["statement"],
                    tags=item.get("tags", []),
                    source=article.get("source", ""),
                ))
            if cards:
                print(f"  [LLM] 提取 {len(cards)} 条政治卡片")
                return cards
        except Exception as e:
            print(f"  [LLM] 政治提取失败: {e}, 降级规则引擎")

        # 降级: 规则引擎
        return self._rule_extract(article)

    def _rule_extract(self, article: dict) -> List[PoliticalCard]:
        """规则引擎降级: 匹配引号内的句子 / 重要句式"""
        content = article.get("content", "")
        cards = []

        # 匹配引号内的核心陈述
        quotes = re.findall(r'[「「]([^」」]+)[」」]', content)
        quotes += re.findall(r'[""]([^""]+)[""]', content)

        # 匹配 "指出/强调/要求..." 后的关键句
        patterns = [
            r'指出[，,]\s*([^。；;]+)',
            r'强调[，,]\s*([^。；;]+)',
            r'(?:(?:中国式现代化|改革开放|共同富裕|高质量发展)[^。]*[。])',
        ]
        for pat in patterns:
            matches = re.findall(pat, content)
            for m in matches[:2]:
                m = m.strip()
                if 10 < len(m) < 60:
                    cards.append(PoliticalCard(statement=m, tags=["时政"], source=article.get("source", "")))

        print(f"  [规则] 提取 {len(cards)} 条政治卡片")
        return cards[:4]

    def _parse_json(self, text: str) -> dict:
        """从 LLM 输出中提取 JSON"""
        # 去掉可能的 markdown ```json 包裹
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        # 找到第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {}


# ============================================================
# 申论文段结构化器
# ============================================================

class EssayStructurer:
    """将文章结构化为三大板块"""

    def __init__(self, ollama: Ollama):
        self.ollama = ollama

    def structure(self, article: dict) -> dict:
        """结构化申论文段"""
        text = f"标题: {article.get('title', '')}\n\n内容: {article.get('content', '')[:2000]}"
        prompt = ESSAY_PROMPT.format(article=text)

        try:
            resp = self.ollama.generate(prompt, temperature=0.3, max_tokens=1536)
            data = self._parse_json(resp)
            if data.get("vocabulary") or data.get("arguments"):
                print(f"  [LLM] 结构化申论文段: {len(data.get('vocabulary',[]))} 词, {len(data.get('arguments',[]))} 论点")
                return data
        except Exception as e:
            print(f"  [LLM] 申论结构化失败: {e}, 降级规则引擎")

        return self._rule_structure(article)

    def _rule_structure(self, article: dict) -> dict:
        """规则引擎降级"""
        content = article.get("content", "")
        return {
            "vocabulary": [],
            "arguments": [],
            "evidence": [],
        }

    def _parse_json(self, text: str) -> dict:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return {}


# ============================================================
# 综合管线
# ============================================================

class OllamaContentPipeline:
    """
    Ollama 驱动的每日内容生成管线

    使用:
        pipe = OllamaContentPipeline("2026-06-03", model="qwen2.5:7b")
        package = pipe.run(articles)
    """

    def __init__(self, target_date: str, model: str = "qwen2.5:7b"):
        self.target_date = target_date
        self.ollama = Ollama(model=model)
        self.political = PoliticalExtractor(self.ollama)
        self.essay = EssayStructurer(self.ollama)

    def run(self, articles: List[dict]) -> dict:
        """跑完整管线"""
        print(f"\n{'='*60}")
        print(f"  Ollama 内容管线 [{self.target_date}]  model={self.ollama.model}")
        print(f"{'='*60}")

        t0 = time.time()

        # 1. 政治理论提取
        print("\n[1/3] 政治理论提取...")
        all_cards = []
        for art in articles[:2]:  # 最多处理 2 篇
            cards = self.political.extract(art)
            all_cards.extend(cards)

        # 2. 申论文段结构化
        print("\n[2/3] 申论文段结构化...")
        main_article = articles[0] if articles else {"title": "", "content": "", "source": ""}
        essay_data = self.essay.structure(main_article)

        # 3. 排他性去重
        print("\n[3/3] 排他性去重...")
        essay_vocab_words = {v["word"] for v in essay_data.get("vocabulary", [])}
        political_vocab_words = set()
        for card in all_cards:
            # 从政治卡片中提取关键词避免与词汇模块重复
            for w in re.findall(r'[一-鿿]{2,4}', card.statement):
                if len(w) >= 2:
                    political_vocab_words.add(w)

        conflicts = essay_vocab_words & political_vocab_words
        if conflicts:
            print(f"  ⚠ 去重: 移除 {len(conflicts)} 个重复词汇: {conflicts}")
            essay_data["vocabulary"] = [v for v in essay_data.get("vocabulary", []) if v["word"] not in conflicts]

        elapsed = time.time() - t0
        print(f"\n  Done in {elapsed:.1f}s")
        return {
            "date": self.target_date,
            "political_cards": [{"statement": c.statement, "tags": c.tags, "source": c.source} for c in all_cards],
            "essay": essay_data,
            "essay_vocab": essay_vocab_words - conflicts,
            "elapsed_seconds": round(elapsed, 1),
        }


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Ollama 内容生成管线")
    parser.add_argument("--date", type=str, default=None, help="目标日期 YYYY-MM-DD")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="Ollama 模型名")
    parser.add_argument("--input", type=str, default=None, help="输入 JSON 文件路径 (含文章列表)")
    args = parser.parse_args()

    target_date = args.date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 加载文章
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            articles = json.load(f)
    else:
        # 用一段真实的人民日报评论来做演示
        articles = [{
            "title": "在进一步全面深化改革中推进中国式现代化",
            "content": """
            改革开放是决定当代中国命运的关键一招，也是决定实现"两个一百年"奋斗目标、
            实现中华民族伟大复兴的关键一招。党的二十届三中全会对进一步全面深化改革、
            推进中国式现代化作出战略部署。

            中国式现代化是人口规模巨大的现代化，是全体人民共同富裕的现代化，
            是物质文明和精神文明相协调的现代化，是人与自然和谐共生的现代化，
            是走和平发展道路的现代化。

            发展新质生产力是推动高质量发展的内在要求和重要着力点。
            必须继续做好创新这篇大文章，推动新质生产力加快发展。

            改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。
            要坚持以人民为中心的发展思想，让改革发展成果更多更公平惠及全体人民。

            2025年我国国内生产总值突破130万亿元，经济实力实现历史性跃升。
            深圳建设中国特色社会主义先行示范区以来，推出1000多项改革创新举措。
            """,
            "source": "人民日报",
            "url": "",
        }]

    pipeline = OllamaContentPipeline(target_date, model=args.model)
    package = pipeline.run(articles)

    # 保存结果
    import os
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"daily_{target_date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {out_path}")
    print(f"政治卡片: {len(package['political_cards'])} 条")
    print(f"申论词汇: {len(package['essay'].get('vocabulary', []))} 个")
    print(f"申论论点: {len(package['essay'].get('arguments', []))} 个")
    print(f"申论论据: {len(package['essay'].get('evidence', []))} 条")


if __name__ == "__main__":
    main()
