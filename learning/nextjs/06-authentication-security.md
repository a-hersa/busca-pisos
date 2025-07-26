# Next.js Authentication & Security

## Overview

This guide covers implementing authentication and security in our Next.js frontend, including JWT token management, protected routes, user session handling, and integration with our FastAPI backend.

## Authentication Strategy

Our busca-pisos project uses:
- **JWT tokens** for stateless authentication
- **HTTP-only approach** (stored in localStorage for simplicity)
- **Role-based access control** (user, admin)
- **Protected routes** with Next.js middleware
- **Automatic token refresh** for better UX

## Authentication Context

### Auth Context Provider

```tsx
// src/contexts/AuthContext.tsx
'use client'
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authService, User, LoginCredentials } from '@/services/authService'
import { ApiError } from '@/lib/api'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
  hasRole: (role: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setIsLoading(false)
        return
      }

      // Verify token with backend
      const userData = await authService.getCurrentUser()
      setUser(userData)
    } catch (error) {
      // Token is invalid or expired
      localStorage.removeItem('token')
      setUser(null)
      
      if (error instanceof ApiError && error.status === 401) {
        console.log('Token expired, user needs to re-authenticate')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await authService.login(credentials)
      
      // Store token
      localStorage.setItem('token', response.access_token)
      
      // Set user in state
      setUser(response.user)
      
      return response
    } catch (error) {
      throw error
    }
  }

  const logout = async () => {
    try {
      // Call logout endpoint to invalidate token on server
      await authService.logout()
    } catch (error) {
      // Even if server logout fails, clear local state
      console.error('Server logout failed:', error)
    } finally {
      // Clear local state
      localStorage.removeItem('token')
      setUser(null)
    }
  }

  const refreshAuth = async () => {
    await checkAuthStatus()
  }

  const hasRole = (role: string): boolean => {
    if (!user) return false
    
    // Admin has access to everything
    if (user.role === 'admin') return true
    
    // Check specific role
    return user.role === role
  }

  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshAuth,
    hasRole,
  }

  return (
    <AuthContext.Provider value={contextValue}>
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
```

## Authentication Components

### Login Form

```tsx
// src/components/auth/LoginForm.tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'react-hot-toast'
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema)
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data)
      toast.success('Welcome back!')
      router.push('/dashboard')
    } catch (error: any) {
      const message = error.message || 'Login failed'
      
      if (message.toLowerCase().includes('username') || message.toLowerCase().includes('password')) {
        setError('root', { message: 'Invalid username or password' })
      } else {
        setError('root', { message })
      }
      
      toast.error('Login failed')
    }
  }

  return (
    <div className="max-w-md w-full space-y-8">
      <div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <a href="/auth/register" className="font-medium text-blue-600 hover:text-blue-500">
            create a new account
          </a>
        </p>
      </div>
      
      <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              {...register('username')}
              type="text"
              autoComplete="username"
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Enter your username"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <div className="mt-1 relative">
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>
        </div>

        {errors.root && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{errors.root.message}</p>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
              Remember me
            </label>
          </div>

          <div className="text-sm">
            <a href="/auth/forgot-password" className="font-medium text-blue-600 hover:text-blue-500">
              Forgot your password?
            </a>
          </div>
        </div>

        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </div>
      </form>
    </div>
  )
}
```

### Registration Form

```tsx
// src/components/auth/RegisterForm.tsx
'use client'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { authService } from '@/services/authService'
import { toast } from 'react-hot-toast'

const registerSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
  email: z
    .string()
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/\d/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

type RegisterFormData = z.infer<typeof registerSchema>

export function RegisterForm() {
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema)
  })

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await authService.register({
        username: data.username,
        email: data.email,
        password: data.password,
        confirm_password: data.confirmPassword,
      })
      
      toast.success('Account created successfully! Please log in.')
      router.push('/auth/login')
    } catch (error: any) {
      const message = error.message || 'Registration failed'
      
      if (message.toLowerCase().includes('username')) {
        setError('username', { message: 'Username is already taken' })
      } else if (message.toLowerCase().includes('email')) {
        setError('email', { message: 'Email is already registered' })
      } else {
        setError('root', { message })
      }
      
      toast.error('Registration failed')
    }
  }

  return (
    <div className="max-w-md w-full space-y-8">
      <div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <a href="/auth/login" className="font-medium text-blue-600 hover:text-blue-500">
            sign in to your existing account
          </a>
        </p>
      </div>
      
      <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              {...register('username')}
              type="text"
              autoComplete="username"
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Choose a username"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              {...register('email')}
              type="email"
              autoComplete="email"
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Enter your email"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              {...register('password')}
              type="password"
              autoComplete="new-password"
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Create a password"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <input
              {...register('confirmPassword')}
              type="password"
              autoComplete="new-password"
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Confirm your password"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>
        </div>

        {errors.root && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{errors.root.message}</p>
          </div>
        )}

        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </div>
      </form>
    </div>
  )
}
```

## Protected Routes

### Authentication Middleware

```tsx
// src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Define protected routes
const protectedRoutes = [
  '/dashboard',
  '/profile',
  '/admin',
]

const adminRoutes = [
  '/admin',
]

const authRoutes = [
  '/auth/login',
  '/auth/register',
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '')

  // Check if current path is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  )
  
  const isAdminRoute = adminRoutes.some(route => 
    pathname.startsWith(route)
  )
  
  const isAuthRoute = authRoutes.some(route => 
    pathname.startsWith(route)
  )

  // Redirect to login if accessing protected route without token
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Redirect authenticated users away from auth pages
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // For admin routes, we'll check the role on the client side
  // since we can't easily decode JWT in middleware
  if (isAdminRoute && token) {
    // Add a header to indicate this is an admin route
    const response = NextResponse.next()
    response.headers.set('x-admin-route', 'true')
    return response
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
```

