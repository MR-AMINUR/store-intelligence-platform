'use client'

import { useState } from 'react'
import Dashboard from '@/components/Dashboard'
import Sidebar from '@/components/Sidebar'

export default function Home() {
  const [selectedStore, setSelectedStore] = useState<string>('store_001')

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar 
        selectedStore={selectedStore} 
        onStoreChange={setSelectedStore} 
      />
      <main className="flex-1 overflow-y-auto">
        <Dashboard storeId={selectedStore} />
      </main>
    </div>
  )
}
