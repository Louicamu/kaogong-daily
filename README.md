# 考公每日学

公务员考试每日积累小程序，面向国考/省考/事业单位备考人群。

## 线上地址

**https://louicamu.github.io/kaogong-daily/**

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Uni-app Vue 3 + Vite + Pinia |
| 样式 | SCSS，Claude 美学（#FBF9F6 宣纸底 / #191919 墨黑 / #C1272D 朱砂丹红） |
| 后端管线 | Python 3 标准库（零外部依赖） |
| 爬虫 | 人民日报/新华社/半月谈，纯 urllib + regex |
| 部署 | GitHub Pages + GitHub Actions |
| 费用 | **完全免费**（无 API 调用，无服务器） |

## 项目结构

```
kaogong-daily-uni/
├── .github/workflows/
│   ├── daily-content.yml     # 每天7:00自动生成内容
│   └── deploy-pages.yml      # 自动部署到GitHub Pages
│
├── ContentManagement/         # Python 内容管线
│   ├── auto_pipeline.py       # ★ 主管线：爬虫→规则提取→JSON
│   ├── crawler.py             # ★ 四大官媒爬虫
│   ├── pipeline.py            # 4:3/10:5比例选词算法
│   └── review_scheduler.py    # 间隔复习调度
│
├── src/                       # 前端源码
│   ├── pages/ (8个页面)
│   │   ├── index/             # 首页：三模块卡片+进度条
│   │   ├── political/         # 政治理论答题页（7题）
│   │   ├── words/             # 选词填空（15词，10:5）
│   │   ├── essay/             # 申论文段（三板块Tab）
│   │   ├── review/            # 错题本
│   │   ├── favorites/         # 收藏
│   │   ├── calendar/          # 学习日历
│   │   └── profile/           # 个人中心
│   ├── components/ (13个)
│   │   ├── word-card.vue      # ★ 3D翻转卡片+原文出处
│   │   ├── word-grid.vue      # ★ 10:5网格布局
│   │   ├── exam-question.vue  # ★ 政治题A/B/C/D选项
│   │   └── tab-section.vue    # 申论三板块Tab
│   ├── store/                 # Pinia 状态管理
│   │   ├── content.js         # 内容加载
│   │   ├── quiz.js            # 答题记录/错题
│   │   └── streak.js          # 连续打卡
│   └── services/
│       ├── content.js         # 数据服务层
│       └── mock.js            # 本地测试数据
│
├── package.json
└── vite.config.js
```

## 核心功能

### 1. 政治理论（7题/天）
- 全部从当日官媒文章提取
- 国考真题格式：A/B/C/D正确/错误选择
- 7种干扰陷阱：半真半假/主体错位/历史跨度/绝对化
- 覆盖：会议精神/新思想/党史/宪法/经济/文化/生态

### 2. 选词填空（15词/天，严格10:5比例）
- 10个高频词：四字成语/两字词语/三字比喻词
- 5个预测词：生僻但规范的同类词
- 每词含：拼音/释义/常考语境/易错点/原文出处/文章日期
- 3D翻转卡片交互

### 3. 申论文段（1篇/天）
- 三大板块：词汇积累/论点积累/论据积累
- 来源于当日官媒评论文章

## 自动化流程

```
每天北京时间 7:00
  ↓
GitHub Actions 触发
  ↓
crawler.py 抓取四大官媒当日文章
  ↓
auto_pipeline.py 规则引擎提取内容
  ↓
生成 src/static/daily/{日期}.json
  ↓
Vite 构建 H5 → GitHub Pages 自动部署
  ↓
https://louicamu.github.io/kaogong-daily/ 更新
```

**全程零费用，零人工干预。**

## 本地开发

```bash
# 安装
cd E:\cc\kaogong-daily-uni
npm install

# H5 开发（浏览器预览）
npm run dev:h5

# 微信小程序
npm run dev:mp-weixin
```

## 手动运行内容管线

```bash
cd ContentManagement

# 生成明天内容
python auto_pipeline.py --date 2026-06-03

# 爬虫单独测试
python crawler.py
```

## 设计系统

```css
--bg-paper: #FBF9F6      /* 微暖宣纸底 */
--text-primary: #191919   /* 炭墨黑 */
--text-secondary: #6B6661 /* 暖瓦灰 */
--accent: #C1272D         /* 朱砂丹红，极度克制 */
--border: #E6E2DA         /* 极淡分割线 */
--font-serif: Noto Serif SC, Source Han Serif CN, Georgia, serif
--font-mono: SF Mono, Consolas, monospace

零卡片原则：无圆角、无阴影、无背景块
纯文字 + 1px线 + 留白
```

## GitHub 仓库

https://github.com/Louicamu/kaogong-daily
