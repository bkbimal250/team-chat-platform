/// Normalized gateway error (never includes tokens).
class ApiException implements Exception {
  const ApiException({
    required this.message,
    this.code,
    this.statusCode,
    this.correlationId,
  });

  final String message;
  final String? code;
  final int? statusCode;
  final String? correlationId;

  bool get isUnauthorized => statusCode == 401;
  bool get isSessionExpired =>
      code == 'SESSION_EXPIRED' || code == 'INVALID_TOKEN' || statusCode == 401;

  @override
  String toString() => 'ApiException($code): $message';
}
