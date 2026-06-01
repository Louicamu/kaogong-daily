/**
 * Mock 数据层 — 云开发未开通时的本地测试数据
 * 提供完整的三大模块内容，确保本地开发可预览全部 UI
 */

const TODAY = new Date();
const y = TODAY.getFullYear();
const m = String(TODAY.getMonth() + 1).padStart(2, '0');
const d = String(TODAY.getDate()).padStart(2, '0');
const TODAY_STR = `${y}-${m}-${d}`;

/**
 * 每日内容概要 (首页)
 */
function getDailyContent(date) {
  return {
    code: 0,
    data: {
      date: date || TODAY_STR,
      exists: true,
      isToday: true,
      modules: {
        politicalTheory: {
          available: true,
          count: 2,
          tags: ['二十大精神', '中国式现代化'],
          previewQuestion: '关于党的二十大报告中提出的"中国式现代化"，以下说法正确的是：',
        },
        wordSet: {
          available: true,
          totalWords: 7,
          highFreqCount: 4,
          predictiveCount: 3,
          previewWords: [
            { word: '擘画', isHighFreq: true },
            { word: '踔厉奋发', isHighFreq: true },
            { word: '行稳致远', isHighFreq: true },
            { word: '新质生产力', isHighFreq: true },
            { word: '数字赋能', isHighFreq: false },
            { word: '积水成器', isHighFreq: false },
            { word: '精准施策', isHighFreq: false },
          ],
        },
        essayPassage: {
          available: true,
          title: '在进一步全面深化改革中推进中国式现代化',
          source: '人民日报',
          readingTime: 8,
          sectionNames: ['词汇积累', '论点积累', '论据积累'],
        },
      },
      userProgress: { politicalTheory: false, wordSet: false, essayPassage: false },
    },
  };
}

/**
 * 政治理论题目
 */
function getPoliticalQuestions(date) {
  return {
    code: 0,
    data: {
      date: date || TODAY_STR,
      total: 2,
      questions: [
        {
          questionId: 'pt_demo_001',
          date: date || TODAY_STR,
          source: '人民日报',
          sourcePublishDate: TODAY_STR,
          questionType: 'correct',
          question: '关于党的二十大报告中提出的"中国式现代化"，以下说法正确的是：',
          options: {
            A: '中国式现代化是全体人民共同富裕的现代化',
            B: '中国式现代化是物质文明高度发达的现代化',
            C: '中国式现代化是西方现代化的翻版',
            D: '中国式现代化以资本为中心',
          },
          correctAnswer: 'A',
          analysis: '党的二十大报告指出，中国式现代化是人口规模巨大的现代化、是全体人民共同富裕的现代化、是物质文明和精神文明相协调的现代化、是人与自然和谐共生的现代化、是走和平发展道路的现代化。选项A正确。选项B遗漏了"精神文明"，选项C错误（中国式现代化打破了"现代化=西方化"的迷思），选项D错误（以人民为中心而非资本为中心）。',
          extendedKnowledge: '中国式现代化的五个特征：人口规模巨大、全体人民共同富裕、物质文明和精神文明相协调、人与自然和谐共生、走和平发展道路。这五个特征既是理论概括，也是实践要求，为全面建成社会主义现代化强国指明了方向。',
          tags: ['二十大精神', '中国式现代化', '高频考点'],
          difficulty: 'medium',
          examFrequency: 'high',
        },
        {
          questionId: 'pt_demo_002',
          date: date || TODAY_STR,
          source: '新华社',
          sourcePublishDate: TODAY_STR,
          questionType: 'incorrect',
          question: '关于"新质生产力"，以下说法错误的是：',
          options: {
            A: '新质生产力是以科技创新为主导的先进生产力',
            B: '发展新质生产力要因地制宜，不能一哄而上',
            C: '新质生产力就是单纯发展高科技产业',
            D: '新质生产力需要与之相适应的新型生产关系',
          },
          correctAnswer: 'C',
          analysis: '新质生产力并非等同于单纯发展高科技产业。它是以科技创新为核心驱动力，以高技术、高效能、高质量为特征，以劳动者、劳动资料、劳动对象及其优化组合的质变为基本内涵的先进生产力。选项C将新质生产力简单等同于发展高科技产业，理解有误。',
          extendedKnowledge: '"新质生产力"由习近平总书记于2023年首次提出。其核心要义是"以新促质"，通过技术革命性突破、生产要素创新性配置、产业深度转型升级，推动生产力实现质的飞跃。',
          tags: ['新质生产力', '经济', '高频考点'],
          difficulty: 'medium',
          examFrequency: 'high',
        },
      ],
    },
  };
}

/**
 * 每日词汇组 (7词, 4:3比例)
 */
