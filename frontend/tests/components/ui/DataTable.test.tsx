import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '@/components/ui/DataTable';

interface TestRow {
  id: string;
  name: string;
  status: string;
}

const columns = [
  { key: 'name' as const, header: 'Name' },
  { key: 'status' as const, header: 'Status' },
];

const sampleData: TestRow[] = [
  { id: '1', name: 'Item A', status: 'Active' },
  { id: '2', name: 'Item B', status: 'Inactive' },
];

describe('DataTable', () => {
  it('renders without crashing', () => {
    render(<DataTable data={sampleData} columns={columns} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders row data correctly', () => {
    // TODO: Verify each row's cell content matches the provided data
    render(<DataTable data={sampleData} columns={columns} />);
    expect(screen.getByText('Item A')).toBeInTheDocument();
    expect(screen.getByText('Item B')).toBeInTheDocument();
  });

  it('handles search filtering when searchable is enabled', () => {
    // TODO: Enable searchable prop, type in the search input, and verify rows are filtered accordingly
    render(
      <DataTable
        data={sampleData}
        columns={columns}
        searchable
        searchKeys={['name']}
      />
    );
  });
});
