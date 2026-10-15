import '../../../services/api/models/me_response.dart';

enum AuthStatus {
  unauthenticated,
  authenticating,
  authenticated,
  sessionExpired,
}

enum DeviceCryptoStatus {
  unknown,
  needsBootstrap,
  bootstrapping,
  ready,
  blockedNoBackend,
  failed,
}

class AuthState {
  const AuthState({
    required this.status,
    this.user,
    this.errorMessage,
    this.cryptoStatus = DeviceCryptoStatus.unknown,
    this.cryptoMessage,
  });

  final AuthStatus status;
  final MeResponseDto? user;
  final String? errorMessage;
  final DeviceCryptoStatus cryptoStatus;
  final String? cryptoMessage;

  static const initial = AuthState(status: AuthStatus.unauthenticated);

  bool get isAuthenticated => status == AuthStatus.authenticated;

  bool get canUseMessaging =>
      isAuthenticated && cryptoStatus == DeviceCryptoStatus.ready;

  AuthState copyWith({
    AuthStatus? status,
    MeResponseDto? user,
    String? errorMessage,
    DeviceCryptoStatus? cryptoStatus,
    String? cryptoMessage,
    bool clearError = false,
    bool clearUser = false,
  }) =>
      AuthState(
        status: status ?? this.status,
        user: clearUser ? null : (user ?? this.user),
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
        cryptoStatus: cryptoStatus ?? this.cryptoStatus,
        cryptoMessage: cryptoMessage ?? this.cryptoMessage,
      );
}
