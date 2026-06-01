/**
 * 每日内容加载器
 * 优先从 static/daily/{date}.json (GitHub Actions 生成) 加载
 * 找不到时降级到 mock 数据
 */

import mockApi from './mock.js'

/** 尝试从静态 JSON 加载某天内容 */
export async function loadDailyContent(date) {
  try {
    const json = await fetchDailyJSON(date)
    if (json) {
      return adaptDailyJSON(json, date)
    }
  } catch (e) {
    console.log('[DailyLoader] 未找到 ' + date + ' 的静态内容，使用 Mock')
  }
  // 降级
  return mockApi.getDailyContent(date)
}

export async function loadPoliticalQuestions(date) {
  try {
    const json = await fetchDailyJSON(date)
    if (json?.politicalTheories?.length) {
      return { code: 0, data: { date, total: json.politicalTheories.length, questions: json.politicalTheories } }
    }
  } catch (_) {}
  return mockApi.getPoliticalQuestions(date)
}

export async function loadDailyWords(date) {
  try {
    const json = await fetchDailyJSON(date)
    if (json?.dailyWords?.length) {
      return { code: 0, data: { date, totalWords: json.dailyWords.length, words: json.dailyWords } }
    }
  } catch (_) {}
  return mockApi.getDailyWordSet(date)
}

export async function loadEssayPassage(date) {
  try {
    const json = await fetchDailyJSON(date)
    if (json?.essayPassage?.title) {
      return { code: 0, data: json.essayPassage }
    }
  } catch (_) {}
  return mockApi.getEssayPassage(date)
}

// ===== 内部 =====

async function fetchDailyJSON(date) {
  return new Promise((resolve, reject) => {
    // uni-app 跨平台请求
    uni.request({
      url: `/static/daily/${date}.json`,
      method: 'GET',
      timeout: 5000,
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          resolve(res.data)
        } else {
          reject(new Error('not found'))
        }
      },
      fail: reject,
    })
  })
}

/** 将 auto_pipeline.py 输出的 JSON 适配为前端期望格式 */
function adaptDailyJSON(json, date) {
  return {
    code: 0,
    data: {
      date,
      exists: true,
      isToday: date === formatToday(),
      modules: {
        politicalTheory: {
          available: (json.politicalTheories || []).length > 0,
          count: (json.politicalTheories || []).length,
          tags: json.politicalTheories?.[0]?.tags || [],
          previewQuestion: json.politicalTheories?.[0]?.question || '',
        },
        wordSet: {
          available: (json.dailyWords || []).length > 0,
          totalWords: (json.dailyWords || []).length,
          highFreqCount: (json.dailyWords || []).filter(w => w.isHighFreq).length,
          predictiveCount: (json.dailyWords || []).filter(w => !w.isHighFreq).length,
          previewWords: (json.dailyWords || []).map(w => ({ word: w.word, isHighFreq: w.isHighFreq })),
        },
        essayPassage: {
          available: !!(json.essayPassage?.title),
          title: json.essayPassage?.title || '',
          source: json.essayPassage?.source || '',
          readingTime: json.essayPassage?.readingTimeMinutes || 8,
          sectionNames: (json.essayPassage?.sections || []).map(s => s.title),
        },
      },
      userProgress: { politicalTheory: false, wordSet: false, essayPassage: false },
    },
  }
}

function formatToday() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

export default { loadDailyContent, loadPoliticalQuestions, loadDailyWords, loadEssayPassage }
