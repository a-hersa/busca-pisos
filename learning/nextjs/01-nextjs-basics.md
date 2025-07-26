# Next.js Basics - Getting Started

## What is Next.js?

Next.js is a React framework that provides additional features and optimizations for building modern web applications. It's built on top of React and adds powerful features like server-side rendering, static site generation, and automatic code splitting.

## Key Features

- **Server-Side Rendering (SSR)**: Render pages on the server for better SEO and performance
- **Static Site Generation (SSG)**: Pre-build pages at build time
- **File-based Routing**: Automatic routing based on file structure
- **API Routes**: Build backend APIs within your Next.js app
- **Image Optimization**: Automatic image optimization and lazy loading
- **TypeScript Support**: Built-in TypeScript support
- **CSS Support**: Built-in CSS and Sass support
- **Fast Refresh**: Instant feedback during development

## App Router vs Pages Router

Next.js 13+ introduced the **App Router** (our project uses this), which is the modern way to build Next.js applications:

### App Router (Current - Recommended)
```
src/app/
├── layout.tsx      # Root layout
├── page.tsx        # Home page
├── dashboard/
│   ├── layout.tsx  # Dashboard layout
│   └── page.tsx    # Dashboard page
└── properties/
    ├── page.tsx    # Properties list
    └── [id]/
        └── page.tsx # Property detail
```

### Pages Router (Legacy)
```
src/pages/
├── index.tsx       # Home page
├── dashboard.tsx   # Dashboard page
└── properties/
    ├── index.tsx   # Properties list
    └── [id].tsx    # Property detail
```

## Project Structure Overview

Let's look at our busca-pisos frontend structure:

```
frontend/
├── src/
│   ├── app/                    # App Router - Pages and layouts
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── globals.css        # Global styles
│   │   ├── dashboard/         # Dashboard section
│   │   ├── properties/        # Properties section
│   │   └── auth/              # Authentication pages
│   ├── components/            # Reusable components
│   │   ├── ui/               # Basic UI components
│   │   ├── forms/            # Form components
│   │   └── layout/           # Layout components
│   ├── lib/                  # Utilities and configurations
│   │   ├── api.ts           # API client setup
│   │   ├── auth.ts          # Authentication utilities
│   │   └── utils.ts         # Helper functions
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript definitions
│   └── styles/              # Additional styles
├── public/                  # Static assets (images, icons)
├── package.json            # Dependencies and scripts
├── next.config.js          # Next.js configuration
├── tailwind.config.js      # Tailwind CSS config
└── tsconfig.json           # TypeScript configuration
```

## Basic Next.js Application

### 1. Root Layout (`src/app/layout.tsx`)

```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

// Font optimization
const inter = Inter({ subsets: ['latin'] })

// Metadata for SEO
export const metadata: Metadata = {
  title: 'Busca Pisos - Property Search Platform',
  description: 'Educational real estate property search and analysis platform',
  keywords: ['real estate', 'properties', 'spain', 'search'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {/* Global navigation */}
          <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">
                    🏠 Busca Pisos
                  </h1>
                </div>
              </div>
            </div>
          </nav>
          
          {/* Main content */}
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
```

### 2. Home Page (`src/app/page.tsx`)

```tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <div className="px-4 py-12 text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        Bienvenido a Busca Pisos
      </h1>
      
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Plataforma educativa para búsqueda y análisis de propiedades 
        inmobiliarias en España
      </p>
      
      <div className="space-x-4">
        <Link href="/properties">
          <Button size="lg">
            Ver Propiedades
          </Button>
        </Link>
        
        <Link href="/dashboard">
          <Button variant="outline" size="lg">
            Dashboard
          </Button>
        </Link>
      </div>
      
      {/* Feature cards */}
      <div className="grid md:grid-cols-3 gap-6 mt-12 max-w-4xl mx-auto">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-2">Búsqueda Avanzada</h3>
          <p className="text-gray-600">
            Filtra propiedades por ubicación, precio, tamaño y más criterios
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-2">Análisis en Tiempo Real</h3>
          <p className="text-gray-600">
            Monitoreo y análisis de datos del mercado inmobiliario
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold mb-2">Dashboard Interactivo</h3>
          <p className="text-gray-600">
            Visualiza estadísticas y tendencias del mercado
          </p>
        </div>
      </div>
    </div>
  )
}
```

## Key Concepts Explained

### 1. Server vs Client Components

Next.js 13+ uses **React Server Components** by default:

```tsx
// Server Component (default) - runs on server
export default function ServerComponent() {
  // This runs on the server
  const data = await fetch('https://api.example.com/data')
  
  return <div>{data.title}</div>
}

// Client Component - runs in browser
'use client'
import { useState } from 'react'

export default function ClientComponent() {
  const [count, setCount] = useState(0)
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  )
}
```

### 2. File-based Routing

Routes are created by adding files to the `app` directory:

```
src/app/
├── page.tsx           → /
├── about/page.tsx     → /about
├── properties/
│   ├── page.tsx       → /properties
│   └── [id]/page.tsx  → /properties/123
└── dashboard/
    ├── layout.tsx     → Layout for /dashboard/*
    └── page.tsx       → /dashboard
```

### 3. Dynamic Routes

Use square brackets for dynamic segments:

```tsx
// src/app/properties/[id]/page.tsx
export default function PropertyPage({
  params
}: {
  params: { id: string }
}) {
  return (
    <div>
      <h1>Property ID: {params.id}</h1>
    </div>
  )
}
```

### 4. Layouts

Layouts wrap pages and persist across navigation:

```tsx
// src/app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white p-4">
        <nav>
          <ul className="space-y-2">
            <li><a href="/dashboard">Overview</a></li>
            <li><a href="/dashboard/properties">Properties</a></li>
            <li><a href="/dashboard/analytics">Analytics</a></li>
          </ul>
        </nav>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 p-6">
        {children}
      </main>
    </div>
  )
}
```

## Environment Setup

### 1. Package.json Configuration

```json
{
  "name": "busca-pisos-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.8.4",
    "react-hook-form": "^7.48.2",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/node": "^20.9.0",
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "typescript": "^5.2.2",
    "eslint": "^8.54.0",
    "eslint-config-next": "14.0.4",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31"
  }
}
```

### 2. Next.js Configuration (`next.config.js`)

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental features
  experimental: {
    // Server actions
    serverActions: true,
  },
  
  // Image domains for external images
  images: {
    domains: ['images.example.com'],
  },
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
  },
  
  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig
```

### 3. TypeScript Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## Development Server

### Running the Application

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Visit http://localhost:3000

# Other commands
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Environment Variables

Create `.env.local` for local development:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## Next Steps

In the next guides, we'll cover:
- File-based routing and navigation
- Building reusable components
- State management with React hooks
- API integration with our FastAPI backend
- Authentication and protected routes

## Practice Exercise

Try these modifications to get familiar with Next.js:

1. **Create a new page** at `/about` with information about the project
2. **Add navigation links** in the root layout to connect pages
3. **Create a simple component** that displays current date and time
4. **Experiment with layouts** by creating a different layout for auth pages

Visit `http://localhost:3000` to see your changes in action!