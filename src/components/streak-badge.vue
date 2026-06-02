<template>
  <view class="streak-badge">
    <text v-if="store.checkToday()" class="mono text-xs warm-gray">
      &#x1F525; 连续学习 {{ store.currentStreak }} 天
    </text>
    <text v-else class="mono text-xs" style="color:var(--text-tertiary);">
      今日尚未打卡
    </text>
  </view>
</template>

<script setup>
import { useStreakStore } from '@/store/streak.js'

const store = useStreakStore()
</script>

<style scoped>
.streak-badge {
  display: inline-flex;
  align-items: center;
}
</style>
