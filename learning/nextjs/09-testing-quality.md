# Next.js Testing & Quality

## Overview

This guide covers testing strategies, code quality tools, and best practices for our Next.js application in the busca-pisos project. We'll explore unit testing, integration testing, E2E testing, and quality assurance tools.

## Testing Strategy

### Testing Pyramid
1. **Unit Tests** (70%) - Individual components and functions
2. **Integration Tests** (20%) - Component interactions and API integration
3. **E2E Tests** (10%) - Complete user workflows

### Tools We'll Use
- **Jest** - Unit and integration testing framework
- **React Testing Library** - Component testing utilities
- **Playwright** - End-to-end testing
- **MSW** - API mocking
- **ESLint** - Code linting
- **TypeScript** - Type checking

## Testing Setup

### Jest Configuration

```javascript
// jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    // Handle module aliases
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/pages/api/**',
    '!src/pages/_app.tsx',
    '!src/pages/_document.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
```

### Test Setup File

```javascript
// jest.setup.js
import '@testing-library/jest-dom'
import { server } from './src/mocks/server'

// Establish API mocking before all tests
beforeAll(() => server.listen())

// Reset any request handlers that we may add during the tests
afterEach(() => server.resetHandlers())

// Clean up after the tests are finished
afterAll(() => server.close())

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
}))

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8001'
```

## Unit Testing Components

### Basic Component Test

```tsx
// src/components/properties/PropertyCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { PropertyCard } from './PropertyCard'
import { Property } from '@/types/property'

const mockProperty: Property = {
  p_id: 1,
  nombre: 'Beautiful Apartment in Madrid',
  precio: 250000,
  metros: '85 m²',
  poblacion: 'Madrid',
  url: 'https://example.com/property/1',
  estatus: 'activo',
  fecha_updated: '2024-01-15T10:00:00Z',
  fecha_crawl: '2024-01-15T10:00:00Z',
}

describe('PropertyCard', () => {
  it('renders property information correctly', () => {
    render(<PropertyCard property={mockProperty} />)
    
    expect(screen.getByText('Beautiful Apartment in Madrid')).toBeInTheDocument()
    expect(screen.getByText('€250,000')).toBeInTheDocument()
    expect(screen.getByText('Madrid')).toBeInTheDocument()
    expect(screen.getByText('85 m²')).toBeInTheDocument()
  })

  it('handles favorite toggle', () => {
    const onFavoriteToggle = jest.fn()
    render(
      <PropertyCard 
        property={mockProperty} 
        onFavoriteToggle={onFavoriteToggle} 
      />
    )
    
    const favoriteButton = screen.getByRole('button', { name: /favorite/i })
    fireEvent.click(favoriteButton)
    
    expect(onFavoriteToggle).toHaveBeenCalledWith(mockProperty.p_id)
  })

  it('displays price correctly for expensive properties', () => {
    const expensiveProperty = { ...mockProperty, precio: 1500000 }
    render(<PropertyCard property={expensiveProperty} />)
    
    expect(screen.getByText('€1,500,000')).toBeInTheDocument()
  })

  it('handles missing price gracefully', () => {
    const propertyWithoutPrice = { ...mockProperty, precio: null }
    render(<PropertyCard property={propertyWithoutPrice} />)
    
    expect(screen.getByText('Price not available')).toBeInTheDocument()
  })
})
```

### Form Component Testing

```tsx
// src/components/forms/PropertySearchForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PropertySearchForm } from './PropertySearchForm'

describe('PropertySearchForm', () => {
  const mockOnSearch = jest.fn()

  beforeEach(() => {
    mockOnSearch.mockClear()
  })

  it('renders all form fields', () => {
    render(<PropertySearchForm onSearch={mockOnSearch} />)
    
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min price/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/max price/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/property type/i)).toBeInTheDocument()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<PropertySearchForm onSearch={mockOnSearch} />)
    
    await user.type(screen.getByLabelText(/location/i), 'Madrid')
    await user.type(screen.getByLabelText(/min price/i), '100000')
    await user.type(screen.getByLabelText(/max price/i), '500000')
    await user.selectOptions(screen.getByLabelText(/property type/i), 'apartment')
    
    await user.click(screen.getByRole('button', { name: /search/i }))
    
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith({
        location: 'Madrid',
        minPrice: 100000,
        maxPrice: 500000,
        propertyType: 'apartment',
      })
    })
  })

  it('shows validation errors for invalid input', async () => {
    const user = userEvent.setup()
    render(<PropertySearchForm onSearch={mockOnSearch} />)
    
    // Enter invalid price range (min > max)
    await user.type(screen.getByLabelText(/min price/i), '500000')
    await user.type(screen.getByLabelText(/max price/i), '100000')
    
    await user.click(screen.getByRole('button', { name: /search/i }))
    
    await waitFor(() => {
      expect(screen.getByText(/max price must be greater than min price/i)).toBeInTheDocument()
    })
    
    expect(mockOnSearch).not.toHaveBeenCalled()
  })

  it('clears form when reset button is clicked', async () => {
    const user = userEvent.setup()
    render(<PropertySearchForm onSearch={mockOnSearch} />)
    
    // Fill in some data
    await user.type(screen.getByLabelText(/location/i), 'Barcelona')
    await user.type(screen.getByLabelText(/min price/i), '200000')
    
    // Click reset
    await user.click(screen.getByRole('button', { name: /clear/i }))
    
    // Verify fields are cleared
    expect(screen.getByLabelText(/location/i)).toHaveValue('')
    expect(screen.getByLabelText(/min price/i)).toHaveValue('')
  })
})
```

