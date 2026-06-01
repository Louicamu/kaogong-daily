<template>
  <view class="page-wrap">
    <view class="page-header">
      <text class="page-title">我的收藏</text>
      <text class="page-count">{{ favorites.length }} 条</text>
    </view>
    <view v-if="loading" class="skeleton-list"><view v-for="i in 3" :key="i" class="sk-item" /></view>
    <view v-else-if="!favorites.length" class="empty">
      <text class="empty-icon">♡</text>
      <text class="empty-title">暂无收藏</text>
      <text class="empty-desc">学习时点击收藏按钮，好词好句不错过</text>
    </view>
    <view v-else class="fav-list">
      <view v-for="f in favorites" :key="f._id" class="fav-item" @click="goItem(f)">
        <view class="fav-type" :class="f.itemType"><text>{{ typeLabel[f.itemType] || '收藏' }}</text></view>
        <view class="fav-content">
          <text class="fav-text">{{ f.title || '无标题' }}</text>
          <text class="fav-date">{{ f.date }}</text>
        </view>
        <text class="fav-arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'

const loading = ref(true)
const favorites = ref([])
const typeLabel = { political_theory: '政治', word: '词汇', essay_passage: '申论' }

onShow(() => {
  contentService.getFavorites().then(res => {
    favorites.value = res?.data?.items || []
    loading.value = false
  })
})

function goItem(f) {
  const routes = { political_theory: '/pages/political/index', word: '/pages/words/index', essay_passage: '/pages/essay/index' }
  const url = routes[f.itemType]
  if (url) uni.navigateTo({ url: url + '?date=' + f.date })
}
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx; }
.page-header { display: flex; justify-content: space-between; align-items: baseline; padding: 32rpx 0 24rpx; }
.page-title { font-family: var(--font-title); font-size: 42rpx; font-weight: 700; color: var(--accent-vermillion); }
.page-count { font-size: 22rpx; color: var(--text-tertiary); }
.empty { display: flex; flex-direction: column; align-items: center; padding: 64rpx 0; }
.empty-icon { font-size: 80rpx; color: var(--divider); margin-bottom: 24rpx; }
.empty-title { font-size: 32rpx; color: var(--text-secondary); }
.empty-desc { font-size: 24rpx; color: var(--text-tertiary); margin-top: 12rpx; }
.fav-list { display: flex; flex-direction: column; }
.fav-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid var(--divider); }
.fav-type { padding: 4rpx 12rpx; border-radius: 2rpx; font-size: 20rpx; flex-shrink: 0; }
.fav-type.political_theory { background: var(--accent-vermillion-bg); color: var(--accent-vermillion); }
.fav-type.word { background: var(--tag-bg); color: var(--text-secondary); }
.fav-type.essay_passage { background: #F5EBE0; color: #8B7D6B; }
.fav-content { flex: 1; min-width: 0; }
.fav-text { font-size: 24rpx; color: var(--text-primary); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fav-date { font-size: 20rpx; color: var(--text-placeholder); margin-top: 4rpx; }
.fav-arrow { font-size: 36rpx; color: var(--text-placeholder); }
</style>
