import { useState } from 'react'
import Dashboard from './components/Dashboard'
import Timeline from './components/Timeline'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')

  return (
    <div>
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-800">
              📊 AIWorkTracker
            </h1>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'dashboard'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📊 概览
              </button>
              <button
                onClick={() => setCurrentView('timeline')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentView === 'timeline'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ⏱️ 时间线
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 内容区域 */}
      {currentView === 'dashboard' ? <Dashboard /> : <Timeline />}
    </div>
  )
}

export default App
