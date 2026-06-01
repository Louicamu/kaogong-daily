<template>
  <view class="page-wrap">
    <view class="article-header">
      <text class="article-title">{{ essay.title }}</text>
      <view class="article-meta">
        <text class="meta-source">{{ essay.source }}</text>
        <text> · </text>
        <text class="meta-date">{{ essay.sourcePublishDate }}</text>
        <text> · </text>
        <text class="meta-read">阅读约{{ essay.readingTime }}分钟</text>
      </view>
    </view>
    <view v-if="loading" class="skeleton-list"><view v-for="i in 3" :key="i" class="sk-item" /></view>
    <view v-else-if="!hasContent" class="empty"><text>今日暂无文段</text></view>
    <view v-else>
      <tab-section :sections="sections" :date="todayDate" />
      <view class="original-section">
        <view class="original-header" @click="expanded = !expanded">
          <text class="original-label">原文精选</text>
          <text class="expand-icon">{{ expanded ? '收起' : '展开' }}</text>
        </view>
        <view v-if="expanded" class="original-content">
          <text class="blockquote-text">{{ essay.originalExcerpt }}</text>
        </view>
      </view>
    </view>
    <view v-if="hasContent && !saved" class="save-area"><button class="btn-save" @click="saveProgress">完成今日申论学习</button></view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'
import tabSection from '@/components/tab-section.vue'

const loading = ref(true)
const hasContent = ref(false)
const essay = ref({})
const sections = ref([])
const todayDate = ref('')
const expanded = ref(false)
const saved = ref(false)

onLoad((options) => {
  const d = options.date || formatDate(new Date())
  todayDate.value = d
  contentService.getEssayPassage(d).then(res => {
    if (res?.data?.title) {
      essay.value = res.data
      sections.value = res.data.sections || []
      hasContent.value = true
    }
    loading.value = false
  })
})

function saveProgress() {
  contentService.recordProgress(todayDate.value, 'essayPassage', { completed: true })
  saved.value = true
  uni.showToast({ title: '已保存', icon: 'success' })
}
function formatDate(d) { return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx 48rpx; }
.article-header { padding: 32rpx 0 24rpx; }
.article-title { font-family: var(--font-title); font-size: 36rpx; font-weight: 700; color: var(--text-primary); display: block; line-height: 1.4; }
.article-meta { display: flex; align-items: center; gap: 4rpx; margin-top: 12rpx; flex-wrap: wrap; font-size: 22rpx; }
.meta-source { color: var(--accent-vermillion); }
.meta-date, .meta-read { color: var(--text-tertiary); }

.skeleton-list { padding: 24rpx 0; }
.sk-item { height: 200rpx; background: var(--divider); border-radius: 12rpx; margin-bottom: 16rpx; }
.empty { display: flex; justify-content: center; padding: 64rpx 0; color: var(--text-secondary); }

.original-section { margin: 32rpx 0; border-top: 1rpx dashed var(--divider); padding-top: 16rpx; }
.original-header { display: flex; justify-content: space-between; padding: 12rpx 0; }
.original-label { font-family: var(--font-title); font-size: 28rpx; color: var(--text-secondary); }
.expand-icon { font-size: 22rpx; color: var(--text-placeholder); }
.original-content { padding: 16rpx 0; }
.blockquote-text { font-size: 24rpx; line-height: 2; color: var(--text-secondary); display: block; text-align: justify; text-indent: 2em; }

.save-area { margin: 32rpx 0; }
.btn-save { width: 100%; padding: 16rpx 0; background: var(--accent-vermillion); color: #fff; font-family: var(--font-title); font-size: 30rpx; letter-spacing: 4rpx; border: none; border-radius: 12rpx; }
</style>
