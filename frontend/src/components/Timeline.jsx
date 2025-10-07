/**
 * Timeline 组件
 * 按时间顺序显示今日所有活动记录
 */

import { useState, useEffect } from 'react';
import api from '../services/api';

export default function Timeline() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  useEffect(() => {
    loadActivities();

    // 每30秒自动刷新一次
    const interval = setInterval(() => {
      loadActivities();
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedDate]);

  const loadActivities = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getActivities(selectedDate);
      setActivities(data);
    } catch (err) {
      setError('加载活动失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 获取类别图标
  const getCategoryIcon = (category) => {
    const icons = {
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
    return icons[category] || '📌';
  };

  // 获取类别颜色
  const getCategoryColor = (category) => {
    const colors = {
      coding: 'bg-blue-100 text-blue-800',
      writing: 'bg-green-100 text-green-800',
      meeting: 'bg-purple-100 text-purple-800',
      browsing: 'bg-yellow-100 text-yellow-800',
      communication: 'bg-pink-100 text-pink-800',
      design: 'bg-indigo-100 text-indigo-800',
      data_analysis: 'bg-orange-100 text-orange-800',
      entertainment: 'bg-red-100 text-red-800',
      other: 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
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
            onClick={loadActivities}
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* 日期选择器 */}
        <div className="mb-6 flex items-center gap-4">
          <label className="text-gray-700 font-medium">选择日期：</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={new Date().toISOString().split('T')[0]}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-gray-600">
            {new Date(selectedDate).toLocaleDateString('zh-CN', {
              weekday: 'long'
            })}
            · 共 {activities.length} 条记录
          </p>
        </div>

        {/* 时间线 */}
        {activities.length > 0 ? (
          <div className="space-y-4">
            {activities.map((activity, index) => (
              <div
                key={activity.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  {/* 时间 */}
                  <div className="flex-shrink-0 w-16 text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {new Date(activity.timestamp).toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>

                  {/* 连接线 */}
                  <div className="flex-shrink-0 flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${
                      activity.analyzed ? 'bg-blue-500' : 'bg-gray-300'
                    }`}></div>
                    {index < activities.length - 1 && (
                      <div className="w-0.5 h-full bg-gray-200 mt-1"></div>
                    )}
                  </div>

                  {/* 内容 */}
                  <div className="flex-1 min-w-0">
                    {/* 应用名和类别 */}
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">
                        {activity.category ? getCategoryIcon(activity.category) : '📌'}
                      </span>
                      <span className="font-medium text-gray-900">
                        {activity.app_name}
                      </span>
                      {activity.category && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          getCategoryColor(activity.category)
                        }`}>
                          {activity.category}
                        </span>
                      )}
                    </div>

                    {/* 描述 */}
                    {activity.description && (
                      <p className="text-gray-700 text-sm mb-2">
                        {activity.description}
                      </p>
                    )}

                    {/* 窗口标题 */}
                    {activity.window_title && (
                      <p className="text-gray-500 text-xs truncate">
                        {activity.window_title}
                      </p>
                    )}

                    {/* 置信度 */}
                    {activity.confidence && (
                      <div className="mt-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">
                            置信度: {activity.confidence}%
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-1.5 max-w-xs">
                            <div
                              className={`h-1.5 rounded-full ${
                                activity.confidence >= 80
                                  ? 'bg-green-500'
                                  : activity.confidence >= 60
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${activity.confidence}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-400 text-lg mb-2">📭 暂无活动记录</p>
            <p className="text-gray-500 text-sm">
              系统正在监控中，请稍后刷新页面
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
