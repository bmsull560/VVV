import * as React from 'react';
import { render, screen } from '@testing-library/react';

test('renders hello', () => {
  render(<div>Hello</div>);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
