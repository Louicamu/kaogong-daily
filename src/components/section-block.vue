<template>
  <view class="section-block" :class="'block-' + type">
    <!-- 词汇 -->
    <block v-if="type === 'vocabulary'">
      <view class="vocab-header">
        <text class="vocab-word">{{ data.word }}</text>
        <view class="vocab-divider" />
      </view>
      <text class="context-sentence">"{{ data.contextSentence }}"</text>
      <text class="explanation-text">{{ data.explanation }}</text>
    </block>
    <!-- 论点 -->
    <block v-if="type === 'argument'">
      <view class="argument-header">
        <view class="dot" />
        <text class="argument-title">{{ data.pointTitle }}</text>
      </view>
      <text class="argument-content">{{ data.pointContent }}</text>
      <view v-if="data.usageGuide" class="argument-guide">
        <text class="guide-label">写作应用</text>
        <text class="guide-text">{{ data.usageGuide }}</text>
      </view>
      <view v-if="data.applicableTopics" class="argument-topics">
        <text class="topics-label">适用话题：</text>
        <text class="topics-text">{{ data.applicableTopics.join('、') }}</text>
      </view>
    </block>
    <!-- 论据 -->
    <block v-if="type === 'evidence'">
      <view class="evidence-type">
        <text class="evidence-tag" :class="data.evidenceType">
          {{ data.evidenceType === 'data' ? '数据' : data.evidenceType === 'case' ? '案例' : '引言' }}
        </text>
      </view>
      <text class="evidence-content">{{ data.content }}</text>
      <view v-if="data.source" class="evidence-source">
        <text>——{{ data.source }}</text>
      </view>
    </block>
  </view>
</template>

<script setup>
defineProps({ type: String, data: Object })
</script>

<style scoped>
.section-block { padding: 16rpx 0; border-bottom: 1rpx dashed var(--divider); }
.section-block:last-child { border-bottom: none; }

.vocab-header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 8rpx; }
.vocab-word { font-family: var(--font-title); font-size: 32rpx; font-weight: 700; color: var(--accent-vermillion); }
.vocab-divider { flex: 1; height: 1rpx; background: var(--divider-vermillion); }
.context-sentence { font-size: 24rpx; color: var(--text-secondary); font-style: italic; display: block; margin-bottom: 4rpx; padding-left: 8rpx; }
.explanation-text { font-size: 22rpx; color: var(--text-tertiary); display: block; padding-left: 8rpx; }

.argument-header { display: flex; align-items: flex-start; gap: 12rpx; margin-bottom: 8rpx; }
.dot { width: 8rpx; height: 8rpx; border-radius: 50%; background: var(--accent-vermillion); margin-top: 10rpx; flex-shrink: 0; }
.argument-title { font-family: var(--font-title); font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.argument-content { font-size: 28rpx; line-height: 1.7; color: var(--text-primary); display: block; padding-left: 20rpx; }
.argument-guide { padding: 8rpx; background: var(--tag-bg); border-radius: 6rpx; margin-top: 8rpx; margin-left: 20rpx; }
.guide-label { font-size: 20rpx; color: var(--accent-vermillion); font-weight: 700; display: block; }
.guide-text { font-size: 22rpx; color: var(--text-secondary); }
.argument-topics { margin-top: 8rpx; padding-left: 20rpx; }
.topics-label { font-size: 20rpx; color: var(--text-tertiary); }
.topics-text { font-size: 20rpx; color: var(--accent-vermillion); }

.evidence-type { margin-bottom: 8rpx; }
.evidence-tag { display: inline-block; padding: 2rpx 12rpx; border-radius: 2rpx; font-size: 20rpx; font-weight: 500; }
.evidence-tag.data { background: #E3F2FD; color: #1565C0; }
.evidence-tag.case { background: #F3E5F5; color: #7B1FA2; }
.evidence-tag.quote { background: #FFF3E0; color: #E65100; }
.evidence-content { font-size: 28rpx; line-height: 1.7; color: var(--text-primary); display: block; }
.evidence-source { margin-top: 8rpx; text-align: right; font-size: 20rpx; color: var(--text-placeholder); }
</style>
