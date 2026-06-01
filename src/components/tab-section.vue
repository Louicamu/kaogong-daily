<template>
  <view class="tab-section">
    <view class="tabs-header">
      <view v-for="tab in tabs" :key="tab.type" class="tab-item" :class="{ active: activeTab === tab.type }" @click="switchTab(tab.type)">
        <text class="tab-label">{{ tab.title }}</text>
      </view>
      <view class="tab-indicator" :style="{ transform: 'translateX(' + indicatorOffset + 'px)', width: indicatorWidth + 'px' }" />
    </view>
    <view class="tabs-content">
      <view v-for="tab in tabs" :key="tab.type" class="tab-panel" :class="{ visible: activeTab === tab.type }">
        <view class="panel-header">
          <text class="panel-title">{{ tab.title }}</text>
          <text class="panel-count">{{ tab.items.length }} 条</text>
        </view>
        <view class="panel-items">
          <section-block v-for="(block, i) in tab.items" :key="i" :type="tab.type" :data="block" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import sectionBlock from './section-block.vue'
const props = defineProps({ sections: Array, date: String })
const emit = defineEmits(['tabchange'])
const activeTab = ref('vocabulary')
const tabs = computed(() => (props.sections || []).map(s => ({ type: s.type, title: s.title, icon: s.icon, items: s.items || [] })))
const indicatorOffset = ref(0)
const indicatorWidth = ref(60)

watch(activeTab, (val) => {
  const idx = tabs.value.findIndex(t => t.type === val)
  indicatorOffset.value = idx * (uni.getSystemInfoSync().windowWidth / 3)
})

function switchTab(type) { activeTab.value = type; emit('tabchange', { activeTab: type }) }
</script>

<style scoped>
.tabs-header { display: flex; position: sticky; top: 0; z-index: 10; background: var(--bg-kraft); border-bottom: 1rpx solid var(--divider); }
.tab-item { flex: 1; display: flex; justify-content: center; padding: 20rpx 0; position: relative; }
.tab-label { font-family: var(--font-title); font-size: 28rpx; color: var(--text-tertiary); transition: color 0.15s; }
.tab-item.active .tab-label { color: var(--accent-vermillion); font-weight: 700; }
.tab-indicator { position: absolute; bottom: 0; left: 0; height: 4rpx; background: var(--accent-vermillion); transition: transform 0.3s ease; width: 60px; }

.tab-panel { display: none; padding-top: 16rpx; }
.tab-panel.visible { display: block; }
.panel-header { display: flex; align-items: baseline; gap: 12rpx; margin-bottom: 24rpx; }
.panel-title { font-family: var(--font-title); font-size: 32rpx; color: var(--accent-vermillion); font-weight: 700; }
.panel-count { font-size: 22rpx; color: var(--text-placeholder); }
.panel-items { display: flex; flex-direction: column; gap: 16rpx; }
</style>
