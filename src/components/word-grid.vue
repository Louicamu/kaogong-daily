<template>
  <view class="word-grid">
    <view class="grid-header">
      <text class="stats-text">今日词汇 <text class="hl">15</text> 词 · 已翻转 <text class="hl">{{ flippedCount }}</text> · 已掌握 <text class="hl">{{ masteredCount }}</text></text>
      <view class="ratio-badges">
        <text class="badge badge-high">高频 10</text>
        <text class="badge badge-pred">预测 5</text>
      </view>
    </view>
    <!-- 高频区 -->
    <view class="section">
      <view class="section-title">
        <text class="title-high">高频常考词汇</text>
        <view class="stripe-high" />
      </view>
      <view class="grid-5x2">
        <word-card v-for="w in highWords" :key="w.wordId" v-bind="w" :isHighFreq="true" :dueForReview="dueWordIds.has(w.wordId)" @flip="onFlip" @master="onMaster(w.wordId, $event)" />
      </view>
    </view>
    <!-- 分割 -->
    <view class="section-divider">
      <view class="divider-ornament" />
      <text class="divider-text">✦ 拓展积累 ✦</text>
      <view class="divider-ornament" />
    </view>
    <!-- 预测区 -->
    <view class="section">
      <view class="section-title">
        <text class="title-pred">预测新词积累</text>
        <view class="stripe-pred" />
      </view>
      <view class="grid-5col">
        <word-card v-for="w in predWords" :key="w.wordId" v-bind="w" :isHighFreq="false" :dueForReview="dueWordIds.has(w.wordId)" @flip="onFlip" @master="onMaster(w.wordId, $event)" />
      </view>
    </view>
    <view v-if="masteredCount >= 4" class="encouragement">
      <text>{{ masteredCount >= 7 ? '今日词汇已掌握过半 ✨' : '已掌握过半，继续加油！' }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import wordCard from './word-card.vue'
import { useQuizStore } from '@/store/quiz'

const props = defineProps({ words: Array, date: String })
const emit = defineEmits(['wordflip', 'masterchange'])
const flippedCount = ref(0)
const masterState = ref({})

const quizStore = useQuizStore()

const highWords = computed(() => (props.words || []).filter(w => w.isHighFreq))
const predWords = computed(() => (props.words || []).filter(w => !w.isHighFreq))
const masteredCount = computed(() => Object.values(masterState.value).filter(Boolean).length)

// Words due for review: check each word's wordId against the store
const dueWordIds = computed(() => {
  const ids = new Set()
  for (const w of (props.words || [])) {
    if (w.wordId && quizStore.isWordDue(w.wordId)) {
      ids.add(w.wordId)
    }
  }
  return ids
})

function onFlip() { flippedCount.value++ }
function onMaster(wordId, e) {
  masterState.value = { ...masterState.value, [wordId]: e.mastered }
  emit('masterchange', { wordId, mastered: e.mastered, masteredCount: masteredCount.value })
}
</script>

<style scoped>
.word-grid { padding: 16rpx 0; }
.grid-header { display: flex; justify-content: space-between; align-items: center; padding: 12rpx 0; margin-bottom: 24rpx; }
.stats-text { font-size: 22rpx; color: var(--text-tertiary); }
.hl { color: var(--accent-vermillion); font-weight: 500; }
.ratio-badges { display: flex; gap: 8rpx; }
.badge { padding: 4rpx 14rpx; border-radius: 2rpx; font-size: 20rpx; }
.badge-high { background: var(--accent-vermillion); color: #fff; }
.badge-pred { border: 1rpx solid #8B7D6B; color: #8B7D6B; }

.section { margin-bottom: 16rpx; }
.section-title { display: flex; align-items: center; margin-bottom: 24rpx; }
.title-high { font-family: var(--font-title); font-size: 30rpx; font-weight: 700; color: var(--accent-vermillion); padding-right: 16rpx; flex-shrink: 0; }
.title-pred { font-family: var(--font-title); font-size: 30rpx; font-weight: 700; color: #8B7D6B; padding-right: 16rpx; flex-shrink: 0; }
.stripe-high { flex: 1; height: 2rpx; background: var(--accent-vermillion-muted); opacity: 0.5; }
.stripe-pred { flex: 1; height: 1rpx; background: var(--divider); }

.grid-5x2 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; gap: 16rpx; }
.grid-5col { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; gap: 16rpx; }

.section-divider { display: flex; align-items: center; gap: 16rpx; margin: 32rpx 0; }
.divider-text { font-family: var(--font-title); font-size: 24rpx; color: var(--text-placeholder); white-space: nowrap; }

.encouragement { margin-top: 32rpx; text-align: center; font-family: var(--font-title); font-size: 28rpx; color: var(--accent-vermillion); }
</style>
