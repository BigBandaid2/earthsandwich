import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // root is resolved relative to this config file's directory (frontend/)
  root: '.',
  build: {
    // output to project root's dist/ rather than frontend/dist/
    outDir: '../dist',
    emptyOutDir: true,
  },
  plugins: [react()],
});
