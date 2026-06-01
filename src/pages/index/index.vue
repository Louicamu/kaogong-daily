<template>
  <view class="page">
    <view class="nav">
      <text class="mono text-2xs accent" style="letter-spacing:0.14em;">KAOGONG DAILY</text>
    </view>

    <scroll-view class="main" scroll-y enhanced :show-scrollbar="false">
      <view class="date-row">
        <view>
          <text class="serif text-2xl ink" style="font-weight:600;">{{ monthDay }}</text>
          <text class="sans text-xs warm-gray" style="margin-left:8px;">{{ dayOfWeek }}</text>
        </view>
        <text class="mono text-xs" :class="store.completedCount === 3 ? 'accent' : 'warm-gray'">{{ store.completedCount }} / 3</text>
      </view>

      <view style="height:1px;background:var(--border);margin:16px 0 28px;">
        <view :style="{ height:'2px', background:'var(--accent)', width: store.progressPercent + '%', transition:'width 0.6s ease' }" />
      </view>

      <!-- 加载 -->
      <view v-if="store.loading" style="padding-top:40px;">
        <text class="mono text-xs warm-gray">LOADING...</text>
      </view>

      <!-- 空 -->
      <view v-else-if="!hasContent" style="padding:60px 0;text-align:center;">
        <text class="serif text-md ink">今日内容暂未更新</text>
        <text class="sans text-xs warm-gray" style="display:block;margin-top:8px;">每日 6:00 前更新</text>
      </view>

      <!-- 模块列表 -->
      <view v-else class="modules">

        <!-- 政治理论 -->
        <view v-if="store.modules.politicalTheory.available" class="module" @click="goPage('/pages/political/index')">
          <text class="mono text-2xs warm-gray" style="letter-spacing:0.12em;margin-bottom:12px;">POLITICAL THEORY</text>
          <text class="mod-title">{{ store.modules.politicalTheory.previewQuestion || '点击作答' }}</text>
          <view class="mod-foot">
            <text class="sans text-xs warm-gray">常识判断 · {{ store.modules.politicalTheory.count }} 题</text>
            <view v-if="store.progress.politicalTheory" class="dot" />
          </view>
          <view class="hr" style="margin-top:24px;" />
        </view>

        <!-- 选词填空 -->
        <view v-if="store.modules.wordSet.available" class="module" @click="goPage('/pages/words/index')">
          <text class="mono text-2xs warm-gray" style="letter-spacing:0.12em;margin-bottom:12px;">VOCABULARY · 4 : 3</text>
          <view class="word-row">
            <text v-for="(chip, i) in store.modules.wordSet.previewWords" :key="i"
              class="word-chip" :class="chip.isHighFreq ? 'ink' : 'warm-gray'"
            >{{ chip.word }}</text>
          </view>
          <view class="mod-foot">
            <text class="sans text-xs warm-gray">高频 {{ store.modules.wordSet.highFreqCount }} · 预测 {{ store.modules.wordSet.predictiveCount }}</text>
            <view v-if="store.progress.wordSet" class="dot" />
          </view>
          <view class="hr" style="margin-top:24px;" />
        </view>

        <!-- 申论文段 -->
        <view v-if="store.modules.essayPassage.available" class="module" @click="goPage('/pages/essay/index')">
          <text class="mono text-2xs warm-gray" style="letter-spacing:0.12em;margin-bottom:12px;">ARGUMENTATIVE ESSAY</text>
          <text class="mod-title">{{ store.modules.essayPassage.title }}</text>
          <view class="mod-foot">
            <text class="sans text-xs warm-gray">{{ store.modules.essayPassage.source }} · {{ store.modules.essayPassage.readingTime }}min</text>
            <view v-if="store.progress.essayPassage" class="dot" />
          </view>
          <view class="hr" style="margin-top:24px;" />
        </view>

      </view>

      <view style="padding:48px 0 32px;text-align:center;">
        <view class="hr-light" style="margin-bottom:20px;" />
        <text class="serif text-sm warm-gray" style="font-style:italic;">合抱之木，生于毫末；九层之台，起于累土。</text>
        <text class="mono text-2xs light-gray" style="display:block;margin-top:6px;">— 道德经</text>
      </view>
      <view style="height:env(safe-area-inset-bottom);" />
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useContentStore } from '@/store/content.js'

const store = useContentStore()
const hasContent = ref(true)
const monthDay = computed(() => { const d = new Date(); return (d.getMonth()+1) + '月' + d.getDate() + '日' })
const dayOfWeek = computed(() => '星期' + ['日','一','二','三','四','五','六'][new Date().getDay()])

onLoad(() => { store.loadDailyContent().then(ok => { hasContent.value = ok }) })
onShow(() => { if (!store.loading) store.loadDailyContent() })

function goPage(path) { uni.navigateTo({ url: path }) }
</script>

<style lang="scss" scoped>
.page { min-height: 100vh; background: var(--bg-paper); }
.nav { padding: 48px 24px 0; }
.main { height: 100vh; padding: 0 24px; }
.date-row { display: flex; justify-content: space-between; align-items: baseline; padding-top: 32px; }

.module { padding: 28px 0 0; cursor: pointer; }
.module:active { opacity: 0.6; }
.mod-title {
  font-family: var(--font-serif); font-size: var(--text-md); color: var(--text-primary);
  letter-spacing: 0.05em; line-height: 1.55; display: block;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.mod-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; }

.word-row { display: flex; flex-wrap: wrap; gap: 0; font-family: var(--font-serif); font-size: var(--text-base); letter-spacing: 0.06em; }
.word-chip::after { content: ' · '; color: var(--border); }
.word-chip:last-child::after { content: none; }

.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
</style>
