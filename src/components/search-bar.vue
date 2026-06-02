<template>
  <view class="search-wrap">
    <view class="search-input-row">
      <input
        class="search-input"
        type="text"
        :placeholder="placeholder"
        :value="modelValue"
        @input="onInput"
        @focus="focused = true"
        @blur="onBlur"
      />
      <text class="search-icon" @click="onSearch">Search</text>
    </view>
    <view v-if="focused && modelValue && results.length" class="search-dropdown">
      <view
        v-for="(r, i) in results" :key="i"
        class="search-result-item"
        @click="onSelect(r)"
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
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '搜索历史内容...' },
  results: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'search', 'select'])

const focused = ref(false)
let debounceTimer = null

function onInput(e) {
  const val = e.detail?.value ?? ''
  emit('update:modelValue', val)
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('search', val)
  }, 300)
}

function onBlur() {
  // 延迟隐藏，给点击结果留时间注册
  setTimeout(() => {
    focused.value = false
  }, 200)
}

function onSearch() {
  if (props.modelValue) {
    emit('search', props.modelValue)
  }
}

function onSelect(r) {
  focused.value = false
  emit('select', r)
}
</script>

<style scoped>
.search-wrap { position: relative; }

.search-input-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding: 14rpx 0;
}

.search-input {
  flex: 1;
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--text-primary);
  border: none;
  outline: none;
  background: transparent;
  height: 44rpx;
  letter-spacing: 0.04em;
}
.search-input::placeholder {
  color: var(--text-tertiary);
  font-family: var(--font-serif);
}

.search-icon {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--accent);
  cursor: pointer;
  padding-left: 12rpx;
  flex-shrink: 0;
  letter-spacing: 0.08em;
}

/* ===== 下拉面板 ===== */
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-paper);
  border: 1px solid var(--border);
  border-top: none;
  z-index: 200;
  max-height: 560rpx;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  padding: 18rpx 16rpx;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
}
.search-result-item:last-child {
  border-bottom: none;
}
.search-result-item:active {
  background: var(--border-light);
}

.result-type {
  padding: 2rpx 10rpx;
  border-radius: 2rpx;
  font-family: var(--font-sans);
  font-size: var(--text-2xs);
  flex-shrink: 0;
  line-height: 1.6;
  margin-top: 2rpx;
}
.type-political {
  background: var(--accent-muted);
  color: var(--accent);
}
.type-word {
  background: #E8E0D8;
  color: var(--text-secondary);
}
.type-essay {
  background: #F5EBE0;
  color: #8B7D6B;
}

.result-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.result-title {
  font-family: var(--font-serif);
  font-size: var(--text-sm);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-snippet {
  font-family: var(--font-serif);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-date {
  font-size: 10px;
  color: var(--text-tertiary);
}
.mono-sm {
  font-family: var(--font-mono);
}
</style>
