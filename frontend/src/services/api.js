/**
 * API 服务层
 * 封装所有与后端的 HTTP 通信
 */

// API基础配置
const API_BASE_URL = 'http://localhost:8000';

/**
 * 通用请求处理函数
 */
async function request(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
}

/**
 * API服务对象
 */
const api = {
  // ========== 健康检查 ==========

  /**
   * 健康检查
   */
  healthCheck: () => request('/api/health'),

  // ========== 活动相关 ==========

  /**
   * 获取今日活动
   */
  getTodayActivities: () => request('/api/activities/today'),

  /**
   * 获取指定日期的活动
   * @param {string} date - 日期字符串 YYYY-MM-DD
   */
  getActivities: (date) => {
    const url = date ? `/api/activities?date=${date}` : '/api/activities';
    return request(url);
  },

  // ========== 摘要相关 ==========

  /**
   * 获取今日摘要
   */
  getTodaySummary: () => request('/api/summary/today'),

  /**
   * 获取指定日期的摘要
   * @param {string} date - 日期字符串 YYYY-MM-DD
   */
  getSummary: (date) => request(`/api/summary/${date}`),

  /**
   * 生成摘要
   * @param {string} date - 日期字符串 YYYY-MM-DD，不传则生成今天的
   */
  generateSummary: (date) => {
    const url = date ? `/api/summary/generate?date=${date}` : '/api/summary/generate';
    return request(url, { method: 'POST' });
  },

  // ========== 统计相关 ==========

  /**
   * 获取今日统计
   */
  getTodayStats: () => request('/api/stats/today'),

  /**
   * 获取指定日期的统计
   * @param {string} date - 日期字符串 YYYY-MM-DD
   */
  getStats: (date) => {
    const url = date ? `/api/stats?date=${date}` : '/api/stats/today';
    return request(url);
  },

  // ========== 设置相关 ==========

  /**
   * 获取用户设置
   */
  getSettings: () => request('/api/settings'),

  /**
   * 更新用户设置
   * @param {object} settings - 设置对象
   */
  updateSettings: (settings) => request('/api/settings', {
    method: 'POST',
    body: JSON.stringify(settings)
  }),
};

export default api;
