import { render, screen, fireEvent } from '@testing-library/react';
import { AIRiskClassifier } from '@/components/compliance/AIRiskClassifier';

describe('AIRiskClassifier', () => {
  it('renders without crashing', () => {
    render(<AIRiskClassifier />);
    expect(screen.getByText('AI System Risk Classification')).toBeInTheDocument();
  });

  it('renders the classification form fields', () => {
    // TODO: Verify form fields are present (system_description, use_case, data_types, file_names, code_content)
    render(<AIRiskClassifier />);
    expect(screen.getByText('Classify Risk Level')).toBeInTheDocument();
  });

  it('calls onClassificationComplete when classification finishes', () => {
    // TODO: Fill in form fields, submit, mock API response, and verify onClassificationComplete callback is invoked
    const onClassificationComplete = jest.fn();
    render(<AIRiskClassifier onClassificationComplete={onClassificationComplete} />);
  });
});
