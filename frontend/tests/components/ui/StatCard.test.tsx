import { render, screen } from '@testing-library/react';
import { StatCard } from '@/components/ui/StatCard';

describe('StatCard', () => {
  const defaultProps = {
    icon: <span data-testid="stat-icon">📊</span>,
    title: 'Total Issues',
    value: '42',
    subtitle: 'Last 30 days',
  };

  it('renders without crashing', () => {
    render(<StatCard {...defaultProps} />);
    expect(screen.getByText('Total Issues')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders the icon and subtitle', () => {
    // TODO: Verify the icon element and subtitle text render correctly
    render(<StatCard {...defaultProps} />);
    expect(screen.getByTestId('stat-icon')).toBeInTheDocument();
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });
});
