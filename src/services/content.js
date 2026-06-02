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
  /** 智能获取: 今天没有就显示昨天的, 回退最多7天 */
  getDailyContent(date) {
    const d = date || formatToday()
    return tryStaticDaily(d)
      .then(res => {
        if (res) return { ...res, data: { ...res.data, actualDate: d, isToday: d === formatToday() } }
        throw new Error('not found')
      })
      .catch(() => this._fallbackDate(d, 'getDailyContent'))
      .then(res => {
        if (res) return res
        return mockApi.getDailyContent(d)
      })
  },

  /** 回退查找: 从指定日期往前找, 最多7天 */
  _fallbackDate(startDate, method) {
    const d = new Date(startDate)
    d.setDate(d.getDate() - 1)
    const prevDate = formatDateObj(d)
    const maxBack = new Date(startDate); maxBack.setDate(maxBack.getDate() - 7)
    const cutoff = formatDateObj(maxBack)

    if (prevDate < cutoff) return Promise.resolve(null)

    const cacheKey = method + '_' + prevDate
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve({ ...cached, _fallback: true, _actualDate: prevDate })

    return tryStaticDaily(prevDate)
      .then(res => {
        if (res) return { ...res, data: { ...res.data, actualDate: prevDate, isToday: false } }
        return this._fallbackDate(prevDate, method)
      })
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
      .catch(() => this._fallbackDate(d, 'politicalQuestions'))
      .catch(() => mockApi.getPoliticalQuestions(d))
      .then(res => { if (res) setCache(cacheKey, res, CACHE_TTL.POLITICAL); return res })
  },
  getDailyWordSet(date) {
    const d = date || formatToday()
    const cacheKey = 'words_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    return tryStaticDaily(d)
      .then(json => json?.dailyWords ? { code: 0, data: { date: d, words: json.dailyWords } } : null)
      .catch(() => this._fallbackDate(d, 'wordSet'))
      .catch(() => mockApi.getDailyWordSet(d))
      .then(res => { if (res) setCache(cacheKey, res, CACHE_TTL.WORD_SET); return res })
  },
  getEssayPassage(date) {
    const d = date || formatToday()
    const cacheKey = 'essay_' + d
    const cached = getCache(cacheKey)
    if (cached) return Promise.resolve(cached)
    return tryStaticDaily(d)
      .then(json => json?.essayPassage ? { code: 0, data: json.essayPassage } : null)
      .catch(() => this._fallbackDate(d, 'essayPassage'))
      .catch(() => mockApi.getEssayPassage(d))
      .then(res => { if (res) setCache(cacheKey, res, CACHE_TTL.ESSAY); return res })
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

function formatDateObj(date) {
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
}

export default api
