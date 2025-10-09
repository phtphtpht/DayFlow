import { Activity, TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';
import api, { Activity as ActivityType } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

interface TimelineItemProps {
  activity: ActivityType;
  isLast: boolean;
}

function TimelineItem({ activity, isLast }: TimelineItemProps) {
  const { t } = useLanguage();

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'bg-gray-500';
    if (confidence >= 80) return 'bg-green-500';
    if (confidence >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getCategoryIcon = (category?: string) => {
    const icons: Record<string, string> = {
      coding: '💻',
      writing: '✍️',
      meeting: '👥',
      browsing: '🌐',
      communication: '💬',
      design: '🎨',
      data_analysis: '📊',
      entertainment: '🎮',
      other: '📌'
    };
    return category ? icons[category] || '📌' : '📌';
  };

  const getCategoryGradient = (category?: string) => {
    const gradients: Record<string, string> = {
      coding: 'from-blue-400 to-blue-600',
      writing: 'from-green-400 to-green-600',
      meeting: 'from-purple-400 to-purple-600',
      browsing: 'from-yellow-400 to-yellow-600',
      communication: 'from-pink-400 to-pink-600',
      entertainment: 'from-orange-400 to-orange-600',
      design: 'from-indigo-400 to-indigo-600',
      data_analysis: 'from-cyan-400 to-cyan-600',
      other: 'from-gray-400 to-gray-600',
    };
    return category ? gradients[category] || gradients.other : gradients.other;
  };

  return (
    <div className="backdrop-blur-lg bg-white/10 rounded-xl p-5 border border-white/20 shadow-lg hover:shadow-xl transition-all duration-300 hover:bg-white/15">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getCategoryGradient(activity.category)} flex items-center justify-center shadow-lg text-2xl`}>
            {getCategoryIcon(activity.category)}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <span className="text-white/70 text-sm font-medium">{formatTime(activity.timestamp)}</span>
            <span className="text-white font-semibold">{activity.app_name}</span>
            {activity.category && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-white/10 text-white border border-white/20">
                {t(`dashboard.categories.${activity.category}`)}
              </span>
            )}
            {activity.confidence !== undefined && (
              <div className="flex items-center gap-1.5 ml-auto">
                <TrendingUp className="w-4 h-4 text-white/70" />
                <span className="text-white/70 text-sm">{t('timeline.confidence')}</span>
                <span className="text-white/90 text-sm font-medium">{activity.confidence}%</span>
                <div className={`w-2 h-2 rounded-full ${getConfidenceColor(activity.confidence)} shadow-sm`} />
              </div>
            )}
          </div>

          {activity.description && (
            <p className="text-white text-base mb-2">{activity.description}</p>
          )}

          <div className="backdrop-blur-sm bg-white/5 rounded-lg px-3 py-2 border border-white/10">
            <p className="text-white/70 text-sm truncate">{activity.window_title}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface TimelineProps {
  selectedDate: Date;
}

export default function Timeline({ selectedDate }: TimelineProps) {
  const { t } = useLanguage();
  const [activities, setActivities] = useState<ActivityType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const dateString = selectedDate.toISOString().split('T')[0];

  useEffect(() => {
    loadActivities(true); // 初始加载显示 loading

    // 每30秒静默刷新数据
    const interval = setInterval(() => {
      loadActivities(false); // 自动刷新不显示 loading
    }, 30000);

    return () => clearInterval(interval);
  }, [dateString]);

  const loadActivities = async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);

    try {
      const data = await api.getActivities(dateString);
      setActivities(data);
    } catch (err) {
      setError(t('timeline.loadFailed'));
      console.error(err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
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
          <p className="text-white font-medium">{t('timeline.loading')}</p>
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
            onClick={loadActivities}
            className="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors"
          >
            {t('timeline.retry')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">{t('timeline.title')}</h2>
        <p className="text-white/70">
          {t('timeline.totalRecords')} {activities.length} {t('timeline.recordsUnit')}
        </p>
      </div>

      {activities.length > 0 ? (
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <TimelineItem
              key={activity.id}
              activity={activity}
              isLast={index === activities.length - 1}
            />
          ))}
        </div>
      ) : (
        <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-12 border border-white/20 text-center">
          <p className="text-white/70 text-lg mb-2">{t('timeline.noActivities')}</p>
          <p className="text-white/50 text-sm">{t('timeline.systemMonitoring')}</p>
        </div>
      )}
    </div>
  );
}
