import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import '../storage/e2ee_storage_keys.dart';
import '../storage/secure_blob_store.dart';

/// Safety numbers, explicit verification, and key-change handling hooks.
class IdentityTrustService {
  IdentityTrustService({SecureBlobStore? blobs})
      : _blobs = blobs ?? SecureBlobStore();

  final SecureBlobStore _blobs;

  Future<bool> isExplicitlyVerified({
    required LocalDeviceCryptoHandle device,
    required E2eeProtocolAddress remote,
  }) async {
    final key = E2eeStorageKeys.remoteIdentityVerified(
      device.userIdentityId,
      device.deviceId,
      remote.userIdentityId,
      remote.deviceId,
    );
    final value = await _blobs.readBytes(key);
    return value != null && value.isNotEmpty;
  }

  Future<void> markVerified({
    required LocalDeviceCryptoHandle device,
    required E2eeProtocolAddress remote,
  }) async {
    final key = E2eeStorageKeys.remoteIdentityVerified(
      device.userIdentityId,
      device.deviceId,
      remote.userIdentityId,
      remote.deviceId,
    );
    await _blobs.writeBytes(key, Uint8List.fromList([1]));
  }

  /// Returns true when the stored remote identity differs from [candidate].
  Future<bool> detectIdentityChange({
    required LocalDeviceCryptoHandle device,
    required E2eeProtocolAddress remote,
    required PublicKey candidate,
  }) async {
    final stored =
        await device.identityKeyStore.getIdentity(remote.toLibsignal());
    if (stored == null) return false;
    return !stored.equals(other: candidate);
  }
}
