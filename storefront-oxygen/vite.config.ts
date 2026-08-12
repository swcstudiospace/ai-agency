import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 3456 },
  build: { outDir: "dist", sourcemap: true },
});
