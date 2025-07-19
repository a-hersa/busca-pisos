'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/use-auth'
import { useWebSocket } from '@/hooks/use-websocket'
import { AdminTab } from './admin-tab'
import { LazyJobsTab, LazyPropertiesTab, LazyAnalyticsTab, LazyComponentWrapper } from '../ui/lazy-loading'
import { 
  LogOut, 
  Briefcase, 
  Home, 
  Shield,
  BarChart3,
  Wifi,
  WifiOff
} from 'lucide-react'

type Tab = 'jobs' | 'properties' | 'analytics' | 'admin'

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('jobs')
  const { user, logout } = useAuth()
  const { isConnected } = useWebSocket()

  const tabs = [
    { id: 'jobs' as Tab, label: 'Trabajos de Crawling', icon: Briefcase },
    { id: 'properties' as Tab, label: 'Propiedades', icon: Home },
    { id: 'analytics' as Tab, label: 'Análisis de Datos', icon: BarChart3 },
    ...(user?.role === 'admin' ? [{ id: 'admin' as Tab, label: 'Administración', icon: Shield }] : [])
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                Inmobiliario Tools
              </h1>
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Conectado' : 'Desconectado'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Bienvenido, <span className="font-medium">{user?.username}</span>
              </span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                {user?.role}
              </span>
              <button
                onClick={logout}
                className="flex items-center space-x-1 text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                <LogOut className="h-4 w-4" />
                <span>Salir</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {activeTab === 'jobs' && (
          <LazyComponentWrapper>
            <LazyJobsTab />
          </LazyComponentWrapper>
        )}
        {activeTab === 'properties' && (
          <LazyComponentWrapper>
            <LazyPropertiesTab />
          </LazyComponentWrapper>
        )}
        {activeTab === 'analytics' && (
          <LazyComponentWrapper>
            <LazyAnalyticsTab />
          </LazyComponentWrapper>
        )}
        {activeTab === 'admin' && user?.role === 'admin' && <AdminTab />}
      </main>
    </div>
  )
}