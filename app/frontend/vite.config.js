import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      // 127.0.0.1 (not "localhost") to force IPv4 and avoid colliding with another
      // service bound to IPv6 *:8000. Backend runs on 8011.
      "/api": { target: "http://127.0.0.1:8011", changeOrigin: true },
    },
  },
});
