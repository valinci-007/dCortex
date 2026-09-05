import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend API runs on :8000; in dev the Vite server proxies /api to it so the browser
// talks to one origin. For the single-process demo the backend serves frontend/dist itself.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
