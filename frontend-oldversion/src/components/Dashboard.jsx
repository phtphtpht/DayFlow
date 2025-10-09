/**
 * Dashboard 组件
 * 显示今日工作概览、统计数据和摘要
 */

import { useState, useEffect } from 'react';
import api from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export default function Dashboard() {
  const { t } = useLanguage();
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  // 加载数据
  useEffect(() => {
    loadData();

    // 每30秒自动刷新一次
    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedDate]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 并行请求统计和摘要
      const [statsData, summaryData] = await Promise.all([
        api.getStats(selectedDate),
        api.getSummary(selectedDate)
      ]);

      setStats(statsData);
      setSummary(summaryData);
    } catch (err) {
      setError(t('dashboard.loadFailed'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 生成摘要
  const handleGenerateSummary = async () => {
    setGenerating(true);
    setError(null);

    try {
      const result = await api.generateSummary(selectedDate);
      setSummary({
        date: result.date,
        summary_text: result.summary_text,
        generated_at: new Date().toISOString()
      });
    } catch (err) {
      setError(err.message || 'Failed to generate summary');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-blue-200"></div>
            <div className="absolute inset-0 rounded-full border-4 border-blue-600 border-t-transparent animate-spin"></div>
          </div>
          <p className="text-gray-600 font-medium">{t('dashboard.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <p className="text-red-600">❌ {error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            {t('dashboard.retry')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* 生成摘要 Loading 遮罩 */}
      {generating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-700">{t('dashboard.generatingSummary')}</p>
            <p className="text-sm text-gray-500 mt-2">{t('dashboard.mayTakeTime')}</p>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-6">
        <div className="max-w-6xl mx-auto">
        {/* 标题区域 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            AIWorkTracker
          </h1>
          <div className="h-1 w-32 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-2"></div>
          <p className="text-gray-600">
            {new Date(selectedDate).toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long'
            })}
          </p>
        </div>

        {/* 日期选择器 */}
        <div className="mb-6 flex items-center gap-4">
          <label className="text-gray-700 font-medium">{t('dashboard.selectDate')}</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={new Date().toISOString().split('T')[0]}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* 总记录数 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium mb-2">{t('dashboard.totalRecords')}</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-blue-600 to-blue-400 bg-clip-text text-transparent">
                  {stats?.total_records || 0}
                </p>
              </div>
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center text-3xl shadow-lg">
                📝
              </div>
            </div>
          </div>

          {/* 已分析 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium mb-2">{t('dashboard.analyzedRecords')}</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-green-600 to-green-400 bg-clip-text text-transparent">
                  {stats?.analyzed_records || 0}
                </p>
              </div>
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center text-3xl shadow-lg">
                ✅
              </div>
            </div>
          </div>

          {/* 工作时长 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium mb-2">{t('dashboard.workHours')}</p>
                <p className="text-4xl font-bold bg-gradient-to-br from-purple-600 to-purple-400 bg-clip-text text-transparent">
                  {(() => {
                    const hours = Math.floor(stats?.work_hours || 0);
                    const minutes = Math.round(((stats?.work_hours || 0) - hours) * 60);
                    return `${hours}${t('common.hours')} ${minutes}${t('common.minutes')}`;
                  })()}
                </p>
              </div>
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center text-3xl shadow-lg">
                ⏱️
              </div>
            </div>
          </div>
        </div>

        {/* 类别分布 */}
        {stats?.category_distribution &&
         Object.keys(stats.category_distribution).length > 0 && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-100 p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {t('dashboard.categoryDistribution')}
            </h2>
            <div className="space-y-3">
              {Object.entries(stats.category_distribution).map(([category, count]) => {
                const percentage = (count / stats.analyzed_records * 100).toFixed(1);

                return (
                  <div key={category}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700 font-medium">
                        {t(`dashboard.categories.${category}`)}
                      </span>
                      <span className="text-gray-500">
                        {count}{t('common.times')} ({percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 via-blue-600 to-purple-500 h-3 rounded-full transition-all duration-1000 ease-out shadow-sm"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 今日摘要 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <span className="text-3xl">📄</span>
              {t('dashboard.dailyLog')}
            </h2>
            <button
              onClick={handleGenerateSummary}
              disabled={generating || (stats?.analyzed_records || 0) === 0}
              className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-300 ${
                generating || (stats?.analyzed_records || 0) === 0
                  ? 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 hover:shadow-lg hover:-translate-y-0.5'
              }`}
            >
              {generating ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⚙️</span>
                  {t('dashboard.generating')}
                </span>
              ) : (
                `🔄 ${t('dashboard.generateSummary')}`
              )}
            </button>
          </div>

          {summary?.summary_text ? (
            <div>
              <div className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl p-6 border border-gray-200 mb-4">
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {summary.summary_text}
                </p>
              </div>
              <p className="text-sm text-gray-500">
                {t('dashboard.generatedAt')} {new Date(summary.generated_at).toLocaleString('zh-CN')}
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-400 mb-4">{t('dashboard.noSummary')}</p>
              {(stats?.analyzed_records || 0) > 0 ? (
                <p className="text-sm text-gray-500">
                  {t('dashboard.clickToGenerate')}
                </p>
              ) : (
                <p className="text-sm text-gray-500">
                  {t('dashboard.noAnalyzed')}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
