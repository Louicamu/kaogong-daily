/**
 * 内容服务层 — 优先真实JSON, 降级mock
 */
import mockApi from './mock.js'

const CACHE_PREFIX = 'kc_'

function getCache(k) {
  try { const r = uni.getStorageSync(CACHE_PREFIX + k); if (r && Date.now() - r.t < r.ttl) return r.data } catch (_) {}
  return null
}
function setCache(k, d, ttl) {
  try { uni.setStorageSync(CACHE_PREFIX + k, { data: d, t: Date.now(), ttl }) } catch (_) {}
}

function tryJSON(url) {
  return new Promise(resolve => {
    uni.request({ url, method: 'GET', timeout: 5000,
      success: r => resolve(r.statusCode === 200 ? r.data : null),
      fail: () => resolve(null)
    })
  })
}

async function loadDailyPkg(date) {
  const json = await tryJSON('/static/daily/' + date + '.json')
  if (json?.politicalTheories) return json
  return buildMockPkg(date)
}

function buildMockPkg(date) {
  return {
    date, engine: 'mock',
    politicalTheories: [
      { questionId: 'm1', questionType: 'correct', question: '以下说法正确的是：',
        options: { A: '中国式现代化是全体人民共同富裕的现代化', B: '中国式现代化是物质文明高度发达的现代化', C: '中国式现代化是西方现代化的翻版', D: '中国式现代化以资本为中心' },
        correctAnswer: 'A', analysis: '二十大报告明确指出。', tags: ['二十大','中国式现代化'], source: '人民日报', date },
      { questionId: 'm2', questionType: 'incorrect', question: '关于新质生产力，以下说法错误的是：',
        options: { A: '新质生产力以科技创新为核心', B: '新质生产力需要新型生产关系', C: '新质生产力就是单纯发展高科技产业', D: '发展新质生产力要因地制宜' },
        correctAnswer: 'C', analysis: '新质生产力不等同于单纯发展高科技产业。', tags: ['新质生产力','经济'], source: '新华社', date },
    ],
    dailyWords: [
      { wordId:'h1',word:'擘画',pinyin:'bò huà',definition:'筹划、安排',examContext:'常搭配"蓝图"',commonMistakes:'易误读为bì',sourceSentence:'党的二十届三中全会擘画了进一步全面深化改革的宏伟蓝图。',sourceArticle:'人民日报评论',category:'政治类',isHighFreq:true},
      { wordId:'h2',word:'踔厉奋发',pinyin:'chuō lì fèn fā',definition:'精神振奋、斗志昂扬',examContext:'新时代精神状态',commonMistakes:'书写易误',sourceSentence:'全党全国各族人民踔厉奋发、勇毅前行。',sourceArticle:'新华社时政',category:'政治类',isHighFreq:true},
      { wordId:'h3',word:'行稳致远',pinyin:'xíng wěn zhì yuǎn',definition:'稳步前进才能到达远方',examContext:'经济政策表述',commonMistakes:'"致"不可写作"至"',category:'经济类',isHighFreq:true},
      { wordId:'h4',word:'新质生产力',pinyin:'xīn zhì shēng chǎn lì',definition:'以科技创新为主导的先进生产力',examContext:'经济板块必考',commonMistakes:'不可简单等同高科技',sourceSentence:'发展新质生产力是推动高质量发展的内在要求和重要着力点。',sourceArticle:'新华社时政',category:'经济类',isHighFreq:true},
      { wordId:'h5',word:'守正创新',pinyin:'shǒu zhèng chuàng xīn',definition:'坚持正道又勇于创新',examContext:'二十大关键词',commonMistakes:'理解不深',sourceSentence:'坚持守正创新，推动理论创新和实践创新良性互动。',sourceArticle:'人民日报理论',category:'文化类',isHighFreq:true},
      { wordId:'h6',word:'赋能',pinyin:'fù néng',definition:'赋予能力或能量',examContext:'数字经济热词',commonMistakes:'不可滥用',sourceSentence:'以数字赋能推动政务服务从能办向好办、易办转变。',sourceArticle:'新华社时政',category:'经济类',isHighFreq:true},
      { wordId:'h7',word:'闭环',pinyin:'bì huán',definition:'管理流程形成完整回路',examContext:'社会治理热词',commonMistakes:'注意搭配',sourceSentence:'建立风险监测预警和闭环管理机制，实现全过程管控。',sourceArticle:'人民日报评论',category:'社会类',isHighFreq:true},
      { wordId:'h8',word:'对标',pinyin:'duì biāo',definition:'对照标准进行比较改进',examContext:'经济改革常用',commonMistakes:'与"对比"区分',sourceSentence:'对标国际高标准经贸规则，稳步扩大制度型开放。',sourceArticle:'新华社时政',category:'经济类',isHighFreq:true},
      { wordId:'h9',word:'牛鼻子',pinyin:'niú bí zi',definition:'比喻事物的关键或主要矛盾',examContext:'改革话题常用比喻',commonMistakes:'非正式书面语慎用',category:'政治类',isHighFreq:true},
      { wordId:'h10',word:'硬骨头',pinyin:'yìng gǔ tou',definition:'比喻艰巨的任务或顽固的问题',examContext:'改革攻坚常用',commonMistakes:'搭配注意',category:'政治类',isHighFreq:true},
      { wordId:'p1',word:'沙盒监管',pinyin:'shā hé jiān guǎn',definition:'在可控空间内测试新业态',examContext:'金融科技热点',commonMistakes:'新概念需理解本质',category:'经济类',isHighFreq:false},
      { wordId:'p2',word:'制度型开放',pinyin:'zhì dù xíng kāi fàng',definition:'以规则规制管理标准对接为主的开放',examContext:'高水平开放新提法',commonMistakes:'与商品开放区分',category:'经济类',isHighFreq:false},
      { wordId:'p3',word:'先立后破',pinyin:'xiān lì hòu pò',definition:'先建立新机制再破除旧机制',examContext:'改革方法论',commonMistakes:'与"先破后立"相反',category:'政治类',isHighFreq:false},
      { wordId:'p4',word:'微治理',pinyin:'wēi zhì lǐ',definition:'针对微小单元的精细化治理',examContext:'基层治理热词',commonMistakes:'冷门新词',category:'社会类',isHighFreq:false},
      { wordId:'p5',word:'全链条',pinyin:'quán liàn tiáo',definition:'涵盖全部环节',examContext:'安全监管常用',commonMistakes:'与"全流程"区别',category:'社会类',isHighFreq:false},
    ],
    essayPassage: {
      title: '在进一步全面深化改革中推进中国式现代化',
      source: '人民日报', sourcePublishDate: date,
      sections: [
        { type:'vocabulary', title:'词汇积累', items:[
          { word:'出发点与落脚点', contextSentence:'改革要以促进社会公平正义、增进人民福祉为出发点和落脚点', explanation:'表述改革目的的规范用语' },
          { word:'关键一招', contextSentence:'改革开放是决定当代中国命运的关键一招', explanation:'改革话题的经典表述' },
        ]},
        { type:'argument', title:'论点积累', items:[
          { pointTitle:'改革开放是关键一招', pointContent:'改革开放是决定当代中国命运的关键一招。', usageGuide:'改革类开篇立论', applicableTopics:['改革开放','经济发展'] },
        ]},
        { type:'evidence', title:'论据积累', items:[
          { evidenceType:'data', content:'2025年GDP突破130万亿元', source:'国家统计局' },
        ]},
      ],
      tags:['改革开放','中国式现代化'], readingTimeMinutes: 8,
    },
  }
}

