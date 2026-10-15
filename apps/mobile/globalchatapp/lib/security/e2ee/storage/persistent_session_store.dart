import 'package:libsignal/libsignal.dart';

import 'e2ee_storage_keys.dart';
import 'string_list_codec.dart';
import 'secure_blob_store.dart';

/// Durable [SessionStore] backed by [FlutterSecureStorage].
class PersistentSessionStore implements SessionStore {
  PersistentSessionStore({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int localDeviceId,
  })  : _blobs = blobs,
        _userIdentityId = userIdentityId,
        _localDeviceId = localDeviceId;

  final SecureBlobStore _blobs;
  final String _userIdentityId;
  final int _localDeviceId;

  String _sessionKey(ProtocolAddress address) => E2eeStorageKeys.sessionRecord(
        _userIdentityId,
        _localDeviceId,
        address.name(),
        address.deviceId(),
      );

  Future<List<String>> _loadIndex() async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.sessionIndex(_userIdentityId, _localDeviceId),
    );
    if (raw == null) return [];
    return StringListCodec.decode(raw);
  }

  Future<void> _saveIndex(List<String> keys) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.sessionIndex(_userIdentityId, _localDeviceId),
      StringListCodec.encode(keys),
    );
    _sessionKeyCache
      ..clear()
      ..addAll(keys);
  }

  final Set<String> _sessionKeyCache = {};

  Future<Set<String>> _sessionKeys() async {
    if (_sessionKeyCache.isNotEmpty) return _sessionKeyCache;
    final index = await _loadIndex();
    _sessionKeyCache.addAll(index);
    return _sessionKeyCache;
  }

  @override
  Future<SessionRecord?> loadSession(ProtocolAddress address) async {
    final data = await _blobs.readBytes(_sessionKey(address));
    if (data == null) return null;
    return SessionRecord.deserialize(bytes: data.toList());
  }

  @override
  Future<void> storeSession(
    ProtocolAddress address,
    SessionRecord record,
  ) async {
    final key = _sessionKey(address);
    await _blobs.writeBytes(key, record.serialize());
    final keys = await _sessionKeys();
    if (!keys.contains(key)) {
      keys.add(key);
      await _saveIndex(keys.toList());
    }
  }

  @override
  Future<bool> containsSession(ProtocolAddress address) async {
    return await _blobs.containsKey(_sessionKey(address));
  }

  @override
  Future<void> deleteSession(ProtocolAddress address) async {
    final key = _sessionKey(address);
    await _blobs.delete(key);
    final keys = await _sessionKeys();
    keys.remove(key);
    await _saveIndex(keys.toList());
  }

  @override
  Future<void> deleteAllSessions(String name) async {
    final keys = await _sessionKeys();
    for (final key in keys.toList()) {
      if (key.contains('/sessions/$name:')) {
        await _blobs.delete(key);
        keys.remove(key);
      }
    }
    await _saveIndex(keys.toList());
  }

  @override
  Future<List<int>> getSubDeviceSessions(String name) async {
    final keys = await _sessionKeys();
    final needle = '/sessions/$name:';
    final deviceIds = <int>[];
    for (final key in keys) {
      final idx = key.indexOf(needle);
      if (idx == -1) continue;
      final suffix = key.substring(idx + needle.length);
      deviceIds.add(int.parse(suffix));
    }
    return deviceIds;
  }
}
