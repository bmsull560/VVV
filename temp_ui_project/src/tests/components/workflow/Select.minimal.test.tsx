import { render, screen } from '@testing-library/react';
import { Select } from '@/components/ui/select';

describe('Select minimal', () => {
  it('renders a basic select element', () => {
    render(
      <Select
        id="test-select"
        label="Test Select"
        value="option1"
        options={[
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2' }
        ]}
        onChange={() => {}}
      />
    );
    expect(screen.getByLabelText('Test Select')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Option 1')).toBeInTheDocument();
  });
});
