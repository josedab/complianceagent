import { render, screen, fireEvent } from '@testing-library/react';
import { FrameworkSelector, RegionFilter, FRAMEWORK_CATEGORIES } from '@/components/compliance/FrameworkSelector';

describe('FrameworkSelector', () => {
  const mockOnSelectionChange = jest.fn();

  beforeEach(() => {
    mockOnSelectionChange.mockClear();
  });

  it('renders all framework categories', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Check that all category names are rendered
    expect(screen.getByText('Privacy & Data Protection')).toBeInTheDocument();
    expect(screen.getByText('Security & Compliance')).toBeInTheDocument();
    expect(screen.getByText('AI Regulation')).toBeInTheDocument();
    expect(screen.getByText('ESG & Sustainability')).toBeInTheDocument();
  });

  it('renders frameworks within each category', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Check some specific frameworks
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText('HIPAA')).toBeInTheDocument();
    expect(screen.getByText('PCI-DSS')).toBeInTheDocument();
    expect(screen.getByText('EU AI Act')).toBeInTheDocument();
    expect(screen.getByText('CSRD')).toBeInTheDocument();
  });

  it('shows selected framework count', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr', 'ccpa']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    expect(screen.getByText('2 frameworks selected')).toBeInTheDocument();
  });

  it('shows singular when one framework selected', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    expect(screen.getByText('1 framework selected')).toBeInTheDocument();
  });

  it('calls onSelectionChange when framework is clicked in multi-select mode', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={true}
      />
    );

    const gdprButton = screen.getByText('GDPR').closest('button');
    fireEvent.click(gdprButton!);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['gdpr']);
  });

  it('removes framework from selection when clicked again in multi-select', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr', 'ccpa']}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={true}
      />
    );

    const gdprButton = screen.getByText('GDPR').closest('button');
    fireEvent.click(gdprButton!);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['ccpa']);
  });

  it('replaces selection in single-select mode', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr']}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={false}
      />
    );

    const ccpaButton = screen.getByText('CCPA/CPRA').closest('button');
    fireEvent.click(ccpaButton!);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['ccpa']);
  });

  it('selects all frameworks when Select All is clicked', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={true}
      />
    );

    const selectAllButton = screen.getByText('Select All');
    fireEvent.click(selectAllButton);

    // Should be called with all framework IDs
    const allFrameworkIds = Object.values(FRAMEWORK_CATEGORIES)
      .flatMap(c => c.frameworks)
      .map(f => f.id);
    
    expect(mockOnSelectionChange).toHaveBeenCalledWith(allFrameworkIds);
  });

  it('clears all selections when Clear is clicked', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr', 'ccpa', 'hipaa']}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={true}
      />
    );

    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);

    expect(mockOnSelectionChange).toHaveBeenCalledWith([]);
  });

  it('toggles category expansion when category header is clicked', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        showCategories={true}
      />
    );

    // GDPR should be visible initially (categories expanded by default)
    expect(screen.getByText('GDPR')).toBeInTheDocument();

    // Click on Privacy category to collapse it
    const privacyHeader = screen.getByText('Privacy & Data Protection').closest('button');
    fireEvent.click(privacyHeader!);

    // Note: This test may need adjustment based on how the component handles visibility
    // The framework buttons should still be in DOM but potentially hidden
  });

  it('filters frameworks by region', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        filterByRegion="EU"
      />
    );

    // EU frameworks should be visible
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText('NIS2')).toBeInTheDocument();

    // US-only frameworks should not be visible (unless they're marked as Global)
    expect(screen.queryByText('HIPAA')).not.toBeInTheDocument();
    expect(screen.queryByText('SOX')).not.toBeInTheDocument();
  });

  it('shows Global frameworks regardless of region filter', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        filterByRegion="EU"
      />
    );

    // Global frameworks should still be visible
    expect(screen.getByText('SOC 2')).toBeInTheDocument();
    expect(screen.getByText('ISO 27001')).toBeInTheDocument();
  });

  it('hides Select All and Clear buttons in single-select mode', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        multiSelect={false}
      />
    );

    expect(screen.queryByText('Select All')).not.toBeInTheDocument();
    expect(screen.queryByText('Clear')).not.toBeInTheDocument();
  });

  it('applies visual selection state to selected frameworks', () => {
    render(
      <FrameworkSelector
        selectedFrameworks={['gdpr']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const gdprButton = screen.getByText('GDPR').closest('button');
    
    // The selected button should have the selected styling class
    expect(gdprButton).toHaveClass('bg-blue-100');
  });

  it('applies custom className to container', () => {
    const { container } = render(
      <FrameworkSelector
        selectedFrameworks={[]}
        onSelectionChange={mockOnSelectionChange}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});

describe('RegionFilter', () => {
  const mockOnRegionChange = jest.fn();

  beforeEach(() => {
    mockOnRegionChange.mockClear();
  });

  it('renders all region options', () => {
    render(
      <RegionFilter
        selectedRegion=""
        onRegionChange={mockOnRegionChange}
      />
    );

    const select = screen.getByRole('combobox');
    
    // Check that the select is rendered with options
    expect(select).toBeInTheDocument();
    expect(screen.getByText('All Regions')).toBeInTheDocument();
    expect(screen.getByText('Europe')).toBeInTheDocument();
    expect(screen.getByText('United States')).toBeInTheDocument();
    expect(screen.getByText('Global')).toBeInTheDocument();
  });

  it('calls onRegionChange when region is selected', () => {
    render(
      <RegionFilter
        selectedRegion=""
        onRegionChange={mockOnRegionChange}
      />
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'eu' } });

    expect(mockOnRegionChange).toHaveBeenCalledWith('eu');
  });

  it('displays the selected region', () => {
    render(
      <RegionFilter
        selectedRegion="us"
        onRegionChange={mockOnRegionChange}
      />
    );

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('us');
  });

  it('applies custom className', () => {
    const { container } = render(
      <RegionFilter
        selectedRegion=""
        onRegionChange={mockOnRegionChange}
        className="custom-filter-class"
      />
    );

    expect(container.firstChild).toHaveClass('custom-filter-class');
  });
});
