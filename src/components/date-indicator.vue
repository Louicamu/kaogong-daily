<template>
  <view class="date-indicator">
    <view class="date-main">
      <text class="date-number">{{ monthDay }}</text>
      <text class="date-divider">·</text>
      <text class="date-weekday">{{ dayOfWeek }}</text>
    </view>
    <text class="date-label">今日学习</text>
  </view>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ date: String, dayOfWeek: String })
const monthDay = computed(() => {
  if (!props.date) return ''
  const p = props.date.split('-')
  return parseInt(p[1]) + '月' + parseInt(p[2]) + '日'
})
</script>
<style scoped>
.date-indicator { display: flex; align-items: baseline; justify-content: space-between; padding: 32rpx 0 16rpx; }
.date-main { display: flex; align-items: baseline; gap: 12rpx; }
.date-number { font-family: var(--font-title); font-size: 48rpx; font-weight: 700; color: var(--accent-vermillion); }
.date-divider { font-size: 36rpx; color: var(--accent-vermillion-muted); }
.date-weekday { font-family: var(--font-title); font-size: 32rpx; color: var(--text-secondary); }
.date-label { font-size: 22rpx; color: var(--text-placeholder); }
</style>
