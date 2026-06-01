<template>
  <view class="page-wrap">
    <view class="profile-header">
      <view class="avatar"><text class="avatar-text">学</text></view>
      <text class="user-name">考公人</text>
      <text class="user-slogan">合抱之木，生于毫末</text>
    </view>
    <view class="stats-section">
      <view class="stat-item">
        <text class="stat-number">{{ stats.totalStudyDays }}</text>
        <text class="stat-label">学习天数</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number">{{ stats.streak }}</text>
        <text class="stat-label">连续天数</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number">{{ stats.totalFavorites }}</text>
        <text class="stat-label">收藏数</text>
      </view>
    </view>
    <view class="menu-section">
      <view class="menu-item" @click="goTab('favorites')"><text>我的收藏</text><text class="menu-arrow">›</text></view>
      <view class="menu-item" @click="goTab('calendar')"><text>学习日历</text><text class="menu-arrow">›</text></view>
      <view class="menu-item"><text>关于考公每日学</text><text class="menu-version">v1.0.0</text></view>
    </view>
    <view class="quote-section">
      <view class="divider-ornament" />
      <text class="quote-text">"日积月累，功不唐捐"</text>
      <view class="divider-ornament" />
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import contentService from '@/services/content.js'

const stats = ref({ totalStudyDays: 0, streak: 0, totalFavorites: 0 })

onShow(() => {
  contentService.getFavorites().then(res => {
    let studyDays = 0
    try {
      const info = uni.getStorageInfoSync()
      studyDays = (info.keys || []).filter(k => k.startsWith('kc_progress_')).length
    } catch (_) {}
    stats.value = {
      totalStudyDays: studyDays,
      streak: studyDays,
      totalFavorites: res?.data?.total || 0,
    }
  })
})

function goTab(page) {
  uni.switchTab({ url: '/pages/' + page + '/index' })
}
</script>

<style scoped>
.page-wrap { min-height: 100vh; background: var(--bg-kraft); padding: 0 24rpx; }
.profile-header { display: flex; flex-direction: column; align-items: center; padding: 48rpx 0 32rpx; }
.avatar { width: 100rpx; height: 100rpx; border-radius: 50%; background: var(--accent-vermillion); display: flex; align-items: center; justify-content: center; margin-bottom: 16rpx; }
.avatar-text { color: #fff; font-family: var(--font-title); font-size: 42rpx; }
.user-name { font-family: var(--font-title); font-size: 32rpx; color: var(--text-primary); }
.user-slogan { font-size: 22rpx; color: var(--text-tertiary); margin-top: 8rpx; }

.stats-section { display: flex; align-items: center; justify-content: center; padding: 24rpx 0; border-top: 1rpx solid var(--divider); border-bottom: 1rpx solid var(--divider); }
.stat-item { flex: 1; display: flex; flex-direction: column; align-items: center; }
.stat-number { font-family: Georgia, serif; font-size: 42rpx; font-weight: 700; color: var(--accent-vermillion); }
.stat-label { font-size: 22rpx; color: var(--text-tertiary); margin-top: 4rpx; }
.stat-divider { width: 1rpx; height: 40rpx; background: var(--divider); }

.menu-section { margin-top: 32rpx; }
.menu-item { display: flex; justify-content: space-between; align-items: center; padding: 16rpx 0; border-bottom: 1rpx solid var(--divider); font-size: 28rpx; color: var(--text-primary); }
.menu-arrow { color: var(--text-placeholder); font-size: 36rpx; }
.menu-version { color: var(--text-placeholder); font-size: 22rpx; }

.quote-section { display: flex; flex-direction: column; align-items: center; gap: 16rpx; margin: 64rpx 0; }
.quote-text { font-family: var(--font-title); font-size: 28rpx; color: var(--text-secondary); font-style: italic; }
</style>
