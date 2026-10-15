# Development

## Analyzer

```bash
flutter analyze
```

## Tests (when needed)

```bash
flutter test
flutter test test/features/groups
```

## Backend for local messaging

1. Run gateway + identity + messaging + realtime + media services (see repo `services/`).
2. Apply DB migrations (messaging E2EE envelope column, identity device keys).
3. Run the app with `--dart-define=API_BASE_URL=...` and `REALTIME_WSS_URL=...` pointing at the gateway.
4. Complete `/device-setup` so keys are published before sending E2EE messages.

## Navigation

- Bootstrap: `/splash` → session restore
- Auth: `/login`, `/register`, `/otp-login`, `/forgot-password`, `/reset-password`, `/session-expired`
- Device E2EE: `/device-setup` (required before `/home/*` when keys are not published)
- Main shell: `/home/chats`, `/home/updates`, `/home/contacts`, `/home/workspace`, `/home/settings`
- Full-screen routes (chat, new group, …) use the root navigator above the shell.

## libsignal (native)

The `libsignal` package registers a **Dart build hook** (`hook/build.dart`) that downloads or bundles platform native libraries during `flutter pub get` / `flutter build`.

- **Android / iOS:** first `flutter run` or `flutter build apk|ipa` triggers the hook; release builds use the same path.
- **Local Rust build (optional):** see the libsignal package README (`make build` in the package checkout).

**Android:** `flutter build apk --debug` completed successfully on this project (libsignal native hook + Gradle). Install the APK on a device/emulator and confirm the app reaches splash without a libsignal load error.

**iOS:** requires macOS:

```bash
flutter build ios --no-codesign
```

`E2eeFoundation.ensureInitialized()` in `bootstrap.dart` loads the native library at app start.

## Theming

`ThemeMode` is controlled by `themeModeProvider` (Riverpod). Default: system.