## Testing with React Query

### Mock API Responses

```tsx
// src/mocks/handlers.ts
import { rest } from 'msw'
import { Property } from '@/types/property'

const mockProperties: Property[] = [
  {
    p_id: 1,
    nombre: 'Apartment in Madrid',
    precio: 250000,
    metros: '85 m²',
    poblacion: 'Madrid',
    url: 'https://example.com/property/1',
    estatus: 'activo',
    fecha_updated: '2024-01-15T10:00:00Z',
    fecha_crawl: '2024-01-15T10:00:00Z',
  },
  {
    p_id: 2,
    nombre: 'House in Barcelona',
    precio: 450000,
    metros: '120 m²',
    poblacion: 'Barcelona',
    url: 'https://example.com/property/2',
    estatus: 'activo',
    fecha_updated: '2024-01-15T11:00:00Z',
    fecha_crawl: '2024-01-15T11:00:00Z',
  },
]

export const handlers = [
  // Get properties
  rest.get('http://localhost:8001/api/properties/', (req, res, ctx) => {
    const skip = parseInt(req.url.searchParams.get('skip') || '0')
    const limit = parseInt(req.url.searchParams.get('limit') || '10')
    const location = req.url.searchParams.get('poblacion')
    
    let filteredProperties = [...mockProperties]
    
    if (location) {
      filteredProperties = filteredProperties.filter(p => 
        p.poblacion.toLowerCase().includes(location.toLowerCase())
      )
    }
    
    const paginatedProperties = filteredProperties.slice(skip, skip + limit)
    
    return res(ctx.json(paginatedProperties))
  }),

  // Get single property
  rest.get('http://localhost:8001/api/properties/:id', (req, res, ctx) => {
    const { id } = req.params
    const property = mockProperties.find(p => p.p_id === parseInt(id as string))
    
    if (!property) {
      return res(ctx.status(404), ctx.json({ detail: 'Property not found' }))
    }
    
    return res(ctx.json(property))
  }),

  // Create property
  rest.post('http://localhost:8001/api/properties/', (req, res, ctx) => {
    const newProperty = {
      p_id: mockProperties.length + 1,
      fecha_updated: new Date().toISOString(),
      fecha_crawl: new Date().toISOString(),
      estatus: 'activo',
      ...req.body,
    }
    
    mockProperties.push(newProperty)
    
    return res(ctx.status(201), ctx.json(newProperty))
  }),

  // Error scenario
  rest.get('http://localhost:8001/api/properties/error', (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ detail: 'Internal server error' }))
  }),
]
```

```tsx
// src/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

### Testing React Query Components

```tsx
// src/components/properties/PropertiesList.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PropertiesList } from './PropertiesList'
import { server } from '@/mocks/server'
import { rest } from 'msw'

// Test wrapper with React Query
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })
}

