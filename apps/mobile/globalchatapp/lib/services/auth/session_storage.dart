import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/security/app_secure_storage.dart';
import 'package:uuid/uuid.dart';

/// Bearer tokens and session metadata — secure storage only.
class SessionStorage {
  SessionStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? createAppSecureStorage();

  final FlutterSecureStorage _storage;

  static const _accessToken = 'gc_auth/access_token';
  static const _refreshToken = 'gc_auth/refresh_token';
  static const _expiresAtMs = 'gc_auth/expires_at_ms';
  static const _sessionId = 'gc_auth/session_id';
  static const _deviceId = 'gc_auth/device_id';
  static const _identityId = 'gc_auth/identity_id';
  static const _installationId = 'gc_auth/installation_id';
  static const _cryptoReady = 'gc_auth/crypto_ready';
  static const _keysPublished = 'gc_auth/keys_published';
  static const _signalDeviceId = 'gc_auth/signal_device_id';

  Future<String> getOrCreateInstallationId() async {
    final existing = await _storage.read(key: _installationId);
    if (existing != null && existing.length >= 16) return existing;
    const uuid = Uuid();
    final id = uuid.v4().replaceAll('-', '');
    await _storage.write(key: _installationId, value: id);
    return id;
  }

  Future<void> saveTokens({
    required String accessToken,
    required String? refreshToken,
    required int expiresInSeconds,
    required String sessionId,
    required String deviceId,
    required String identityId,
  }) async {
    final expiresAt =
        DateTime.now().millisecondsSinceEpoch + (expiresInSeconds * 1000);
    await _storage.write(key: _accessToken, value: accessToken);
    if (refreshToken != null) {
      await _storage.write(key: _refreshToken, value: refreshToken);
    }
    await _storage.write(key: _expiresAtMs, value: expiresAt.toString());
    await _storage.write(key: _sessionId, value: sessionId);
    await _storage.write(key: _deviceId, value: deviceId);
    await _storage.write(key: _identityId, value: identityId);
  }

  Future<String?> readAccessToken() => _storage.read(key: _accessToken);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshToken);

  Future<bool> hasStoredSession() async =>
      await _storage.containsKey(key: _accessToken);

  Future<bool> isAccessTokenExpired({int skewSeconds = 60}) async {
    final raw = await _storage.read(key: _expiresAtMs);
    if (raw == null) return true;
    final expiresAt = int.tryParse(raw);
    if (expiresAt == null) return true;
    return DateTime.now().millisecondsSinceEpoch >=
        expiresAt - (skewSeconds * 1000);
  }

  Future<StoredSession?> readSession() async {
    final access = await readAccessToken();
    if (access == null) return null;
    final refresh = await readRefreshToken();
    final sessionId = await _storage.read(key: _sessionId);
    final deviceId = await _storage.read(key: _deviceId);
    final identityId = await _storage.read(key: _identityId);
    if (sessionId == null || deviceId == null || identityId == null) {
      return null;
    }
    return StoredSession(
      accessToken: access,
      refreshToken: refresh,
      sessionId: sessionId,
      deviceId: deviceId,
      identityId: identityId,
    );
  }

  Future<void> clearAuth() async {
    for (final key in [
      _accessToken,
      _refreshToken,
      _expiresAtMs,
      _sessionId,
      _deviceId,
      _identityId,
      _cryptoReady,
      _keysPublished,
    ]) {
      await _storage.delete(key: key);
    }
  }

  Future<void> setCryptoReady(bool value) async {
    await _storage.write(
      key: _cryptoReady,
      value: value ? '1' : '0',
    );
  }

  Future<bool> isCryptoReady() async {
    final v = await _storage.read(key: _cryptoReady);
    return v == '1';
  }

  Future<void> setKeysPublished(bool value) async {
    await _storage.write(
      key: _keysPublished,
      value: value ? '1' : '0',
    );
  }

  Future<bool> areKeysPublished() async {
    final v = await _storage.read(key: _keysPublished);
    return v == '1';
  }

  Future<int?> readSignalDeviceId() async {
    final raw = await _storage.read(key: _signalDeviceId);
    return raw == null ? null : int.tryParse(raw);
  }

  Future<void> saveSignalDeviceId(int id) async {
    await _storage.write(key: _signalDeviceId, value: id.toString());
  }
}

class StoredSession {
  const StoredSession({
    required this.accessToken,
    required this.refreshToken,
    required this.sessionId,
    required this.deviceId,
    required this.identityId,
  });

  final String accessToken;
  final String? refreshToken;
  final String sessionId;
  final String deviceId;
  final String identityId;
}
