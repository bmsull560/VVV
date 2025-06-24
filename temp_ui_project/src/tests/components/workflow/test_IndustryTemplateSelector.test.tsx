import { render, screen, fireEvent } from '@testing-library/react';
import { IndustryTemplateSelector } from '../../../components/workflow/IndustryTemplateSelector';
import { industryTemplates } from '../../../types/industryTemplates';

describe('IndustryTemplateSelector', () => {
  const mockOnSelect = jest.fn();

  beforeEach(() => {
    mockOnSelect.mockClear();
  });

  it('renders correctly with default state', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    expect(screen.getByText('Select an Industry Template')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search templates...')).toBeInTheDocument();
    expect(screen.getByText('All Industries')).toBeInTheDocument();
  });

  it('displays industry templates', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    Object.values(industryTemplates).forEach(template => {
      expect(screen.getByText(template.industry)).toBeInTheDocument();
    });
  });

  it('filters templates based on search input', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'Software' } });
    expect(screen.getByText('Software & Technology')).toBeInTheDocument();
    expect(screen.queryByText('Healthcare')).not.toBeInTheDocument();
  });

  it('calls onSelect with the correct template when a template is clicked', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    const healthcareTemplate = screen.getByText('Healthcare');
    fireEvent.click(healthcareTemplate);
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
    expect(mockOnSelect).toHaveBeenCalledWith(Object.values(industryTemplates).find(t => t.industry === 'healthcare'));
  });

  it('displays "No templates found" when search yields no results', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'NonExistentIndustry' } });
    expect(screen.getByText('No templates found.')).toBeInTheDocument();
  });

  it('resets filter when "All Industries" is clicked', () => {
    render(<IndustryTemplateSelector onSelect={mockOnSelect} />);
    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'Software' } });
    expect(screen.getByText('Software & Technology')).toBeInTheDocument();
    
    const allIndustriesButton = screen.getByText('All Industries');
    fireEvent.click(allIndustriesButton);
    expect(screen.getByText('Healthcare')).toBeInTheDocument(); // Should show all again
  });
});