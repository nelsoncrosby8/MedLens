import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Bind-mounted source under Docker Desktop on macOS doesn't deliver inotify events;
    // fall back to polling when running in the container (VITE_DOCKER set by compose).
    watch: process.env.VITE_DOCKER ? { usePolling: true } : undefined,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
