import { useState, useEffect } from 'react';
import api from '../services/api';
import { useLanguage } from '../contexts/LanguageContext';

export default function Settings() {
  const { t, language, setLanguage: setGlobalLanguage } = useLanguage();
  const [settings, setSettings] = useState({
    language: 'en',
    openai_model: 'gpt-5-mini'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings', err);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      await api.updateSettings(settings);
      setMessage({ type: 'success', text: t('settings.saveSuccess') });

      // 更新全局语言状态
      if (settings.language !== language) {
        setGlobalLanguage(settings.language);
      }
    } catch (err) {
      console.error('Failed to save settings', err);
      setMessage({ type: 'error', text: t('settings.saveFailed') });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">{t('settings.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          {t('settings.title')}
        </h1>
        <p className="text-gray-600 mb-8">
          {t('settings.subtitle')}
        </p>

        <div className="bg-white rounded-lg shadow p-6 mb-4">
          {/* Language Setting */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('settings.language')}
            </label>
            <select
              value={settings.language}
              onChange={(e) => setSettings({...settings, language: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="en">{t('settings.languageOptions.en')}</option>
              <option value="zh">{t('settings.languageOptions.zh')}</option>
              <option value="ja">{t('settings.languageOptions.ja')}</option>
            </select>
            <p className="mt-2 text-sm text-gray-500">
              {t('settings.languageHint')}
            </p>
          </div>

          {/* Model Setting */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('settings.model')}
            </label>
            <select
              value={settings.openai_model}
              onChange={(e) => setSettings({...settings, openai_model: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gpt-5-mini">{t('settings.modelOptions.gpt-5-mini')}</option>
              <option value="gpt-5">{t('settings.modelOptions.gpt-5')}</option>
            </select>
            <p className="mt-2 text-sm text-gray-500">
              {t('settings.modelHint')}
            </p>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className={`w-full px-4 py-2 rounded-lg font-medium ${
              saving
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {saving ? t('settings.saving') : t('settings.saveButton')}
          </button>
        </div>

        {/* Message */}
        {message && (
          <div className={`rounded-lg p-4 ${
            message.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            {t('settings.note')} <strong>{t('settings.note')}:</strong> {t('settings.noteText')}
          </p>
        </div>
      </div>
    </div>
  );
}
