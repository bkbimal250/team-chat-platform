import '../../security/e2ee/repositories/e2ee_keys_repository.dart';
import '../../security/e2ee/repositories/http_e2ee_keys_repository.dart';
import '../../security/e2ee/services/device_identity_service.dart';
import '../../security/e2ee/services/e2ee_foundation.dart';
import '../api/e2ee/e2ee_api.dart';
import '../auth/session_storage.dart';
import 'signal_device_id.dart';

class DeviceCryptoBootstrapResult {
  const DeviceCryptoBootstrapResult({
    required this.localReady,
    required this.publishResult,
  });

  final bool localReady;
  final E2eePublishResult publishResult;

  bool get canEnterApp =>
      localReady && publishResult.status == E2eePublishStatus.published;

  bool get blockedOnBackend =>
      localReady && publishResult.status == E2eePublishStatus.notConfigured;
}

/// Post-auth: local Signal identity + optional public-key upload.
class DeviceCryptoBootstrap {
  DeviceCryptoBootstrap({
    SessionStorage? sessionStorage,
    DeviceIdentityService? deviceIdentity,
    E2eeApi? e2eeApi,
    SignalDeviceIdRegistry? signalIds,
  })  : _sessionStorage = sessionStorage ?? SessionStorage(),
        _deviceIdentity = deviceIdentity ?? DeviceIdentityService(),
        _e2eeApi = e2eeApi,
        _signalIds = signalIds ?? SignalDeviceIdRegistry();

  final SessionStorage _sessionStorage;
  final DeviceIdentityService _deviceIdentity;
  final E2eeApi? _e2eeApi;
  final SignalDeviceIdRegistry _signalIds;

  E2eeKeysRepository _keysRepo(String backendDeviceId) {
    if (_e2eeApi == null) {
      return GatewayE2eeKeysRepository();
    }
    return HttpE2eeKeysRepository(
      _e2eeApi!,
      backendDeviceId: backendDeviceId,
    );
  }

  Future<DeviceCryptoBootstrapResult> run({
    required String identityId,
    required String backendDeviceId,
  }) async {
    E2eeFoundation.requireInitialized();
    final signalDeviceId = await _signalIds.resolve(backendDeviceId);
    await _sessionStorage.saveSignalDeviceId(signalDeviceId);

    final handle = await _deviceIdentity.openOrCreateDevice(
      userIdentityId: identityId,
      deviceId: signalDeviceId,
    );
    final bundle = await _deviceIdentity.prepareUploadBundle(handle);
    final keysRepo = _keysRepo(backendDeviceId);
    final publish = await keysRepo.publishDeviceBundle(bundle);

    await _sessionStorage.setCryptoReady(true);
    await _sessionStorage.setKeysPublished(publish.isSuccess);

    return DeviceCryptoBootstrapResult(
      localReady: true,
      publishResult: publish,
    );
  }

  Future<DeviceCryptoBootstrapResult> retryPublish({
    required String identityId,
    required String backendDeviceId,
  }) async {
    final signalDeviceId =
        await _sessionStorage.readSignalDeviceId() ??
        await _signalIds.resolve(backendDeviceId);
    final handle = await _deviceIdentity.openOrCreateDevice(
      userIdentityId: identityId,
      deviceId: signalDeviceId,
    );
    final bundle = await _deviceIdentity.prepareUploadBundle(handle);
    final publish = await _keysRepo(backendDeviceId).publishDeviceBundle(bundle);
    await _sessionStorage.setKeysPublished(publish.isSuccess);
    return DeviceCryptoBootstrapResult(
      localReady: true,
      publishResult: publish,
    );
  }
}
