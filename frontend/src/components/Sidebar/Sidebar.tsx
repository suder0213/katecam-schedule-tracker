import { useState, type ReactNode } from 'react'
import { TodoTab } from './TodoTab'
import { TeamTab } from './TeamTab'

export interface SidebarTab {
  key: string
  label: string
  content: ReactNode
}

interface SidebarProps {
  // Manager/dev-only tabs get appended here in later phases (student list, Agent panel).
  extraTabs?: SidebarTab[]
}

export function Sidebar({ extraTabs = [] }: SidebarProps) {
  const tabs: SidebarTab[] = [
    { key: 'todo', label: 'TODO', content: <TodoTab /> },
    { key: 'team', label: 'Team', content: <TeamTab /> },
    ...extraTabs,
  ]
  const [activeKey, setActiveKey] = useState(tabs[0].key)
  const activeTab = tabs.find((t) => t.key === activeKey) ?? tabs[0]

  return (
    <aside className="w-64 shrink-0 border-r border-neutral-200 bg-white">
      <div className="flex border-b border-neutral-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveKey(tab.key)}
            className={`flex-1 px-3 py-2.5 text-sm font-medium transition ${
              activeKey === tab.key
                ? 'border-b-2 border-kakao-yellow-dark text-kakao-black'
                : 'text-neutral-400 hover:text-neutral-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="max-h-[calc(100vh-7rem)] overflow-y-auto">{activeTab.content}</div>
    </aside>
  )
}