function renderWithQueryClient(ui: React.ReactElement) {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('PropertiesList', () => {
  it('displays loading state initially', () => {
    renderWithQueryClient(<PropertiesList />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('displays properties after loading', async () => {
    renderWithQueryClient(<PropertiesList />)
    
    await waitFor(() => {
      expect(screen.getByText('Apartment in Madrid')).toBeInTheDocument()
      expect(screen.getByText('House in Barcelona')).toBeInTheDocument()
    })
  })

  it('displays error message on API failure', async () => {
    // Override the handler to return an error
    server.use(
      rest.get('http://localhost:8001/api/properties/', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Server error' }))
      })
    )

    renderWithQueryClient(<PropertiesList />)
    
    await waitFor(() => {
      expect(screen.getByText(/error loading properties/i)).toBeInTheDocument()
      expect(screen.getByText(/server error/i)).toBeInTheDocument()
    })
  })

  it('displays empty state when no properties found', async () => {
    server.use(
      rest.get('http://localhost:8001/api/properties/', (req, res, ctx) => {
        return res(ctx.json([]))
      })
    )

    renderWithQueryClient(<PropertiesList />)
    
    await waitFor(() => {
      expect(screen.getByText(/no properties found/i)).toBeInTheDocument()
    })
  })

  it('refetches data when retry button is clicked', async () => {
    // First, make the API fail
    server.use(
      rest.get('http://localhost:8001/api/properties/', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Server error' }))
      })
    )

    renderWithQueryClient(<PropertiesList />)
    
    await waitFor(() => {
      expect(screen.getByText(/error loading properties/i)).toBeInTheDocument()
    })

    // Reset to successful response
    server.resetHandlers()

    // Click retry button
    const retryButton = screen.getByRole('button', { name: /try again/i })
    fireEvent.click(retryButton)

    // Should show properties now
    await waitFor(() => {
      expect(screen.getByText('Apartment in Madrid')).toBeInTheDocument()
    })
  })
})
```

## Testing Custom Hooks

```tsx
// src/hooks/useProperties.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProperties } from './useProperties'
import { server } from '@/mocks/server'
import { rest } from 'msw'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useProperties', () => {
  it('fetches properties successfully', async () => {
    const { result } = renderHook(() => useProperties(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toHaveLength(2)
    expect(result.current.data[0].nombre).toBe('Apartment in Madrid')
  })

  it('handles API errors gracefully', async () => {
    server.use(
      rest.get('http://localhost:8001/api/properties/', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Server error' }))
      })
    )

    const { result } = renderHook(() => useProperties(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeTruthy()
  })

  it('filters properties by location', async () => {
    const { result } = renderHook(
      () => useProperties({ poblacion: 'Madrid' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toHaveLength(1)
    expect(result.current.data[0].poblacion).toBe('Madrid')
  })
})
```

## Integration Testing

### Testing Page Components

```tsx
// src/app/properties/page.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import PropertiesPage from './page'

// Mock the child components
jest.mock('@/components/properties/PropertiesList', () => {
  return function MockPropertiesList() {
    return <div>Properties List Component</div>
  }
})

jest.mock('@/components/properties/PropertyFilters', () => {
  return function MockPropertyFilters() {
    return <div>Property Filters Component</div>
  }
})

describe('Properties Page', () => {
  function renderPage() {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } }
    })
    
    return render(
      <QueryClientProvider client={queryClient}>
        <PropertiesPage />
      </QueryClientProvider>
    )
  }

  it('renders page title and components', () => {
    renderPage()
    
    expect(screen.getByText(/properties/i)).toBeInTheDocument()
    expect(screen.getByText('Properties List Component')).toBeInTheDocument()
    expect(screen.getByText('Property Filters Component')).toBeInTheDocument()
  })

  it('has proper page metadata', () => {
    renderPage()
    
    // Test would need to be adjusted based on how metadata is tested in Next.js 13+
    expect(document.title).toContain('Properties')
  })
})
```

## End-to-End Testing with Playwright

### Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2E Test Examples

```typescript
// e2e/properties.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Properties Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/properties')
  })

  test('displays properties list', async ({ page }) => {
    // Wait for properties to load
    await expect(page.getByText('Loading properties')).toBeHidden()
    
    // Check that properties are displayed
    await expect(page.getByTestId('property-card')).toHaveCount.greaterThan(0)
  })

  test('filters properties by location', async ({ page }) => {
    // Enter location filter
    await page.getByLabel('Location').fill('Madrid')
    await page.getByRole('button', { name: 'Search' }).click()
    
    // Wait for results
    await page.waitForResponse('**/api/properties/**')
    
    // Verify filtered results
    const propertyCards = page.getByTestId('property-card')
    await expect(propertyCards.first()).toContainText('Madrid')
  })

  test('navigates to property detail', async ({ page }) => {
    // Click on first property
    await page.getByTestId('property-card').first().click()
    
    // Verify navigation to detail page
    await expect(page).toHaveURL(/\/properties\/\d+/)
    await expect(page.getByTestId('property-detail')).toBeVisible()
  })

  test('handles empty search results', async ({ page }) => {
    // Search for non-existent location
    await page.getByLabel('Location').fill('NonExistentCity')
    await page.getByRole('button', { name: 'Search' }).click()
    
    // Verify empty state
    await expect(page.getByText('No properties found')).toBeVisible()
  })
})
```

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('user can log in', async ({ page }) => {
    await page.goto('/auth/login')
    
    // Fill login form
    await page.getByLabel('Username').fill('testuser')
    await page.getByLabel('Password').fill('testpassword')
    await page.getByRole('button', { name: 'Sign in' }).click()
    
    // Verify successful login
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome back')).toBeVisible()
  })

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/auth/login')
    
    await page.getByLabel('Username').fill('invalid')
    await page.getByLabel('Password').fill('wrong')
    await page.getByRole('button', { name: 'Sign in' }).click()
    
    await expect(page.getByText('Invalid username or password')).toBeVisible()
  })

  test('user can register', async ({ page }) => {
    await page.goto('/auth/register')
    
    await page.getByLabel('Username').fill('newuser')
    await page.getByLabel('Email').fill('newuser@example.com')
    await page.getByLabel('Password', { exact: true }).fill('NewPassword123!')
    await page.getByLabel('Confirm Password').fill('NewPassword123!')
    await page.getByRole('button', { name: 'Create account' }).click()
    
    await expect(page).toHaveURL('/auth/login')
    await expect(page.getByText('Account created successfully')).toBeVisible()
  })

  test('protected routes redirect to login', async ({ page }) => {
    await page.goto('/dashboard')
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login/)
  })
})
```

