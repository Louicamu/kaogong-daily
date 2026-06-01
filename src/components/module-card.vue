<template>
  <view class="module-card" :class="{ completed }" @click="goPage">
    <view class="module-header">
      <image class="module-icon" :src="icon" mode="aspectFit" />
      <view class="module-title-group">
        <text class="module-title">{{ title }}</text>
        <text class="module-subtitle">{{ subtitle }}</text>
      </view>
      <view v-if="completed" class="completed-badge"><text>✓</text></view>
    </view>
    <view class="module-preview">
      <text v-if="previewText && type !== 'words'" class="preview-text line-clamp-2">{{ previewText }}</text>
      <view v-if="wordChips?.length" class="word-chips">
        <view v-for="(chip, i) in wordChips" :key="i" class="word-chip" :class="chip.isHighFreq ? 'chip-high' : 'chip-predictive'">
          <text class="chip-text">{{ chip.word }}</text>
        </view>
      </view>
      <view v-if="source" class="essay-source"><text>来源：{{ source }}</text></view>
    </view>
    <view class="module-footer">
      <view class="footer-tags">
        <text v-for="t in tags" :key="t" class="tag">{{ t }}</text>
      </view>
      <text v-if="readingTime" class="reading-time">阅读约{{ readingTime }}分钟</text>
    </view>
    <view class="bottom-accent" />
  </view>
</template>

<script setup>
const props = defineProps({
  type: String, icon: String, title: String, subtitle: String,
  previewText: String, questionType: String, wordChips: Array,
  source: String, tags: Array, readingTime: Number,
  completed: Boolean, navigatePath: String, date: String,
})
const emit = defineEmits(['cardtap'])
function goPage() {
  if (props.navigatePath) {
    uni.navigateTo({ url: props.navigatePath + (props.date ? '?date=' + props.date : '') })
  }
  emit('cardtap', { type: props.type, date: props.date })
}
</script>

<style scoped>
.module-card { position: relative; padding: 32rpx 0; transition: opacity 0.15s; }
.module-card:active { opacity: 0.7; }
.bottom-accent { width: 100%; height: 1rpx; background: linear-gradient(90deg, transparent, var(--accent-vermillion-muted) 15%, var(--accent-vermillion-muted) 85%, transparent); }

.module-header { display: flex; align-items: flex-start; gap: 16rpx; }
.module-icon { width: 52rpx; height: 52rpx; flex-shrink: 0; }
.module-title-group { flex: 1; }
.module-title { font-family: var(--font-title); font-size: 36rpx; font-weight: 700; color: var(--accent-vermillion); display: block; }
.completed .module-title { color: var(--text-tertiary); }
.module-subtitle { font-size: 22rpx; color: var(--text-tertiary); display: block; margin-top: 4rpx; }
.completed-badge { width: 40rpx; height: 40rpx; border-radius: 50%; background: var(--correct-color); display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; }

.module-preview { margin-top: 16rpx; padding-left: 68rpx; }
.preview-text { font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.word-chips { display: flex; flex-wrap: wrap; gap: 8rpx; }
.word-chip { padding: 6rpx 16rpx; border-radius: 20rpx; }
.chip-high { background: var(--accent-vermillion-bg); }
.chip-high .chip-text { color: var(--accent-vermillion); font-family: var(--font-title); font-size: 24rpx; font-weight: 500; }
.chip-predictive { background: var(--tag-bg); }
.chip-predictive .chip-text { color: #8B7D6B; font-family: var(--font-title); font-size: 24rpx; }

.essay-source { margin-top: 4rpx; font-size: 22rpx; color: var(--text-tertiary); }

.module-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 16rpx; padding-left: 68rpx; }
.footer-tags { display: flex; gap: 8rpx; }
.tag { display: inline-flex; padding: 4rpx 12rpx; font-size: 20rpx; background: var(--tag-bg); border-radius: 4rpx; color: var(--text-secondary); }
.reading-time { font-size: 20rpx; color: var(--text-placeholder); flex-shrink: 0; }
</style>