function getDailyWordSet(date) {
  return {
    code: 0,
    data: {
      date: date || TODAY_STR,
      totalWords: 7,
      words: [
        {
          wordId: 'wb_001', word: '擘画', wordType: 'idiom',
          frequency: 'high', pinyin: 'bò huà',
          definition: '筹划、安排。指计划、布置，多用于宏观战略层面的规划。常与"蓝图""发展""未来"搭配使用。',
          examContext: '常用于申论大作文中描述国家战略规划、顶层设计。如：擘画蓝图、擘画发展、擘画未来。',
          commonMistakes: '1. 读音易错：读作"bì"而非"bò"。\n2. 搭配不当："擘画"后常接宏观词汇，不用于具体小事。',
          exampleSentence: '党的二十大擘画了以中国式现代化全面推进中华民族伟大复兴的宏伟蓝图。',
          category: '政治类', displayOrder: 1, isHighFreq: true,
        },
        {
          wordId: 'wb_002', word: '踔厉奋发', wordType: 'idiom',
          frequency: 'high', pinyin: 'chuō lì fèn fā',
          definition: '形容精神振奋、斗志昂扬。踔：跳跃、超越；厉：猛烈、迅疾。',
          examContext: '常见于时政报道和领导人讲话中，描述新时代的精神状态。常与"勇毅前行"连用。',
          commonMistakes: '1. "踔"易误写为"卓"或"焯"。\n2. 理解偏误：不是一般的"奋发"，强调昂扬向上的精神劲头。',
          exampleSentence: '全党全国各族人民踔厉奋发、勇毅前行，为全面建设社会主义现代化国家而团结奋斗。',
          category: '政治类', displayOrder: 2, isHighFreq: true,
        },
        {
          wordId: 'wb_003', word: '行稳致远', wordType: 'idiom',
          frequency: 'high', pinyin: 'xíng wěn zhì yuǎn',
          definition: '稳步前进才能到达远方。比喻做事要稳扎稳打，不能急于求成。',
          examContext: '常用于经济政策表述。"稳中求进"的同义升级表达。可用于论证改革的渐进性。',
          commonMistakes: '1. "致"不可写作"至"。\n2. 多用于宏观政策层面，不适用于描述个人短期行为。',
          exampleSentence: '坚持稳中求进工作总基调，推动经济行稳致远。',
          category: '经济类', displayOrder: 3, isHighFreq: true,
        },
        {
          wordId: 'wb_004', word: '新质生产力', wordType: 'word_pair',
          frequency: 'high', pinyin: 'xīn zhì shēng chǎn lì',
          definition: '以科技创新为主导，以高技术、高效能、高质量为特征的先进生产力形态。',
          examContext: '2023年由习近平总书记首次提出，是经济板块"必考"概念。需掌握其核心要义和与传统生产力的区别。',
          commonMistakes: '1. 不可简单等同于"高科技产业"。\n2. 需理解"以新促质"的核心逻辑。',
          exampleSentence: '发展新质生产力是推动高质量发展的内在要求和重要着力点。',
          category: '经济类', displayOrder: 4, isHighFreq: true,
        },
        {
          wordId: 'wp_001', word: '数字赋能', wordType: 'word_pair',
          frequency: 'predictive', pinyin: 'shù zì fù néng',
          definition: '通过数字化技术手段为传统产业、政务服务等注入新动力和新能力。',
          examContext: '数字经济板块热词。可用于论述数字化转型、智慧城市、数字政府等话题。预测未来考题会涉及。',
          commonMistakes: '"赋能"不可滥用。需要明确数字技术带来了什么具体能力提升。',
          exampleSentence: '以数字赋能推动政务服务从"能办"向"好办、易办"转变。',
          category: '经济类', displayOrder: 5, isHighFreq: false,
        },
        {
          wordId: 'wp_002', word: '积水成器', wordType: 'idiom',
          frequency: 'predictive', pinyin: 'jī shuǐ chéng qì',
          definition: '像水一样不断积累才能成为有用的器物。比喻持之以恒、厚积薄发方可成大器。',
          examContext: '较冷门词汇，但与"大器晚成"相近。可用于申论中论述培养人才、长期建设等话题。',
          commonMistakes: '非高频词，使用时注意语境适配。不适用于描述快速见效的事务。',
          exampleSentence: '人才培养要积水成器，不可急功近利。',
          category: '文化类', displayOrder: 6, isHighFreq: false,
        },
        {
          wordId: 'wp_003', word: '精准施策', wordType: 'word_pair',
          frequency: 'predictive', pinyin: 'jīng zhǔn shī cè',
          definition: '针对不同情况采取精确有效的政策措施，避免"一刀切"的粗放治理方式。',
          examContext: '社会治理板块高频概念。可用于论述精准扶贫、精准防控、精准服务等话题。',
          commonMistakes: '与"对症下药"可互换，但"精准施策"更偏政策层面。',
          exampleSentence: '坚持精准施策，因地制宜推进乡村全面振兴。',
          category: '社会类', displayOrder: 7, isHighFreq: false,
        },
      ],
      layout: {
        highFreqIndices: [0, 1, 2, 3],
        predictiveIndices: [4, 5, 6],
        visualGrouping: 'alternating',
      },
    },
  };
}

