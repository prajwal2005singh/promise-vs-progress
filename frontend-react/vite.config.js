import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    port: 5173,

    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        //rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Citizen-uploaded evidence photos, served by FastAPI's /uploads
      // static mount (see backend/main.py) -- same dev-proxy treatment
      // as /api so <img src="/uploads/..."> works in `npm run dev` too.
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
