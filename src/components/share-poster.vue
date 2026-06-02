<template>
  <view class="poster-mask" @click.self="$emit('close')">
    <view class="poster-modal">
      <!-- hidden canvas -- only used for generation, not displayed -->
      <canvas
        canvas-id="sharePosterCanvas"
        class="poster-canvas-offscreen"
        :style="{ width: CANVAS_W + 'px', height: CANVAS_H + 'px' }"
      />

      <view class="poster-card">
        <!-- generated image -->
        <image
          v-if="posterReady && posterImage"
          :src="posterImage"
          class="poster-image"
          mode="aspectFit"
        />
        <!-- loading state -->
        <view v-else-if="!posterError" class="poster-loading">
          <view class="loading-ring" />
          <text class="loading-splash">生成学习海报...</text>
        </view>
        <!-- error state -->
        <view v-else class="poster-error">
          <text class="error-icon">!</text>
          <text class="error-text">{{ posterError }}</text>
        </view>
      </view>

      <view class="action-row">
        <view
          class="action-btn btn-save"
          :class="{ disabled: !posterReady }"
          @click="saveImage"
        >
          <text>保存图片</text>
        </view>
        <view class="action-btn btn-close" @click="$emit('close')">
          <text>关闭</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useContentStore } from '@/store/content.js'
import contentService from '@/services/content.js'

defineEmits(['close'])

// ---------- canvas constants ----------
const CANVAS_W = 540
const CANVAS_H = 864

// ---------- state ----------
const store = useContentStore()
const posterImage = ref('')
const posterReady = ref(false)
const posterError = ref('')

