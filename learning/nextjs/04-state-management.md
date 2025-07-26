# Next.js State Management

## Overview

State management in Next.js applications involves handling different types of state: local component state, global application state, server state, and form state. This guide covers the patterns used in our busca-pisos project.

## Types of State

### 1. Local Component State
- UI state (modals, dropdowns, toggles)
- Component-specific data
- Temporary form input values

### 2. Global Application State
- User authentication state
- Theme preferences
- Navigation state

### 3. Server State
- Data fetched from APIs
- Cache management
- Background updates

### 4. Form State
- Form input values
- Validation errors
- Submission status

## Local State with React Hooks

### useState Hook

Basic state management for components:

```tsx
// src/components/properties/PropertyCard.tsx
'use client'
import { useState } from 'react'
import { Heart, HeartIcon } from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'

interface PropertyCardProps {
  property: Property
}

export function PropertyCard({ property }: PropertyCardProps) {
  const [isFavorite, setIsFavorite] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  const toggleFavorite = () => {
    setIsFavorite(!isFavorite)
    // Could also update server state here
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow">
      <div className="relative">
        <img 
          src={property.imageUrl} 
          alt={property.nombre}
          className="w-full h-48 object-cover rounded-t-lg"
        />
        
        {/* Favorite button */}
        <button
          onClick={toggleFavorite}
          className="absolute top-2 right-2 p-2 bg-white rounded-full shadow"
        >
          {isFavorite ? (
            <HeartSolidIcon className="h-5 w-5 text-red-500" />
          ) : (
            <HeartIcon className="h-5 w-5 text-gray-400" />
          )}
        </button>
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-lg mb-2">{property.nombre}</h3>
        <p className="text-2xl font-bold text-blue-600 mb-2">
          €{property.precio?.toLocaleString()}
        </p>
        
        {/* Expandable description */}
        <div>
          <p className={`text-gray-600 ${isExpanded ? '' : 'line-clamp-2'}`}>
            {property.description}
          </p>
          {property.description.length > 100 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-500 text-sm mt-1 hover:underline"
            >
              {isExpanded ? 'Ver menos' : 'Ver más'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
```

### useEffect Hook

Managing side effects and lifecycle:

```tsx
// src/components/dashboard/PropertyStats.tsx
'use client'
import { useState, useEffect } from 'react'

export function PropertyStats() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true // Prevent state updates if component unmounts

    const fetchStats = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/properties/stats')
        
        if (!response.ok) {
          throw new Error('Failed to fetch stats')
        }
        
        const data = await response.json()
        
        if (isMounted) {
          setStats(data)
          setError(null)
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchStats()

    // Cleanup function
    return () => {
      isMounted = false
    }
  }, []) // Empty dependency array - runs once on mount

  if (loading) return <div>Loading stats...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-semibold">Total Properties</h3>
        <p className="text-3xl font-bold text-blue-600">
          {stats?.totalProperties || 0}
        </p>
      </div>
      {/* More stat cards... */}
    </div>
  )
}
```

### Custom Hooks

Extracting stateful logic into reusable hooks:

```tsx
// src/hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(
  key: string, 
  initialValue: T
): [T, (value: T) => void] {
  // Get from local storage then parse stored json or return initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }
    
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // Return a wrapped version of useState's setter function that persists to localStorage
  const setValue = (value: T) => {
    try {
      setStoredValue(value)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(value))
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue]
}

// Usage in components
export function ThemeToggle() {
  const [theme, setTheme] = useLocalStorage('theme', 'light')
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Current theme: {theme}
    </button>
  )
}
```

```tsx
// src/hooks/useToggle.ts
import { useState, useCallback } from 'react'

export function useToggle(initialValue = false): [boolean, () => void] {
  const [value, setValue] = useState(initialValue)
  
  const toggle = useCallback(() => {
    setValue(prev => !prev)
  }, [])
  
  return [value, toggle]
}

// Usage
export function Modal() {
  const [isOpen, toggleOpen] = useToggle(false)
  
  return (
    <>
      <button onClick={toggleOpen}>Open Modal</button>
      {isOpen && <div>Modal content...</div>}
    </>
  )
}
```

