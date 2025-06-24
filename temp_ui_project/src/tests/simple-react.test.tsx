import { render } from '@testing-library/react';

test('simple react test', () => {
  const { container } = render(<div>Hello world</div>);
  expect(container.textContent).toBe('Hello world');
});
