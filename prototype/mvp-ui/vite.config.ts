import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Local dev: /. GitHub Pages: /Agent/ (set via VITE_BASE_PATH in CI).
const base = process.env.VITE_BASE_PATH ?? "/";

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/sockets": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
      "/alive": "http://127.0.0.1:8000",
      "/ready": "http://127.0.0.1:8000",
    },
  },
  preview: {
    host: true,
    port: 4173,
    allowedHosts: true,
  },
});
