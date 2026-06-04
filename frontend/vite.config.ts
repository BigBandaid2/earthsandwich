import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => ({
  // root is resolved relative to this config file's directory (frontend/)
  root: '.',
  // In dev, serve the project-root public/ dir so /media/* resolves to
  // public/media/*. Disabled at build time so media files aren't copied
  // into dist/ and baked into the Docker image.
  publicDir: command === 'serve' ? '../public' : false,
  build: {
    // output to project root's dist/ rather than frontend/dist/
    outDir: '../dist',
    emptyOutDir: true,
  },
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
  },
}));
