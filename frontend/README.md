# ComplianceAgent Frontend

Next.js 14 App Router dashboard for real-time compliance monitoring, regulation tracking, and team collaboration.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev
```

> **Prerequisites**: Node.js 20+, npm 10+. The backend API must be running on `http://localhost:8000` (see root README).

## Environment Variables

Create a `.env.local` file (or set in your shell):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_APP_URL` | Frontend app URL | `http://localhost:3000` |

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
| `npm run format` | Format code with Prettier |
| `npm run format:check` | Check formatting without changes |

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
- **State Management**: [Zustand](https://zustand-demo.pmnd.rs/)
- **Charts**: [Recharts](https://recharts.org/)
- **Code Editor**: [Monaco Editor](https://microsoft.github.io/monaco-editor/) (for in-browser code viewing)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Testing**: Jest + React Testing Library

## Development Tips

- **API requests** go through the client in `src/lib/`. All endpoints use React Query for caching and refetching.
- **Shared UI components** in `src/components/ui/` wrap Radix primitives with Tailwind styling.
- **Page routes** follow Next.js App Router conventions — each folder under `app/` is a route segment.
- **Authentication** is handled via JWT tokens stored in cookies. Protected routes are in the `dashboard/` group.
