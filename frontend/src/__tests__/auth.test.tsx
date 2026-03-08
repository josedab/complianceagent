import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/login',
}))

// Mock the API
const mockLogin = jest.fn()
const mockLogout = jest.fn()
const mockMe = jest.fn()

jest.mock('@/lib/api', () => ({
  authApi: {
    login: (...args: unknown[]) => mockLogin(...args),
    logout: () => mockLogout(),
    me: () => mockMe(),
  },
}))

// Must import AFTER mocks are set up
import LoginPage from '@/app/(auth)/login/page'
import { AuthProvider, useAuth } from '@/contexts/auth'

// Helper to render with auth provider
function renderWithAuth(ui: React.ReactElement) {
  return render(<AuthProvider>{ui}</AuthProvider>)
}

// Test component that consumes useAuth
function AuthConsumer() {
  const { user, loading, error, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.full_name : 'null'}</span>
      <span data-testid="error">{error || 'null'}</span>
      <button data-testid="logout" onClick={logout}>Logout</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockMe.mockRejectedValue(new Error('Not authenticated'))
  })

  it('starts in loading state and resolves to no user', async () => {
    renderWithAuth(<AuthConsumer />)

    // Eventually loading should be false and user null
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })
    expect(screen.getByTestId('user')).toHaveTextContent('null')
  })

  it('loads user from /auth/me on mount', async () => {
    mockMe.mockResolvedValue({ data: { id: '1', email: 'test@example.com', full_name: 'Test User', is_active: true } })

    renderWithAuth(<AuthConsumer />)

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('Test User')
    })
    expect(screen.getByTestId('loading')).toHaveTextContent('false')
  })

  it('logout clears user and redirects', async () => {
    mockMe.mockResolvedValue({ data: { id: '1', email: 'test@example.com', full_name: 'Test User', is_active: true } })
    mockLogout.mockResolvedValue({})

    renderWithAuth(<AuthConsumer />)

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('Test User')
    })

    fireEvent.click(screen.getByTestId('logout'))

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('null')
    })
    expect(mockLogout).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockMe.mockRejectedValue(new Error('Not authenticated'))
  })

  it('renders login form', async () => {
    renderWithAuth(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByText('Sign in to your account')).toBeInTheDocument()
    })
    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('shows link to signup', async () => {
    renderWithAuth(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByText('start your 14-day free trial')).toBeInTheDocument()
    })
  })

  it('calls login on form submit', async () => {
    mockLogin.mockResolvedValue({ data: { access_token: 'tok', refresh_token: 'ref' } })
    mockMe.mockResolvedValueOnce(new Error('Not authenticated'))
      .mockResolvedValue({ data: { id: '1', email: 'user@test.com', full_name: 'User', is_active: true } })

    renderWithAuth(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'user@test.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('user@test.com', 'password123')
    })
  })

  it('displays error on failed login', async () => {
    mockLogin.mockRejectedValue({
      response: { data: { detail: 'Invalid email or password' } },
    })

    renderWithAuth(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'bad@test.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(screen.getByText(/Login failed|Invalid email/)).toBeInTheDocument()
    })
  })
})
