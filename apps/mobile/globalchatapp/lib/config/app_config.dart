/// Runtime configuration (no secrets). Override via `--dart-define`.
abstract final class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.michat.in',
  );

  static const realtimeWssUrl = String.fromEnvironment(
    'REALTIME_WSS_URL',
    defaultValue: 'wss://ws.michat.in/api/v1/realtime',
  );

  static const appName = 'GlobalChat';
}
