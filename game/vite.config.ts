import { defineConfig } from "vite";

export default defineConfig({
  base: "/holdfast/",
  publicDir: "public",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: "index.html"
    }
  }
});
