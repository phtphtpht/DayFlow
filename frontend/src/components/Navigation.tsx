import { LayoutDashboard, Clock, Settings } from 'lucide-react';
import type { PageType } from '../types';

interface NavigationProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

export default function Navigation({ currentPage, onPageChange }: NavigationProps) {
  const navItems = [
    { id: 'dashboard' as PageType, label: '仪表板', icon: LayoutDashboard },
    { id: 'timeline' as PageType, label: '时间线', icon: Clock },
    { id: 'settings' as PageType, label: '设置', icon: Settings },
  ];

  return (
    <nav className="backdrop-blur-lg bg-white/10 border-b border-white/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-lg">
              <Clock className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">DayFlow</h1>
          </div>

          <div className="flex gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onPageChange(item.id)}
                  className={`
                    flex items-center gap-2 px-6 py-2.5 rounded-xl
                    transition-all duration-300 font-medium
                    ${isActive
                      ? 'bg-white/20 text-white shadow-lg backdrop-blur-md'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
