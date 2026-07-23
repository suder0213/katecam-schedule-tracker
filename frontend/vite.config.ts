import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Native `npm run dev` on the host talks to the backend via localhost. Inside
// docker-compose, "localhost" inside the frontend container means the
// frontend container itself, not the backend one — that container needs the
// backend's service name instead (Docker's internal DNS resolves it).
// docker-compose.yml sets BACKEND_ORIGIN=http://backend:8000 for the frontend
// service to override this default.
const backendOrigin = process.env.BACKEND_ORIGIN ?? 'http://localhost:8000'

// Only set inside docker-compose. Docker Desktop's bind mounts don't forward
// native filesystem events from the Windows host into the container, so
// chokidar/Vite never notices file edits without polling — the dev server
// keeps serving stale transformed modules. Native `npm run dev` on the host
// doesn't need this, so it's gated behind the same env var as BACKEND_ORIGIN.
const runningInDocker = process.env.BACKEND_ORIGIN !== undefined

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    watch: runningInDocker ? { usePolling: true, interval: 300 } : undefined,
    // No path rewriting: the refresh_token cookie is scoped to Path=/auth by the
    // backend, so the browser-visible request path must match backend routes
    // exactly (an /api prefix would break that path match and the cookie would
    // never be sent).
    proxy: {
      '/auth': backendOrigin,
      '/users': backendOrigin,
      '/teams': backendOrigin,
      '/schedules': backendOrigin,
      '/crawl-texts': backendOrigin,
      '/schedule-proposals': backendOrigin,
      '/health': backendOrigin,
    },
  },
})
