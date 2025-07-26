# Next.js Routing & Navigation

## Overview

Next.js uses file-based routing with the App Router, where the file structure in the `app` directory determines your application's routes. This guide covers routing patterns used in our busca-pisos project.

## App Router Architecture

### Basic File Structure

```
src/app/
├── layout.tsx          # Root layout (applies to all pages)
├── page.tsx           # Home page (/)
├── loading.tsx        # Global loading UI
├── error.tsx          # Global error UI
├── not-found.tsx      # 404 page
├── globals.css        # Global styles
├── properties/        # /properties route group
│   ├── layout.tsx     # Layout for properties section
│   ├── page.tsx       # Properties list (/properties)
│   ├── loading.tsx    # Loading UI for properties
│   └── [id]/          # Dynamic route
│       ├── page.tsx   # Property detail (/properties/123)
│       └── loading.tsx # Loading UI for property detail
├── dashboard/         # /dashboard route group
│   ├── layout.tsx     # Dashboard layout with sidebar
│   ├── page.tsx       # Dashboard home (/dashboard)
│   ├── analytics/     # Nested route
│   │   └── page.tsx   # Analytics page (/dashboard/analytics)
│   └── jobs/          # Jobs management
│       ├── page.tsx   # Jobs list (/dashboard/jobs)
│       └── [id]/
│           └── page.tsx # Job detail (/dashboard/jobs/123)
└── auth/              # Authentication routes
    ├── layout.tsx     # Auth layout (centered forms)
    ├── login/
    │   └── page.tsx   # Login page (/auth/login)
    └── register/
        └── page.tsx   # Register page (/auth/register)
```

## Route Types

### 1. Static Routes

Simple pages with fixed URLs:

```tsx
// src/app/about/page.tsx
export default function AboutPage() {
  return (
    <div>
      <h1>About Busca Pisos</h1>
      <p>Educational real estate platform built with Next.js and FastAPI.</p>
    </div>
  )
}
```

### 2. Dynamic Routes

Use square brackets for dynamic segments:

```tsx
// src/app/properties/[id]/page.tsx
import { PropertyDetail } from '@/components/properties/PropertyDetail'

export default function PropertyPage({
  params
}: {
  params: { id: string }
}) {
  return (
    <div>
      <h1>Property Details</h1>
      <PropertyDetail propertyId={params.id} />
    </div>
  )
}

// Generates metadata dynamically
export async function generateMetadata({
  params
}: {
  params: { id: string }
}) {
  const property = await fetchProperty(params.id)
  
  return {
    title: `${property.nombre} - Busca Pisos`,
    description: `${property.poblacion} - €${property.precio}`,
  }
}
```

### 3. Catch-all Routes

Use `[...slug]` for catch-all segments:

```tsx
// src/app/search/[...filters]/page.tsx
export default function SearchPage({
  params
}: {
  params: { filters: string[] }
}) {
  // URL: /search/madrid/apartments/under-200k
  // params.filters = ['madrid', 'apartments', 'under-200k']
  
  return (
    <div>
      <h1>Search Results</h1>
      <p>Filters: {params.filters.join(' > ')}</p>
    </div>
  )
}
```

### 4. Optional Catch-all Routes

Use `[[...slug]]` for optional catch-all:

```tsx
// src/app/blog/[[...slug]]/page.tsx
export default function BlogPage({
  params
}: {
  params: { slug?: string[] }
}) {
  if (!params.slug) {
    // /blog - Blog home
    return <BlogHome />
  }
  
  if (params.slug.length === 1) {
    // /blog/category - Category page
    return <BlogCategory category={params.slug[0]} />
  }
  
  // /blog/category/post - Post page
  return <BlogPost category={params.slug[0]} post={params.slug[1]} />
}
```

## Layouts

### Root Layout

The root layout wraps all pages:

```tsx
// src/app/layout.tsx
import { Providers } from './providers'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Navigation />
            <main className="flex-1">
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  )
}
```

### Nested Layouts

Layouts can be nested for different sections:

```tsx
// src/app/dashboard/layout.tsx
import { DashboardSidebar } from '@/components/dashboard/Sidebar'
import { DashboardHeader } from '@/components/dashboard/Header'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <DashboardSidebar />
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <DashboardHeader />
        
        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

### Authentication Layout

Special layout for auth pages:

```tsx
// src/app/auth/layout.tsx
import { AuthBackground } from '@/components/auth/AuthBackground'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          {children}
        </div>
      </div>
      
      {/* Right side - Background */}
      <div className="hidden lg:block relative w-0 flex-1">
        <AuthBackground />
      </div>
    </div>
  )
}
```

## Navigation Components

### Main Navigation

```tsx
// src/components/layout/Navigation.tsx
'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Inicio', href: '/' },
  { name: 'Propiedades', href: '/properties' },
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'Analíticas', href: '/dashboard/analytics' },
]

