/**
 * 搜索服务 — 跨模块全文检索（本地 mock + static JSON）
 *
 * 搜索范围：
 *   词汇定义 & 考试语境（word / word_pair）
 *   政治理论题目 & 选项 & 解析（political_theory）
 *   申论文段标题 & 原文精选（essay_passage）
 *
 * 返回结果按匹配度排序：
 *   精确匹配 > 前缀匹配 > 词边界匹配 > 子串匹配 > 逐字模糊
 */
import contentService from './content.js'

/** @param {Date} d */
function fmt(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * 对一段文本计算与查询的匹配分数
 * @param {string} query
 * @param {string} text
 * @returns {number} 0-100
 */
function scoreMatch(query, text) {
  if (!text) return 0
  const q = query.toLowerCase()
  const lower = text.toLowerCase()

  // 精确相等
  if (lower === q) return 100
  // 前缀匹配
  if (lower.startsWith(q)) return 80
  // 词边界匹配（中文标点 / 空格作为分隔符）
  if (new RegExp(`(^|[\\s，。、；：""''（）《》])${escapeRegex(q)}(?=[\\s，。、；：""''（）《》]|$)`, 'i').test(text)) return 60
  // 普通子串
  if (lower.includes(q)) return 40
  // 逐字模糊（按顺序每个字出现即通过）
  let qi = 0
  for (let i = 0; i < lower.length && qi < q.length; i++) {
    if (lower[i] === q[qi]) qi++
  }
  return qi === q.length ? 20 : 0
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 主搜索入口
 * @param {string} query - 用户输入
 * @returns {Promise<Array<{type:string, typeLabel:string, title:string, snippet:string, date:string, route:string, score:number}>>}
 */
export async function search(query) {
  if (!query || !query.trim()) return []

  const q = query.trim()
  const today = fmt(new Date())
  const results = []

  // 一次性加载今日全部数据（含缓存 / mock 降级）
  const [wordRes, politicalRes, essayRes] = await Promise.all([
    contentService.getDailyWordSet(today).catch(() => null),
    contentService.getPoliticalQuestions(today).catch(() => null),
    contentService.getEssayPassage(today).catch(() => null),
  ])

  // ---- 词汇 ----
  const words = wordRes?.data?.words || []
  for (const w of words) {
    const score = scoreMatch(q, `${w.word} ${w.definition || ''} ${w.examContext || ''}`)
    if (score > 0) {
      results.push({
        type: 'word',
        typeLabel: '词',
        title: w.word,
        snippet: w.definition || '',
        date: wordRes.data.date,
        route: `/pages/words/index?date=${wordRes.data.date}`,
        score,
      })
    }
  }

  // ---- 政治理论 ----
  const questions = politicalRes?.data?.questions || []
  for (const pt of questions) {
    const optText = Object.values(pt.options || {}).join(' ')
    const score = scoreMatch(q, `${pt.question} ${pt.analysis || ''} ${optText}`)
    if (score > 0) {
      const title = pt.question.length > 35 ? pt.question.slice(0, 35) + '...' : pt.question
      results.push({
        type: 'political',
        typeLabel: '政',
        title,
        snippet: (pt.tags || []).join(' · '),
        date: politicalRes.data.date,
        route: `/pages/political/index?date=${politicalRes.data.date}`,
        score,
      })
    }
  }

  // ---- 申论文段 ----
  const essay = essayRes?.data
  if (essay) {
    const excerpt = (essay.originalExcerpt || '').replace(/\s+/g, ' ').trim()
    const score = scoreMatch(q, `${essay.title || ''} ${excerpt}`)
    if (score > 0) {
      results.push({
        type: 'essay',
        typeLabel: '申',
        title: essay.title || '',
        snippet: excerpt.length > 80 ? excerpt.slice(0, 80) + '...' : excerpt,
        date: essay.date || essay.sourcePublishDate || today,
        route: `/pages/essay/index?date=${essay.date || essay.sourcePublishDate || today}`,
        score,
      })
    }
  }

  // 按分数降序
  results.sort((a, b) => b.score - a.score)
  return results
}
