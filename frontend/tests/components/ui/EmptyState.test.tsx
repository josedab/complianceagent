import { render, screen } from '@testing-library/react';
import { EmptyState, NoSearchResults, ErrorState, LoadingState } from '@/components/ui/EmptyState';

describe('EmptyState', () => {
  it('renders without crashing', () => {
    render(<EmptyState title="No data" description="Nothing to display" />);
    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('Nothing to display')).toBeInTheDocument();
  });

  it('renders action buttons when provided', () => {
    // TODO: Pass primary/secondary actions and verify buttons render with correct labels and onClick handlers
    render(
      <EmptyState
        title="Empty"
        description="No items"
        actions={[{ label: 'Add Item', onClick: jest.fn() }]}
      />
    );
  });
});

describe('NoSearchResults', () => {
  it('renders without crashing', () => {
    // TODO: Verify the NoSearchResults variant renders its default title and description
    render(<NoSearchResults />);
  });
});

describe('ErrorState', () => {
  it('renders without crashing', () => {
    // TODO: Verify the ErrorState variant renders error-specific messaging
    render(<ErrorState />);
  });
});

describe('LoadingState', () => {
  it('renders loading spinner', () => {
    // TODO: Verify the LoadingState variant renders an animated spinner and loading message
    render(<LoadingState />);
  });
});
