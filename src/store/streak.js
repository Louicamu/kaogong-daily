import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'kc_streak'

function loadDates() {
  try {
    const raw = uni.getStorageSync(STORAGE_KEY)
    return Array.isArray(raw) ? raw : []
  } catch (_) {
    return []
  }
}

function saveDates(dates) {
  try {
    uni.setStorageSync(STORAGE_KEY, dates)
  } catch (_) { /* storage full or unavailable */ }
}

function getTodayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getYesterdayStr() {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const useStreakStore = defineStore('streak', () => {
  const studiedDates = ref(loadDates())

  // Longest consecutive streak ever achieved
  const streakDays = computed(() => {
    const dates = studiedDates.value
    if (dates.length === 0) return 0
    const sorted = [...dates].sort()
    let longest = 1
    let current = 1
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i - 1])
      const curr = new Date(sorted[i])
      const diff = (curr - prev) / (1000 * 60 * 60 * 24)
      if (Math.abs(diff - 1) < 0.01) {
        current++
        if (current > longest) longest = current
      } else if (diff > 1) {
        current = 1
      }
    }
    return longest
  })

  // Current ongoing streak (counting backward from today or yesterday)
  const currentStreak = computed(() => {
    const dates = studiedDates.value
    if (dates.length === 0) return 0
    const sorted = [...dates].sort().reverse()
    const today = getTodayStr()
    const yesterday = getYesterdayStr()
    if (sorted[0] !== today && sorted[0] !== yesterday) return 0
    let streak = 1
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i - 1])
      const curr = new Date(sorted[i])
      const diff = (prev - curr) / (1000 * 60 * 60 * 24)
      if (Math.abs(diff - 1) < 0.01) {
        streak++
      } else {
        break
      }
    }
    return streak
  })

  const totalDays = computed(() => studiedDates.value.length)

  function trackStudyDate(dateStr) {
    if (!dateStr) dateStr = getTodayStr()
    if (!studiedDates.value.includes(dateStr)) {
      studiedDates.value.push(dateStr)
      studiedDates.value.sort()
      saveDates(studiedDates.value)
    }
  }

  function checkToday() {
    return studiedDates.value.includes(getTodayStr())
  }

  // Returns date strings (YYYY-MM-DD) for the current Monday—Sunday week
  function getWeekDates() {
    const now = new Date()
    const day = now.getDay()
    const mondayOffset = day === 0 ? -6 : 1 - day
    const monday = new Date(now)
    monday.setDate(now.getDate() + mondayOffset)
    const week = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      const str = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      week.push(str)
    }
    return week
  }

  return {
    studiedDates,
    streakDays,
    currentStreak,
    totalDays,
    trackStudyDate,
    checkToday,
    getWeekDates,
  }
})
