# Frontend Development Guide

This guide covers the development practices, patterns, and workflows specific to the ComplianceAgent Next.js/React frontend.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Development Patterns](#development-patterns)
- [Component Development](#component-development)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Styling](#styling)
- [Testing](#testing)
- [Performance](#performance)

---

## Architecture Overview

The frontend uses Next.js 14 with the App Router:

```
┌─────────────────────────────────────────────────────────────────┐
│                         App Router                               │
│   Page components, layouts, loading/error states                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Components Layer                           │
│   Reusable UI components, feature components                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────┬─────────────────────────────────────────┐
│    State Management   │            API Layer                     │
│    React Query +      │    API client, data fetching            │
│    Zustand            │    hooks, transformations               │
└───────────────────────┴─────────────────────────────────────────┘
```

**Key Design Principles:**
- **Server Components by Default**: Use React Server Components where possible
- **Client Components for Interactivity**: Use `'use client'` only when needed
- **Type Safety**: Full TypeScript coverage with strict mode
- **Component Composition**: Small, focused components that compose well

---

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Auth route group (login, register)
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── dashboard/         # Dashboard routes (protected)
│   │   │   ├── page.tsx       # Dashboard home
│   │   │   ├── regulations/
│   │   │   ├── repositories/
│   │   │   ├── compliance/
│   │   │   └── settings/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Landing page
│   │   └── globals.css        # Global styles
│   │
│   ├── components/            # Reusable components
│   │   ├── ui/               # Base UI primitives (Radix-based)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── layout/           # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   └── footer.tsx
│   │   ├── regulations/      # Feature: Regulations
│   │   ├── compliance/       # Feature: Compliance
│   │   └── charts/           # Data visualization
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useRegulations.ts
│   │   └── useCompliance.ts
│   │
│   ├── lib/                  # Utilities and API client
│   │   ├── api.ts           # API client instance
│   │   ├── auth.ts          # Auth utilities
│   │   └── utils.ts         # Helper functions
│   │
│   ├── stores/              # Zustand state stores
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   │
│   └── types/               # TypeScript type definitions
│       ├── api.ts           # API response types
│       ├── models.ts        # Domain models
│       └── index.ts         # Re-exports
│
├── public/                  # Static assets
├── tests/                   # Test files
├── tailwind.config.ts       # Tailwind configuration
├── next.config.js           # Next.js configuration
└── package.json             # Dependencies
```

---

## Setting Up Development Environment

### Prerequisites

```bash
# Install Node.js 20+
brew install node@20  # macOS
# or use nvm for version management

# Install pnpm (optional, recommended)
npm install -g pnpm
```

### Installation

```bash
cd frontend

# Install dependencies
npm install
# or with pnpm
pnpm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Environment Variables

Create `.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# App Configuration
NEXT_PUBLIC_APP_NAME=ComplianceAgent
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Development Patterns

### Server Components (Default)

Use server components for data fetching and static content:

```tsx
// app/dashboard/regulations/page.tsx
import { RegulationList } from '@/components/regulations/regulation-list';
import { getRegulations } from '@/lib/api';

export default async function RegulationsPage() {
  // Data fetched on server
  const regulations = await getRegulations();
  
  return (
    <div>
      <h1>Regulations</h1>
      <RegulationList regulations={regulations} />
    </div>
  );
}
```

### Client Components (When Needed)

Use `'use client'` for interactivity:

```tsx
// components/regulations/regulation-filter.tsx
'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface RegulationFilterProps {
  onFilterChange: (filters: FilterState) => void;
}

export function RegulationFilter({ onFilterChange }: RegulationFilterProps) {
  const [framework, setFramework] = useState<string>('');
  
  const handleChange = (value: string) => {
    setFramework(value);
    onFilterChange({ framework: value });
  };
  
  return (
    <div className="flex gap-4">
      <Select value={framework} onValueChange={handleChange}>
        {/* ... */}
      </Select>
    </div>
  );
}
```

### TypeScript Strict Mode

Always define explicit types:

```tsx
// ✅ Correct: Explicit types
interface RegulationCardProps {
  regulation: Regulation;
  onSelect: (id: string) => void;
  isLoading?: boolean;
}

export function RegulationCard({
  regulation,
  onSelect,
  isLoading = false,
}: RegulationCardProps): JSX.Element {
  // ...
}

// ❌ Wrong: Implicit any
export function RegulationCard({ regulation, onSelect, isLoading }) {
  // ...
}
```

---

## Component Development

### Component Structure

```tsx
// components/regulations/regulation-card.tsx
'use client';

import { memo } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Regulation } from '@/types';

interface RegulationCardProps {
  /** The regulation to display */
  regulation: Regulation;
  /** Callback when card is clicked */
  onSelect?: (id: string) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Displays a regulation summary in a card format.
 */
export const RegulationCard = memo(function RegulationCard({
  regulation,
  onSelect,
  className,
}: RegulationCardProps) {
  return (
    <Card
      className={cn('cursor-pointer hover:shadow-md transition-shadow', className)}
      onClick={() => onSelect?.(regulation.id)}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{regulation.name}</h3>
          <Badge variant={getStatusVariant(regulation.status)}>
            {regulation.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {regulation.framework} • {regulation.jurisdiction}
        </p>
        <p className="text-sm mt-2">
          {regulation.requirementsCount} requirements
        </p>
      </CardContent>
    </Card>
  );
});
```

### UI Components (Radix-based)

We use Radix UI primitives with Tailwind:

```tsx
// components/ui/button.tsx
import { forwardRef } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
```

---

## State Management

### React Query (Server State)

```tsx
// hooks/useRegulations.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Regulation, RegulationCreate } from '@/types';

export function useRegulations(filters?: RegulationFilters) {
  return useQuery({
    queryKey: ['regulations', filters],
    queryFn: () => api.regulations.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useRegulation(id: string) {
  return useQuery({
    queryKey: ['regulations', id],
    queryFn: () => api.regulations.get(id),
    enabled: !!id,
  });
}

export function useCreateRegulation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: RegulationCreate) => api.regulations.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['regulations'] });
    },
  });
}
```

### Zustand (Client State)

```tsx
// stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'system',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
```

---

## API Integration

### API Client

```tsx
// lib/api.ts
import { getAuthToken } from './auth';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = getAuthToken();
    
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(response.status, error.detail);
    }
    
    return response.json();
  }
  
  regulations = {
    list: (filters?: RegulationFilters) =>
      this.fetch<PaginatedResponse<Regulation>>('/regulations', {
        method: 'GET',
        // ... query params
      }),
    
    get: (id: string) =>
      this.fetch<Regulation>(`/regulations/${id}`),
    
    create: (data: RegulationCreate) =>
      this.fetch<Regulation>('/regulations', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  };
  
  compliance = {
    getStatus: () =>
      this.fetch<ComplianceStatus>('/compliance/status'),
    
    generateCode: (mappingId: string) =>
      this.fetch<GeneratedCode>('/compliance/generate', {
        method: 'POST',
        body: JSON.stringify({ mapping_id: mappingId }),
      }),
  };
}

