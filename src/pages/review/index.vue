<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">错题回顾</text>
      <text class="page-subtitle mono text-2xs warm-gray">{{ wrongCount }} 题待复习</text>
    </view>

    <!-- Loading -->
    <view v-if="loading" class="skeleton-list">
      <view v-for="i in 3" :key="i" class="sk-item" />
    </view>

    <!-- Empty state -->
    <view v-else-if="!groupedWrongs.length" class="empty">
      <text class="empty-icon">✓</text>
      <text class="empty-main">暂无错题，继续保持！</text>
      <text class="empty-sub mono text-2xs light-gray">做错的题目会自动出现在这里</text>
    </view>

    <!-- Wrong questions grouped by date -->
    <view v-else class="wrong-list">
      <view v-for="group in groupedWrongs" :key="group.date" class="date-group">
        <view class="date-head">
          <text class="date-label serif">{{ formatDateLabel(group.date) }}</text>
          <text class="date-count mono text-2xs light-gray">{{ group.items.length }} 题</text>
        </view>
        <view class="hr" />

        <view v-for="item in group.items" :key="item.questionId" class="wrong-item">
          <!-- Collapsed header -->
          <view class="wrong-head" @click="toggleExpand(item.questionId)">
            <text class="q-id mono text-2xs accent">Q</text>
            <text class="q-preview serif text-sm">{{ item.questionData?.question || '题目加载中' }}</text>
            <view class="meta-stack">
              <text class="mono text-2xs warm-gray">已答 {{ getRetryCount(item.questionId) }} 次</text>
              <text class="mono text-2xs warm-gray" v-if="item.date">最后错题 {{ formatShortDate(item.date) }}</text>
            </view>
            <text class="expand-icon mono accent">{{ expanded[item.questionId] ? '−' : '+' }}</text>
          </view>

          <!-- Expanded re-answer area -->
          <view v-if="expanded[item.questionId]" class="q-body">
            <exam-question
              v-bind="item.questionData"
              :key="'re-' + item.questionId + '-' + answerVersion"
              @answer="onReAnswer(item, $event)"
            />
          </view>
        </view>
      </view>
    </view>

    <!-- Bottom padding -->
    <view class="bottom-spacer" />
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useQuizStore } from '@/store/quiz.js'
import examQuestion from '@/components/exam-question.vue'

const store = useQuizStore()
const loading = ref(false)
const expanded = reactive({})
const answerVersion = ref(0)

const wrongCount = computed(() => store.wrongQuestions.length)

// Group wrong questions by date, newest first
const groupedWrongs = computed(() => {
  const items = store.wrongQuestions.map(item => ({
    ...item,
    _retryCount: store.getRetryCount(item.questionId),
  }))

  const groups = {}
  for (const item of items) {
    const d = item.date || 'unknown'
    if (!groups[d]) groups[d] = []
    groups[d].push(item)
  }

  return Object.entries(groups)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([date, items]) => ({ date, items }))
})

function formatDateLabel(dateStr) {
  if (!dateStr) return ''
  const p = dateStr.split('-')
  return parseInt(p[1]) + '月' + parseInt(p[2]) + '日'
}

function formatShortDate(dateStr) {
  return formatDateLabel(dateStr)
}

function toggleExpand(questionId) {
  expanded[questionId] = !expanded[questionId]
}

function getRetryCount(questionId) {
  return store.getRetryCount(questionId)
}

function onReAnswer(item, e) {
  store.recordAnswer({
    questionId: e.questionId,
    date: item.date,
    module: item.module || 'politicalTheory',
    selectedOption: e.selectedOption,
    correctAnswer: e.correctAnswer,
    isCorrect: e.isCorrect,
    questionData: item.questionData,
  })

  if (e.isCorrect) {
    // Collapse if answered correctly — confirmatory feedback
    expanded[e.questionId] = false
  }

  // Force re-mount of exam-question for next tap
  answerVersion.value++

  uni.showToast({
    title: e.isCorrect ? '回答正确！' : '回答错误',
    icon: e.isCorrect ? 'success' : 'none',
    duration: 1200,
  })
}
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  background: var(--bg-paper);
  padding: 0 24px;
}

/* ---- Header ---- */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 32px 0 24px;
}
.page-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--accent);
}
.page-subtitle {
  letter-spacing: 0.06em;
}

/* ---- Skeleton ---- */
.skeleton-list {
  padding: 16px 0;
}
.sk-item {
  height: 80px;
  background: var(--border-light);
  margin-bottom: 12px;
}

/* ---- Empty ---- */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0;
}
.empty-icon {
  font-size: 48px;
  color: var(--correct);
  margin-bottom: 16px;
  opacity: 0.6;
}
.empty-main {
  font-family: var(--font-serif);
  font-size: var(--text-md);
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.empty-sub {
  letter-spacing: 0.06em;
}

/* ---- Date Group ---- */
.date-group {
  margin-bottom: 32px;
}
.date-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 8px 0 12px;
}
.date-label {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.06em;
}
.date-count {
  letter-spacing: 0.06em;
}

/* ---- Wrong Item ---- */
.wrong-item {
  border-bottom: 1px solid var(--border-light);
}
.wrong-item:last-child {
  border-bottom: none;
}

.wrong-head {
  padding: 16px 0;
  cursor: pointer;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  position: relative;
}
.wrong-head:active {
  opacity: 0.6;
}

.q-id {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.q-preview {
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--text-primary);
  letter-spacing: 0.04em;
  line-height: 1.5;
  padding-right: 20px;
}

.meta-stack {
  width: 100%;
  display: flex;
  gap: 16px;
  padding-left: 28px;
}
.meta-stack text {
  letter-spacing: 0.06em;
}

.expand-icon {
  position: absolute;
  right: 0;
  top: 16px;
  font-size: var(--text-md);
  font-weight: 600;
  width: 20px;
  text-align: center;
}

/* ---- Question Body (expanded) ---- */
.q-body {
  padding: 0 0 20px 0;
  margin-top: 4px;
}

/* ---- Bottom spacer ---- */
.bottom-spacer {
  height: 48px;
}
</style>
