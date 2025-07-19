'use client'

import { useAuth } from '@/hooks/use-auth'
import { LoginForm } from '@/components/auth/login-form'
import { Dashboard } from '@/components/dashboard/dashboard'
import { Loader2 } from 'lucide-react'

export default function HomePage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Inmobiliario Tools
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Inicia sesión para acceder al panel de control
            </p>
          </div>
          <LoginForm />
        </div>
      </div>
    )
  }

  return <Dashboard />
}