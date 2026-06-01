<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">学习日历</text>
      <text class="page-subtitle">{{ currentMonth }}</text>
    </view>
    <view class="month-nav">
      <text class="nav-arrow" @click="prevMonth">‹</text>
      <text class="nav-label">{{ currentMonth }}</text>
      <text class="nav-arrow" @click="nextMonth">›</text>
    </view>
    <view class="weekday-row">
      <text v-for="d in weekdays" :key="d" class="weekday">{{ d }}</text>
    </view>
    <view class="date-grid">
      <view
        v-for="(cell, i) in dateCells" :key="i"
        class="date-cell"
        :class="{
          'cell-today': cell.isToday,
          'cell-has-content': cell.hasContent,
          'cell-studied': cell.isStudied,
          'cell-other': !cell.inMonth,
        }"
        @click="onTapDate(cell.date)"
      >
        <text class="date-num">{{ cell.day }}</text>
        <view v-if="cell.hasContent && !cell.isStudied" class="date-dot" />
        <text v-if="cell.isStudied" class="date-check">✓</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'

const weekdays = ['日','一','二','三','四','五','六']
const currentMonth = ref('')
const dateCells = ref([])
const today = ref(formatDate(new Date()))

function formatDate(d) { return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }

onLoad(() => {
  const now = new Date()
  today.value = formatDate(now)
  loadMonth(now.getFullYear(), now.getMonth() + 1)
})

function loadMonth(y, m) {
  const mStr = String(m).padStart(2,'0')
  currentMonth.value = `${y}-${mStr}`
  contentService.getCalendar(`${y}-${mStr}`).then(res => {
    const dateMap = {}
    ;(res?.data?.publishedDates || []).forEach(d => { dateMap[d.date] = d })
    const firstDay = new Date(y, m-1, 1).getDay()
    const daysInMonth = new Date(y, m, 0).getDate()
    const cells = []
    for (let i = 0; i < firstDay; i++) cells.push({ day: '', inMonth: false, date: '' })
    for (let d = 1; d <= daysInMonth; d++) {
      const ds = `${y}-${mStr}-${String(d).padStart(2,'0')}`
      cells.push({
        day: d, inMonth: true, date: ds,
        isToday: ds === today.value,
        hasContent: !!dateMap[ds],
        isStudied: dateMap[ds]?.studied,
      })
    }
    dateCells.value = cells
  }).catch(() => {
    // 离线日历
    const firstDay = new Date(y, m-1, 1).getDay()
    const daysInMonth = new Date(y, m, 0).getDate()
    const cells = []
    for (let i = 0; i < firstDay; i++) cells.push({ day: '', inMonth: false, date: '' })
    for (let d = 1; d <= daysInMonth; d++) {
      const ds = `${y}-${mStr}-${String(d).padStart(2,'0')}`
      cells.push({ day: d, inMonth: true, date: ds, isToday: ds === today.value, hasContent: false, isStudied: false })
    }
    dateCells.value = cells
  })
}

function prevMonth() { const [y,m] = currentMonth.value.split('-').map(Number); loadMonth(y, m-1 || 12) }
function nextMonth() { const [y,m] = currentMonth.value.split('-').map(Number); loadMonth(m===12?y+1:y, m===12?1:m+1) }
function onTapDate(date) { if (date) uni.navigateTo({ url: '/pages/index/index?targetDate=' + date }) }
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx; }
.page-header { padding: 32rpx 0 8rpx; }
.page-title { font-family: var(--font-title); font-size: 42rpx; font-weight: 700; color: var(--accent-vermillion); display: block; }
.page-subtitle { font-size: 22rpx; color: var(--text-tertiary); }
.month-nav { display: flex; justify-content: space-between; align-items: center; padding: 16rpx 0; }
.nav-arrow { padding: 8rpx 16rpx; font-size: 48rpx; color: var(--accent-vermillion); }
.nav-label { font-family: var(--font-title); font-size: 32rpx; color: var(--text-primary); }
.weekday-row { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; padding-bottom: 12rpx; border-bottom: 1rpx solid var(--divider); }
.weekday { font-size: 22rpx; color: var(--text-tertiary); padding: 8rpx 0; }
.date-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8rpx; margin-top: 12rpx; }
.date-cell { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 6rpx; position: relative; }
.cell-today { background: var(--accent-vermillion-bg); }
.cell-other .date-num { color: var(--divider); }
.cell-studied { background: #F0F8F0; }
.date-num { font-size: 28rpx; color: var(--text-primary); }
.date-dot { width: 8rpx; height: 8rpx; border-radius: 50%; background: var(--accent-vermillion); margin-top: 2rpx; }
.date-check { font-size: 20rpx; color: var(--correct-color); margin-top: 2rpx; }
</style>
