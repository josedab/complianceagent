import { render, screen, fireEvent } from '@testing-library/react';
import { CodeBlock, InlineCode, detectLanguage } from '@/components/ui/CodeBlock';

describe('CodeBlock', () => {
  it('renders without crashing', () => {
    render(<CodeBlock code="const x = 1;" language="typescript" />);
    expect(screen.getByText(/const/)).toBeInTheDocument();
  });

  it('renders filename and language badge in header', () => {
    // TODO: Pass filename and language props, verify the header shows the filename and a language badge
    render(
      <CodeBlock code="print('hi')" language="python" filename="main.py" />
    );
  });

  it('copies code to clipboard when copy button is clicked', () => {
    // TODO: Mock navigator.clipboard.writeText, click the copy button, and verify "Copied!" feedback appears
    render(<CodeBlock code="const x = 1;" />);
  });
});

describe('InlineCode', () => {
  it('renders without crashing', () => {
    // TODO: Verify inline code element renders with correct styling
    render(<InlineCode>someVariable</InlineCode>);
    expect(screen.getByText('someVariable')).toBeInTheDocument();
  });
});

describe('detectLanguage', () => {
  it('detects language from filename extension', () => {
    // TODO: Test detectLanguage with various file extensions (.ts, .py, .go, .rs) and verify correct language string
    expect(detectLanguage('example.ts')).toBeDefined();
  });
});
