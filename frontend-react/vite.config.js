import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // In dev, the React app runs on :5173 and the FastAPI backend on
    // :8000. Proxying /api/* to FastAPI means the frontend code always
    // calls same-origin relative paths (no CORS headaches, and no
    // hardcoded backend URL to swap out for production).
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    // FastAPI serves this straight out of backend/static in production.
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
