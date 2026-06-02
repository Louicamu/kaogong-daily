<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">学习日历</text>
      <text class="page-subtitle">{{ currentMonth }}</text>
    </view>

    <!-- 搜索栏 -->
    <search-bar
      v-model="searchQuery"
      :results="searchResults"
      @search="onSearch"
      @select="onSelectResult"
    />

    <!-- 搜索模式：结果列表 -->
    <view v-if="isSearching" class="search-results-area">
      <view v-if="searchLoading" class="search-state">
        <text class="mono text-xs warm-gray">搜索中...</text>
      </view>
      <view v-else-if="searchResults.length === 0" class="search-state">
        <text class="serif text-sm warm-gray">未找到相关内容</text>
        <text class="mono text-2xs light-gray" style="display:block;margin-top:6rpx;">试试其他关键词</text>
      </view>
      <view v-else class="search-results-list">
        <view
          v-for="(r, i) in searchResults" :key="i"
          class="search-result-item"
          @click="onSelectResult(r)"
        >
          <text class="result-type" :class="'type-' + r.type">{{ r.typeLabel }}</text>
          <view class="result-body">
            <text class="result-title">{{ r.title }}</text>
            <text class="result-snippet">{{ r.snippet }}</text>
            <text class="result-date mono-sm">{{ r.date }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 日历模式 -->
    <view v-else>
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
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'
import { search as searchContent } from '@/services/search.js'
import searchBar from '@/components/search-bar.vue'

const weekdays = ['日','一','二','三','四','五','六']
const currentMonth = ref('')
const dateCells = ref([])
const today = ref(formatDate(new Date()))

// 搜索状态
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const isSearching = computed(() => searchQuery.value.length > 0)

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

// 搜索处理
async function onSearch(query) {
  searchQuery.value = query
  if (!query) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    searchResults.value = await searchContent(query)
  } catch (e) {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

function onSelectResult(r) {
  searchQuery.value = ''
  searchResults.value = []
  if (r.route) {
    uni.navigateTo({ url: r.route })
  }
}
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

/* 搜索区域 */
.search-results-area { padding: 16rpx 0; min-height: 200rpx; }
.search-state { display: flex; flex-direction: column; align-items: center; padding: 48rpx 0; gap: 8rpx; }
.search-results-list { display: flex; flex-direction: column; }
.search-result-item { display: flex; align-items: flex-start; gap: 14rpx; padding: 18rpx 0; border-bottom: 1rpx solid var(--divider); cursor: pointer; }
.search-result-item:last-child { border-bottom: none; }
.search-result-item:active { opacity: 0.6; }

.result-type { padding: 2rpx 10rpx; border-radius: 2rpx; font-family: var(--font-sans); font-size: var(--text-2xs); flex-shrink: 0; line-height: 1.6; margin-top: 2rpx; }
.type-political { background: var(--accent-vermillion-bg); color: var(--accent-vermillion); }
.type-word { background: var(--tag-bg); color: var(--text-secondary); }
.type-essay { background: #F5EBE0; color: #8B7D6B; }

.result-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4rpx; }
.result-title { font-family: var(--font-title); font-size: 26rpx; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-snippet { font-size: 22rpx; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-date { font-size: 20rpx; color: var(--text-placeholder); }
.mono-sm { font-family: var(--font-mono); }
</style>