export function Navigation() {
  const pathname = usePathname()
  
  return (
    <nav className="bg-white shadow border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <Link href="/" className="flex items-center">
              <span className="text-xl font-bold text-gray-900">
                🏠 Busca Pisos
              </span>
            </Link>
            
            {/* Navigation links */}
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
                    pathname === item.href
                      ? "border-blue-500 text-gray-900"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  )}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          
          {/* User menu */}
          <div className="flex items-center">
            <UserMenu />
          </div>
        </div>
      </div>
    </nav>
  )
}
```

### Dashboard Sidebar

```tsx
// src/components/dashboard/Sidebar.tsx
'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  HomeIcon, 
  BuildingOfficeIcon, 
  ChartBarIcon,
  CogIcon 
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: HomeIcon },
  { name: 'Properties', href: '/dashboard/properties', icon: BuildingOfficeIcon },
  { name: 'Analytics', href: '/dashboard/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: CogIcon },
]

export function DashboardSidebar() {
  const pathname = usePathname()
  
  return (
    <div className="flex flex-col w-64 bg-gray-800">
      <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <h2 className="text-lg font-semibold text-white">Dashboard</h2>
        </div>
        
        <nav className="mt-5 flex-1 px-2 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "group flex items-center px-2 py-2 text-sm font-medium rounded-md",
                  isActive
                    ? "bg-gray-900 text-white"
                    : "text-gray-300 hover:bg-gray-700 hover:text-white"
                )}
              >
                <item.icon
                  className="mr-3 h-6 w-6 flex-shrink-0"
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
```

## Navigation Hooks and Utilities

### usePathname Hook

```tsx
'use client'
import { usePathname } from 'next/navigation'

export function Breadcrumbs() {
  const pathname = usePathname()
  
  // Convert /dashboard/properties/123 to breadcrumbs
  const segments = pathname.split('/').filter(Boolean)
  
  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-1">
        <li>
          <Link href="/" className="text-gray-400 hover:text-gray-500">
            Inicio
          </Link>
        </li>
        {segments.map((segment, index) => {
          const href = '/' + segments.slice(0, index + 1).join('/')
          const isLast = index === segments.length - 1
          
          return (
            <li key={segment} className="flex">
              <ChevronRightIcon className="h-5 w-5 text-gray-400" />
              {isLast ? (
                <span className="ml-1 text-sm font-medium text-gray-500 capitalize">
                  {segment}
                </span>
              ) : (
                <Link
                  href={href}
                  className="ml-1 text-sm font-medium text-gray-500 hover:text-gray-700 capitalize"
                >
                  {segment}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
```

### useRouter for Programmatic Navigation

```tsx
'use client'
import { useRouter } from 'next/navigation'

export function SearchForm() {
  const router = useRouter()
  
  const handleSearch = (searchParams: SearchParams) => {
    // Build query string
    const params = new URLSearchParams()
    if (searchParams.location) params.set('location', searchParams.location)
    if (searchParams.minPrice) params.set('min_price', searchParams.minPrice.toString())
    if (searchParams.maxPrice) params.set('max_price', searchParams.maxPrice.toString())
    
    // Navigate to search results
    router.push(`/properties/search?${params.toString()}`)
  }
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      handleSearch(formData)
    }}>
      {/* Form fields */}
    </form>
  )
}
```

## Route Groups

Use parentheses to group routes without affecting the URL:

```
src/app/
├── (marketing)/           # Route group - not in URL
│   ├── layout.tsx        # Marketing layout
│   ├── page.tsx          # Home page (/)
│   ├── about/
│   │   └── page.tsx      # About page (/about)
│   └── contact/
│       └── page.tsx      # Contact page (/contact)
├── (app)/                # App route group
│   ├── layout.tsx        # App layout
│   ├── dashboard/
│   │   └── page.tsx      # Dashboard (/dashboard)
│   └── properties/
│       └── page.tsx      # Properties (/properties)
└── layout.tsx            # Root layout
```

## Parallel Routes

Display multiple pages simultaneously:

```
src/app/dashboard/
├── layout.tsx
├── page.tsx
├── @analytics/           # Parallel route slot
│   └── page.tsx
└── @notifications/       # Parallel route slot
    └── page.tsx
```

```tsx
// src/app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  notifications,
}: {
  children: React.ReactNode
  analytics: React.ReactNode
  notifications: React.ReactNode
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        {children}
      </div>
      <div className="space-y-6">
        {analytics}
        {notifications}
      </div>
    </div>
  )
}
```

## Loading and Error States

### Loading UI

```tsx
// src/app/properties/loading.tsx
export default function PropertiesLoading() {
  return (
    <div className="space-y-4">
      <div className="h-8 bg-gray-200 rounded animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg border p-4 space-y-3">
            <div className="h-40 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Error Boundaries

```tsx
// src/app/properties/error.tsx
'use client'
import { useEffect } from 'react'

export default function PropertiesError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to error reporting service
    console.error('Properties page error:', error)
  }, [error])

  return (
    <div className="text-center py-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        Algo salió mal
      </h2>
      <p className="text-gray-600 mb-6">
        No pudimos cargar las propiedades. Por favor, inténtalo de nuevo.
      </p>
      <button
        onClick={reset}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Intentar de nuevo
      </button>
    </div>
  )
}
```

## Practice Exercises

1. **Create a properties filter page** at `/properties/search` with query parameters
2. **Build a breadcrumb component** that shows the current navigation path
3. **Implement a mobile navigation menu** with responsive design
4. **Add loading states** for slow-loading property pages
5. **Create parallel routes** for a dashboard with multiple widgets

## Next Steps

In the next guide, we'll explore:
- Building reusable React components
- Component composition patterns
- Server vs Client components
- Component libraries and design systems