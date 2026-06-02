<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">政治理论积累</text>
      <text class="page-date">{{ displayDate }}</text>
    </view>
    <view v-if="loading" class="skeleton-list"><view v-for="i in 2" :key="i" class="sk-item" /></view>
    <view v-else-if="!questions.length" class="empty"><text>今日暂无题目</text></view>
    <view v-else class="questions-list">
      <view v-for="(q, idx) in questions" :key="q.questionId">
        <view class="q-number"><text>第 {{ idx + 1 }} 题</text></view>
        <exam-question v-bind="q" :previousAnswer="prevAnswers[idx]" @answer="onAnswer(idx, $event)" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'
import examQuestion from '@/components/exam-question.vue'
import { useQuizStore } from '@/store/quiz.js'

const quizStore = useQuizStore()
const loading = ref(true)
const questions = ref([])
const prevAnswers = ref([])
const todayDate = ref('')
const displayDate = ref('')

onLoad((options) => {
  const d = options.date || formatDate(new Date())
  todayDate.value = d
  const p = d.split('-')
  displayDate.value = parseInt(p[1]) + '月' + parseInt(p[2]) + '日'
  contentService.getPoliticalQuestions(d).then(res => {
    questions.value = res?.data?.questions || []
    loading.value = false
  })
})

function onAnswer(idx, e) {
  contentService.recordProgress(todayDate.value, 'politicalTheory', { questionId: e.questionId, isCorrect: e.isCorrect })
  const q = questions.value[idx]
  if (q) {
    quizStore.recordAnswer({
      questionId: e.questionId,
      date: todayDate.value,
      module: 'politicalTheory',
      selectedOption: e.selectedOption,
      correctAnswer: e.correctAnswer,
      isCorrect: e.isCorrect,
      questionData: {
        questionId: q.questionId,
        question: q.question,
        questionType: q.questionType,
        options: q.options,
        correctAnswer: q.correctAnswer,
        analysis: q.analysis,
        extendedKnowledge: q.extendedKnowledge,
        tags: q.tags,
        examFrequency: q.examFrequency,
        source: q.source,
        sourcePublishDate: q.sourcePublishDate,
        date: q.date,
      },
    })
  }
}
function formatDate(d) { return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx; }
.page-header { padding: 32rpx 0 24rpx; }
.page-title { font-family: var(--font-title); font-size: 42rpx; font-weight: 700; color: var(--accent-vermillion); display: block; }
.page-date { font-size: 22rpx; color: var(--text-tertiary); margin-top: 8rpx; }
.skeleton-list { padding: 24rpx 0; }
.sk-item { height: 300rpx; background: var(--divider); border-radius: 12rpx; margin-bottom: 24rpx; }
.empty { display: flex; justify-content: center; padding: 64rpx 0; color: var(--text-secondary); }
.q-number { padding: 16rpx 0 8rpx; font-family: var(--font-title); font-size: 30rpx; color: var(--accent-vermillion); font-weight: 700; }
</style>
