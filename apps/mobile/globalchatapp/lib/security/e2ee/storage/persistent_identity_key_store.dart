import 'dart:math';
import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import 'e2ee_storage_keys.dart';
import 'secure_blob_store.dart';

/// Own identity + remote identity keys, persisted in secure storage.
class PersistentIdentityKeyStore implements IdentityKeyStore {
  PersistentIdentityKeyStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
    required IdentityKeyPair identityKeyPair,
    required int localRegistrationId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId,
        _identityKeyPair = identityKeyPair,
        _localRegistrationId = localRegistrationId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;
  final IdentityKeyPair _identityKeyPair;
  final int _localRegistrationId;

  static Future<PersistentIdentityKeyStore> loadOrCreate({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  }) async {
    final pairKey =
        E2eeStorageKeys.localIdentityKeyPair(userIdentityId, localDeviceId);
    final regKey =
        E2eeStorageKeys.localRegistrationId(userIdentityId, localDeviceId);

    final pairBytes = await blobs.readBytes(pairKey);
    final regBytes = await blobs.readBytes(regKey);

    if (pairBytes != null && regBytes != null) {
      final pair = IdentityKeyPair.deserialize(bytes: pairBytes.toList());
      final regId = _readRegistrationId(regBytes);
      return PersistentIdentityKeyStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: localDeviceId,
        identityKeyPair: pair,
        localRegistrationId: regId,
      );
    }

    final pair = IdentityKeyPair.generate();
    final regId = _generateRegistrationId();
    await blobs.writeBytes(pairKey, pair.serialize());
    await blobs.writeBytes(regKey, _writeRegistrationId(regId));
    return PersistentIdentityKeyStore(
      blobs: blobs,
      userIdentityId: userIdentityId,
      localDeviceId: localDeviceId,
      identityKeyPair: pair,
      localRegistrationId: regId,
    );
  }

  /// libsignal registration ids are 14-bit non-zero values (1–16383).
  static int _generateRegistrationId() {
    final random = Random.secure();
    return random.nextInt(16383) + 1;
  }

  static Uint8List _writeRegistrationId(int id) =>
      Uint8List.fromList([id >> 24, id >> 16, id >> 8, id & 0xff]);

  static int _readRegistrationId(Uint8List bytes) {
    if (bytes.length < 4) return 1;
    return (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3];
  }

  String _remoteKey(ProtocolAddress address) =>
      E2eeStorageKeys.remoteIdentity(
        _userIdentityId,
        _localDeviceId,
        address.name(),
        address.deviceId(),
      );

  @override
  Future<IdentityKeyPair> getIdentityKeyPair() async => _identityKeyPair;

  @override
  Future<int> getLocalRegistrationId() async => _localRegistrationId;

  @override
  Future<bool> saveIdentity(
    ProtocolAddress address,
    PublicKey identityKey,
  ) async {
    final key = _remoteKey(address);
    final existingBytes = await _blobs.readBytes(key);
    final serialized = Uint8List.fromList(identityKey.serialize());

    if (existingBytes == null) {
      await _blobs.writeBytes(key, serialized);
      return true;
    }

    final existing = PublicKey.deserialize(bytes: existingBytes.toList());
    if (!existing.equals(other: identityKey)) {
      await _blobs.writeBytes(key, serialized);
      return true;
    }
    return false;
  }

  @override
  Future<PublicKey?> getIdentity(ProtocolAddress address) async {
    final data = await _blobs.readBytes(_remoteKey(address));
    if (data == null) return null;
    return PublicKey.deserialize(bytes: data.toList());
  }

  @override
  Future<bool> isTrustedIdentity(
    ProtocolAddress address,
    PublicKey identityKey,
    Direction direction,
  ) async {
    final existing = await getIdentity(address);
    if (existing == null) {
      return direction == Direction.receiving;
    }
    return existing.equals(other: identityKey);
  }
}
