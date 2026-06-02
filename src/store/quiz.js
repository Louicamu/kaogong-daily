import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY_ANSWERS = 'kc_quiz_answers'
const STORAGE_KEY_MASTERY = 'kc_quiz_mastery'

function loadArray(key) {
  try {
    const raw = uni.getStorageSync(key)
    return Array.isArray(raw) ? raw : []
  } catch (_) {
    return []
  }
}

function saveArray(key, data) {
  try {
    uni.setStorageSync(key, data)
  } catch (_) { /* storage full or unavailable */ }
}

export const useQuizStore = defineStore('quiz', () => {
  // ---- state ----
  const answers = ref(loadArray(STORAGE_KEY_ANSWERS))
  const wordMastery = ref(loadArray(STORAGE_KEY_MASTERY))

  // ---- computed ----
  // Latest answer per question; only those whose latest attempt is wrong
  const wrongQuestions = computed(() => {
    const latest = {}
    for (const a of answers.value) {
      latest[a.questionId] = a
    }
    return Object.keys(latest)
      .map(id => latest[id])
      .filter(a => !a.isCorrect)
      .sort((a, b) => b.timestamp - a.timestamp)
  })

  // Words with "struggling" status
  const weakWords = computed(() =>
    wordMastery.value.filter(w => w.status === 'struggling')
  )

  // Words due for review today based on spaced repetition schedule
  const reviewIntervals = { mastered: 7, familiar: 3, struggling: 1 }

  const dueReviewWords = computed(() => {
    const now = Date.now()
    return wordMastery.value.filter(w => {
      const intervalDays = reviewIntervals[w.status] || 1
      const intervalMs = intervalDays * 24 * 60 * 60 * 1000
      return (now - w.lastReviewed) >= intervalMs
    })
  })

  // ---- actions ----
  function recordAnswer({ questionId, date, module, selectedOption, correctAnswer, isCorrect, questionData }) {
    answers.value.push({
      questionId,
      date,
      module,
      selectedOption,
      correctAnswer,
      isCorrect,
      timestamp: Date.now(),
      questionData,
    })
    saveArray(STORAGE_KEY_ANSWERS, answers.value)
  }

  function recordWordMastery({ wordId, word, status }) {
    const idx = wordMastery.value.findIndex(w => w.wordId === wordId)
    if (idx >= 0) {
      wordMastery.value[idx] = { wordId, word, status, lastReviewed: Date.now() }
    } else {
      wordMastery.value.push({ wordId, word, status, lastReviewed: Date.now() })
    }
    saveArray(STORAGE_KEY_MASTERY, wordMastery.value)
  }

  function getWrongQuestions() {
    return wrongQuestions.value
  }

  function getWeakWords() {
    return weakWords.value
  }

  function getRetryCount(questionId) {
    return answers.value.filter(a => a.questionId === questionId).length
  }

  function getLastWrongDate(questionId) {
    const wrongs = answers.value.filter(a => a.questionId === questionId && !a.isCorrect)
    return wrongs.length > 0 ? wrongs[wrongs.length - 1].date : null
  }

  // Remove all answers for a given questionId (used when user clears history)
  function clearQuestionHistory(questionId) {
    answers.value = answers.value.filter(a => a.questionId !== questionId)
    saveArray(STORAGE_KEY_ANSWERS, answers.value)
  }

  // Check if a specific word is due for review
  function isWordDue(wordId) {
    const w = wordMastery.value.find(r => r.wordId === wordId)
    if (!w) return false
    const intervalDays = reviewIntervals[w.status] || 1
    const intervalMs = intervalDays * 24 * 60 * 60 * 1000
    return (Date.now() - w.lastReviewed) >= intervalMs
  }

  // Reset all quiz data
  function resetAll() {
    answers.value = []
    wordMastery.value = []
    saveArray(STORAGE_KEY_ANSWERS, answers.value)
    saveArray(STORAGE_KEY_MASTERY, wordMastery.value)
  }

  return {
    answers,
    wordMastery,
    wrongQuestions,
    weakWords,
    dueReviewWords,
    recordAnswer,
    recordWordMastery,
    getWrongQuestions,
    getWeakWords,
    getRetryCount,
    getLastWrongDate,
    clearQuestionHistory,
    isWordDue,
    resetAll,
  }
})