## Global State with Context API

### Authentication Context

```tsx
// src/contexts/AuthContext.tsx
'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  username: string
  email: string
  role: string
}

interface AuthContextType {
  user: User | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          setLoading(false)
          return
        }

        const response = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        })

        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        } else {
          localStorage.removeItem('token')
        }
      } catch (error) {
        console.error('Auth check failed:', error)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    const { user, token } = await response.json()
    localStorage.setItem('token', token)
    setUser(user)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
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

### Theme Context

```tsx
// src/contexts/ThemeContext.tsx
'use client'
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')

  // Load theme from localStorage and system preference
  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme
    const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' 
      : 'light'
    
    setTheme(stored || systemPreference)
  }, [])

  // Update localStorage and document class when theme changes
  useEffect(() => {
    localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
```

### Providers Setup

```tsx
// src/app/providers.tsx
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        retry: 1,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
```

## Server State with TanStack Query

### Query Client Setup

```tsx
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on 404s
        if (error?.status === 404) return false
        return failureCount < 3
      },
    },
  },
})
```

### API Functions

```tsx
// src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export const api = {
  // Properties
  getProperties: async (params?: PropertySearchParams): Promise<Property[]> => {
    const url = new URL(`${API_BASE_URL}/api/properties/`)
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, value.toString())
        }
      })
    }
    
    const response = await fetch(url.toString())
    if (!response.ok) {
      throw new Error('Failed to fetch properties')
    }
    return response.json()
  },

  getProperty: async (id: string): Promise<Property> => {
    const response = await fetch(`${API_BASE_URL}/api/properties/${id}`)
    if (!response.ok) {
      throw new Error('Failed to fetch property')
    }
    return response.json()
  },

  // Analytics
  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await fetch(`${API_BASE_URL}/api/analytics/`)
    if (!response.ok) {
      throw new Error('Failed to fetch analytics')
    }
    return response.json()
  }
}
```

### Query Hooks

```tsx
// src/hooks/useProperties.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useProperties(searchParams?: PropertySearchParams) {
  return useQuery({
    queryKey: ['properties', searchParams],
    queryFn: () => api.getProperties(searchParams),
    enabled: true, // Always enabled
  })
}

export function useProperty(id: string) {
  return useQuery({
    queryKey: ['property', id],
    queryFn: () => api.getProperty(id),
    enabled: !!id, // Only run if ID is provided
  })
}

export function useCreateProperty() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: api.createProperty,
    onSuccess: () => {
      // Invalidate properties list to refetch
      queryClient.invalidateQueries({ queryKey: ['properties'] })
    },
  })
}

export function useUpdateProperty() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PropertyUpdate }) =>
      api.updateProperty(id, data),
    onSuccess: (_, { id }) => {
      // Invalidate specific property and properties list
      queryClient.invalidateQueries({ queryKey: ['property', id] })
      queryClient.invalidateQueries({ queryKey: ['properties'] })
    },
  })
}
```

### Using Queries in Components

```tsx
// src/components/properties/PropertiesList.tsx
'use client'
import { useState } from 'react'
import { useProperties } from '@/hooks/useProperties'
import { PropertyCard } from './PropertyCard'
import { PropertyFilters } from './PropertyFilters'

export function PropertiesList() {
  const [filters, setFilters] = useState<PropertySearchParams>({})
  
  const {
    data: properties,
    isLoading,
    error,
    refetch
  } = useProperties(filters)

  if (isLoading) {
    return <div>Loading properties...</div>
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error loading properties</p>
        <button 
          onClick={() => refetch()}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div>
      <PropertyFilters 
        filters={filters} 
        onFiltersChange={setFilters} 
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {properties?.map((property) => (
          <PropertyCard key={property.p_id} property={property} />
        ))}
      </div>
      
      {properties?.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No properties found</p>
        </div>
      )}
    </div>
  )
}
```

## Form State Management

### With react-hook-form

```tsx
// src/components/forms/PropertySearchForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const searchSchema = z.object({
  location: z.string().optional(),
  minPrice: z.number().min(0).optional(),
  maxPrice: z.number().min(0).optional(),
  propertyType: z.enum(['apartment', 'house', 'commercial']).optional(),
})

