import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Shared [FlutterSecureStorage] options (sessions + E2EE blobs).
FlutterSecureStorage createAppSecureStorage() {
  if (!kIsWeb && Platform.isAndroid) {
    return const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
      ),
    );
  }
  return const FlutterSecureStorage();
}
