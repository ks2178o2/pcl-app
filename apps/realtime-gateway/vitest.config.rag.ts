import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: [
        'src/components/rag/**/*',
        'src/lib/api/rag-features.ts',
        'src/hooks/useRAGFeatures.ts',
        'src/types/rag-features.ts',
        'src/lib/validation/rag-features.ts'
      ],
      exclude: [
        'src/**/*.test.tsx',
        'src/**/*.test.ts',
        'src/test-setup.ts',
        'src/main.tsx',
        'src/App.tsx'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    include: [
      'src/**/*.{test,spec}.{js,ts,tsx}',
      'src/components/rag/**/*.{test,spec}.{js,ts,tsx}'
    ],
    exclude: [
      'node_modules',
      'dist',
      '.git',
      '.cache'
    ]
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
