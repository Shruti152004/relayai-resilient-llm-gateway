/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/sessions': 'http://127.0.0.1:8000',
    },
  },
  preview: {
    port: 3000,
    host: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
  },
});
