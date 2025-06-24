export default {
  preset: 'ts-jest',
  testEnvironment: 'jest-environment-jsdom-sixteen',
  extensionsToTreatAsEsm: ['.ts', '.tsx'],

  globals: {
    'import.meta.env.VITE_API_BASE_URL': 'http://localhost:8000',
  },
  roots: ['<rootDir>/src'],
  testMatch: [
    '**/*.test.{ts,tsx}',
    '**/*.spec.{ts,tsx}'
  ],
  transform: {
    '^.+\\.(ts|tsx)?$': ['ts-jest', { tsconfig: 'tsconfig.app.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  moduleDirectories: ['node_modules', 'src'],
  modulePaths: ['<rootDir>/src'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],
  transformIgnorePatterns: [
    '/node_modules/',
    '\.pnp\.[^\/]+$'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html']
};
