import { render, screen } from '@testing-library/react';
import {
  ComplianceTrendChart,
  RiskDistributionChart,
  FrameworkComparisonChart,
} from '@/components/dashboard/Charts';

jest.mock('recharts', () => {
  const actual = jest.requireActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-chart">{children}</div>
    ),
  };
});

describe('ComplianceTrendChart', () => {
  it('renders without crashing', () => {
    render(<ComplianceTrendChart data={[]} />);
    expect(screen.getByTestId('responsive-chart')).toBeInTheDocument();
  });
});

describe('RiskDistributionChart', () => {
  it('renders without crashing', () => {
    render(<RiskDistributionChart data={[]} />);
    expect(screen.getByTestId('responsive-chart')).toBeInTheDocument();
  });
});

describe('FrameworkComparisonChart', () => {
  it('renders without crashing', () => {
    render(<FrameworkComparisonChart data={[]} />);
    expect(screen.getByTestId('responsive-chart')).toBeInTheDocument();
  });
});
