<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">选词填空积累</text>
      <text class="page-date">{{ displayDate }}</text>
    </view>
    <view v-if="loading" class="skeleton-list"><view v-for="i in 3" :key="i" class="sk-item" /></view>
    <view v-else-if="!words.length" class="empty"><text>今日暂无词汇</text></view>
    <view v-else>
      <word-grid :words="words" :date="todayDate" @masterchange="onMasterChange" />
      <view v-if="!saved" class="save-area"><button class="btn-save" @click="saveProgress">完成今日词汇学习</button></view>
      <view v-else class="save-done"><text>✓ 学习进度已保存</text></view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'
import wordGrid from '@/components/word-grid.vue'
import { useQuizStore } from '@/store/quiz.js'

const quizStore = useQuizStore()
const loading = ref(true)
const words = ref([])
const todayDate = ref('')
const displayDate = ref('')
const saved = ref(false)
const masterState = ref({})

onLoad((options) => {
  const d = options.date || formatDate(new Date())
  todayDate.value = d
  displayDate.value = d.split('-')[1] + '月' + d.split('-')[2] + '日'
  contentService.getDailyWordSet(d).then(res => {
    words.value = res?.data?.words || []
    loading.value = false
  })
})

function onMasterChange(e) {
  masterState.value[e.wordId] = e.mastered
  const wordObj = words.value.find(w => w.wordId === e.wordId)
  quizStore.recordWordMastery({
    wordId: e.wordId,
    word: wordObj?.word || '',
    status: e.mastered ? 'mastered' : 'struggling',
  })
}
function saveProgress() {
  contentService.recordProgress(todayDate.value, 'wordSet', { completed: true, masterState: masterState.value })
  saved.value = true
  uni.showToast({ title: '已保存', icon: 'success' })
}
function formatDate(d) { return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx 48rpx; }
.page-header { padding: 32rpx 0 24rpx; }
.page-title { font-family: var(--font-title); font-size: 42rpx; font-weight: 700; color: var(--accent-vermillion); display: block; }
.page-date { font-size: 22rpx; color: var(--text-tertiary); margin-top: 8rpx; }
.skeleton-list { padding: 24rpx 0; }
.sk-item { height: 200rpx; background: var(--divider); border-radius: 12rpx; margin-bottom: 16rpx; }
.empty { display: flex; justify-content: center; padding: 64rpx 0; color: var(--text-secondary); }
.save-area { margin: 32rpx 0; }
.btn-save { width: 100%; padding: 16rpx 0; background: var(--accent-vermillion); color: #fff; font-family: var(--font-title); font-size: 30rpx; letter-spacing: 4rpx; border: none; border-radius: 12rpx; }
.save-done { text-align: center; padding: 32rpx; font-family: var(--font-title); font-size: 30rpx; color: var(--correct-color); }
</style>
