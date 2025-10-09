/**
 * 语言上下文
 * 管理全局语言状态
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { t } from '../i18n/translations';
import api from '../services/api';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('zh');
  const [loading, setLoading] = useState(true);

  // 从后端加载语言设置
  useEffect(() => {
    const loadLanguage = async () => {
      try {
        const settings = await api.getSettings();
        setLanguage(settings.language || 'zh');
      } catch (err) {
        console.error('Failed to load language setting:', err);
        // 默认使用中文
        setLanguage('zh');
      } finally {
        setLoading(false);
      }
    };

    loadLanguage();
  }, []);

  // 提供翻译函数
  const translate = (key) => {
    return t(language, key);
  };

  const value = {
    language,
    setLanguage,
    t: translate,
    loading
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

// 自定义 Hook
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
}

export default LanguageContext;
