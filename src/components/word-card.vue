<template>
  <view class="wrapper" @click="flip">
    <view class="flip" :class="{ flipped: isFlipped }">
      <!-- FRONT -->
      <view class="face front">
        <text class="mono freq" :class="isHighFreq ? 'accent' : 'warm-gray'">{{ isHighFreq ? 'HIGH' : 'PRED' }}</text>
        <text v-if="dueForReview" class="mono review-badge">REVIEW</text>
        <view class="word-block">
          <text class="serif word-main">{{ word }}</text>
          <text v-if="pinyin" class="sans text-2xs warm-gray" style="margin-top:4px;">{{ pinyin }}</text>
        </view>
        <text class="mono text-2xs light-gray" style="position:absolute;bottom:16px;">{{ category }}</text>
        <text class="mono text-2xs light-gray" style="position:absolute;bottom:4px;">— tap —</text>
      </view>
      <!-- BACK -->
      <view class="face back">
        <view class="back-top">
          <text class="serif text-md accent">{{ word }}</text>
          <text class="mono text-2xs" :class="isHighFreq ? 'accent' : 'warm-gray'">{{ isHighFreq ? 'HIGH FREQ' : 'PREDICTIVE' }}</text>
        </view>
        <scroll-view class="back-body" scroll-y>
          <view class="block">
            <text class="mono text-2xs accent" style="margin-bottom:4px;">DEFINITION</text>
            <text class="serif text-sm ink">{{ definition }}</text>
          </view>
          <view v-if="examContext" class="block">
            <text class="mono text-2xs accent" style="margin-bottom:4px;">CONTEXT</text>
            <text class="serif text-sm ink">{{ examContext }}</text>
          </view>
          <view v-if="sourceSentence" class="block quote">
            <text class="mono text-2xs warm-gray" style="margin-bottom:4px;">原文出处</text>
            <text class="serif text-sm ink" style="font-style:italic;">"{{ sourceSentence }}"</text>
            <text v-if="sourceArticle" class="mono text-2xs warm-gray" style="display:block;margin-top:4px;">—— {{ sourceArticle }}</text>
          </view>
          <view v-if="commonMistakes" class="block warn">
            <text class="mono text-2xs" style="color:var(--wrong);margin-bottom:4px;">COMMON MISTAKES</text>
            <text class="serif text-sm ink">{{ commonMistakes }}</text>
          </view>
        </scroll-view>
        <view class="back-foot">
          <text class="mono text-2xs" :class="mastered ? 'accent' : 'warm-gray'" @click.stop="toggleMaster">{{ mastered ? 'MASTERED' : 'MARK MASTERED' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({
  word: String, wordId: String, pinyin: String, definition: String,
  examContext: String, sourceSentence: String, sourceArticle: String,
  commonMistakes: String, category: String,
  isHighFreq: Boolean, mastered: Boolean, displayOrder: Number,
  dueForReview: Boolean,
})
const emit = defineEmits(['flip', 'master'])
const isFlipped = ref(false)
function flip() { isFlipped.value = !isFlipped.value; emit('flip', { wordId: props.wordId }) }
function toggleMaster() { emit('master', { wordId: props.wordId, mastered: !props.mastered }) }
</script>

<style scoped>
.wrapper { perspective: 1200px; width: 100%; aspect-ratio: 1 / 1.25; max-height: 400px; }
.flip { position: relative; width: 100%; height: 100%; transform-style: preserve-3d; transition: transform 0.55s cubic-bezier(0.4,0,0.2,1); }
.flip.flipped { transform: rotateY(180deg); }
.face { position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; }

.front {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: #FBF9F6; border: 1px solid #E6E2DA; padding: 20px; z-index: 2;
}
.freq { position: absolute; top: 12px; left: 12px; font-size: 10px; letter-spacing: 0.12em; }
.review-badge { position: absolute; top: 12px; right: 12px; font-size: 10px; letter-spacing: 0.12em; color: var(--accent-vermillion, #C1272D); }
.word-block { display: flex; flex-direction: column; align-items: center; }
.word-main { font-size: 44px; font-weight: 600; color: #191919; letter-spacing: 0.08em; }

.back {
  display: flex; flex-direction: column; background: #FBF9F6; border: 1px solid #E6E2DA;
  transform: rotateY(180deg); overflow: hidden;
}
.back-top { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #E6E2DA; flex-shrink: 0; }
.back-body { flex: 1; padding: 14px 16px; overflow-y: auto; }
.block { margin-bottom: 16px; }
.quote { padding: 10px; background: #F5F2ED; border-left: 2px solid #C1272D; }
.warn { padding: 10px; background: #FEF9F8; border-left: 2px solid #B71C1C; }
.back-foot { padding: 10px 16px; border-top: 1px solid #E6E2DA; flex-shrink: 0; text-align: right; }
</style>
