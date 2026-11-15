import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, /api se reenvía a uvicorn (cd backend && uvicorn musclesense.api.app:app --reload).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  build: { chunkSizeWarningLimit: 6000 },
});