export const api = new ApiClient();
```

---

## Styling

### Tailwind CSS

```tsx
// Use Tailwind utility classes
<div className="flex items-center gap-4 p-4 bg-card rounded-lg shadow-sm">
  <Avatar className="h-10 w-10" />
  <div className="flex-1">
    <h3 className="font-medium">{name}</h3>
    <p className="text-sm text-muted-foreground">{email}</p>
  </div>
</div>
```

### cn() Utility

```tsx
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<div className={cn(
  'p-4 rounded-lg',
  isActive && 'bg-primary text-primary-foreground',
  className
)} />
```

### Theme Variables

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    /* ... */
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... */
  }
}
```

---

## Testing

### Jest + React Testing Library

```tsx
// tests/components/regulation-card.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { RegulationCard } from '@/components/regulations/regulation-card';

const mockRegulation = {
  id: '1',
  name: 'GDPR',
  framework: 'gdpr',
  jurisdiction: 'EU',
  status: 'active',
  requirementsCount: 147,
};

describe('RegulationCard', () => {
  it('renders regulation information', () => {
    render(<RegulationCard regulation={mockRegulation} />);
    
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText('gdpr • EU')).toBeInTheDocument();
    expect(screen.getByText('147 requirements')).toBeInTheDocument();
  });
  
  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<RegulationCard regulation={mockRegulation} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByRole('article'));
    
    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```

### Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm test -- --coverage
```

---

## Performance

### Image Optimization

```tsx
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="ComplianceAgent"
  width={120}
  height={40}
  priority // For above-the-fold images
/>
```

### Code Splitting

```tsx
// Lazy load heavy components
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('@/components/charts/compliance-chart'), {
  loading: () => <Skeleton className="h-64" />,
  ssr: false, // If the component doesn't support SSR
});
```

### Memoization

```tsx
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive computations
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);

// Memoize callbacks
const handleSelect = useCallback((id: string) => {
  setSelected(id);
}, []);

// Memoize components
export const RegulationCard = memo(function RegulationCard(props) {
  // ...
});
```

---

## Commands Reference

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run start        # Start production server

# Testing
npm test             # Run tests
npm run test:watch   # Watch mode
npm run test:coverage # Coverage report

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix lint issues
npm run type-check   # TypeScript check
```

---

## Next Steps

- [API Reference](../api/reference.md) - Backend API documentation
- [Component Library](../components/README.md) - UI component documentation
- [Testing Guide](testing.md) - Comprehensive testing strategies
