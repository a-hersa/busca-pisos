'use client'

import { Suspense, lazy } from 'react'
import { Loader2 } from 'lucide-react'

// Lazy load heavy components to improve initial bundle size
export const LazyAnalyticsTab = lazy(() => 
  import('../dashboard/analytics-tab').then(module => ({ default: module.AnalyticsTab }))
)

export const LazyPropertiesTab = lazy(() => 
  import('../dashboard/properties-tab').then(module => ({ default: module.PropertiesTab }))
)

export const LazyJobsTab = lazy(() => 
  import('../dashboard/jobs-tab').then(module => ({ default: module.JobsTab }))
)

interface LazyComponentWrapperProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function LazyComponentWrapper({ children, fallback }: LazyComponentWrapperProps) {
  const defaultFallback = (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
    </div>
  )

  return (
    <Suspense fallback={fallback || defaultFallback}>
      {children}
    </Suspense>
  )
}