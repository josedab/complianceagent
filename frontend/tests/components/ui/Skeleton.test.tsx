import { render, screen } from '@testing-library/react';
import {
  Skeleton,
  CardSkeleton,
  StatCardSkeleton,
  TableSkeleton,
  DashboardSkeleton,
} from '@/components/ui/Skeleton';

describe('Skeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('animate-pulse');
  });

  it('applies custom className', () => {
    // TODO: Pass a custom className and verify it is merged with the default skeleton classes
    const { container } = render(<Skeleton className="h-8 w-32" />);
    expect(container.firstChild).toBeInTheDocument();
  });
});

describe('CardSkeleton', () => {
  it('renders without crashing', () => {
    // TODO: Verify the card skeleton renders placeholder rectangles matching the card layout
    render(<CardSkeleton />);
  });
});

describe('StatCardSkeleton', () => {
  it('renders without crashing', () => {
    // TODO: Verify the stat card skeleton renders placeholder elements for icon, title, value, and subtitle
    render(<StatCardSkeleton />);
  });
});

describe('TableSkeleton', () => {
  it('renders without crashing', () => {
    // TODO: Verify the table skeleton renders the correct number of placeholder rows (default and custom rows prop)
    render(<TableSkeleton />);
  });
});

describe('DashboardSkeleton', () => {
  it('renders without crashing', () => {
    // TODO: Verify the dashboard skeleton composes stat card and chart skeletons into a full layout
    render(<DashboardSkeleton />);
  });
});
