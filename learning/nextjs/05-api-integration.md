# Next.js API Integration

## Overview

This guide covers how to integrate your Next.js frontend with the FastAPI backend in our busca-pisos project, including REST API communication, WebSocket connections, error handling, and real-time updates.

## API Client Setup

### Base API Configuration

```tsx
// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

class ApiClient {
  private baseURL: string
  private defaultHeaders: HeadersInit

  constructor() {
    this.baseURL = API_BASE_URL
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    // Get auth token if available
    const token = typeof window !== 'undefined' 
      ? localStorage.getItem('token') 
      : null

    const config: RequestInit = {
      headers: {
        ...this.defaultHeaders,
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      // Handle different response types
      if (!response.ok) {
        const errorData = await response.text()
        let errorMessage: string
        
        try {
          const parsedError = JSON.parse(errorData)
          errorMessage = parsedError.detail || parsedError.message || 'Request failed'
        } catch {
          errorMessage = errorData || `HTTP ${response.status}: ${response.statusText}`
        }
        
        throw new ApiError(errorMessage, response.status)
      }

      // Handle empty responses
      if (response.status === 204) {
        return {} as T
      }

      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return await response.json()
      }
      
      return await response.text() as unknown as T
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      
      // Network or other errors
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error occurred',
        0
      )
    }
  }

  // HTTP Methods
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(endpoint, this.baseURL)
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, value.toString())
        }
      })
    }
    
    return this.request<T>(url.pathname + url.search)
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    })
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }
}

// Custom error class
export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

// Export singleton instance
export const api = new ApiClient()
```

### API Service Modules

```tsx
// src/services/propertyService.ts
import { api } from '@/lib/api'

export interface Property {
  p_id: number
  nombre: string
  precio: number
  metros: string
  poblacion: string
  url: string
  estatus: string
  fecha_updated: string
  fecha_crawl: string
}

export interface PropertySearchParams {
  skip?: number
  limit?: number
  poblacion?: string
  precio_min?: number
  precio_max?: number
  metros_min?: number
  estatus?: string
}

export interface PropertyCreate {
  nombre: string
  precio?: number
  metros?: string
  poblacion?: string
  url: string
  estatus?: string
}

export interface PropertyUpdate {
  nombre?: string
  precio?: number
  metros?: string
  poblacion?: string
  estatus?: string
}

export const propertyService = {
  // Get paginated properties list
  getProperties: (params?: PropertySearchParams): Promise<Property[]> =>
    api.get('/api/properties/', params),

  // Get single property by ID
  getProperty: (id: string): Promise<Property> =>
    api.get(`/api/properties/${id}`),

  // Search properties with filters
  searchProperties: (params: PropertySearchParams): Promise<Property[]> =>
    api.get('/api/properties/search', params),

  // Create new property
  createProperty: (data: PropertyCreate): Promise<Property> =>
    api.post('/api/properties/', data),

  // Update existing property
  updateProperty: (id: string, data: PropertyUpdate): Promise<Property> =>
    api.put(`/api/properties/${id}`, data),

  // Delete property
  deleteProperty: (id: string): Promise<void> =>
    api.delete(`/api/properties/${id}`),

  // Get property statistics
  getPropertyStats: (): Promise<any> =>
    api.get('/api/analytics/properties/stats'),
}
```

```tsx
// src/services/authService.ts
import { api } from '@/lib/api'

export interface User {
  user_id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  confirm_password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export const authService = {
  // Login user
  login: (credentials: LoginCredentials): Promise<AuthResponse> =>
    api.post('/auth/login', credentials),

  // Register new user
  register: (data: RegisterData): Promise<User> =>
    api.post('/auth/register', data),

  // Get current user profile
  getCurrentUser: (): Promise<User> =>
    api.get('/auth/me'),

  // Refresh access token
  refreshToken: (): Promise<AuthResponse> =>
    api.post('/auth/refresh'),

  // Logout (invalidate token)
  logout: (): Promise<void> =>
    api.post('/auth/logout'),

  // Request password reset
  requestPasswordReset: (email: string): Promise<void> =>
    api.post('/auth/password-reset-request', { email }),

  // Reset password with token
  resetPassword: (token: string, newPassword: string): Promise<void> =>
    api.post('/auth/password-reset', { token, new_password: newPassword }),
}
```

## React Query Integration

### Query Hooks for Properties

