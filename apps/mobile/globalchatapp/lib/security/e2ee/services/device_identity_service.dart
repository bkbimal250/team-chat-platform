import '../models/device_public_key_bundle.dart';
import '../models/local_device_crypto_handle.dart';
import '../protocol/e2ee_protocol.dart';
import 'e2ee_foundation.dart';

/// Registers or opens cryptographic state for this physical device.
///
/// Each device gets its own identity keys; keys are never copied from another
/// device installation.
class DeviceIdentityService {
  DeviceIdentityService({E2eeProtocol? protocol})
      : _protocol = protocol ?? E2eeFoundation.protocol;

  final E2eeProtocol _protocol;

  Future<LocalDeviceCryptoHandle> openOrCreateDevice({
    required String userIdentityId,
    required int deviceId,
  }) async {
    E2eeFoundation.requireInitialized();
    return _protocol.openDevice(
      userIdentityId: userIdentityId,
      deviceId: deviceId,
    );
  }

  Future<DevicePublicKeyBundle> prepareUploadBundle(
    LocalDeviceCryptoHandle device,
  ) =>
      _protocol.ensurePreKeys(device: device);
}
