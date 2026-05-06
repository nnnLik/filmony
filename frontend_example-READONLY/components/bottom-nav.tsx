'use client'

import { Home, Search, UserCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

type Tab = 'feed' | 'search' | 'profile'

interface BottomNavProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

export function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  const tabs = [
    { id: 'feed' as Tab, label: 'Лента', icon: Home },
    { id: 'search' as Tab, label: 'Поиск', icon: Search },
    { id: 'profile' as Tab, label: 'Профиль', icon: UserCircle },
  ]

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-background border-t border-border">
      <div className="max-w-md mx-auto flex items-center justify-around py-2 px-4">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={cn(
                'flex flex-col items-center gap-1 py-2 px-4 rounded-xl transition-colors',
                isActive 
                  ? 'text-primary' 
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <Icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 1.5} />
              <span className="text-xs font-medium">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
