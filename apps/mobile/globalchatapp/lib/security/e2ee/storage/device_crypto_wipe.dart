import 'e2ee_storage_keys.dart';
import 'secure_blob_store.dart';

/// Removes all cryptographic material for a device (logout / device removal).
class DeviceCryptoWipe {
  DeviceCryptoWipe(this._blobs);

  final SecureBlobStore _blobs;

  Future<void> wipeDevice({
    required String userIdentityId,
    required int localDeviceId,
  }) async {
    await _blobs.deleteAllWithPrefix(
      E2eeStorageKeys.devicePrefix(userIdentityId, localDeviceId),
    );
  }
}