## Code Quality Tools

### ESLint Configuration

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
    'plugin:testing-library/react',
    'plugin:jest-dom/recommended',
  ],
  plugins: ['testing-library', 'jest-dom'],
  rules: {
    // Custom rules
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    
    // Testing rules
    'testing-library/await-async-query': 'error',
    'testing-library/no-await-sync-query': 'error',
    'testing-library/no-debugging-utils': 'warn',
    'jest-dom/prefer-checked': 'error',
    'jest-dom/prefer-enabled-disabled': 'error',
  },
  overrides: [
    {
      files: ['**/__tests__/**/*', '**/*.{test,spec}.*'],
      env: {
        jest: true,
      },
    },
  ],
}
```

### Package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm run type-check && npm run lint && npm run test && npm run test:e2e"
  }
}
```

## Performance Testing

### Testing Core Web Vitals

```typescript
// e2e/performance.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Performance', () => {
  test('meets Core Web Vitals thresholds', async ({ page }) => {
    await page.goto('/')
    
    // Measure performance metrics
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const metrics = {}
          
          entries.forEach((entry) => {
            if (entry.entryType === 'largest-contentful-paint') {
              metrics.lcp = entry.startTime
            }
            if (entry.entryType === 'first-input') {
              metrics.fid = entry.processingStart - entry.startTime
            }
            if (entry.entryType === 'layout-shift') {
              metrics.cls = entry.value
            }
          })
          
          resolve(metrics)
        }).observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] })
      })
    })
    
    // Assert Core Web Vitals thresholds
    expect(metrics.lcp).toBeLessThan(2500) // LCP should be < 2.5s
    expect(metrics.fid).toBeLessThan(100)  // FID should be < 100ms
    expect(metrics.cls).toBeLessThan(0.1)  // CLS should be < 0.1
  })
})
```

## Testing Best Practices

### 1. Test Structure
```tsx
// Follow the Arrange-Act-Assert pattern
describe('Component', () => {
  it('should do something', () => {
    // Arrange
    const props = { /* test data */ }
    
    // Act
    render(<Component {...props} />)
    
    // Assert
    expect(screen.getByText('Expected text')).toBeInTheDocument()
  })
})
```

### 2. Accessible Queries
```tsx
// Prefer accessible queries
screen.getByRole('button', { name: /submit/i })  // ✅ Good
screen.getByTestId('submit-button')              // ⚠️ OK as fallback
screen.getByClassName('submit-btn')              // ❌ Avoid
```

### 3. Async Testing
```tsx
// Always await async operations
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Or use findBy queries (which wait automatically)
expect(await screen.findByText('Loaded')).toBeInTheDocument()
```

### 4. Mock External Dependencies
```tsx
// Mock API calls, external libraries, etc.
jest.mock('@/lib/api', () => ({
  api: {
    getProperties: jest.fn(),
  },
}))
```

## Practice Exercises

1. **Write integration tests** for the complete property search flow
2. **Add visual regression testing** with Playwright
3. **Implement accessibility testing** with axe-core
4. **Create performance budgets** and monitoring
5. **Add snapshot testing** for critical components

## Next Steps

With comprehensive testing in place, you can:
- Set up CI/CD pipelines with automated testing
- Implement code coverage requirements
- Add visual regression testing
- Monitor real-world performance metrics
- Ensure accessibility compliance

This completes our Next.js learning guide series covering all essential aspects of modern React development with Next.js!