import { Globe, Save, Check, Bot } from 'lucide-react';
import { useState, useEffect } from 'react';
import api, { Settings as SettingsType } from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';
import { Language } from '../i18n/translations';

export default function Settings() {
  const { t, language: currentLanguage, setLanguage: setGlobalLanguage } = useLanguage();
  const [settings, setSettings] = useState<Partial<SettingsType>>({
    language: 'en',
    openai_model: 'gpt-5-mini'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings', err);
      setError(t('settings.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setIsSaved(false);

    try {
      await api.updateSettings(settings);
      setIsSaved(true);

      // 更新全局语言状态
      if (settings.language && settings.language !== currentLanguage) {
        setGlobalLanguage(settings.language as Language);
      }

      setTimeout(() => setIsSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save settings', err);
      setError(t('settings.saveFailed'));
    } finally {
      setSaving(false);
    }
  };

  const languages = [
    { code: 'zh', label: t('settings.languageOptions.zh'), flag: '🇨🇳' },
    { code: 'en', label: t('settings.languageOptions.en'), flag: '🇺🇸' },
    { code: 'ja', label: t('settings.languageOptions.ja'), flag: '🇯🇵' },
  ];

  const models = [
    { value: 'gpt-5-mini', label: t('settings.modelOptions.gpt-5-mini') },
    { value: 'gpt-5', label: t('settings.modelOptions.gpt-5') },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-white/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-white border-t-transparent animate-spin"></div>
          </div>
          <p className="text-white font-medium">{t('settings.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">{t('settings.title')}</h2>
        <p className="text-white/70">{t('settings.subtitle')}</p>
      </div>

      {/* 语言设置 */}
      <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-lg">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">{t('settings.language')}</h3>
            <p className="text-white/70 text-sm">{t('settings.languageHint')}</p>
          </div>
        </div>

        <div className="space-y-3">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSettings({...settings, language: lang.code})}
              className={`
                w-full flex items-center justify-between p-4 rounded-xl
                transition-all duration-300 border
                ${settings.language === lang.code
                  ? 'bg-white/20 border-white/40 shadow-lg'
                  : 'bg-white/5 border-white/10 hover:bg-white/10'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{lang.flag}</span>
                <span className="text-white font-medium text-lg">{lang.label}</span>
              </div>
              {settings.language === lang.code && (
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* AI 模型设置 */}
      <div className="backdrop-blur-lg bg-white/10 rounded-2xl p-6 border border-white/20 shadow-xl mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">{t('settings.model')}</h3>
            <p className="text-white/70 text-sm">{t('settings.modelHint')}</p>
          </div>
        </div>

        <div className="space-y-3">
          {models.map((model) => (
            <button
              key={model.value}
              onClick={() => setSettings({...settings, openai_model: model.value})}
              className={`
                w-full flex items-center justify-between p-4 rounded-xl
                transition-all duration-300 border
                ${settings.openai_model === model.value
                  ? 'bg-white/20 border-white/40 shadow-lg'
                  : 'bg-white/5 border-white/10 hover:bg-white/10'
                }
              `}
            >
              <span className="text-white font-medium text-lg">{model.label}</span>
              {settings.openai_model === model.value && (
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 保存按钮 */}
      <button
        onClick={handleSave}
        disabled={saving || isSaved}
        className={`
          w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl
          font-medium text-white transition-all duration-300 shadow-lg backdrop-blur-lg
          ${isSaved
            ? 'bg-gradient-to-r from-green-500 to-green-600'
            : saving
            ? 'bg-white/10 cursor-not-allowed'
            : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:shadow-xl'
          }
        `}
      >
        {isSaved ? (
          <>
            <Check className="w-5 h-5" />
            {t('settings.saveSuccess')}
          </>
        ) : saving ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            {t('settings.saving')}
          </>
        ) : (
          <>
            <Save className="w-5 h-5" />
            {t('settings.saveButton')}
          </>
        )}
      </button>

      {/* 错误消息 */}
      {error && (
        <div className="mt-4 backdrop-blur-lg bg-red-500/20 border border-red-300/30 rounded-xl p-4">
          <p className="text-white text-sm">❌ {error}</p>
        </div>
      )}

      {/* 提示信息 */}
      <div className="mt-6 backdrop-blur-lg bg-blue-500/20 border border-blue-300/30 rounded-xl p-4">
        <p className="text-white/90 text-sm">
          {t('settings.note')} {t('settings.noteText')}
        </p>
      </div>
    </div>
  );
}
