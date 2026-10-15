import 'package:dio/dio.dart';

import '../api/auth/auth_api.dart';
import '../api/client/gateway_client.dart';
import '../api/interceptors/error_interceptor.dart';
import '../api/models/device_input.dart';
import '../api/models/me_response.dart';
import '../api/models/token_response.dart';
import 'session_storage.dart';

class AuthRepository {
  AuthRepository({
    SessionStorage? sessionStorage,
    GatewayClient? gatewayClient,
  }) : _storage = sessionStorage ?? SessionStorage() {
    _client = gatewayClient ?? GatewayClient(sessionStorage: _storage);
    _api = AuthApi(_client);
  }

  final SessionStorage _storage;
  late final GatewayClient _client;
  late final AuthApi _api;

  SessionStorage get sessionStorage => _storage;

  Future<DeviceInputDto> deviceInput() =>
      DeviceInputDto.current(storage: _storage);

  Future<MeResponseDto> _persistTokenAndLoadProfile(
    TokenResponseDto token,
  ) async {
    await _storage.saveTokens(
      accessToken: token.accessToken,
      refreshToken: token.refreshToken,
      expiresInSeconds: token.expiresIn,
      sessionId: token.sessionId,
      deviceId: token.deviceId,
      identityId: '',
    );
    final me = await _api.me();
    await _storage.saveTokens(
      accessToken: token.accessToken,
      refreshToken: token.refreshToken,
      expiresInSeconds: token.expiresIn,
      sessionId: token.sessionId,
      deviceId: token.deviceId,
      identityId: me.identityId,
    );
    return me;
  }

  Future<MeResponseDto> loginWithPassword({
    required String email,
    required String password,
  }) async {
    final device = await deviceInput();
    try {
      final token = await _api.loginWithPassword(
        email: email.trim(),
        password: password,
        device: device,
      );
      return await _persistTokenAndLoadProfile(token);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<MeResponseDto> registerPersonal({
    required String displayName,
    required String email,
    required String phone,
    required String password,
  }) async {
    final device = await deviceInput();
    try {
      final token = await _api.registerPersonal(
        displayName: displayName,
        email: email.trim(),
        phone: phone.trim(),
        password: password,
        device: device,
      );
      return await _persistTokenAndLoadProfile(token);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<({String? challengeId, String? developmentCode})> requestOtp({
    required String phone,
    required String purpose,
  }) async {
    try {
      final body = await _api.requestOtp(
        phoneNumber: phone.trim(),
        purpose: purpose,
      );
      return (
        challengeId: body['challenge_id'] as String?,
        developmentCode: body['development_code'] as String?,
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<MeResponseDto> verifyOtp({
    required String challengeId,
    required String code,
  }) async {
    final device = await deviceInput();
    try {
      final token = await _api.verifyOtp(
        challengeId: challengeId,
        code: code,
        device: device,
      );
      return await _persistTokenAndLoadProfile(token);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<String?> forgotPassword({required String email}) async {
    try {
      final body = await _api.forgotPassword(email: email.trim());
      return body['development_reset_token'] as String?;
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      await _api.resetPassword(token: token.trim(), newPassword: newPassword);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<MeResponseDto?> restoreSession() async {
    if (!await _storage.hasStoredSession()) return null;
    try {
      if (await _storage.isAccessTokenExpired()) {
        final refresh = await _storage.readRefreshToken();
        if (refresh == null || refresh.isEmpty) return null;
        final token = await _api.refresh(refreshToken: refresh);
        return await _persistTokenAndLoadProfile(token);
      }
      return await _api.me();
    } on DioException catch (e) {
      final api = apiExceptionFromDio(e);
      if (api != null && api.isSessionExpired) return null;
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      await _api.logout();
    } on DioException {
      // Clear local session even if revoke fails.
    }
    await _storage.clearAuth();
  }

  Future<MeResponseDto> refreshMe() => _api.me();

  Future<MeResponseDto> switchOrganization(String organizationId) async {
    final token = await _api.switchContext(organizationId: organizationId);
    return _persistTokenAndLoadProfile(token);
  }

  Future<DeviceCryptoStatusSnapshot> readCryptoSnapshot() async {
    final ready = await _storage.isCryptoReady();
    final published = await _storage.areKeysPublished();
    if (ready && published) {
      return DeviceCryptoStatusSnapshot.ready;
    }
    if (ready && !published) {
      return DeviceCryptoStatusSnapshot.blockedNoBackend;
    }
    return DeviceCryptoStatusSnapshot.needsBootstrap;
  }
}

enum DeviceCryptoStatusSnapshot {
  needsBootstrap,
  ready,
  blockedNoBackend,
}
