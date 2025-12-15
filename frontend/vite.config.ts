import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { execSync } from "child_process";

// Get git SHA at build time
function getGitSha(): string {
  try {
    return execSync("git rev-parse --short HEAD").toString().trim();
  } catch (error) {
    return "unknown";
  }
}

export default defineConfig({
  plugins: [vue()],
  define: {
    __GIT_SHA__: JSON.stringify(getGitSha()),
  },
  server: {
    port: 5173,
    allowedHosts: ["localhost", "photosafe.melloy.life"],
    proxy: {
      "/api": {
        target: process.env.VITE_API_URL || "http://localhost:8000",
        changeOrigin: true,
      },
      "/uploads": {
        target: process.env.VITE_API_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
  },
});
