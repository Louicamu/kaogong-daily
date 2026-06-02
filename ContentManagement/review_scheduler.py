"""
考公每日学 — 间隔重复复习调度器

Schedule:
  - mastered:  7 天 (完全掌握的词, 每周过一遍)
  - familiar:  3 天 (基本记住, 但不够牢)
  - struggling: 1 天 (需要天天巩固)

无外部依赖, 纯 datetime 实现。
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


class SpacedRepetitionScheduler:
    """间隔重复复习调度器"""

    # 复习间隔 (天), 按掌握程度
    INTERVALS = {
        "mastered": 7,
        "familiar": 3,
        "struggling": 1,
    }

    # 有效状态集合
    VALID_STATUSES = set(INTERVALS.keys())

    def __init__(self, schedule: Optional[Dict[str, int]] = None):
        """
        :param schedule: 可选自定义间隔, 如 {"mastered": 10, "familiar": 5, "struggling": 2}
        """
        if schedule is not None:
            self.schedule = schedule
        else:
            self.schedule = dict(self.INTERVALS)

    # ---------------------------------------------------------------
    # 核心方法
    # ---------------------------------------------------------------

    def getDueWords(self, today: str, wordRecords: List[Dict]) -> List[Dict]:
        """
        返回今日到期需要复习的词汇列表。

        :param today: 日期字符串 "YYYY-MM-DD"
        :param wordRecords: 词汇掌握记录列表, 每项含 wordId, status, lastReviewed
        :return: 到期需要复习的记录列表
        """
        today_dt = self._parse_date(today)
        due = []
        for rec in wordRecords:
            next_date = self._get_next_review_date(rec)
            if next_date is not None and next_date <= today_dt:
                due.append(rec)
        return due

    def updateReviewDate(self, wordId: str, status: str) -> Dict:
        """
        根据当前掌握状态更新 nextReviewDate。

        :param wordId: 词汇 ID
        :param status: mastered / familiar / struggling
        :return: 更新后的记录 dict {wordId, status, lastReviewed, nextReviewDate}
        """
        if status not in self.VALID_STATUSES:
            raise ValueError(f"无效状态 '{status}', 有效值: {', '.join(sorted(self.VALID_STATUSES))}")

        now = datetime.now()
        interval_days = self.schedule.get(status, 1)
        next_review = now + timedelta(days=interval_days)

        return {
            "wordId": wordId,
            "status": status,
            "lastReviewed": now.strftime("%Y-%m-%d"),
            "nextReviewDate": next_review.strftime("%Y-%m-%d"),
        }

    def toJSON(self) -> str:
        """
        导出调度器配置供前端消费。

        JSON 结构:
        {
          "schedule": { "mastered": 7, "familiar": 3, "struggling": 1 },
          "todayDueCount": 0,        // 由前端填充
          "wordRecords": []           // 由前端填充
        }
        """
        return json.dumps({
            "schedule": self.schedule,
            "todayDueCount": 0,
            "wordRecords": [],
        }, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------------
    # 内部辅助
    # ---------------------------------------------------------------

    def _parse_date(self, date_str: str) -> datetime:
        """将 "YYYY-MM-DD" 转为 datetime 对象"""
        return datetime.strptime(date_str, "%Y-%m-%d")

    def _get_next_review_date(self, record: Dict) -> Optional[datetime]:
        """从记录中解析 nextReviewDate"""
        raw = record.get("nextReviewDate")
        if raw:
            return self._parse_date(raw)
        # 没有 nextReviewDate 则用 lastReviewed + 间隔推算
        last = record.get("lastReviewed")
        status = record.get("status", "struggling")
        if last:
            interval = self.schedule.get(status, 1)
            return self._parse_date(last) + timedelta(days=interval)
        return None


# ---------------------------------------------------------------
# 便捷工厂
# ---------------------------------------------------------------

def make_scheduler(schedule: Optional[Dict[str, int]] = None) -> SpacedRepetitionScheduler:
    """创建调度器实例"""
    return SpacedRepetitionScheduler(schedule)


def compute_due_words(today: str, wordRecords: List[Dict]) -> List[Dict]:
    """一行调用: 返回 today 到期词汇"""
    return SpacedRepetitionScheduler().getDueWords(today, wordRecords)


# ---------------------------------------------------------------
# 自测
# ---------------------------------------------------------------

if __name__ == "__main__":
    sched = SpacedRepetitionScheduler()

    # 模拟一条词汇记录
    records = [
        {
            "wordId": "wc_001",
            "word": "擘画",
            "status": "struggling",
            "lastReviewed": "2026-06-01",
            "nextReviewDate": "2026-06-02",
        },
        {
            "wordId": "wc_002",
            "word": "新质生产力",
            "status": "mastered",
            "lastReviewed": "2026-05-25",
            "nextReviewDate": "2026-06-01",
        },
        {
            "wordId": "wc_003",
            "word": "踔厉奋发",
            "status": "familiar",
            "lastReviewed": "2026-05-30",
            "nextReviewDate": "2026-06-02",
        },
    ]

    today = "2026-06-02"
    due = sched.getDueWords(today, records)
    print(f"今日 ({today}) 到期复习: {len(due)} 个")
    for w in due:
        print(f"  - {w['word']} ({w['status']}, 上次: {w['lastReviewed']})")

    # 测试 updateReviewDate
    updated = sched.updateReviewDate("wc_001", "mastered")
    print(f"\n复习后更新: {json.dumps(updated, ensure_ascii=False)}")

    # 导出配置
    print(f"\n调度配置:\n{sched.toJSON()}")
