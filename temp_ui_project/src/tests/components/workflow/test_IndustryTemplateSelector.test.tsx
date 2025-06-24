import { render, screen, fireEvent } from '@testing-library/react';
import IndustryTemplateSelector from '@/components/discovery/IndustryTemplateSelector';
import { industryTemplates } from '../../../types/industryTemplates';

// Helper to select an industry via the native <select>
const selectIndustry = async (industryValue: string) => {
  const select = screen.getByTestId('industry-select-trigger') as HTMLSelectElement;
  fireEvent.change(select, { target: { value: industryValue } });
};
describe('IndustryTemplateSelector', () => {
  const mockOnSelect = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    mockOnSelect.mockClear();
    mockOnCancel.mockClear();
  });

  it('renders correctly with default state', () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);

    expect(screen.getByText('Select Industry Template')).toBeInTheDocument();
    expect(screen.getByText('Choose an industry template to pre-populate common value drivers and metrics.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /skip template/i })).toBeInTheDocument();
  });

  it('calls onCancel when Skip Template is clicked', () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);

    fireEvent.click(screen.getByRole('button', { name: /skip template/i }));
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('shows the correct default template details', () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);

    const defaultTemplate = industryTemplates.technology;
    expect(screen.getByText(`${defaultTemplate.name} Template`)).toBeInTheDocument();
    expect(screen.getByText(defaultTemplate.description)).toBeInTheDocument();
  });

  it('changes template details when a new industry is selected', async () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);

    // Pick a different industry
    await selectIndustry('healthcare');

    // Wait for the template header to update
    expect(screen.getByText(/Healthcare\s*Template/)).toBeInTheDocument();
    expect(screen.getByText(industryTemplates.healthcare.description)).toBeInTheDocument();
  });

  it('calls onSelectTemplate with the correct template after selection', async () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);

    await selectIndustry('manufacturing');

    // Click the Apply Template button
    const applyButton = screen.getByRole('button', { name: /apply template/i });
    fireEvent.click(applyButton);

    expect(mockOnSelect).toHaveBeenCalledTimes(1);
    expect(mockOnSelect).toHaveBeenCalledWith(expect.objectContaining({ industry: 'manufacturing' }));
  });
});