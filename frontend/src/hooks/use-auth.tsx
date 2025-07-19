'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, LoginRequest, RegisterRequest } from '@/types'
import { authApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      const userData = await authApi.me()
      setUser(userData)
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (data: LoginRequest) => {
    try {
      const response = await authApi.login(data)
      
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      setUser(response.user)
      toast.success('¡Sesión iniciada correctamente!')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Error al iniciar sesión'
      toast.error(message)
      throw error
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      const user = await authApi.register(data)
      toast.success('¡Usuario registrado correctamente! Ahora puedes iniciar sesión.')
      return user
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Error al registrar usuario'
      toast.error(message)
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      setUser(null)
      toast.success('Sesión cerrada')
    }
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}