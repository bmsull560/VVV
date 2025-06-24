import { render, screen } from '@testing-library/react';
import IndustryTemplateSelector from '@/components/discovery/IndustryTemplateSelector';

describe('IndustryTemplateSelector minimal', () => {
  it('renders and shows the dropdown trigger', () => {
    render(
      <IndustryTemplateSelector onSelectTemplate={jest.fn()} onCancel={jest.fn()} />
    );
    // Should render the dropdown trigger
    expect(screen.getByTestId('industry-select-trigger')).toBeInTheDocument();
    expect(screen.getByText('Select Industry Template')).toBeInTheDocument();
  });
});
