import { useState } from 'react'
import Dashboard from './components/Dashboard'
import Timeline from './components/Timeline'
import Settings from './components/Settings'
import { useLanguage } from './contexts/LanguageContext'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-800">
              {t('appTitle')}
            </h1>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentPage === 'dashboard'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {t('nav.dashboard')}
              </button>
              <button
                onClick={() => setCurrentPage('timeline')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentPage === 'timeline'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {t('nav.timeline')}
              </button>
              <button
                onClick={() => setCurrentPage('settings')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentPage === 'settings'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {t('nav.settings')}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 内容区域 */}
      <main>
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'timeline' && <Timeline />}
        {currentPage === 'settings' && <Settings />}
      </main>
    </div>
  )
}

export default App