/**
 * 申论文段
 */
function getEssayPassage(date) {
  return {
    code: 0,
    data: {
      date: date || TODAY_STR,
      source: '人民日报',
      sourcePublishDate: TODAY_STR,
      title: '在进一步全面深化改革中推进中国式现代化',
      authors: '本报评论员',
      originalExcerpt: '当前，我国改革发展进入关键时期。党的二十大擘画了以中国式现代化全面推进中华民族伟大复兴的宏伟蓝图，对全面深化改革作出战略部署。改革开放是决定当代中国命运的关键一招，也是决定实现"两个一百年"奋斗目标、实现中华民族伟大复兴的关键一招。改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。发展新质生产力是推动高质量发展的内在要求和重要着力点，必须继续做好创新这篇大文章，推动新质生产力加快发展。中国式现代化，是中国共产党领导的社会主义现代化，既有各国现代化的共同特征，更有基于自己国情的中国特色。',
      sections: [
        {
          type: 'vocabulary',
          title: '词汇积累',
          icon: 'pen',
          items: [
            { word: '擘画', contextSentence: '擘画了以中国式现代化全面推进中华民族伟大复兴的宏伟蓝图', explanation: '筹划、安排。多用于宏观战略规划，常搭配"蓝图""发展"。' },
            { word: '新质生产力', contextSentence: '发展新质生产力是推动高质量发展的内在要求和重要着力点', explanation: '以科技创新为主导的先进生产力形态，核心是"以新促质"。' },
            { word: '出发点与落脚点', contextSentence: '改革要以促进社会公平正义、增进人民福祉为出发点和落脚点', explanation: '表述改革目的和政策导向的规范用语，申论中可直接引用。' },
          ],
        },
        {
          type: 'argument',
          title: '论点积累',
          icon: 'target',
          items: [
            {
              pointTitle: '改革开放是决定当代中国命运的关键一招',
              pointContent: '改革开放是决定当代中国命运的关键一招，也是决定实现"两个一百年"奋斗目标、实现中华民族伟大复兴的关键一招。',
              usageGuide: '适用于改革类话题的开篇立论。可搭配论述：全面深化改革、高水平对外开放、制度型开放。',
              applicableTopics: ['改革开放', '经济发展', '制度创新'],
            },
            {
              pointTitle: '以人民为中心的改革导向',
              pointContent: '改革要以促进社会公平正义、增进人民福祉为出发点和落脚点。',
              usageGuide: '适用于民生类、社会治理类话题。可延伸论述共同富裕、基本公共服务均等化、民生保障。',
              applicableTopics: ['民生', '共同富裕', '社会治理'],
            },
          ],
        },
        {
          type: 'evidence',
          title: '论据积累',
          icon: 'database',
          items: [
            { evidenceType: 'data', content: '2025年我国GDP突破130万亿元，同比增长5.0%，经济实力实现历史性跃升。', source: '国家统计局2026年1月公报' },
            { evidenceType: 'case', content: '深圳建设中国特色社会主义先行示范区以来，在营商环境、科技创新、民生幸福等方面取得显著成效，累计推出1000多项改革创新举措，成为全面深化改革的生动实践。', source: '新华社2026年5月报道' },
            { evidenceType: 'quote', content: '"改革开放只有进行时，没有完成时。"', source: '习近平总书记在中央深改委会议上的重要讲话' },
          ],
        },
      ],
      tags: ['改革开放', '中国式现代化', '经济发展'],
      readingTimeMinutes: 8,
      difficulty: 'medium',
    },
  };
}

/**
 * 收藏列表（默认为空，本地无数据）
 */
function getFavorites() {
  return {
    code: 0,
    data: { total: 0, items: [] },
  };
}

/**
 * 学习日历
 */
function getCalendar(month) {
  const today = new Date();
  const dates = [];
  // 生成当月所有日期，随机标记部分为"有内容"
  const [yy, mm] = (month || `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}`).split('-').map(Number);
  const daysInMonth = new Date(yy, mm, 0).getDate();
  for (let i = 1; i <= daysInMonth; i++) {
    const ds = `${yy}-${String(mm).padStart(2,'0')}-${String(i).padStart(2,'0')}`;
    dates.push({
      date: ds,
      isPublished: i <= today.getDate(),
      modules: { pt: i <= today.getDate(), ws: i <= today.getDate(), ep: i <= today.getDate() },
      studied: i < today.getDate() && Math.random() > 0.3,
    });
  }
  return { code: 0, data: { month: month || `${yy}-${String(mm).padStart(2,'0')}`, publishedDates: dates } };
}

const mockApi = {
  getDailyContent,
  getPoliticalQuestions,
  getDailyWordSet,
  getEssayPassage,
  getFavorites,
  getCalendar,
};
export default mockApi;
export {
  getDailyContent,
  getPoliticalQuestions,
  getDailyWordSet,
  getEssayPassage,
  getFavorites,
  getCalendar,
};
