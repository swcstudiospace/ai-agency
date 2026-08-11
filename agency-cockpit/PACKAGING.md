# Packaging — Web PWA · Desktop · Mobile

Agency Cockpit is one React codebase, three delivery surfaces.

| Target | Tech | Artifact |
|--------|------|----------|
| **Web app** | Vite + **PWA** (vite-plugin-pwa) | `dist/` static + service worker |
| **Desktop** | **Tauri v2** | `.deb` / `.AppImage` / `.dmg` / `.msi` / `.exe` |
| **Mobile** | **Tauri v2 Android / iOS** | `.apk` / `.aab` / `.ipa` |

Identifier: `ai.autonogrammer.agency-cockpit`

---

## Prerequisites

### All
```bash
cd agency-cockpit
npm install
npm run icons
```

### Desktop (Linux example)
```bash
sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file \
  libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
# Rust: https://rustup.rs
```

### Android
- Android Studio / SDK 34+, NDK, JDK 17
- `rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android`
- First time: `npm run android:init`

### iOS (macOS only)
- Xcode 15+, CocoaPods
- Apple Developer Team ID → set in `src-tauri/tauri.conf.json` → `bundle.iOS.developmentTeam`
- `rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim`
- First time: `npm run ios:init`

---

## Web app (PWA)

```bash
npm run build:web          # → dist/ (installable PWA)
npm run preview:web        # http://0.0.0.0:4173
# Docker
npm run build:web && docker build -t agency-cockpit-web . && docker run -p 8080:80 agency-cockpit-web
```

Installable in Chrome/Edge/Safari (Add to Home Screen). Offline shell via Workbox.

Env for API endpoints (optional):
```bash
VITE_AGENTOS_URL=http://127.0.0.1:7777
VITE_DROP_URL=http://127.0.0.1:7788
VITE_BRIDGE_URL=http://127.0.0.1:7790
```

---

## Desktop (Tauri v2)

```bash
npm run desktop:dev        # hot reload
npm run desktop:build      # all bundles for host OS
npm run desktop:build:deb
npm run desktop:build:appimage
```

Outputs under:
`src-tauri/target/release/bundle/{deb,appimage,dmg,msi,nsis}/`

---

## Mobile (Tauri v2)

```bash
# Android
npm run android:init       # once — generates src-tauri/gen/android
npm run android:dev        # device/emulator
npm run android:build      # APK
npm run android:build:aab  # Play Store bundle

# iOS (macOS)
npm run ios:init
# set developmentTeam in tauri.conf.json
npm run ios:dev
npm run ios:build
```

Generated native projects live in `src-tauri/gen/` (gitignored by default after init).

---

## Scripts map

| Script | Purpose |
|--------|---------|
| `dev` / `dev:web` | Vite dev server :1420 |
| `build:web` | Typecheck + PWA production build |
| `desktop:dev` / `desktop:build` | Tauri desktop |
| `android:*` / `ios:*` | Tauri mobile |
| `icons` | Regenerate PNG/SVG icons |
| `package:all` | icons + web + desktop host build |

---

## Platform detection (runtime)

`src/lib/platform.ts` + `<PlatformBadge />`:
- `web` — browser / PWA
- `tauri-desktop` — Windows / macOS / Linux shell
- `tauri-mobile` — Android / iOS WebView

Use `openExternal()` for links (shell plugin on Tauri, `window.open` on web).

---

## CI

Workflow template: `.github/workflows/package.yml`  
Builds **web PWA** + **Linux desktop** artifacts. Enable macOS/Windows/Android/iOS jobs on appropriate runners.

---

## Honest constraints

1. **This machine** can fully verify **web PWA** and (with WebKit deps) **Linux desktop**.  
2. **iOS** requires a Mac + signing team.  
3. **Android** requires SDK/NDK; first `android:init` is interactive-ish via CLI.  
4. Placeholder **ico/icns** are PNG-based; for store polish, replace with real `iconutil` / `png2icons` assets.  
5. Mobile safe-areas: CSS uses `viewport-fit=cover`; add `env(safe-area-inset-*)` padding when testing on notched devices.
