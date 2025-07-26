# Next.js Learning Guide

A comprehensive guide to learning Next.js using the **busca-pisos** project as a practical example.

## Overview

This learning guide covers all essential Next.js concepts with real-world examples from our Spanish real estate data platform frontend. Each guide builds upon previous concepts and includes practical exercises.

## Prerequisites

- **React** experience (components, hooks, state)
- **TypeScript** knowledge (helpful but not required)
- **HTML/CSS** fundamentals
- **JavaScript ES6+** features
- **Node.js** and **npm** basics

## Learning Path

### Core Concepts (Essential)

1. **[Next.js Basics](01-nextjs-basics.md)** ⭐
   - What is Next.js and why use it
   - App Router vs Pages Router
   - Project structure and configuration
   - Development server setup
   - File-based routing fundamentals

2. **[Routing & Navigation](02-routing-navigation.md)** ⭐
   - App Router architecture
   - Dynamic routes and parameters
   - Navigation components
   - Layouts and nested routing
   - Route groups and parallel routes

3. **[Components & Layouts](03-components-layouts.md)** ⭐
   - Component organization
   - Server vs Client components
   - Layout patterns
   - Reusable UI components
   - Component composition

4. **[State Management](04-state-management.md)** ⭐
   - React hooks (useState, useEffect)
   - Context API for global state
   - TanStack Query for server state
   - Form state management
   - Local storage integration

5. **[API Integration](05-api-integration.md)** ⭐
   - Fetching data from FastAPI backend
   - API routes in Next.js
   - TanStack Query patterns
   - Error handling and loading states
   - Real-time updates with WebSockets

### Advanced Topics

6. **[Authentication & Security](06-authentication-security.md)**
   - JWT token management
   - Protected routes and middleware
   - User session handling
   - Role-based access control
   - Secure API communication

7. **[Styling & UI](07-styling-ui.md)**
   - Tailwind CSS setup and usage
   - Component styling patterns
   - Responsive design
   - Dark mode implementation
   - UI component libraries

8. **[Performance & Optimization](08-performance-optimization.md)**
   - Server-side rendering (SSR)
   - Static site generation (SSG)
   - Image optimization
   - Code splitting and lazy loading
   - Caching strategies

9. **[Testing & Quality](09-testing-quality.md)**
   - Component testing with Jest
   - Integration testing
   - E2E testing with Playwright
   - TypeScript configuration
   - ESLint and code quality

## Project Structure

The guides use examples from this real estate platform frontend:

```
busca-pisos/frontend/
├── src/
│   ├── app/                    # App Router pages and layouts
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── dashboard/         # Dashboard pages
│   │   ├── properties/        # Property pages
│   │   └── auth/              # Authentication pages
│   ├── components/            # Reusable components
│   │   ├── ui/               # Basic UI components
│   │   ├── forms/            # Form components
│   │   └── layout/           # Layout components
│   ├── lib/                  # Utilities and configurations
│   │   ├── api.ts           # API client
│   │   ├── auth.ts          # Authentication utilities
│   │   └── utils.ts         # Helper functions
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript type definitions
│   └── styles/              # Global styles
├── public/                  # Static assets
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── next.config.js          # Next.js configuration
```

## How to Use This Guide

### Option 1: Sequential Learning
Follow the guides in order from 1-9 for comprehensive coverage.

### Option 2: Topic-Focused
Jump to specific topics based on your needs:
- **Frontend Basics**: Guides 1-3
- **State & Data**: Guides 4-5
- **Authentication**: Guide 6
- **Advanced Features**: Guides 7-9

### Option 3: Project-Based
Use the real project to practice:
1. Set up the frontend development environment
2. Read the relevant guide
3. Experiment with the existing code
4. Complete the practice exercises

## Getting Started

### 1. Set Up the Development Environment
```bash
# Navigate to frontend directory
cd busca-pisos/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Visit http://localhost:3000
```