### Route Guards

```tsx
// src/components/auth/RouteGuard.tsx
'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface RouteGuardProps {
  children: React.ReactNode
  requiredRole?: string
  fallback?: React.ReactNode
}

export function RouteGuard({ 
  children, 
  requiredRole, 
  fallback = <div>Loading...</div> 
}: RouteGuardProps) {
  const { user, isLoading, isAuthenticated, hasRole } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/auth/login')
        return
      }

      if (requiredRole && !hasRole(requiredRole)) {
        router.push('/unauthorized')
        return
      }
    }
  }, [isLoading, isAuthenticated, user, requiredRole, router, hasRole])

  if (isLoading) {
    return <>{fallback}</>
  }

  if (!isAuthenticated) {
    return null
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return null
  }

  return <>{children}</>
}

// Usage in layouts
export function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RouteGuard requiredRole="admin">
      <div className="admin-layout">
        {children}
      </div>
    </RouteGuard>
  )
}
```

### Protected Page Component

```tsx
// src/components/auth/withAuth.tsx
'use client'
import { ComponentType } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

interface WithAuthOptions {
  requiredRole?: string
  redirectTo?: string
}

export function withAuth<P extends object>(
  Component: ComponentType<P>,
  options: WithAuthOptions = {}
) {
  const { requiredRole, redirectTo = '/auth/login' } = options

  return function AuthenticatedComponent(props: P) {
    const { user, isLoading, isAuthenticated, hasRole } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading) {
        if (!isAuthenticated) {
          router.push(redirectTo)
          return
        }

        if (requiredRole && !hasRole(requiredRole)) {
          router.push('/unauthorized')
          return
        }
      }
    }, [isLoading, isAuthenticated, user, router])

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )
    }

    if (!isAuthenticated || (requiredRole && !hasRole(requiredRole))) {
      return null
    }

    return <Component {...props} />
  }
}

// Usage
const AdminDashboard = withAuth(DashboardComponent, { requiredRole: 'admin' })
const UserProfile = withAuth(ProfileComponent)
```

## User Session Management

### Session Persistence

```tsx
// src/hooks/useSession.ts
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'

export function useSession() {
  const { user, isLoading, refreshAuth } = useAuth()
  const router = useRouter()

  // Check session validity periodically
  useEffect(() => {
    const checkSession = async () => {
      try {
        await refreshAuth()
      } catch (error) {
        // Session expired, redirect to login
        router.push('/auth/login')
      }
    }

    // Check session every 5 minutes
    const interval = setInterval(checkSession, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [refreshAuth, router])

  // Check session on window focus
  useEffect(() => {
    const handleFocus = () => {
      if (!isLoading && user) {
        refreshAuth()
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [isLoading, user, refreshAuth])

  return { user, isLoading }
}
```

### User Profile Component

```tsx
// src/components/auth/UserProfile.tsx
'use client'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'

interface ProfileData {
  username: string
  email: string
}

export function UserProfile() {
  const { user, logout } = useAuth()
  const [isEditing, setIsEditing] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
    reset
  } = useForm<ProfileData>({
    defaultValues: {
      username: user?.username || '',
      email: user?.email || '',
    }
  })

  const onSubmit = async (data: ProfileData) => {
    try {
      // Update profile API call would go here
      toast.success('Profile updated successfully!')
      setIsEditing(false)
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      toast.success('Logged out successfully')
    } catch (error) {
      toast.error('Logout failed')
    }
  }

  if (!user) return null

  return (
    <div className="max-w-2xl mx-auto bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Profile</h3>
      </div>
      
      <div className="px-6 py-4">
        {!isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <p className="mt-1 text-sm text-gray-900">{user.username}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="mt-1 text-sm text-gray-900">{user.email}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <span className="mt-1 inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {user.role}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Member since</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setIsEditing(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Edit Profile
              </button>
              
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                {...register('username')}
                type="text"
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                {...register('email')}
                type="email"
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
              
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false)
                  reset()
                }}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
```

## Security Best Practices

### 1. Token Storage
```tsx
// Instead of localStorage, consider using httpOnly cookies for production
// This example shows localStorage for simplicity

// src/lib/tokenStorage.ts
export const tokenStorage = {
  set: (token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token)
    }
  },
  
  get: (): string | null => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token')
    }
    return null
  },
  
  remove: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
  }
}
```

### 2. CSRF Protection
```tsx
// src/lib/csrf.ts
export function getCSRFToken(): string {
  return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
}

// Add to API client
private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const config: RequestInit = {
    headers: {
      ...this.defaultHeaders,
      'X-CSRF-Token': getCSRFToken(),
      ...options.headers,
    },
    credentials: 'include', // Send cookies
    ...options,
  }
  
  // ... rest of implementation
}
```

### 3. Input Sanitization
```tsx
// src/lib/sanitize.ts
import DOMPurify from 'isomorphic-dompurify'

export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html)
}

export function sanitizeInput(input: string): string {
  return input.trim().replace(/[<>]/g, '')
}
```

## Practice Exercises

1. **Implement password reset** flow with email verification
2. **Add two-factor authentication** using TOTP
3. **Create role-based navigation** menus
4. **Implement session timeout** warnings
5. **Add social login** with OAuth providers

## Next Steps

In the next guide, we'll explore:
- Styling with Tailwind CSS
- Component design systems
- Responsive design patterns
- Dark mode implementation