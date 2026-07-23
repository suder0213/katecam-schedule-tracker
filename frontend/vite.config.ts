import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // No path rewriting: the refresh_token cookie is scoped to Path=/auth by the
    // backend, so the browser-visible request path must match backend routes
    // exactly (an /api prefix would break that path match and the cookie would
    // never be sent).
    proxy: {
      '/auth': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
      '/teams': 'http://localhost:8000',
      '/schedules': 'http://localhost:8000',
      '/crawl-texts': 'http://localhost:8000',
      '/schedule-proposals': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
