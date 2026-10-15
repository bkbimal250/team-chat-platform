import 'package:libsignal/libsignal.dart';

import 'e2ee_storage_keys.dart';
import 'int_list_codec.dart';
import 'secure_blob_store.dart';

class PersistentPreKeyStore implements PreKeyStore {
  PersistentPreKeyStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;

  String _key(int id) =>
      E2eeStorageKeys.preKeyRecord(_userIdentityId, _localDeviceId, id);

  Future<List<int>> _index() async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.preKeyIndex(_userIdentityId, _localDeviceId),
    );
    if (raw == null) return [];
    return IntListCodec.decode(raw);
  }

  Future<void> _writeIndex(List<int> ids) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.preKeyIndex(_userIdentityId, _localDeviceId),
      IntListCodec.encode(ids),
    );
  }

  @override
  Future<PreKeyRecord?> loadPreKey(int preKeyId) async {
    final data = await _blobs.readBytes(_key(preKeyId));
    if (data == null) return null;
    return PreKeyRecord.deserialize(bytes: data.toList());
  }

  @override
  Future<void> storePreKey(int preKeyId, PreKeyRecord record) async {
    await _blobs.writeBytes(_key(preKeyId), record.serialize());
    final ids = await _index();
    if (!ids.contains(preKeyId)) {
      ids.add(preKeyId);
      await _writeIndex(ids);
    }
  }

  @override
  Future<bool> containsPreKey(int preKeyId) async =>
      await _blobs.containsKey(_key(preKeyId));

  @override
  Future<void> removePreKey(int preKeyId) async {
    await _blobs.delete(_key(preKeyId));
    final ids = await _index();
    ids.remove(preKeyId);
    await _writeIndex(ids);
  }

  @override
  Future<List<int>> getAllPreKeyIds() async => await _index();
}

class PersistentSignedPreKeyStore implements SignedPreKeyStore {
  PersistentSignedPreKeyStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;

  String _key(int id) => E2eeStorageKeys.signedPreKeyRecord(
        _userIdentityId,
        _localDeviceId,
        id,
      );

  Future<List<int>> _index() async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.signedPreKeyIndex(_userIdentityId, _localDeviceId),
    );
    if (raw == null) return [];
    return IntListCodec.decode(raw);
  }

  Future<void> _writeIndex(List<int> ids) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.signedPreKeyIndex(_userIdentityId, _localDeviceId),
      IntListCodec.encode(ids),
    );
  }

  @override
  Future<SignedPreKeyRecord?> loadSignedPreKey(int signedPreKeyId) async {
    final data = await _blobs.readBytes(_key(signedPreKeyId));
    if (data == null) return null;
    return SignedPreKeyRecord.deserialize(bytes: data.toList());
  }

  @override
  Future<void> storeSignedPreKey(
    int signedPreKeyId,
    SignedPreKeyRecord record,
  ) async {
    await _blobs.writeBytes(_key(signedPreKeyId), record.serialize());
    final ids = await _index();
    if (!ids.contains(signedPreKeyId)) {
      ids.add(signedPreKeyId);
      await _writeIndex(ids);
    }
  }

  @override
  Future<bool> containsSignedPreKey(int signedPreKeyId) async =>
      await _blobs.containsKey(_key(signedPreKeyId));

  @override
  Future<void> removeSignedPreKey(int signedPreKeyId) async {
    await _blobs.delete(_key(signedPreKeyId));
    final ids = await _index();
    ids.remove(signedPreKeyId);
    await _writeIndex(ids);
  }

  @override
  Future<List<int>> getAllSignedPreKeyIds() async => await _index();
}

class PersistentKyberPreKeyStore implements KyberPreKeyStore {
  PersistentKyberPreKeyStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;

  String _key(int id) => E2eeStorageKeys.kyberPreKeyRecord(
        _userIdentityId,
        _localDeviceId,
        id,
      );

  Future<List<int>> _index() async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.kyberPreKeyIndex(_userIdentityId, _localDeviceId),
    );
    if (raw == null) return [];
    return IntListCodec.decode(raw);
  }

  Future<void> _writeIndex(List<int> ids) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.kyberPreKeyIndex(_userIdentityId, _localDeviceId),
      IntListCodec.encode(ids),
    );
  }

  @override
  Future<KyberPreKeyRecord?> loadKyberPreKey(int kyberPreKeyId) async {
    final data = await _blobs.readBytes(_key(kyberPreKeyId));
    if (data == null) return null;
    return KyberPreKeyRecord.deserialize(bytes: data.toList());
  }

  @override
  Future<void> storeKyberPreKey(
    int kyberPreKeyId,
    KyberPreKeyRecord record,
  ) async {
    await _blobs.writeBytes(_key(kyberPreKeyId), record.serialize());
    final ids = await _index();
    if (!ids.contains(kyberPreKeyId)) {
      ids.add(kyberPreKeyId);
      await _writeIndex(ids);
    }
  }

  @override
  Future<bool> containsKyberPreKey(int kyberPreKeyId) async =>
      await _blobs.containsKey(_key(kyberPreKeyId));

  final Set<int> _usedOneTimeKyberIds = {};

  @override
  Future<void> markKyberPreKeyUsed(
    int kyberPreKeyId,
    int signedPreKeyId,
    PublicKey baseKey,
  ) async {
    _usedOneTimeKyberIds.add(kyberPreKeyId);
    await removeKyberPreKey(kyberPreKeyId);
  }

  @override
  Future<void> removeKyberPreKey(int kyberPreKeyId) async {
    await _blobs.delete(_key(kyberPreKeyId));
    final ids = await _index();
    ids.remove(kyberPreKeyId);
    await _writeIndex(ids);
  }

  @override
  Future<List<int>> getAllKyberPreKeyIds() async => await _index();
}
