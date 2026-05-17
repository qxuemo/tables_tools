import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";
import { scanPlugin } from "./src/vite-plugin-scan";

export default defineConfig({
  plugins: [vue(), scanPlugin()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/data": {
        target: "http://localhost:3000",
        bypass(_req) {
          return undefined;
        },
      },
    },
  },
  publicDir: false,
  // Serve data/ directory as static files
});
