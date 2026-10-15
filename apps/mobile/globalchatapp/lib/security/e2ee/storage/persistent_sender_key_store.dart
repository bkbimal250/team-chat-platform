import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import 'e2ee_storage_keys.dart';
import 'string_list_codec.dart';
import 'secure_blob_store.dart';

class PersistentSenderKeyStore implements SenderKeyStore {
  PersistentSenderKeyStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;

  String _recordKey(SenderKeyName name) {
    final addr = name.sender;
    return E2eeStorageKeys.senderKeyRecord(
      _userIdentityId,
      _localDeviceId,
      addr.name(),
      addr.deviceId(),
      name.distributionId,
    );
  }

  Future<List<String>> _index() async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.senderKeyIndex(_userIdentityId, _localDeviceId),
    );
    if (raw == null) return [];
    return StringListCodec.decode(raw);
  }

  Future<void> _writeIndex(List<String> keys) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.senderKeyIndex(_userIdentityId, _localDeviceId),
      StringListCodec.encode(keys),
    );
  }

  @override
  Future<Uint8List?> loadSenderKey(SenderKeyName senderKeyName) async {
    return await _blobs.readBytes(_recordKey(senderKeyName));
  }

  @override
  Future<void> storeSenderKey(
    SenderKeyName senderKeyName,
    Uint8List record,
  ) async {
    final key = _recordKey(senderKeyName);
    await _blobs.writeBytes(key, record);
    final keys = await _index();
    if (!keys.contains(key)) {
      keys.add(key);
      await _writeIndex(keys);
    }
  }
}
