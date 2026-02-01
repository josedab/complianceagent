import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeToggle, ThemeProvider } from '@/components/ThemeToggle';

// Mock matchMedia
const mockMatchMedia = (matches: boolean) => ({
  matches,
  media: '',
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});

describe('ThemeToggle', () => {
  beforeEach(() => {
    // Reset localStorage
    localStorage.clear();
    // Reset DOM
    document.documentElement.classList.remove('dark');
    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => mockMatchMedia(false)),
    });
  });

  it('renders the theme toggle button', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('starts with light mode by default when system prefers light', () => {
    render(<ThemeToggle />);
    
    // After mount, should show the theme button
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('System theme'));
  });

  it('cycles through themes when clicked', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Initial state is system
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('System'));
    
    // Click to switch to light
    fireEvent.click(button);
    expect(localStorage.getItem('theme')).toBe('light');
    
    // Click to switch to dark
    fireEvent.click(button);
    expect(localStorage.getItem('theme')).toBe('dark');
    
    // Click to switch back to system
    fireEvent.click(button);
    expect(localStorage.getItem('theme')).toBe('system');
  });

  it('loads saved theme from localStorage', () => {
    localStorage.setItem('theme', 'dark');
    
    render(<ThemeToggle />);
    
    // Should display dark mode
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Dark'));
  });

  it('applies dark class to document when dark theme is selected', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Click to light, then dark
    fireEvent.click(button); // light
    fireEvent.click(button); // dark
    
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('removes dark class when light theme is selected', () => {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
    
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // Click to cycle to system, then light
    fireEvent.click(button); // system
    fireEvent.click(button); // light
    
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('has accessible title attribute', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title');
  });
});

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        ...mockMatchMedia(false),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      })),
    });
  });

  it('renders children', () => {
    render(
      <ThemeProvider>
        <div data-testid="child">Child content</div>
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('applies dark theme from localStorage on mount', () => {
    localStorage.setItem('theme', 'dark');
    
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    );
    
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('applies light theme from localStorage on mount', () => {
    localStorage.setItem('theme', 'light');
    document.documentElement.classList.add('dark');
    
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    );
    
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('uses system preference when no theme is stored', () => {
    // Mock system preference as dark
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        ...mockMatchMedia(true),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      })),
    });
    
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    );
    
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('adds event listener for system preference changes', () => {
    const addEventListenerMock = jest.fn();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        ...mockMatchMedia(false),
        addEventListener: addEventListenerMock,
        removeEventListener: jest.fn(),
      })),
    });
    
    render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    );
    
    expect(addEventListenerMock).toHaveBeenCalledWith('change', expect.any(Function));
  });

  it('cleans up event listener on unmount', () => {
    const removeEventListenerMock = jest.fn();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        ...mockMatchMedia(false),
        addEventListener: jest.fn(),
        removeEventListener: removeEventListenerMock,
      })),
    });
    
    const { unmount } = render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    );
    
    unmount();
    
    expect(removeEventListenerMock).toHaveBeenCalledWith('change', expect.any(Function));
  });
});