// ---------- data fetching ----------
async function fetchPosterData () {
  const now = new Date()
  const monthDay = (now.getMonth() + 1) + '月' + now.getDate() + '日'

  // ensure daily content is loaded
  if (!store.modules.politicalTheory.available && !store.loading) {
    await store.loadDailyContent().catch(() => {})
  }

  // --- compute stats from store ---
  const questionCount = store.modules.politicalTheory.count || 0
  const wordCount = store.modules.wordSet.totalWords
    || (store.modules.wordSet.highFreqCount + store.modules.wordSet.predictiveCount)
    || 0
  const essayCount = store.modules.essayPassage.available ? 1 : 0

  // --- fetch a quote from today's essay ---
  let quote = '改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。'
  try {
    const res = await contentService.getEssayPassage()
    if (res && res.code === 0 && res.data) {
      const essay = res.data
      // 1. prefer quote-type evidence
      if (essay.sections) {
        for (const sec of essay.sections) {
          if (sec.type === 'evidence' && sec.items) {
            const found = sec.items.find(i => i.evidenceType === 'quote')
            if (found) { quote = found.content; break }
          }
        }
      }
      // 2. fallback: argument point
      if (!quote && essay.sections) {
        for (const sec of essay.sections) {
          if (sec.type === 'argument' && sec.items && sec.items.length) {
            const p = sec.items[0].pointContent || sec.items[0].point
            if (p) { quote = p; break }
          }
        }
      }
      // 3. fallback: last sentence from originalExcerpt
      if (!quote && essay.originalExcerpt) {
        const parts = essay.originalExcerpt
          .split(/[。！？\n]/)
          .map(s => s.trim())
          .filter(s => s.length > 10)
        if (parts.length) quote = parts[parts.length - 1] + '。'
      }
    }
  } catch (_) { /* use default quote */ }

  // strip surrounding quotes
  quote = quote.replace(/^["""']+|["""']+$/g, '')

  return {
    dateStr: monthDay,
    quote,
    questionCount,
    wordCount,
    essayCount,
    completed: {
      politicalTheory: !!store.progress.politicalTheory,
      wordSet: !!store.progress.wordSet,
      essayPassage: !!store.progress.essayPassage,
    },
  }
}

// ---------- canvas drawing ----------
function wrapText (ctx, text, maxWidth) {
  const lines = []
  let line = ''
  for (const char of text) {
    const testLine = line + char
    if (ctx.measureText(testLine).width > maxWidth && line.length > 0) {
      lines.push(line)
      line = char
    } else {
      line = testLine
    }
  }
  if (line) lines.push(line)
  return lines
}

function drawCheckmark (ctx, cx, cy, size) {
  const s = size * 0.3
  ctx.beginPath()
  ctx.moveTo(cx - s, cy)
  ctx.lineTo(cx - s * 0.3, cy + s * 0.8)
  ctx.lineTo(cx + s * 1.1, cy - s * 0.6)
  ctx.stroke()
}

function drawFakeQR (ctx, x, y, size) {
  // outer frame
  ctx.setFillStyle('#191919')
  // three-position blocks
  const bs = size * 0.18
  ctx.fillRect(x + 3, y + 3, bs, bs)                     // top-left
  ctx.fillRect(x + size - bs - 3, y + 3, bs, bs)           // top-right
  ctx.fillRect(x + 3, y + size - bs - 3, bs, bs)           // bottom-left
  ctx.fillRect(x + size - bs - 3, y + size - bs - 3, bs, bs) // bottom-right
  // timing patterns
  ctx.fillRect(x + size * 0.45, y + size * 0.18, bs * 0.3, bs * 0.6)
  ctx.fillRect(x + size * 0.18, y + size * 0.45, bs * 0.6, bs * 0.3)
  ctx.fillRect(x + size * 0.45, y + size * 0.62, bs * 0.3, bs * 0.25)
  // scattered data dots
  const dots = [
    [0.30, 0.30], [0.55, 0.35], [0.38, 0.52], [0.62, 0.55],
    [0.50, 0.48], [0.28, 0.60], [0.55, 0.70], [0.35, 0.68],
  ]
  for (const [rx, ry] of dots) {
    ctx.fillRect(x + size * rx, y + size * ry, bs * 0.25, bs * 0.25)
  }
}

function drawPoster (ctx, data) {
  const w = CANVAS_W
  const h = CANVAS_H

  // ---------- background ----------
  ctx.setFillStyle('#FBF9F6')
  ctx.fillRect(0, 0, w, h)

  // subtle frame
  ctx.setStrokeStyle('#E6E2DA')
  ctx.setLineWidth(1)
  ctx.strokeRect(22, 22, w - 44, h - 44)

  // ---------- brand marker ----------
  ctx.setFontSize(11)
  ctx.setFillStyle('#9C9790')
  ctx.setTextAlign('center')
  ctx.font = '11px sans-serif'
  ctx.fillText('KAOGONG DAILY', w / 2, 48)

  // ---------- title ----------
  ctx.setFontSize(32)
  ctx.setFillStyle('#C1272D')
  ctx.font = 'bold 32px serif'
  ctx.fillText('考公每日学 · ' + data.dateStr, w / 2, 90)

  // accent underline
  ctx.setStrokeStyle('#C1272D')
  ctx.setLineWidth(2)
  ctx.beginPath()
  ctx.moveTo(w / 2 - 40, 110)
  ctx.lineTo(w / 2 + 40, 110)
  ctx.stroke()

  // ---------- "今日已学" ----------
  ctx.setFontSize(16)
  ctx.setFillStyle('#6B6661')
  ctx.font = '16px serif'
  ctx.fillText('今日已学', w / 2, 150)

  // ---------- 3 module indicators ----------
  const moduleInfos = [
    { key: 'politicalTheory', label: '政治理论', count: data.questionCount + '题' },
    { key: 'wordSet', label: '选词填空', count: data.wordCount + '词' },
    { key: 'essayPassage', label: '申论文段', count: data.essayCount + '篇' },
  ]
  const positions = [135, 270, 405]
  const circleY = 200
  const circleR = 22

  ctx.setTextAlign('center')

  moduleInfos.forEach((mod, i) => {
    const cx = positions[i]
    const done = data.completed[mod.key]

    // circle
    ctx.beginPath()
    ctx.arc(cx, circleY, circleR, 0, Math.PI * 2)
    if (done) {
      ctx.setFillStyle('#C1272D')
      ctx.fill()
      ctx.setStrokeStyle('#FFFFFF')
      ctx.setLineWidth(3)
      drawCheckmark(ctx, cx, circleY, circleR * 1.6)
    } else {
      ctx.setStrokeStyle('#E6E2DA')
      ctx.setLineWidth(2)
      ctx.stroke()
      // hollow center
      ctx.setFillStyle('#FBF9F6')
      ctx.fill()
    }

    // module name
    ctx.setFontSize(14)
    ctx.setFillStyle('#191919')
    ctx.font = '14px serif'
    ctx.fillText(mod.label, cx, circleY + 54)

    // count
    ctx.setFontSize(11)
    ctx.setFillStyle('#6B6661')
    ctx.font = '11px sans-serif'
    ctx.fillText(mod.count, cx, circleY + 76)
  })

  // ---------- stats line ----------
  ctx.setFontSize(19)
  ctx.setFillStyle('#C1272D')
  ctx.font = 'bold 19px serif'
  ctx.fillText(
    data.questionCount + '题 · ' + data.wordCount + '词 · ' + data.essayCount + '篇申论',
    w / 2, 320
  )

  // ---------- divider ----------
  ctx.setStrokeStyle('#E6E2DA')
  ctx.setLineWidth(1)
  ctx.beginPath()
  ctx.moveTo(170, 352)
  ctx.lineTo(370, 352)
  ctx.stroke()

  // ---------- quote ----------
  const quoteLines = wrapText(ctx, '“' + data.quote + '”', 440, 15)
  ctx.setFontSize(15)
  ctx.setFillStyle('#191919')
  ctx.font = '15px serif'

  let quoteY = 395
  const lineHeight = 26
  for (const line of quoteLines) {
    ctx.fillText(line, w / 2, quoteY)
    quoteY += lineHeight
  }

  // attribution
  ctx.setFontSize(12)
  ctx.setFillStyle('#9C9790')
  ctx.font = '12px sans-serif'
  ctx.fillText('—— 今日申论素材', w / 2, quoteY + 12)

  // ---------- QR placeholder ----------
  const qrSize = 56
  const qrX = (w - qrSize) / 2
  const qrY = 520

  ctx.setStrokeStyle('#D4CFC7')
  ctx.setLineWidth(1)
  ctx.strokeRect(qrX, qrY, qrSize, qrSize)
  drawFakeQR(ctx, qrX, qrY, qrSize)

  ctx.setFontSize(13)
  ctx.setFillStyle('#6B6661')
  ctx.font = '13px serif'
  ctx.fillText('扫码加入每日积累', w / 2, qrY + qrSize + 30)

  // ---------- footer ----------
  ctx.setStrokeStyle('#F0EDE7')
  ctx.setLineWidth(1)
  ctx.beginPath()
  ctx.moveTo(80, 690)
  ctx.lineTo(w - 80, 690)
  ctx.stroke()

  ctx.setFontSize(11)
  ctx.setFillStyle('#9C9790')
  ctx.font = '11px sans-serif'
  ctx.fillText('考公每日学', w / 2, 720)

  ctx.setFontSize(10)
  ctx.fillText('内容由 AI 自动生成 · 仅供学习参考', w / 2, 740)
}

// ---------- generate poster ----------
async function generatePoster () {
  return new Promise((resolve, reject) => {
    // small delay to ensure canvas is in DOM
    setTimeout(() => {
      try {
        const ctx = uni.createCanvasContext('sharePosterCanvas')
        drawPoster(ctx, posterData.value)
        ctx.draw(false, () => {
          uni.canvasToTempFilePath({
            canvasId: 'sharePosterCanvas',
            destWidth: 1080,
            destHeight: 1728,
            success: (res) => {
              posterImage.value = res.tempFilePath
              posterReady.value = true
              resolve()
            },
            fail: (err) => {
              reject(new Error('Canvas export failed: ' + JSON.stringify(err)))
            },
          })
        })
      } catch (e) {
        reject(e)
      }
    }, 80)
  })
}

const posterData = ref(null)

onMounted(async () => {
  try {
    posterData.value = await fetchPosterData()
    await generatePoster()
  } catch (e) {
    console.error('Poster generation error:', e)
    posterError.value = '海报生成失败，请稍后重试'
  }
})

// ---------- save to album ----------
function saveImage () {
  if (!posterReady.value || !posterImage.value) return

  uni.saveImageToPhotosAlbum({
    filePath: posterImage.value,
    success: () => {
      uni.showToast({ title: '已保存到相册', icon: 'success' })
    },
    fail: (err) => {
      if (err.errMsg && err.errMsg.indexOf('auth') !== -1) {
        uni.showModal({
          title: '需要权限',
          content: '保存到相册需要您授权',
          success: (res) => {
            if (res.confirm) uni.openSetting()
          },
        })
      } else {
        uni.showToast({ title: '保存失败，请重试', icon: 'none' })
      }
    },
  })
}
</script>

<style scoped>
.poster-mask {
  position: fixed;
  z-index: 999;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.poster-modal {
  width: 88vw;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.poster-card {
  width: 100%;
  background: #FBF9F6;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 28px rgba(0, 0, 0, 0.13);
  position: relative;
}

.poster-canvas-offscreen {
  position: fixed;
  left: -9999px;
  top: 0;
  pointer-events: none;
}

.poster-image {
  width: 100%;
  display: block;
}

/* ---- loading ---- */
.poster-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 0;
  min-height: 300px;
}

.loading-ring {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border, #E6E2DA);
  border-top-color: var(--accent, #C1272D);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-splash {
  margin-top: 16px;
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--text-secondary, #6B6661);
}

/* ---- error ---- */
.poster-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  min-height: 200px;
}

.error-icon {
  width: 48px;
  height: 48px;
  border: 2px solid var(--accent, #C1272D);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 700;
  color: var(--accent, #C1272D);
  margin-bottom: 12px;
  line-height: 1;
}

.error-text {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--text-secondary, #6B6661);
  text-align: center;
  padding: 0 24px;
}

/* ---- actions ---- */
.action-row {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  width: 100%;
}

.action-btn {
  flex: 1;
  height: 46px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif, serif);
  font-size: 16px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.action-btn:active {
  opacity: 0.75;
}

.btn-save {
  background: var(--accent, #C1272D);
  color: #ffffff;
}

.btn-save.disabled {
  opacity: 0.45;
  pointer-events: none;
}

.btn-close {
  background: var(--border, #E6E2DA);
  color: var(--text-primary, #191919);
}
</style>
