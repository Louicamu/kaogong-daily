/**
 * 内容服务层 — 云函数调用 + 本地缓存 + Mock 降级 (ESM)
 */
import mockApi from './mock.js'

const CACHE_PREFIX = 'kc_'
const CACHE_TTL = {
  DAILY_CONTENT: 12 * 60 * 60 * 1000,
  WORD_SET: 24 * 60 * 60 * 1000,
  POLITICAL: 24 * 60 * 60 * 1000,
  ESSAY: 7 * 24 * 60 * 60 * 1000,
  FAVORITES: 5 * 60 * 1000,
}

/** 调用云函数（带 Mock 降级） */
function callCloud(name, mockName, params) {
  return new Promise((resolve) => {
    // H5 / 浏览器环境 — 直接使用 mock
    if (typeof wx === 'undefined' || !wx || !wx.cloud) {
      const fn = mockApi[mockName]
      resolve(fn ? fn(params) : null)
      return
    }
    wx.cloud.callFunction({ name, data: params || {} })
      .then(res => resolve(res.result))
      .catch(err => {
        console.warn('[Mock] 云函数 ' + name + ' 失败:', err.errMsg || err.message)
        const fn = mockApi[mockName]
        resolve(fn ? fn(params) : null)
      })
  })
}

/** 缓存读写 */
function getCache(key) {
  try {
    const raw = uni.getStorageSync(CACHE_PREFIX + key)
    if (raw && Date.now() - raw.t < raw.ttl) return raw.data
  } catch (e) { /* ignore */ }
  return null
}
function setCache(key, data, ttl) {
  try { uni.setStorageSync(CACHE_PREFIX + key, { data, t: Date.now(), ttl }) } catch (e) { /* ignore */ }
}

const api = {
  getDailyContent(date) {
    const d = date || formatToday()
    const cacheKey = 'daily_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    // 1️⃣ 优先: static/daily/{date}.json (GitHub Actions 生成)
    // 2️⃣ 降级: mock
    return tryStaticDaily(d)
      .then(res => { if (res) { setCache(cacheKey, res, CACHE_TTL.DAILY_CONTENT); return res } })
      .catch(() => mockApi.getDailyContent(d))
      .then(res => { setCache(cacheKey, res, CACHE_TTL.DAILY_CONTENT); return res })
  },
  getCachedDaily(date) {
    return getCache('daily_' + (date || 'today'))
  },
  getPoliticalQuestions(date) {
    const d = date || formatToday()
    const cacheKey = 'political_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    return tryStaticDaily(d)
      .then(json => json?.politicalTheories ? { code: 0, data: { date: d, questions: json.politicalTheories } } : null)
      .catch(() => mockApi.getPoliticalQuestions(d))
      .then(res => { setCache(cacheKey, res, CACHE_TTL.POLITICAL); return res })
  },
  getDailyWordSet(date) {
    const d = date || formatToday()
    const cacheKey = 'words_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    return tryStaticDaily(d)
      .then(json => json?.dailyWords ? { code: 0, data: { date: d, words: json.dailyWords } } : null)
      .catch(() => mockApi.getDailyWordSet(d))
      .then(res => { setCache(cacheKey, res, CACHE_TTL.WORD_SET); return res })
  },
  getEssayPassage(date) {
    const d = date || formatToday()
    const cacheKey = 'essay_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    return tryStaticDaily(d)
      .then(json => json?.essayPassage ? { code: 0, data: json.essayPassage } : null)
      .catch(() => mockApi.getEssayPassage(d))
      .then(res => { setCache(cacheKey, res, CACHE_TTL.ESSAY); return res })
  },
  getCalendar(month) {
    return callCloud('getCalendar', 'getCalendar', { month })
  },
  recordProgress(date, module, data) {
    return callCloud('recordProgress', null, { date, module, action: 'update', completed: data?.completed }).then(res => {
      if (res) return res
      const key = 'progress_' + date
      let existing = {}
      try { existing = uni.getStorageSync(CACHE_PREFIX + key) || {} } catch (e) {}
      existing[module] = { completed: true }
      try { uni.setStorageSync(CACHE_PREFIX + key, existing) } catch (e) {}
      return { code: 0, data: { updated: true } }
    })
  },
  getUserProgress(date) {
    return callCloud('recordProgress', null, { date, action: 'get' }).then(res => {
      if (res) return res
      const key = 'progress_' + date
      let data = {}
      try { data = uni.getStorageSync(CACHE_PREFIX + key) || {} } catch (e) {}
      return {
        code: 0,
        data: {
          politicalTheory: !!(data.politicalTheory?.completed),
          wordSet: !!(data.wordSet?.completed),
          essayPassage: !!(data.essayPassage?.completed),
        },
      }
    })
  },
  addFavorite(itemType, itemId, date, notes) {
    return callCloud('addFavorite', null, { itemType, itemId, date, notes }).then(res => {
      if (res) return res
      let favs = []
      try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
      if (!favs.find(f => f.itemId === itemId && f.itemType === itemType)) {
        favs.unshift({ _id: 'local_' + Date.now(), itemType, itemId, date, title: notes || '', notes: notes || '', createdAt: Date.now() })
        try { uni.setStorageSync(CACHE_PREFIX + 'favs', favs) } catch (e) {}
      }
      return { code: 0, data: { existed: false } }
    })
  },
  removeFavorite(itemType, itemId) {
    return callCloud('removeFavorite', null, { itemType, itemId }).then(res => {
      if (res) return res
      let favs = []
      try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
      favs = favs.filter(f => !(f.itemId === itemId && f.itemType === itemType))
      try { uni.setStorageSync(CACHE_PREFIX + 'favs', favs) } catch (e) {}
      return { code: 0, data: { removed: true } }
    })
  },
  getFavorites() {
    return callCloud('getFavorites', 'getFavorites', {}).then(res => {
      if (res) return res
      let favs = []
      try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
      return { code: 0, data: { total: favs.length, items: favs } }
    })
  },
}

// ===== 静态 JSON 加载 (GitHub Actions 输出) =====

function tryStaticDaily(date) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `/static/daily/${date}.json`,
      method: 'GET',
      timeout: 5000,
      success: (res) => {
        if (res.statusCode === 200 && res.data?.date) {
          resolve(res.data)
        } else {
          reject(new Error('not found'))
        }
      },
      fail: reject,
    })
  })
}

function formatToday() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

export default api
