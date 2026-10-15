import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/security/app_secure_storage.dart';
import '../exceptions/e2ee_exception.dart';

/// Low-level secure key–value storage for serialized cryptographic records.
///
/// Values are base64-encoded bytes. Keys must never appear in logs.
class SecureBlobStore {
  SecureBlobStore({FlutterSecureStorage? storage})
      : _storage = storage ?? createAppSecureStorage();

  final FlutterSecureStorage _storage;

  Future<Uint8List?> readBytes(String key) async {
    try {
      final encoded = await _storage.read(key: key);
      if (encoded == null) return null;
      return base64Decode(encoded);
    } catch (_) {
      throw const E2eeStorageException();
    }
  }

  Future<void> writeBytes(String key, Uint8List value) async {
    try {
      await _storage.write(key: key, value: base64Encode(value));
    } catch (_) {
      throw const E2eeStorageException();
    }
  }

  Future<void> delete(String key) async {
    try {
      await _storage.delete(key: key);
    } catch (_) {
      throw const E2eeStorageException();
    }
  }

  Future<bool> containsKey(String key) async {
    try {
      return await _storage.containsKey(key: key);
    } catch (_) {
      throw const E2eeStorageException();
    }
  }

  Future<void> deleteAllWithPrefix(String prefix) async {
    try {
      final all = await _storage.readAll();
      for (final key in all.keys) {
        if (key.startsWith(prefix)) {
          await _storage.delete(key: key);
        }
      }
    } catch (_) {
      throw const E2eeStorageException();
    }
  }
}
