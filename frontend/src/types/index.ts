export interface ActivityRecord {
  id: string;
  timestamp: string;
  appName: string;
  activityDescription: string;
  windowTitle: string;
  confidence: number;
  category?: string;
}

export interface StatCard {
  title: string;
  value: number;
  icon: string;
}

export interface ActivityCategory {
  name: string;
  percentage: number;
  color: string;
}

export type Language = 'zh' | 'en' | 'ja';

export type PageType = 'dashboard' | 'timeline' | 'settings';