export default {
  async getDailyContent(date) {
    const d = date || getToday()
    const ck = 'daily_' + d
    const c = getCache(ck)
    if (c) return c
    const p = await loadDailyPkg(d)
    const mods = {
      politicalTheory: { available: (p.politicalTheories||[]).length > 0, count: (p.politicalTheories||[]).length, tags: p.politicalTheories?.[0]?.tags||[], previewQuestion: p.politicalTheories?.[0]?.question||'' },
      wordSet: { available: (p.dailyWords||[]).length > 0, totalWords: (p.dailyWords||[]).length, highFreqCount: (p.dailyWords||[]).filter(w=>w.isHighFreq).length, predictiveCount: (p.dailyWords||[]).filter(w=>!w.isHighFreq).length, previewWords: (p.dailyWords||[]).slice(0,7).map(w=>({word:w.word,isHighFreq:w.isHighFreq})) },
      essayPassage: { available: !!p.essayPassage, title: p.essayPassage?.title||'', source: p.essayPassage?.source||'', readingTime: 8, sectionNames: ['词汇积累','论点积累','论据积累'] },
    }
    const r = { code: 0, data: { date: d, exists: true, isToday: d===getToday(), modules: mods, userProgress:{politicalTheory:false,wordSet:false,essayPassage:false} } }
    setCache(ck, r, 3600000)
    return r
  },
  getCachedDaily(date) { return getCache('daily_'+(date||'today')) },
  async getPoliticalQuestions(date) { const d=date||getToday(); const p=await loadDailyPkg(d); return {code:0,data:{date:d,questions:p.politicalTheories||[]}} },
  async getDailyWordSet(date) { const d=date||getToday(); const p=await loadDailyPkg(d); return {code:0,data:{date:d,words:p.dailyWords||[]}} },
  async getEssayPassage(date) { const d=date||getToday(); const p=await loadDailyPkg(d); return {code:0,data:p.essayPassage||{}} },
  getCalendar(m) { return Promise.resolve(mockApi.getCalendar(m)) },
  recordProgress(date, mod) { const k='progress_'+date; let e={}; try{e=uni.getStorageSync(CACHE_PREFIX+k)||{}}catch(_){}; e[mod]={completed:true}; try{uni.setStorageSync(CACHE_PREFIX+k,e)}catch(_){}; return Promise.resolve({code:0,data:{updated:true}}) },
  getUserProgress(date) { const k='progress_'+date; let d={}; try{d=uni.getStorageSync(CACHE_PREFIX+k)||{}}catch(_){}; return Promise.resolve({code:0,data:{politicalTheory:!!d.politicalTheory?.completed,wordSet:!!d.wordSet?.completed,essayPassage:!!d.essayPassage?.completed}}) },
  addFavorite(ty,id,date,notes) { let f=[]; try{f=uni.getStorageSync(CACHE_PREFIX+'favs')||[]}catch(_){}; if(!f.find(x=>x.itemId===id&&x.itemType===ty)){f.unshift({_id:'l'+Date.now(),itemType:ty,itemId:id,date,title:notes||'',notes:notes||'',createdAt:Date.now()});try{uni.setStorageSync(CACHE_PREFIX+'favs',f)}catch(_){}}; return Promise.resolve({code:0,data:{existed:false}}) },
  removeFavorite(ty,id) { let f=[]; try{f=uni.getStorageSync(CACHE_PREFIX+'favs')||[]}catch(_){}; f=f.filter(x=>!(x.itemId===id&&x.itemType===ty)); try{uni.setStorageSync(CACHE_PREFIX+'favs',f)}catch(_){}; return Promise.resolve({code:0,data:{removed:true}}) },
  getFavorites() { let f=[]; try{f=uni.getStorageSync(CACHE_PREFIX+'favs')||[]}catch(_){}; return Promise.resolve({code:0,data:{total:f.length,items:f}}) },
}

function getToday() { const d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0') }