```tsx
// src/hooks/useProperties.ts
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { propertyService, Property, PropertySearchParams, PropertyCreate, PropertyUpdate } from '@/services/propertyService'
import { toast } from 'react-hot-toast'

// Query keys factory
export const propertyKeys = {
  all: ['properties'] as const,
  lists: () => [...propertyKeys.all, 'list'] as const,
  list: (params?: PropertySearchParams) => [...propertyKeys.lists(), params] as const,
  details: () => [...propertyKeys.all, 'detail'] as const,
  detail: (id: string) => [...propertyKeys.details(), id] as const,
  search: (params: PropertySearchParams) => [...propertyKeys.all, 'search', params] as const,
  stats: () => [...propertyKeys.all, 'stats'] as const,
}

// Get properties list
export function useProperties(
  params?: PropertySearchParams,
  options?: Omit<UseQueryOptions<Property[]>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: propertyKeys.list(params),
    queryFn: () => propertyService.getProperties(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

// Get single property
export function useProperty(
  id: string,
  options?: Omit<UseQueryOptions<Property>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: propertyKeys.detail(id),
    queryFn: () => propertyService.getProperty(id),
    enabled: !!id,
    ...options,
  })
}

// Search properties
export function usePropertySearch(
  params: PropertySearchParams,
  enabled = true
) {
  return useQuery({
    queryKey: propertyKeys.search(params),
    queryFn: () => propertyService.searchProperties(params),
    enabled: enabled && Object.keys(params).length > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes for search results
  })
}

// Property statistics
export function usePropertyStats() {
  return useQuery({
    queryKey: propertyKeys.stats(),
    queryFn: propertyService.getPropertyStats,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Create property mutation
export function useCreateProperty() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: propertyService.createProperty,
    onSuccess: (newProperty) => {
      // Update properties lists
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() })
      
      // Add to cache
      queryClient.setQueryData(
        propertyKeys.detail(newProperty.p_id.toString()),
        newProperty
      )
      
      toast.success('Property created successfully!')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create property: ${error.message}`)
    },
  })
}

// Update property mutation
export function useUpdateProperty() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PropertyUpdate }) =>
      propertyService.updateProperty(id, data),
    onSuccess: (updatedProperty, { id }) => {
      // Update property in cache
      queryClient.setQueryData(
        propertyKeys.detail(id),
        updatedProperty
      )
      
      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() })
      
      toast.success('Property updated successfully!')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update property: ${error.message}`)
    },
  })
}

// Delete property mutation
export function useDeleteProperty() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: propertyService.deleteProperty,
    onSuccess: (_, propertyId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: propertyKeys.detail(propertyId) })
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: propertyKeys.lists() })
      
      toast.success('Property deleted successfully!')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete property: ${error.message}`)
    },
  })
}
```

### Authentication Hooks

```tsx
// src/hooks/useAuth.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authService, User, LoginCredentials, RegisterData } from '@/services/authService'
import { toast } from 'react-hot-toast'
import { useRouter } from 'next/navigation'

const authKeys = {
  user: ['auth', 'user'] as const,
}

