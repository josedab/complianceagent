import { render, screen, fireEvent } from '@testing-library/react';
import { CodeGenerationPreview } from '@/components/compliance/CodeGenerationPreview';

const mockGeneratedCode = {
  files: [
    {
      path: 'src/example.ts',
      content: 'console.log("hello");',
      language: 'typescript',
      operation: 'new' as const,
    },
  ],
  tests: [],
  documentation: '',
  warnings: [],
  complianceNotes: [],
  pullRequestSuggestion: {
    title: 'Test PR',
    description: 'Test description',
    branch: 'feature/test',
  },
};

describe('CodeGenerationPreview', () => {
  it('renders without crashing', () => {
    render(<CodeGenerationPreview generatedCode={mockGeneratedCode} />);
    expect(screen.getByText('Generated Code Preview')).toBeInTheDocument();
  });

  it('renders file tabs and file cards', () => {
    // TODO: Verify Files/Tests/Documentation tabs render and file cards show operation badges (New/Modified/Deleted)
    render(<CodeGenerationPreview generatedCode={mockGeneratedCode} />);
    expect(screen.getByText('Files')).toBeInTheDocument();
  });

  it('calls onApprove and onReject callbacks', () => {
    // TODO: Click "Approve & Create PR" and "Reject" buttons, verify respective callbacks are invoked
    const onApprove = jest.fn();
    const onReject = jest.fn();
    render(
      <CodeGenerationPreview
        generatedCode={mockGeneratedCode}
        onApprove={onApprove}
        onReject={onReject}
      />
    );
  });
});
