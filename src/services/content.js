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
    return Promise.resolve(mockApi.getDailyContent(date))
  },
  getCachedDaily(date) {
    return getCache('daily_' + (date || 'today'))
  },
  getPoliticalQuestions(date) {
    return Promise.resolve(mockApi.getPoliticalQuestions(date))
  },
  getDailyWordSet(date) {
    return Promise.resolve(mockApi.getDailyWordSet(date))
  },
  getEssayPassage(date) {
    return Promise.resolve(mockApi.getEssayPassage(date))
  },
  getCalendar(month) {
    return Promise.resolve(mockApi.getCalendar(month))
  },
  recordProgress(date, module, data) {
    const key = 'progress_' + date
    let existing = {}
    try { existing = uni.getStorageSync(CACHE_PREFIX + key) || {} } catch (e) {}
    existing[module] = { completed: true }
    try { uni.setStorageSync(CACHE_PREFIX + key, existing) } catch (e) {}
    return Promise.resolve({ code: 0, data: { updated: true } })
  },
  getUserProgress(date) {
    const key = 'progress_' + date
    let data = {}
    try { data = uni.getStorageSync(CACHE_PREFIX + key) || {} } catch (e) {}
    return Promise.resolve({
      code: 0,
      data: {
        politicalTheory: !!(data.politicalTheory?.completed),
        wordSet: !!(data.wordSet?.completed),
        essayPassage: !!(data.essayPassage?.completed),
      },
    })
  },
  addFavorite(itemType, itemId, date, notes) {
    let favs = []
    try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
    if (!favs.find(f => f.itemId === itemId && f.itemType === itemType)) {
      favs.unshift({ _id: 'local_' + Date.now(), itemType, itemId, date, title: notes || '', notes: notes || '', createdAt: Date.now() })
      try { uni.setStorageSync(CACHE_PREFIX + 'favs', favs) } catch (e) {}
    }
    return Promise.resolve({ code: 0, data: { existed: false } })
  },
  removeFavorite(itemType, itemId) {
    let favs = []
    try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
    favs = favs.filter(f => !(f.itemId === itemId && f.itemType === itemType))
    try { uni.setStorageSync(CACHE_PREFIX + 'favs', favs) } catch (e) {}
    return Promise.resolve({ code: 0, data: { removed: true } })
  },
  getFavorites() {
    let favs = []
    try { favs = uni.getStorageSync(CACHE_PREFIX + 'favs') || [] } catch (e) {}
    return Promise.resolve({ code: 0, data: { total: favs.length, items: favs } })
  },
}

export default api
