import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '@/components/ui/DataTable';

interface TestRow {
  id: string;
  name: string;
  status: string;
  [key: string]: unknown;
}

const columns = [
  { key: 'name' as const, header: 'Name' },
  { key: 'status' as const, header: 'Status' },
];

const sampleData: TestRow[] = [
  { id: '1', name: 'Item A', status: 'Active' },
  { id: '2', name: 'Item B', status: 'Inactive' },
  { id: '3', name: 'Widget C', status: 'Active' },
];

describe('DataTable', () => {
  it('renders without crashing', () => {
    render(<DataTable data={sampleData} columns={columns} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders all row data correctly', () => {
    render(<DataTable data={sampleData} columns={columns} />);
    // Verify each row's name cell content matches provided data
    expect(screen.getByText('Item A')).toBeInTheDocument();
    expect(screen.getByText('Item B')).toBeInTheDocument();
    expect(screen.getByText('Widget C')).toBeInTheDocument();
    // Verify status values render (Active appears twice)
    expect(screen.getAllByText('Active')).toHaveLength(2);
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('filters rows when searching with searchable enabled', () => {
    render(
      <DataTable
        data={sampleData}
        columns={columns}
        searchable
        searchKeys={['name']}
      />
    );

    // Find the search input and type a query
    const searchInput = screen.getByRole('textbox');
    fireEvent.change(searchInput, { target: { value: 'Widget' } });

    // Only "Widget C" should remain visible
    expect(screen.getByText('Widget C')).toBeInTheDocument();
    expect(screen.queryByText('Item A')).not.toBeInTheDocument();
    expect(screen.queryByText('Item B')).not.toBeInTheDocument();
  });

  it('shows all rows when search is cleared', () => {
    render(
      <DataTable
        data={sampleData}
        columns={columns}
        searchable
        searchKeys={['name']}
      />
    );

    const searchInput = screen.getByRole('textbox');
    // Filter then clear
    fireEvent.change(searchInput, { target: { value: 'Item' } });
    expect(screen.queryByText('Widget C')).not.toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Item A')).toBeInTheDocument();
    expect(screen.getByText('Widget C')).toBeInTheDocument();
  });

  it('renders empty state when no data provided', () => {
    render(<DataTable data={[]} columns={columns} />);
    // Should show some indication of no data
    expect(screen.queryByText('Item A')).not.toBeInTheDocument();
  });
});
