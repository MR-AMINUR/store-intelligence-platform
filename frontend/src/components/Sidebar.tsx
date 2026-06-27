'use client'

import { Store, Activity, TrendingUp, Map, AlertTriangle, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  selectedStore: string
  onStoreChange: (storeId: string) => void
}

const stores = [
  { id: 'store_001', name: 'Store 001', location: 'Downtown' },
  { id: 'store_002', name: 'Store 002', location: 'Mall' },
  { id: 'store_1', name: 'Store 1', location: 'Purplle Store 1' },
  { id: 'store_2', name: 'Store 2', location: 'Purplle Store 2' },
]

export default function Sidebar({ selectedStore, onStoreChange }: SidebarProps) {
  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Store className="w-8 h-8 text-primary-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Store Intel</h1>
            <p className="text-xs text-gray-500">Analytics Platform</p>
          </div>
        </div>
      </div>

      {/* Store Selection */}
      <div className="p-4 border-b border-gray-200">
        <label className="block text-xs font-medium text-gray-700 mb-2">
          SELECT STORE
        </label>
        <select
          value={selectedStore}
          onChange={(e) => onStoreChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {stores.map((store) => (
            <option key={store.id} value={store.id}>
              {store.name} - {store.location}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        <NavItem icon={Activity} label="Overview" active />
        <NavItem icon={TrendingUp} label="Metrics" />
        <NavItem icon={Map} label="Heatmap" />
        <NavItem icon={AlertTriangle} label="Anomalies" />
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <button className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 w-full">
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </button>
        <div className="mt-4 text-xs text-gray-400">
          <p>© 2024 Store Intelligence</p>
          <p className="mt-1">v1.0.0</p>
        </div>
      </div>
    </div>
  )
}

interface NavItemProps {
  icon: React.ElementType
  label: string
  active?: boolean
}

function NavItem({ icon: Icon, label, active }: NavItemProps) {
  return (
    <button
      className={cn(
        'flex items-center space-x-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors',
        active
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-700 hover:bg-gray-50'
      )}
    >
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </button>
  )
}
