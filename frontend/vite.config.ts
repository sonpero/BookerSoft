import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

const BACKEND_ORIGIN = "http://127.0.0.1:8000";

// A bare GET "/books/123" is the SPA's own book detail page (React Router
// renders it); every other /books/... request — including DELETE/PATCH on
// that exact same path — is an API call that belongs to the backend. The
// method check matters: without it, a DELETE to /books/123 was silently
// misrouted to Vite's own page serving instead of the backend, and never
// reached FastAPI at all (which is what "delete doesn't work" turned out
// to be).
function bypassBookDetailRoute(req: { url?: string; method?: string }): string | undefined {
  if (req.method === "GET" && /^\/books\/\d+$/.test(req.url ?? "")) {
    return req.url;
  }
  return undefined;
}

export default defineConfig(({ command }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  // Asset URLs inside the built index.html must be prefixed with /static/
  // (that's where FastAPI's StaticFiles mount serves them from) — but the
  // dev server must keep serving its own module graph from the root, or
  // Vite would only respond under http://localhost:5173/static/ instead of
  // /. This is build-tool config, not a conditional API URL in app code.
  base: command === "build" ? "/static/" : "/",
  build: {
    outDir: fileURLToPath(new URL("../src/bookersoft/static", import.meta.url)),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/books": {
        target: BACKEND_ORIGIN,
        changeOrigin: true,
        bypass: bypassBookDetailRoute,
      },
      "/users": { target: BACKEND_ORIGIN, changeOrigin: true },
      "/me": { target: BACKEND_ORIGIN, changeOrigin: true },
      "/login": { target: BACKEND_ORIGIN, changeOrigin: true },
      "/logout": { target: BACKEND_ORIGIN, changeOrigin: true },
      // /static/* in production is FastAPI's StaticFiles mount over the
      // Vite build output. In dev nothing needs to reach the backend for
      // it: every /static/X reference (theme.css, login's own assets) is a
      // file already in this project's public/, which Vite serves at /X —
      // so just strip the prefix and let Vite handle it, same URL as prod.
      "/static": {
        target: BACKEND_ORIGIN,
        bypass(req) {
          return (req.url ?? "").replace(/^\/static/, "") || "/";
        },
      },
    },
  },
}));
