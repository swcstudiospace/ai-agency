# Mobile project notes (Tauri v2)

Native projects are **generated** on developer machines — not fully committed:

```bash
npm run android:init   # → src-tauri/gen/android
npm run ios:init       # → src-tauri/gen/apple  (macOS + Xcode)
```

`src-tauri/gen/` is gitignored.

## Android checklist
1. Install Android Studio, SDK 34, NDK, platform-tools
2. `export ANDROID_HOME=...` and put `platform-tools` on PATH
3. `rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android`
4. `npm run android:init`
5. `npm run android:dev` or `npm run android:build` / `android:build:aab`

## iOS checklist
1. macOS + Xcode 15+
2. Set `bundle.iOS.developmentTeam` in `src-tauri/tauri.conf.json`
3. `rustup target add aarch64-apple-ios aarch64-apple-ios-sim`
4. `npm run ios:init && npm run ios:dev`

Identifier is shared: `ai.autonogrammer.agency-cockpit`
