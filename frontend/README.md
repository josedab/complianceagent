# ComplianceAgent Frontend

Next.js 16 App Router dashboard for real-time compliance monitoring, regulation tracking, and team collaboration.

## Quick Start

```bash
# Install dependencies
npm ci

# Start development server (http://localhost:3000)
npm run dev
```

> **Prerequisites**: Node.js 20.19+ (or 22.13+), npm 10+. The backend API must be running on `http://localhost:8000` (see root README).

## Environment Variables

Create a `.env.local` file (or set in your shell):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | `same-origin` or backend API **root origin** (no `/api/v1` suffix) | `http://localhost:8000` in development |
| `NEXT_PUBLIC_WS_URL` | WebSocket origin (optional; derived from the API URL) | — |

> **Production validation:** use `same-origin` behind the reverse proxy, or set
> an explicit HTTPS API origin. Missing, invalid, HTTP, or localhost values fail
> the production build (`next build`) fast — see `src/lib/config.ts`. The value is a
> single source of truth used by both API clients and the CSP `connect-src`.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Production build |
| `npm run start` | Serve production build |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking |
| `npm test` | Run Jest tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run e2e` | Run Playwright end-to-end tests |
| `npm run e2e:ui` | Run Playwright with the interactive UI |
| `npm run format` | Format code with Prettier |
| `npm run format:check` | Check formatting without changes |

Jest covers maintained application, hook, and component modules. Playwright specs
under `tests/e2e/` run only through the E2E scripts. Static prototype dashboards
under `src/app/dashboard/` and `src/components/nextgen/` are excluded from the
unit coverage denominator until they are promoted to maintained product surfaces.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Authentication pages (login, register)
│   ├── dashboard/          # Main dashboard and feature pages
│   │   ├── actions/        # Compliance actions
│   │   ├── audit/          # Audit trail viewer
│   │   ├── regulations/    # Regulation browser
│   │   ├── repositories/   # Repository management
│   │   ├── settings/       # Organization settings
│   │   └── telemetry/      # Real-time telemetry
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Landing page
│   └── providers.tsx       # React Query, Theme, Toast providers
├── components/
│   ├── compliance/         # Compliance-specific components
│   ├── dashboard/          # Dashboard charts and widgets
│   ├── telemetry/          # Telemetry visualizations
│   └── ui/                 # Shared UI primitives (Radix-based)
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities, API client, helpers
└── types/                  # TypeScript type definitions
```

## Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/) with App Router
- **Language**: TypeScript 5.3+
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with `clsx` + `tailwind-merge`
- **Components**: [Radix UI](https://www.radix-ui.com/) primitives
- **Data Fetching**: [TanStack React Query](https://tanstack.com/query) v5
- **Charts**: [Recharts](https://recharts.org/)
- **Code Editor**: [Monaco Editor](https://microsoft.github.io/monaco-editor/) (for in-browser code viewing)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Testing**: Jest + React Testing Library; Playwright for E2E

## Development Tips

- **API requests** go through the client in `src/lib/`. All endpoints use React Query for caching and refetching.
- **Shared UI components** in `src/components/ui/` wrap Radix primitives with Tailwind styling.
- **Page routes** follow Next.js App Router conventions — each folder under `app/` is a route segment.
- **Authentication** uses HttpOnly access and refresh cookies with automatic refresh-token rotation. Protected routes are in the `dashboard/` group.
