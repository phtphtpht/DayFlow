import { useState } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import Timeline from './components/Timeline';
import Settings from './components/Settings';
import DatePicker from './components/DatePicker';
import type { PageType } from './types';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');
  const [selectedDate, setSelectedDate] = useState(new Date());

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard selectedDate={selectedDate} />;
      case 'timeline':
        return <Timeline selectedDate={selectedDate} />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard selectedDate={selectedDate} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex justify-end mb-6">
          <DatePicker selectedDate={selectedDate} onDateChange={setSelectedDate} />
        </div>
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
