import { render, screen, fireEvent } from '@testing-library/react';
import IndustryTemplateSelector from '@/components/discovery/IndustryTemplateSelector';
import { industryTemplates } from '../../../types/industryTemplates';

// Helper to get the Select dropdown and select an industry
const selectIndustry = async (industryValue: string) => {
  // Open the dropdown
  const trigger = screen.getByRole('button', { name: /industry/i });
  fireEvent.mouseDown(trigger);

  // Select the desired industry option
  const option = await screen.findByText(
    Object.values(industryTemplates).find(t => t.industry === industryValue)?.name || industryValue,
    undefined,
    { timeout: 1000 }
  );
  fireEvent.click(option);
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
    expect(screen.getByText('Healthcare Template')).toBeInTheDocument();
    expect(screen.getByText(industryTemplates.healthcare.description)).toBeInTheDocument();
  });

  it('calls onSelectTemplate with the correct template after selection', async () => {
    render(<IndustryTemplateSelector onSelectTemplate={mockOnSelect} onCancel={mockOnCancel} />);
    await selectIndustry('manufacturing');
    // Simulate clicking the "Apply" button if present, or call the handler directly
    // This assumes an "Apply" or similar button is present in the UI
    const applyButton = screen.queryByRole('button', { name: /apply/i }) || screen.queryByRole('button', { name: /continue/i });
    if (applyButton) {
      fireEvent.click(applyButton);
    } else {
      // If no explicit apply button, call the handler (simulate selection)
      // This fallback may need adjustment if the UI changes
      fireEvent.click(screen.getByText('Manufacturing Template'));
    }
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
    expect(mockOnSelect).toHaveBeenCalledWith(expect.objectContaining({ industry: 'manufacturing' }));
  });
});