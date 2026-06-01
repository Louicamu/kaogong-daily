<script setup>
import { onLaunch } from '@dcloudio/uni-app'
onLaunch(() => { console.log('考公每日学') })
</script>

<style lang="scss">
/* ============================================================
   考公每日学 — Claude 官方美学设计系统
   微暖宣纸 + 墨黑正文 + 克制的朱砂点缀 + 零卡片排版
   ============================================================ */

page {
  /* —— 色板 —— */
  --bg-paper:        #FBF9F6;   /* 微暖宣纸底 */
  --text-primary:    #191919;   /* 炭墨黑 */
  --text-secondary:  #6B6661;   /* 暖瓦灰 */
  --text-tertiary:   #9C9790;   /* 浅灰 */
  --accent:          #C1272D;   /* 朱砂丹红 (极度克制使用) */
  --accent-muted:    #E8D5D5;   /* 淡红 */
  --border:          #E6E2DA;   /* 极淡分割线 */
  --border-light:    #F0EDE7;   /* 更淡 */
  --correct:         #1B5E20;   /* 墨绿 (正确) */
  --wrong:           #B71C1C;   /* 暗红 (错误) */
  --surface:         #F5F2ED;   /* 微凸表面 (极少使用) */

  /* —— 字型栈 —— */
  --font-serif:      "Noto Serif SC", "Source Han Serif CN", "STSong", Georgia, "宋体", serif;
  --font-mono:       "SF Mono", "Cascadia Code", "Consolas", "Courier New", monospace;
  --font-sans:       -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;

  /* —— 字号 (基于 1rem = 16px) —— */
  --text-2xs: 11px;
  --text-xs:  12px;
  --text-sm:  13px;
  --text-base:15px;
  --text-md:  17px;
  --text-lg:  20px;
  --text-xl:  24px;
  --text-2xl: 30px;

  /* —— 间距 —— */
  --sp-2xs:  4px;
  --sp-xs:   8px;
  --sp-sm:  12px;
  --sp-md:  20px;
  --sp-lg:  32px;
  --sp-xl:  48px;
  --sp-2xl: 64px;

  /* —— 排版常量 —— */
  --letter-spacing: 0.04em;
  --line-height:    1.65;

  background: var(--bg-paper);
  color: var(--text-primary);
  font-family: var(--font-serif);
  font-size: var(--text-base);
  letter-spacing: var(--letter-spacing);
  line-height: var(--line-height);
  -webkit-font-smoothing: antialiased;
}

/* ============================================================
   通用原子类 (零卡片风格)
   ============================================================ */

/* 细线分割 */
.hr {
  width: 100%; height: 1px; background: var(--border);
}
.hr-light {
  width: 100%; height: 1px; background: var(--border-light);
}

/* 丹红细线 (仅用于重要分割) */
.hr-accent {
  width: 60px; height: 2px; background: var(--accent);
}

/* 衬线文本 */
.serif     { font-family: var(--font-serif); }
.sans      { font-family: var(--font-sans); }
.mono      { font-family: var(--font-mono); }

.text-2xs  { font-size: var(--text-2xs); }
.text-xs   { font-size: var(--text-xs); }
.text-sm   { font-size: var(--text-sm); }
.text-base { font-size: var(--text-base); }
.text-md   { font-size: var(--text-md); }
.text-lg   { font-size: var(--text-lg); }
.text-xl   { font-size: var(--text-xl); }
.text-2xl  { font-size: var(--text-2xl); }

.ink        { color: var(--text-primary); }
.warm-gray  { color: var(--text-secondary); }
.light-gray { color: var(--text-tertiary); }
.accent     { color: var(--accent); }

.tracking { letter-spacing: var(--letter-spacing); }
.leading  { line-height: var(--line-height); }

/* 内联标签 (纯文本风格, 无背景卡片) */
.tag-accent {
  font-family: var(--font-sans);
  font-size: var(--text-2xs);
  color: var(--accent);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.tag-muted {
  font-family: var(--font-sans);
  font-size: var(--text-2xs);
  color: var(--text-tertiary);
  letter-spacing: 0.06em;
}
</style>
