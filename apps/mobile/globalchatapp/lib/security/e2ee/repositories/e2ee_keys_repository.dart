import '../models/device_public_key_bundle.dart';

/// Result of attempting to publish keys to the gateway.
enum E2eePublishStatus {
  published,
  notConfigured,
  failed,
}

class E2eePublishResult {
  const E2eePublishResult({
    required this.status,
    this.message,
  });

  final E2eePublishStatus status;
  final String? message;

  bool get isSuccess => status == E2eePublishStatus.published;
}

/// Upload/fetch E2EE public key material via the gateway.
abstract interface class E2eeKeysRepository {
  Future<E2eePublishResult> publishDeviceBundle(DevicePublicKeyBundle bundle);

  Future<E2eePublishResult> replenishOneTimePreKeys(
    DevicePublicKeyBundle partialBundle,
  );
}

/// Gateway endpoints for device E2EE keys are not deployed yet (Phase 2B).
class GatewayE2eeKeysRepository implements E2eeKeysRepository {
  static const notConfiguredMessage =
      'Server E2EE key endpoints are not available yet. '
      'See docs/E2EE-BACKEND-CONTRACT.md.';

  @override
  Future<E2eePublishResult> publishDeviceBundle(
    DevicePublicKeyBundle bundle,
  ) async {
    return const E2eePublishResult(
      status: E2eePublishStatus.notConfigured,
      message: notConfiguredMessage,
    );
  }

  @override
  Future<E2eePublishResult> replenishOneTimePreKeys(
    DevicePublicKeyBundle partialBundle,
  ) async {
    return const E2eePublishResult(
      status: E2eePublishStatus.notConfigured,
      message: notConfiguredMessage,
    );
  }
}
