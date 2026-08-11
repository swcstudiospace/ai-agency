# Agency Cockpit

React mission control for the Hermes × Agno 30-agent agency.

## Surfaces
| | |
|--|--|
| **Web PWA** | Installable browser app |
| **Desktop** | Tauri v2 (Linux/macOS/Windows) |
| **Mobile** | Tauri v2 Android + iOS |

See **[PACKAGING.md](./PACKAGING.md)** for full build matrix.

## Quick start
```bash
npm install
npm run icons
npm run dev          # web → http://127.0.0.1:1420
npm run desktop:dev  # Tauri window
```

## Build
```bash
npm run build:web           # PWA → dist/
npm run desktop:build       # native bundles
npm run android:init && npm run android:build
npm run ios:init && npm run ios:build   # macOS only
```
