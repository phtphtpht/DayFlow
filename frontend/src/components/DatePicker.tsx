import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface DatePickerProps {
  selectedDate: Date;
  onDateChange: (date: Date) => void;
}

export default function DatePicker({ selectedDate, onDateChange }: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const changeDate = (days: number) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + days);
    onDateChange(newDate);
  };

  const setToday = () => {
    onDateChange(new Date());
    setIsOpen(false);
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const handleDateInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value + 'T00:00:00');
    onDateChange(newDate);
    setIsOpen(false);
  };

  const getDateInputValue = () => {
    return selectedDate.toISOString().split('T')[0];
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2 backdrop-blur-lg bg-white/10 rounded-xl p-3 border border-white/20 shadow-lg">
        <button
          onClick={() => changeDate(-1)}
          className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-all duration-300"
        >
          <ChevronLeft className="w-5 h-5 text-white" />
        </button>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-4 py-1 hover:bg-white/10 rounded-lg transition-all duration-300"
        >
          <Calendar className="w-5 h-5 text-white" />
          <span className="text-white font-medium min-w-[140px]">
            {formatDate(selectedDate)}
          </span>
        </button>

        <button
          onClick={() => changeDate(1)}
          className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-all duration-300"
        >
          <ChevronRight className="w-5 h-5 text-white" />
        </button>
      </div>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 right-0 z-50 backdrop-blur-lg bg-white/10 rounded-xl p-4 border border-white/20 shadow-2xl min-w-[240px]">
            <div className="space-y-3">
              {/* 日期输入框 */}
              <div className="mb-3 pb-3 border-b border-white/20">
                <label className="block text-white/70 text-sm mb-2">选择日期</label>
                <input
                  type="date"
                  value={getDateInputValue()}
                  onChange={handleDateInputChange}
                  max={new Date().toISOString().split('T')[0]}
                  className="w-full px-3 py-2 bg-white/20 text-white rounded-lg border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all"
                />
              </div>

              {/* 快捷选项 */}
              <div>
                <button
                  onClick={setToday}
                  className={`
                    w-full px-4 py-2 rounded-lg text-left transition-all duration-300
                    ${isToday(selectedDate)
                      ? 'bg-white/20 text-white font-medium'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                    }
                  `}
                >
                  📅 今天
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
