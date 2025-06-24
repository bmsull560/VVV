import React from 'react';

test('minimal test', () => {
  expect(typeof React).toBe('object');
  expect(React).not.toBeNull();
});
