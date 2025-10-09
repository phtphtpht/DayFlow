import { Database, CheckCircle, Clock, Sparkles } from 'lucide-react';
import { useState, useEffect } from 'react';
import api, { Stats, Summary } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ElementType;
  gradient: string;
}

function StatCard({ title, value, icon: Icon, gradient }: StatCardProps) {
  return (
    <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl ${gradient} flex items-center justify-center shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
      <h3 className="text-white/70 text-sm font-medium mb-1">{title}</h3>
      <p className="text-3xl font-bold text-white">{typeof value === 'number' ? value.toLocaleString() : value}</p>
    </div>
  );
}

interface ActivityBarProps {
  category: string;
  percentage: number;
  count: number;
  color: string;
}

function ActivityBar({ category, percentage, count, color }: ActivityBarProps) {
  const { t } = useLanguage();

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-medium">{category}</span>
        <span className="text-white/70 text-sm">
          {count}{t('common.times')} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
        <div
          className={`h-full ${color} rounded-full transition-all duration-1000 ease-out shadow-lg`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface DashboardProps {
  selectedDate: Date;
}

export default function Dashboard({ selectedDate }: DashboardProps) {
  const { t } = useLanguage();
  const [stats, setStats] = useState<Stats | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dateString = selectedDate.toISOString().split('T')[0];

  useEffect(() => {
    loadData(true); // 初始加载显示 loading

    // 每30秒静默刷新数据
    const interval = setInterval(() => {
      loadData(false); // 自动刷新不显示 loading
    }, 30000);

    return () => clearInterval(interval);
  }, [dateString]);

  const loadData = async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);

    try {
      const [statsData, summaryData] = await Promise.all([
        api.getStats(dateString),
        api.getSummary(dateString)
      ]);

      setStats(statsData);
      setSummary(summaryData);
    } catch (err) {
      setError(t('dashboard.loadFailed'));
      console.error(err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const handleGenerateSummary = async () => {
    setGenerating(true);
    setError(null);

    try {
      const result = await api.generateSummary(dateString);
      setSummary(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate summary');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-white/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-white border-t-transparent animate-spin"></div>
          </div>
          <p className="text-white font-medium">{t('dashboard.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="backdrop-blur-lg bg-red-500/20 border border-red-300/30 rounded-2xl p-6 max-w-md">
          <p className="text-white mb-4">❌ {error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors"
          >
            {t('dashboard.retry')}
          </button>
        </div>
      </div>
    );
  }

  const workHoursDisplay = (() => {
    const hours = Math.floor(stats?.work_hours || 0);
    const minutes = Math.round(((stats?.work_hours || 0) - hours) * 60);
    return `${hours}${t('common.hours')} ${minutes}${t('common.minutes')}`;
  })();

  const categoryColors: Record<string, string> = {
    coding: 'bg-gradient-to-r from-blue-400 to-blue-600',
    writing: 'bg-gradient-to-r from-green-400 to-green-600',
    meeting: 'bg-gradient-to-r from-purple-400 to-purple-600',
    browsing: 'bg-gradient-to-r from-yellow-400 to-yellow-600',
    communication: 'bg-gradient-to-r from-pink-400 to-pink-600',
    entertainment: 'bg-gradient-to-r from-orange-400 to-orange-600',
    design: 'bg-gradient-to-r from-indigo-400 to-indigo-600',
    data_analysis: 'bg-gradient-to-r from-cyan-400 to-cyan-600',
    other: 'bg-gradient-to-r from-gray-400 to-gray-600',
  };

  return (
    <>
      {/* 生成摘要 Loading 遮罩 */}
      {generating && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="backdrop-blur-lg bg-white/10 border border-white/20 rounded-2xl p-6 text-center">
            <div className="relative w-12 h-12 mx-auto mb-4">
              <div className="absolute inset-0 rounded-full border-4 border-white/20"></div>
              <div className="absolute inset-0 rounded-full border-4 border-white border-t-transparent animate-spin"></div>
            </div>
            <p className="text-white font-medium">{t('dashboard.generatingSummary')}</p>
            <p className="text-sm text-white/70 mt-2">{t('dashboard.mayTakeTime')}</p>
          </div>
        </div>
      )}

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title={t('dashboard.totalRecords')}
            value={stats?.total_records || 0}
            icon={Database}
            gradient="bg-gradient-to-br from-blue-400 to-blue-600"
          />
          <StatCard
            title={t('dashboard.analyzedRecords')}
            value={stats?.analyzed_records || 0}
            icon={CheckCircle}
            gradient="bg-gradient-to-br from-green-400 to-green-600"
          />
          <StatCard
            title={t('dashboard.workHours')}
            value={workHoursDisplay}
            icon={Clock}
            gradient="bg-gradient-to-br from-purple-400 to-purple-600"
          />
        </div>

        {/* 类别分布 */}
        {stats?.category_distribution && Object.keys(stats.category_distribution).length > 0 && (
          <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
            <h2 className="text-2xl font-bold text-white mb-6">{t('dashboard.categoryDistribution')}</h2>
            <div>
              {Object.entries(stats.category_distribution).map(([category, count]) => {
                const percentage = (count / stats.analyzed_records * 100);
                return (
                  <ActivityBar
                    key={category}
                    category={t(`dashboard.categories.${category}`)}
                    percentage={percentage}
                    count={count}
                    color={categoryColors[category] || categoryColors.other}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* 今日摘要 */}
        <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">{t('dashboard.dailyLog')}</h2>
            <button
              onClick={handleGenerateSummary}
              disabled={generating || (stats?.analyzed_records || 0) === 0}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Sparkles className="w-5 h-5" />
              {generating ? t('dashboard.generating') : t('dashboard.generateSummary')}
            </button>
          </div>

          {summary?.summary_text ? (
            <div>
              <div className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10 mb-4">
                <p className="text-white/90 leading-relaxed text-lg whitespace-pre-wrap">
                  {summary.summary_text}
                </p>
              </div>
              <p className="text-sm text-white/60">
                {t('dashboard.generatedAt')} {new Date(summary.generated_at).toLocaleString('zh-CN')}
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-white/60 mb-4">{t('dashboard.noSummary')}</p>
              {(stats?.analyzed_records || 0) > 0 ? (
                <p className="text-sm text-white/50">{t('dashboard.clickToGenerate')}</p>
              ) : (
                <p className="text-sm text-white/50">{t('dashboard.noAnalyzed')}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
