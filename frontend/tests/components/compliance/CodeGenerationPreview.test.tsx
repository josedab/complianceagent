import { render, screen, fireEvent } from '@testing-library/react';
import { CodeGenerationPreview } from '@/components/compliance/CodeGenerationPreview';

const mockGeneratedCode = {
  files: [
    {
      path: 'src/example.ts',
      content: 'console.log("hello");',
      language: 'typescript',
      operation: 'create' as const,
    },
  ],
  tests: [],
  documentation: '',
  warnings: [],
  compliance_notes: [],
  confidence: 0.95,
  pr_suggestion: {
    title: 'Test PR',
    body: 'Test description',
  },
};

describe('CodeGenerationPreview', () => {
  it('renders without crashing', () => {
    render(<CodeGenerationPreview generatedCode={mockGeneratedCode} />);
    expect(screen.getByText('Generated Code Preview')).toBeInTheDocument();
  });

  it('renders file tabs and file cards', () => {
    render(<CodeGenerationPreview generatedCode={mockGeneratedCode} />);
    // Tab text includes count e.g. "Files (2)" — match the prefix
    expect(screen.getByText(/^Files/)).toBeInTheDocument();
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
