import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/security/app_secure_storage.dart';

/// Maps Identity service device UUID → libsignal device id (1–127).
class SignalDeviceIdRegistry {
  SignalDeviceIdRegistry({FlutterSecureStorage? storage})
      : _storage = storage ?? createAppSecureStorage();

  final FlutterSecureStorage _storage;
  static const _key = 'gc_auth/signal_device_map';

  Future<int> resolve(String backendDeviceUuid) async {
    final map = await _readMap();
    final existing = map[backendDeviceUuid];
    if (existing != null) return existing;

    final used = map.values.toSet();
    for (var id = 1; id <= 127; id++) {
      if (!used.contains(id)) {
        map[backendDeviceUuid] = id;
        await _writeMap(map);
        return id;
      }
    }
    throw StateError('No libsignal device ids available for this identity');
  }

  Future<Map<String, int>> _readMap() async {
    final raw = await _storage.read(key: _key);
    if (raw == null) return {};
    final decoded = jsonDecode(raw);
    if (decoded is! Map) return {};
    return decoded.map(
      (k, v) => MapEntry(k.toString(), (v as num).toInt()),
    );
  }

  Future<void> _writeMap(Map<String, int> map) async {
    await _storage.write(key: _key, value: jsonEncode(map));
  }
}
