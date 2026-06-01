<template>
  <view class="eq">
    <view class="eq-head">
      <text class="mono text-2xs accent" style="letter-spacing:0.12em;">{{ qType === 'correct' ? 'SELECT CORRECT' : 'SELECT INCORRECT' }}</text>
      <view style="display:flex;gap:8px;">
        <text v-for="t in tags" :key="t" class="mono text-2xs warm-gray">{{ t }}</text>
      </view>
    </view>

    <text class="eq-q">{{ question }}</text>

    <view class="options">
      <view
        v-for="opt in optionList" :key="opt.key"
        class="opt"
        :class="{
          'opt-sel': selected === opt.key,
          'opt-ok': submitted && opt.key === correctAnswer,
          'opt-err': submitted && selected === opt.key && opt.key !== correctAnswer,
        }"
        @click="selectOption(opt.key)"
      >
        <text class="mono opt-key" :class="selected === opt.key ? 'accent' : 'warm-gray'">{{ opt.key }}</text>
        <text class="opt-txt">{{ opt.value }}</text>
        <text v-if="submitted && opt.key === correctAnswer" class="accent" style="flex-shrink:0;">✓</text>
        <text v-else-if="submitted && selected === opt.key" style="color:var(--wrong);flex-shrink:0;">✗</text>
      </view>
    </view>

    <view v-if="!submitted" style="margin-top:28px;">
      <view class="submit" :class="{ disabled: !selected }" @click="submit">
        <text class="mono text-xs" style="letter-spacing:0.12em;color:#fff;">SUBMIT</text>
      </view>
    </view>

    <view v-if="submitted" class="analysis">
      <view class="result" :class="isCorrect ? 'result-ok' : 'result-err'">
        <text class="mono text-xs">{{ isCorrect ? 'CORRECT' : 'INCORRECT — ANSWER: ' + correctAnswer }}</text>
      </view>
      <view style="margin-top:20px;">
        <text class="mono text-2xs accent" style="display:block;margin-bottom:6px;">ANALYSIS</text>
        <text class="serif text-sm ink" style="line-height:1.7;">{{ analysis }}</text>
      </view>
      <view v-if="extendedKnowledge" style="margin-top:16px;padding:12px;background:#F5F2ED;border-left:2px solid #C1272D;">
        <text class="mono text-2xs accent" style="display:block;margin-bottom:4px;">EXTENDED</text>
        <text class="serif text-sm ink">{{ extendedKnowledge }}</text>
      </view>
    </view>

    <view class="hr" style="margin-top:32px;" />
    <text class="sans text-2xs light-gray" style="display:block;margin-top:8px;">{{ source }} · {{ sourcePublishDate }}</text>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  questionId: String, question: String, questionType: { type: String, default: 'correct' },
  options: Object, correctAnswer: String, analysis: String, extendedKnowledge: String,
  tags: Array, examFrequency: String, source: String, sourcePublishDate: String,
  date: String, previousAnswer: String,
})
const emit = defineEmits(['answer'])
const selected = ref(props.previousAnswer || '')
const submitted = ref(!!props.previousAnswer)
const isCorrect = computed(() => selected.value === props.correctAnswer)
const qType = computed(() => props.questionType)
const optionList = computed(() => Object.entries(props.options || {}).map(([k, v]) => ({ key: k, value: v })))

function selectOption(key) { if (!submitted.value) selected.value = key }
function submit() {
  if (!selected.value) return; submitted.value = true
  emit('answer', { questionId: props.questionId, selectedOption: selected.value, correctAnswer: props.correctAnswer, isCorrect: isCorrect.value })
}
</script>

<style scoped>
.eq { padding: 0; }
.eq-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 8px; }

.eq-q {
  font-family: var(--font-serif); font-size: var(--text-md); color: var(--text-primary);
  letter-spacing: 0.05em; line-height: 1.7; display: block;
}

.options { display: flex; flex-direction: column; gap: 1px; margin-top: 28px; }
.opt {
  display: flex; align-items: flex-start; gap: 14px; padding: 14px 0;
  border-bottom: 1px solid var(--border-light); transition: background 0.15s;
}
.opt-sel { background: #FCFAF7; }
.opt-ok { background: #F7FAF5; }
.opt-err { background: #FDF7F7; }
.opt-key { font-size: var(--text-base); font-weight: 600; width: 24px; flex-shrink: 0; }
.opt-txt {
  flex: 1; font-family: var(--font-serif); font-size: var(--text-base);
  color: var(--text-primary); letter-spacing: 0.04em; line-height: 1.55;
}

.submit {
  display: flex; justify-content: center; padding: 14px 0;
  background: #C1272D; cursor: pointer;
}
.submit.disabled { background: #E6E2DA; }
.submit:active { opacity: 0.85; }

.analysis { margin-top: 28px; }
.result { padding: 10px 14px; }
.result-ok { background: #F2F7F0; }
.result-err { background: #FDF5F5; }
</style>