export function useCurrentUser() {
  return useQuery({
    queryKey: authKeys.user,
    queryFn: authService.getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation({
    mutationFn: authService.login,
    onSuccess: (response) => {
      // Store token
      localStorage.setItem('token', response.access_token)
      
      // Update user cache
      queryClient.setQueryData(authKeys.user, response.user)
      
      toast.success('Welcome back!')
      router.push('/dashboard')
    },
    onError: (error: Error) => {
      toast.error(`Login failed: ${error.message}`)
    },
  })
}

export function useRegister() {
  const router = useRouter()

  return useMutation({
    mutationFn: authService.register,
    onSuccess: () => {
      toast.success('Account created successfully! Please log in.')
      router.push('/auth/login')
    },
    onError: (error: Error) => {
      toast.error(`Registration failed: ${error.message}`)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation({
    mutationFn: authService.logout,
    onSuccess: () => {
      // Clear token and cache
      localStorage.removeItem('token')
      queryClient.clear()
      
      toast.success('Logged out successfully')
      router.push('/')
    },
    onError: () => {
      // Even if API call fails, clear local state
      localStorage.removeItem('token')
      queryClient.clear()
      router.push('/')
    },
  })
}
```

## WebSocket Integration

### WebSocket Hook

```tsx
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface UseWebSocketOptions {
  reconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (message: WebSocketMessage) => void
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
) {
  const {
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const queryClient = useQueryClient()

  const connect = () => {
    try {
      const token = localStorage.getItem('token')
      const wsUrl = token ? `${url}?token=${token}` : url
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
        console.log('WebSocket connected')
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Handle different message types
          switch (message.type) {
            case 'property_update':
              // Invalidate property queries
              queryClient.invalidateQueries({ queryKey: ['properties'] })
              break
              
            case 'job_status_update':
              // Update job status in cache
              queryClient.invalidateQueries({ queryKey: ['jobs'] })
              break
              
            case 'analytics_update':
              // Refresh analytics data
              queryClient.invalidateQueries({ queryKey: ['analytics'] })
              break
          }
          
          // Call custom message handler
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      wsRef.current.onclose = (event) => {
        setIsConnected(false)
        
        if (!event.wasClean && reconnectAttemptsRef.current < reconnectAttempts) {
          setTimeout(() => {
            reconnectAttemptsRef.current++
            console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`)
            connect()
          }, reconnectInterval)
        }
      }
      
      wsRef.current.onerror = (error) => {
        setError('WebSocket connection error')
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      setError('Failed to create WebSocket connection')
      console.error('WebSocket connection error:', error)
    }
  }

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  useEffect(() => {
    connect()
    return disconnect
  }, [url])

  return {
    isConnected,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
  }
}
```

### Real-time Dashboard Component

```tsx
// src/components/dashboard/RealTimeDashboard.tsx
'use client'
import { useWebSocket } from '@/hooks/useWebSocket'
import { usePropertyStats } from '@/hooks/useProperties'
import { toast } from 'react-hot-toast'

export function RealTimeDashboard() {
  const { data: stats, refetch } = usePropertyStats()
  
  const { isConnected, error } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL}/ws/dashboard`,
    {
      onMessage: (message) => {
        switch (message.type) {
          case 'new_property':
            toast.success(`New property added: ${message.data.nombre}`)
            refetch() // Refresh stats
            break
            
          case 'property_sold':
            toast.info(`Property sold: ${message.data.nombre}`)
            refetch()
            break
            
          case 'crawl_completed':
            toast.success(`Crawl completed: ${message.data.properties_found} properties found`)
            refetch()
            break
        }
      }
    }
  )

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Real-time Dashboard</h1>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">Connection error: {error}</p>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold text-gray-900">Total Properties</h3>
          <p className="text-3xl font-bold text-blue-600">
            {stats?.totalProperties || 0}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold text-gray-900">Active Listings</h3>
          <p className="text-3xl font-bold text-green-600">
            {stats?.activeProperties || 0}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold text-gray-900">Average Price</h3>
          <p className="text-3xl font-bold text-purple-600">
            €{stats?.averagePrice?.toLocaleString() || 0}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg border">
          <h3 className="text-lg font-semibold text-gray-900">Last Updated</h3>
          <p className="text-sm text-gray-600">
            {stats?.lastUpdated ? new Date(stats.lastUpdated).toLocaleString() : 'Never'}
          </p>
        </div>
      </div>
    </div>
  )
}
```

## Error Handling

### Global Error Handler

```tsx
// src/components/ErrorBoundary.tsx
'use client'
import React from 'react'
import { ApiError } from '@/lib/api'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught error:', error, errorInfo)
    
    // Report to error tracking service
    if (typeof window !== 'undefined') {
      // Example: Sentry.captureException(error)
    }
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />
    }

    return this.props.children
  }
}

function ErrorFallback({ error }: { error?: Error }) {
  const isApiError = error instanceof ApiError
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
          <svg
            className="w-6 h-6 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>
        
        <div className="mt-4 text-center">
          <h3 className="text-lg font-medium text-gray-900">
            {isApiError ? 'API Error' : 'Something went wrong'}
          </h3>
          
          <p className="mt-2 text-sm text-gray-500">
            {error?.message || 'An unexpected error occurred'}
          </p>
          
          {isApiError && (
            <p className="mt-1 text-xs text-gray-400">
              Status: {(error as ApiError).status}
            </p>
          )}
        </div>
        
        <div className="mt-6">
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Reload Page
          </button>
        </div>
      </div>
    </div>
  )
}
```

### Query Error Handling

```tsx
// src/components/properties/PropertiesWithErrorHandling.tsx
'use client'
import { useProperties } from '@/hooks/useProperties'
import { ApiError } from '@/lib/api'

export function PropertiesWithErrorHandling() {
  const { data, isLoading, error, refetch } = useProperties()

  if (isLoading) {
    return <div>Loading properties...</div>
  }

  if (error) {
    const isApiError = error instanceof ApiError
    const isNetworkError = error.message.includes('Network')
    
    return (
      <div className="text-center py-12">
        <div className="max-w-md mx-auto">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {isNetworkError ? 'Connection Problem' : 'Error Loading Properties'}
          </h3>
          
          <p className="text-gray-600 mb-4">
            {isNetworkError 
              ? 'Please check your internet connection and try again.'
              : error.message
            }
          </p>
          
          {isApiError && (
            <p className="text-sm text-gray-500 mb-4">
              Error code: {(error as ApiError).status}
            </p>
          )}
          
          <button
            onClick={() => refetch()}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Render properties */}
      {data?.map(property => (
        <div key={property.p_id}>
          {/* Property card */}
        </div>
      ))}
    </div>
  )
}
```

## Practice Exercises

1. **Implement optimistic updates** for property favorites
2. **Create a real-time chat** using WebSockets
3. **Add infinite scrolling** for properties list
4. **Build an offline-first** properties cache
5. **Implement retry logic** for failed API calls

## Next Steps

In the next guide, we'll explore:
- JWT authentication implementation
- Protected routes and middleware
- User session management
- Role-based access control