type SearchFormData = z.infer<typeof searchSchema>

interface PropertySearchFormProps {
  onSearch: (data: SearchFormData) => void
  initialValues?: Partial<SearchFormData>
}

export function PropertySearchForm({ onSearch, initialValues }: PropertySearchFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
    reset
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
    defaultValues: initialValues
  })

  // Watch form values for real-time updates
  const minPrice = watch('minPrice')

  const onSubmit = async (data: SearchFormData) => {
    await onSearch(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <input
            type="text"
            {...register('location')}
            placeholder="e.g., Madrid, Barcelona"
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
          {errors.location && (
            <p className="text-red-500 text-sm mt-1">{errors.location.message}</p>
          )}
        </div>

        {/* Min Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Price (€)
          </label>
          <input
            type="number"
            {...register('minPrice', { valueAsNumber: true })}
            placeholder="50,000"
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
          {errors.minPrice && (
            <p className="text-red-500 text-sm mt-1">{errors.minPrice.message}</p>
          )}
        </div>

        {/* Max Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Price (€)
          </label>
          <input
            type="number"
            {...register('maxPrice', { 
              valueAsNumber: true,
              validate: (value) => {
                if (minPrice && value && value < minPrice) {
                  return 'Max price must be greater than min price'
                }
                return true
              }
            })}
            placeholder="500,000"
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
          {errors.maxPrice && (
            <p className="text-red-500 text-sm mt-1">{errors.maxPrice.message}</p>
          )}
        </div>

        {/* Property Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Property Type
          </label>
          <select
            {...register('propertyType')}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="">All Types</option>
            <option value="apartment">Apartment</option>
            <option value="house">House</option>
            <option value="commercial">Commercial</option>
          </select>
        </div>
      </div>

      <div className="flex space-x-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Searching...' : 'Search Properties'}
        </button>
        
        <button
          type="button"
          onClick={() => reset()}
          className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300"
        >
          Clear
        </button>
      </div>
    </form>
  )
}
```

## State Management Best Practices

### 1. Choose the Right Tool
- **Local state**: `useState` for simple UI state
- **Global state**: Context for theme, auth
- **Server state**: TanStack Query for API data
- **Form state**: react-hook-form for complex forms

### 2. Optimize Re-renders
```tsx
// Use React.memo for expensive components
export const PropertyCard = React.memo(({ property }: PropertyCardProps) => {
  // Component implementation
})

// Use useMemo for expensive calculations
function PropertyList({ properties }: { properties: Property[] }) {
  const sortedProperties = useMemo(() => {
    return properties.sort((a, b) => b.precio - a.precio)
  }, [properties])
  
  return (
    <div>
      {sortedProperties.map(property => (
        <PropertyCard key={property.id} property={property} />
      ))}
    </div>
  )
}
```

### 3. Error Boundaries
```tsx
// src/components/ErrorBoundary.tsx
'use client'
import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error }>
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      const Fallback = this.props.fallback || DefaultErrorFallback
      return <Fallback error={this.state.error!} />
    }

    return this.props.children
  }
}

function DefaultErrorFallback({ error }: { error: Error }) {
  return (
    <div className="text-center py-12">
      <h2 className="text-xl font-bold text-red-600 mb-2">Something went wrong</h2>
      <p className="text-gray-600">{error.message}</p>
    </div>
  )
}
```

## Practice Exercises

1. **Create a favorites system** using local storage and global state
2. **Build a shopping cart** with add/remove functionality
3. **Implement real-time notifications** using WebSocket and state
4. **Add form validation** with complex business rules
5. **Create a theme switcher** with system preference detection

## Next Steps

In the next guide, we'll explore:
- API integration patterns
- Real-time data with WebSockets
- Error handling and loading states
- Optimistic updates and caching strategies