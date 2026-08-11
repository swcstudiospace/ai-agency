/** Runtime platform detection: web PWA vs Tauri desktop vs Tauri mobile. */

export type AppShell = "web" | "tauri-desktop" | "tauri-mobile";

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
    __TAURI__?: unknown;
  }
}

export function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(window.__TAURI_INTERNALS__ || window.__TAURI__);
}

export function isMobileViewport(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(max-width: 860px), (pointer: coarse)").matches;
}

export function detectShell(): AppShell {
  if (!isTauri()) return "web";
  // Tauri mobile sets these env-like markers at build time when available
  const platform =
    (import.meta as ImportMeta & { env?: Record<string, string> }).env?.TAURI_ENV_PLATFORM ||
    (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_TAURI_PLATFORM ||
    "";
  if (/android|ios/i.test(platform) || isMobileViewport()) {
    // Prefer mobile shell styling when running under Tauri on phone form-factor
    if (/android|ios/i.test(platform)) return "tauri-mobile";
  }
  // UA fallback for Android WebView / iOS WKWebView in Tauri
  const ua = typeof navigator !== "undefined" ? navigator.userAgent : "";
  if (/Android|iPhone|iPad/i.test(ua) && isTauri()) return "tauri-mobile";
  return "tauri-desktop";
}

export async function getNativePlatformInfo(): Promise<Record<string, unknown> | null> {
  if (!isTauri()) return null;
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    return (await invoke("platform_info")) as Record<string, unknown>;
  } catch {
    return { shell: "tauri", error: "invoke_failed" };
  }
}

export async function openExternal(url: string): Promise<void> {
  if (isTauri()) {
    try {
      const { open } = await import("@tauri-apps/plugin-shell");
      await open(url);
      return;
    } catch {
      /* fall through */
    }
  }
  window.open(url, "_blank", "noopener,noreferrer");
}
