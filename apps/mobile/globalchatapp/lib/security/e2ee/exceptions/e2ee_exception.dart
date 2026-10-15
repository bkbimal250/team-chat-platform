/// E2EE-layer failures (crypto, storage, trust). Never log inner exception details
/// that may contain key material or plaintext.
sealed class E2eeException implements Exception {
  const E2eeException(this.message);

  final String message;

  @override
  String toString() => 'E2eeException: $message';
}

final class E2eeNotInitializedException extends E2eeException {
  const E2eeNotInitializedException()
      : super('Signal library is not initialized');
}

final class E2eeDeviceNotBootstrappedException extends E2eeException {
  const E2eeDeviceNotBootstrappedException()
      : super('This device has no local cryptographic identity');
}

final class E2eeUntrustedIdentityException extends E2eeException {
  const E2eeUntrustedIdentityException(this.addressLabel)
      : super('Identity key changed or is not trusted for $addressLabel');

  final String addressLabel;
}

final class E2eeStorageException extends E2eeException {
  const E2eeStorageException() : super('Secure storage operation failed');
}

final class E2eeSessionException extends E2eeException {
  const E2eeSessionException(String detail) : super(detail);
}
