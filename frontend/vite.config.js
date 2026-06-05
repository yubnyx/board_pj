import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // /api 로 시작하는 요청은 백엔드(8000)로 넘겨줍니다 (CORS 걱정 없이 개발)
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
