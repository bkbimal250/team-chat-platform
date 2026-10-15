import '../../../services/api/e2ee/e2ee_api.dart';
import '../../../services/api/models/e2ee_models.dart';
import '../models/device_public_key_bundle.dart';
import 'e2ee_keys_repository.dart';

class HttpE2eeKeysRepository implements E2eeKeysRepository {
  HttpE2eeKeysRepository(this._api, {required this.backendDeviceId});

  final E2eeApi _api;
  final String backendDeviceId;

  @override
  Future<E2eePublishResult> publishDeviceBundle(
    DevicePublicKeyBundle bundle,
  ) async {
    try {
      await _api.uploadDeviceKeys(
        backendDeviceId: backendDeviceId,
        bundle: bundle,
      );
      return const E2eePublishResult(status: E2eePublishStatus.published);
    } catch (e) {
      return E2eePublishResult(
        status: E2eePublishStatus.failed,
        message: e.toString(),
      );
    }
  }

  @override
  Future<E2eePublishResult> replenishOneTimePreKeys(
    DevicePublicKeyBundle partialBundle,
  ) async {
    try {
      await _api.replenishPreKeys(
        backendDeviceId: backendDeviceId,
        keys: partialBundle.oneTimePreKeys,
      );
      return const E2eePublishResult(status: E2eePublishStatus.published);
    } catch (e) {
      return E2eePublishResult(
        status: E2eePublishStatus.failed,
        message: e.toString(),
      );
    }
  }

  Future<List<PublicDeviceE2eeDto>> listDevices(String identityId) =>
      _api.listUserDevices(identityId);

  Future<PreKeyBundleDto> fetchBundle({
    required String identityId,
    required String deviceId,
  }) =>
      _api.fetchPreKeyBundle(identityId: identityId, deviceId: deviceId);
}
