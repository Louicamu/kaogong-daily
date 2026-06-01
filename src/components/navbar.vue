<template>
  <view class="navbar" :style="{ paddingTop: statusBarHeight + 'px', background: bgColor }">
    <view class="navbar-inner">
      <text class="navbar-title">{{ title }}</text>
    </view>
  </view>
</template>
<script setup>
import { ref } from 'vue'
defineProps({ title: { type: String, default: '考公每日学' }, bgColor: { type: String, default: '#F4F0EA' } })
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 20)
</script>
<style scoped>
.navbar { width: 100%; position: sticky; top: 0; z-index: 100; }
.navbar-inner { display: flex; align-items: center; justify-content: center; height: 44px; padding: 0 24rpx; }
.navbar-title { font-family: var(--font-title); font-size: 34rpx; font-weight: 700; color: var(--accent-vermillion); letter-spacing: 2rpx; }
</style>
