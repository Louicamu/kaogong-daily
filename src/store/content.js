import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import contentService from '@/services/content.js'

export const useContentStore = defineStore('content', () => {
  const todayDate = ref(getTodayStr())
  const loading = ref(false)
  const modules = ref({
    politicalTheory: { available: false, count: 0, tags: [], previewQuestion: '' },
    wordSet: { available: false, totalWords: 0, highFreqCount: 0, predictiveCount: 0, previewWords: [] },
    essayPassage: { available: false, title: '', source: '', readingTime: 0, sectionNames: [] },
  })
  const progress = ref({ politicalTheory: false, wordSet: false, essayPassage: false })

  const completedCount = computed(() => Object.values(progress.value).filter(Boolean).length)
  const progressPercent = computed(() => Math.round((completedCount.value / 3) * 100))

const _contentDate = ref('')

async function loadDailyContent(date) {
    loading.value = true
    try {
      const res = await contentService.getDailyContent(date || todayDate.value)
      if (res?.data) {
        const d = res.data
        _contentDate.value = d.actualDate || d.date || todayDate.value
        modules.value = {
          politicalTheory: d.modules?.politicalTheory || { available: false },
          wordSet: d.modules?.wordSet || { available: false },
          essayPassage: d.modules?.essayPassage || { available: false },
        }
        progress.value = d.userProgress || { politicalTheory: false, wordSet: false, essayPassage: false }
        return true
      }
      return false
    } catch (e) {
      console.error('加载每日内容失败:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  function getTodayStr() {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  }

  return { todayDate, loading, modules, progress, completedCount, progressPercent, loadDailyContent, _contentDate }
})