### 2. Explore the Application
- **Main Dashboard**: http://localhost:3000
- **Property Listings**: http://localhost:3000/properties
- **User Authentication**: http://localhost:3000/auth
- **Admin Panel**: http://localhost:3000/admin

### 3. Start Learning
Begin with **[Next.js Basics](01-nextjs-basics.md)** and follow along with the running application.

## Code Examples

Each guide includes:
- ✅ **Real code** from the project
- ✅ **Working examples** you can test
- ✅ **Best practices** and patterns
- ✅ **Common pitfalls** to avoid
- ✅ **Practice exercises** for hands-on learning

## Key Features Covered

### 🎨 Modern UI/UX
- Tailwind CSS for styling
- Responsive design patterns
- Component-based architecture
- Dark mode support
- Accessible user interfaces

### 🔄 State Management
- React hooks for local state
- TanStack Query for server state
- Context API for global state
- Form state with react-hook-form
- Real-time data synchronization

### 🌐 API Integration
- RESTful API communication
- WebSocket connections
- Error handling and retries
- Loading and empty states
- Optimistic updates

### 🔐 Authentication & Security
- JWT token handling
- Protected route patterns
- User session management
- Role-based access control
- Secure API requests

### ⚡ Performance
- Server-side rendering
- Static generation
- Image optimization
- Code splitting
- Caching strategies

## Practice Projects

Build these features as you learn:

### Beginner Projects
1. **Property Card Component** - Display property information
2. **Search Filter Component** - Filter properties by criteria
3. **User Profile Page** - Display and edit user information

### Intermediate Projects
1. **Property Favorites System** - Save and manage favorite properties
2. **Real-time Notifications** - Display live updates
3. **Advanced Search Interface** - Complex filtering and sorting

### Advanced Projects
1. **Dashboard Analytics** - Charts and data visualization
2. **Multi-step Property Forms** - Complex form workflows
3. **Admin Management Interface** - User and content management

## Learning Resources

### Official Documentation
- **[Next.js Documentation](https://nextjs.org/docs)**
- **[React Documentation](https://react.dev/)**
- **[TypeScript Documentation](https://www.typescriptlang.org/docs/)**

### Video Tutorials
- Next.js 14 Tutorial Series on YouTube
- React and Next.js courses on Udemy
- Frontend Masters Next.js courses

### Books
- "Learning React" by Alex Banks and Eve Porcello
- "Full Stack React" by Anthony Accomazzo
- "TypeScript Quickly" by Yakov Fain

## Getting Help

### Common Issues
- **Hydration errors**: Check server/client component usage
- **Routing problems**: Verify file-based routing structure
- **API connection**: Check backend server and CORS settings
- **Build errors**: Review TypeScript types and imports

### Community Support
- **Stack Overflow**: Tag your questions with `next.js`
- **GitHub Discussions**: Next.js community discussions
- **Discord**: Next.js community server
- **Reddit**: r/nextjs subreddit

## Contributing

Found an error or want to improve the guides?

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Submit a pull request**

## Next Steps

After completing this guide, you'll be able to:

- ✅ **Build modern web applications** with Next.js 14
- ✅ **Implement responsive UIs** with Tailwind CSS
- ✅ **Manage application state** effectively
- ✅ **Integrate with APIs** and handle real-time data
- ✅ **Implement authentication** and protected routes
- ✅ **Optimize performance** with SSR and SSG
- ✅ **Write tests** for your components and features

### Advanced Topics to Explore
- **Micro-frontend architecture** with Next.js
- **Progressive Web Apps** (PWA) features
- **Internationalization** (i18n) with next-intl
- **Advanced animations** with Framer Motion
- **E-commerce patterns** and payment integration
- **Serverless deployment** on Vercel/Netlify

---

**Happy Learning!** 🚀

Start with **[Next.js Basics](01-nextjs-basics.md)** and build your way up to creating sophisticated web applications with Next.js.