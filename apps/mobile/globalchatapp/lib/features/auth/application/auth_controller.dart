import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../security/e2ee/repositories/e2ee_keys_repository.dart';
import '../../../security/e2ee/repositories/e2ee_keys_repository.dart';
import '../../../services/api/errors/api_exception.dart';
import '../../../services/api/providers/api_providers.dart';
import '../../../services/auth/auth_repository.dart';
import '../../../services/devices/device_crypto_bootstrap.dart';
import '../../../services/realtime/realtime_client.dart';
import 'auth_state.dart';

final authRepositoryProvider = Provider(
  (ref) => AuthRepository(
    sessionStorage: ref.watch(sessionStorageProvider),
    gatewayClient: ref.watch(gatewayClientProvider),
  ),
);

final deviceCryptoBootstrapProvider = Provider((ref) => DeviceCryptoBootstrap(
      e2eeApi: ref.watch(e2eeApiProvider),
    ));

final authControllerProvider =
    NotifierProvider<AuthController, AuthState>(AuthController.new);

/// Notifies [GoRouter] when auth changes.
final authRouterRefreshProvider = Provider<AuthRouterRefresh>((ref) {
  final refresh = AuthRouterRefresh();
  ref.onDispose(refresh.dispose);
  ref.listen(authControllerProvider, (_, _) => refresh.notifyRouter());
  return refresh;
});

class AuthRouterRefresh extends ChangeNotifier {
  void notifyRouter() => notifyListeners();
}

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() => AuthState.initial;

  AuthRepository get _auth => ref.read(authRepositoryProvider);
  DeviceCryptoBootstrap get _bootstrap =>
      ref.read(deviceCryptoBootstrapProvider);

  Future<void> restoreFromStorage() async {
    state = state.copyWith(
      status: AuthStatus.authenticating,
      clearError: true,
    );
    try {
      final me = await _auth.restoreSession();
      if (me == null) {
        state = const AuthState(status: AuthStatus.unauthenticated);
        return;
      }
      final crypto = await _auth.readCryptoSnapshot();
      state = AuthState(
        status: AuthStatus.authenticated,
        user: me,
        cryptoStatus: _mapCrypto(crypto),
        cryptoMessage: crypto == DeviceCryptoStatusSnapshot.blockedNoBackend
            ? GatewayE2eeKeysRepository.notConfiguredMessage
            : null,
      );
      if (state.canUseMessaging) {
        await ref.read(realtimeClientProvider).connect();
      }
    } on ApiException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
    }
  }

  DeviceCryptoStatus _mapCrypto(DeviceCryptoStatusSnapshot snap) {
    switch (snap) {
      case DeviceCryptoStatusSnapshot.ready:
        return DeviceCryptoStatus.ready;
      case DeviceCryptoStatusSnapshot.blockedNoBackend:
        return DeviceCryptoStatus.blockedNoBackend;
      case DeviceCryptoStatusSnapshot.needsBootstrap:
        return DeviceCryptoStatus.needsBootstrap;
    }
  }

  Future<bool> login(String email, String password) =>
      _authenticate(() => _auth.loginWithPassword(email: email, password: password));

  Future<bool> registerPersonal({
    required String displayName,
    required String email,
    required String phone,
    required String password,
  }) =>
      _authenticate(
        () => _auth.registerPersonal(
          displayName: displayName,
          email: email,
          phone: phone,
          password: password,
        ),
      );

  Future<bool> verifyOtp({
    required String challengeId,
    required String code,
  }) =>
      _authenticate(
        () => _auth.verifyOtp(challengeId: challengeId, code: code),
      );

  Future<bool> _authenticate(Future<dynamic> Function() action) async {
    state = state.copyWith(
      status: AuthStatus.authenticating,
      clearError: true,
    );
    try {
      final me = await action();
      state = AuthState(
        status: AuthStatus.authenticated,
        user: me,
        cryptoStatus: DeviceCryptoStatus.needsBootstrap,
      );
      return true;
    } on ApiException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      return false;
    }
  }

  Future<void> runDeviceCryptoBootstrap() async {
    final user = state.user;
    if (user == null) return;
    state = state.copyWith(
      cryptoStatus: DeviceCryptoStatus.bootstrapping,
      clearError: true,
    );
    try {
      final result = await _bootstrap.run(
        identityId: user.identityId,
        backendDeviceId: user.deviceId,
      );
      if (result.canEnterApp) {
        state = state.copyWith(
          cryptoStatus: DeviceCryptoStatus.ready,
          cryptoMessage: null,
        );
        await ref.read(realtimeClientProvider).connect();
      } else if (result.blockedOnBackend) {
        state = state.copyWith(
          cryptoStatus: DeviceCryptoStatus.blockedNoBackend,
          cryptoMessage: result.publishResult.message,
        );
      } else {
        state = state.copyWith(
          cryptoStatus: DeviceCryptoStatus.failed,
          cryptoMessage: result.publishResult.message ?? 'Key upload failed',
        );
      }
    } catch (e, st) {
      debugPrint('Device crypto bootstrap failed: $e\n$st');
      final detail = e.toString();
      final message = detail.contains('E2eeStorageException')
          ? 'Secure storage failed on this device. Try wiping app data or use a physical device.'
          : detail.contains('E2eeNotInitializedException')
              ? 'Encryption library did not start. Restart the app.'
              : 'Could not initialize secure messaging on this device.';
      state = state.copyWith(
        cryptoStatus: DeviceCryptoStatus.failed,
        cryptoMessage: message,
      );
    }
  }

  Future<void> refreshProfile() async {
    try {
      final me = await _auth.refreshMe();
      state = state.copyWith(user: me);
    } on ApiException catch (e) {
      state = state.copyWith(errorMessage: e.message);
    }
  }

  Future<bool> switchOrganization(String organizationId) async {
    try {
      final me = await _auth.switchOrganization(organizationId);
      state = state.copyWith(user: me, clearError: true);
      return true;
    } on ApiException catch (e) {
      state = state.copyWith(errorMessage: e.message);
      return false;
    }
  }

  Future<void> retryKeyPublish() async {
    final user = state.user;
    if (user == null) return;
    state = state.copyWith(cryptoStatus: DeviceCryptoStatus.bootstrapping);
    final result = await _bootstrap.retryPublish(
      identityId: user.identityId,
      backendDeviceId: user.deviceId,
    );
    if (result.canEnterApp) {
      state = state.copyWith(
        cryptoStatus: DeviceCryptoStatus.ready,
        cryptoMessage: null,
      );
    } else {
      state = state.copyWith(
        cryptoStatus: DeviceCryptoStatus.blockedNoBackend,
        cryptoMessage: result.publishResult.message,
      );
    }
  }

  Future<void> logout() async {
    await _auth.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void markSessionExpired() {
    state = const AuthState(status: AuthStatus.sessionExpired);
  }

  Future<void> forgotPassword(String email) async {
    state = state.copyWith(status: AuthStatus.authenticating, clearError: true);
    try {
      await _auth.forgotPassword(email: email);
      state = state.copyWith(status: AuthStatus.unauthenticated);
    } on ApiException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
    }
  }

  Future<bool> resetPassword(String token, String newPassword) async {
    state = state.copyWith(status: AuthStatus.authenticating, clearError: true);
    try {
      await _auth.resetPassword(token: token, newPassword: newPassword);
      state = const AuthState(status: AuthStatus.unauthenticated);
      return true;
    } on ApiException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      return false;
    }
  }
}
