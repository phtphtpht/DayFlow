/**
 * 国际化翻译文件
 * 包含中文、英文、日文的所有界面文本
 */

export const translations = {
  zh: {
    // 导航栏
    appTitle: '🤖 AIWorkTracker',
    nav: {
      dashboard: '📊 概览',
      timeline: '⏱️ 时间线',
      settings: '⚙️ 设置'
    },

    // Dashboard
    dashboard: {
      title: '今日工作概览',
      selectDate: '选择日期：',
      totalRecords: '总记录数',
      analyzedRecords: '已分析',
      workHours: '工作时长',
      categoryDistribution: '📊 工作类型分布',
      dailyLog: '📄 今日工作日志',
      generateSummary: '🔄 生成摘要',
      generating: '生成中...',
      noSummary: '📭 暂无工作日志',
      clickToGenerate: '点击"生成摘要"按钮创建今日工作日志',
      noAnalyzed: '暂无已分析的活动记录，请稍后再试',
      generatedAt: '生成时间:',
      loading: '加载中...',
      loadFailed: '❌ 加载数据失败，请确保后端服务已启动',
      retry: '重试',
      generatingSummary: '正在生成摘要...',
      mayTakeTime: '这可能需要10-30秒',
      categories: {
        coding: '💻 编程',
        writing: '✍️ 写作',
        meeting: '👥 会议',
        browsing: '🌐 浏览',
        communication: '💬 沟通',
        entertainment: '🎮 娱乐',
        design: '🎨 设计',
        data_analysis: '📈 数据分析',
        other: '📌 其他'
      }
    },

    // Timeline
    timeline: {
      title: '活动时间线',
      selectDate: '选择日期：',
      totalRecords: '共',
      recordsUnit: '条记录',
      noActivities: '📭 暂无活动记录',
      systemMonitoring: '系统正在监控中，请稍后刷新页面',
      loading: '加载中...',
      loadFailed: '❌ 加载活动失败',
      retry: '重试',
      confidence: '置信度:'
    },

    // Settings
    settings: {
      title: '⚙️ 设置',
      subtitle: '配置 AIWorkTracker 偏好设置',
      language: '🌍 AI 输出语言',
      languageOptions: {
        en: 'English',
        zh: '中文 (Chinese)',
        ja: '日本語 (Japanese)'
      },
      languageHint: 'AI 将使用此语言生成工作描述和摘要',
      model: '🤖 OpenAI 模型',
      modelOptions: {
        'gpt-5-mini': 'GPT-5 Mini (推荐)',
        'gpt-5': 'GPT-5'
      },
      modelHint: '更高级的模型提供更好的分析效果，但成本更高',
      saveButton: '💾 保存设置',
      saving: '保存中...',
      saveSuccess: '✅ 设置保存成功！',
      saveFailed: '❌ 设置保存失败',
      loadFailed: '加载设置失败',
      loading: '加载中...',
      note: 'ℹ️',
      noteText: '注意：语言更改将应用于新的分析。现有记录不受影响。'
    },

    // 通用
    common: {
      hours: '小时',
      minutes: '分钟',
      times: '次'
    }
  },

  en: {
    // Navigation
    appTitle: '🤖 AIWorkTracker',
    nav: {
      dashboard: '📊 Dashboard',
      timeline: '⏱️ Timeline',
      settings: '⚙️ Settings'
    },

    // Dashboard
    dashboard: {
      title: "Today's Work Overview",
      selectDate: 'Select Date:',
      totalRecords: 'Total Records',
      analyzedRecords: 'Analyzed',
      workHours: 'Work Hours',
      categoryDistribution: '📊 Work Category Distribution',
      dailyLog: '📄 Daily Work Log',
      generateSummary: '🔄 Generate Summary',
      generating: 'Generating...',
      noSummary: '📭 No Work Log',
      clickToGenerate: 'Click "Generate Summary" to create today\'s work log',
      noAnalyzed: 'No analyzed activity records, please try again later',
      generatedAt: 'Generated at:',
      loading: 'Loading...',
      loadFailed: '❌ Failed to load data. Please ensure backend service is running',
      retry: 'Retry',
      generatingSummary: 'Generating summary...',
      mayTakeTime: 'This may take 10-30 seconds',
      categories: {
        coding: '💻 Coding',
        writing: '✍️ Writing',
        meeting: '👥 Meeting',
        browsing: '🌐 Browsing',
        communication: '💬 Communication',
        entertainment: '🎮 Entertainment',
        design: '🎨 Design',
        data_analysis: '📈 Data Analysis',
        other: '📌 Other'
      }
    },

    // Timeline
    timeline: {
      title: 'Activity Timeline',
      selectDate: 'Select Date:',
      totalRecords: '',
      recordsUnit: ' records',
      noActivities: '📭 No Activity Records',
      systemMonitoring: 'System is monitoring, please refresh later',
      loading: 'Loading...',
      loadFailed: '❌ Failed to load activities',
      retry: 'Retry',
      confidence: 'Confidence:'
    },

    // Settings
    settings: {
      title: '⚙️ Settings',
      subtitle: 'Configure AIWorkTracker preferences',
      language: '🌍 AI Output Language',
      languageOptions: {
        en: 'English',
        zh: '中文 (Chinese)',
        ja: '日本語 (Japanese)'
      },
      languageHint: 'AI will generate work descriptions and summaries in this language',
      model: '🤖 OpenAI Model',
      modelOptions: {
        'gpt-5-mini': 'GPT-5 Mini (Recommended)',
        'gpt-5': 'GPT-5'
      },
      modelHint: 'Higher models provide better analysis but cost more',
      saveButton: '💾 Save Settings',
      saving: 'Saving...',
      saveSuccess: '✅ Settings saved successfully!',
      saveFailed: '❌ Failed to save settings',
      loadFailed: 'Failed to load settings',
      loading: 'Loading...',
      note: 'ℹ️',
      noteText: 'Note: Language changes will apply to new analyses. Existing records will not be affected.'
    },

    // Common
    common: {
      hours: 'hours',
      minutes: 'min',
      times: 'times'
    }
  },

  ja: {
    // ナビゲーション
    appTitle: '🤖 AIWorkTracker',
    nav: {
      dashboard: '📊 ダッシュボード',
      timeline: '⏱️ タイムライン',
      settings: '⚙️ 設定'
    },

    // Dashboard
    dashboard: {
      title: '本日の作業概要',
      selectDate: '日付を選択：',
      totalRecords: '総記録数',
      analyzedRecords: '分析済み',
      workHours: '作業時間',
      categoryDistribution: '📊 作業カテゴリー分布',
      dailyLog: '📄 本日の作業ログ',
      generateSummary: '🔄 サマリー生成',
      generating: '生成中...',
      noSummary: '📭 作業ログなし',
      clickToGenerate: '「サマリー生成」をクリックして本日の作業ログを作成',
      noAnalyzed: '分析済みの活動記録がありません。後でもう一度お試しください',
      generatedAt: '生成時刻:',
      loading: '読み込み中...',
      loadFailed: '❌ データの読み込みに失敗しました。バックエンドサービスが起動していることを確認してください',
      retry: '再試行',
      generatingSummary: 'サマリー生成中...',
      mayTakeTime: 'これには10〜30秒かかる場合があります',
      categories: {
        coding: '💻 コーディング',
        writing: '✍️ 執筆',
        meeting: '👥 会議',
        browsing: '🌐 ブラウジング',
        communication: '💬 コミュニケーション',
        entertainment: '🎮 エンターテイメント',
        design: '🎨 デザイン',
        data_analysis: '📈 データ分析',
        other: '📌 その他'
      }
    },

    // Timeline
    timeline: {
      title: '活動タイムライン',
      selectDate: '日付を選択：',
      totalRecords: '合計',
      recordsUnit: '件の記録',
      noActivities: '📭 活動記録なし',
      systemMonitoring: 'システムが監視中です。後でページを更新してください',
      loading: '読み込み中...',
      loadFailed: '❌ 活動の読み込みに失敗しました',
      retry: '再試行',
      confidence: '信頼度:'
    },

    // Settings
    settings: {
      title: '⚙️ 設定',
      subtitle: 'AIWorkTracker の設定を構成',
      language: '🌍 AI 出力言語',
      languageOptions: {
        en: 'English',
        zh: '中文 (Chinese)',
        ja: '日本語 (Japanese)'
      },
      languageHint: 'AIはこの言語で作業の説明とサマリーを生成します',
      model: '🤖 OpenAI モデル',
      modelOptions: {
        'gpt-5-mini': 'GPT-5 Mini (推奨)',
        'gpt-5': 'GPT-5'
      },
      modelHint: '高度なモデルはより良い分析を提供しますが、コストが高くなります',
      saveButton: '💾 設定を保存',
      saving: '保存中...',
      saveSuccess: '✅ 設定が正常に保存されました！',
      saveFailed: '❌ 設定の保存に失敗しました',
      loadFailed: '設定の読み込みに失敗しました',
      loading: '読み込み中...',
      note: 'ℹ️',
      noteText: '注意：言語の変更は新しい分析に適用されます。既存の記録は影響を受けません。'
    },

    // Common
    common: {
      hours: '時間',
      minutes: '分',
      times: '回'
    }
  }
};

/**
 * 获取翻译文本
 * @param {string} lang - 语言代码
 * @param {string} key - 翻译键（支持点号分隔的嵌套键）
 * @returns {string} - 翻译文本
 */
export function t(lang, key) {
  const keys = key.split('.');
  let value = translations[lang] || translations['en'];

  for (const k of keys) {
    value = value[k];
    if (value === undefined) {
      console.warn(`Translation missing for key: ${key} in language: ${lang}`);
      return key;
    }
  }

  return value;
}

export default translations;
