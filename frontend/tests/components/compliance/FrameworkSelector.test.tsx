import { render, screen, fireEvent } from '@testing-library/react';
import { FrameworkSelector } from '@/components/compliance/FrameworkSelector';

describe('FrameworkSelector', () => {
  const defaultProps = {
    selectedFrameworks: [] as string[],
    onSelectionChange: jest.fn(),
  };

  it('renders without crashing', () => {
    render(<FrameworkSelector {...defaultProps} />);
    expect(screen.getByText('Regulatory Frameworks')).toBeInTheDocument();
  });

  it('renders Select All and Clear buttons', () => {
    // TODO: Verify "Select All" and "Clear" buttons are present and functional
    render(<FrameworkSelector {...defaultProps} />);
    expect(screen.getByText('Select All')).toBeInTheDocument();
  });

  it('calls onSelectionChange when a framework is toggled', () => {
    // TODO: Click a framework checkbox and verify onSelectionChange is called with updated selection
    const onSelectionChange = jest.fn();
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={onSelectionChange}
      />
    );
  });
});
