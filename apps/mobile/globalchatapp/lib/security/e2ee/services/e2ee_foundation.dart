import 'package:libsignal/libsignal.dart';

import '../exceptions/e2ee_exception.dart';
import '../protocol/libsignal_e2ee_protocol.dart';

/// One-time native library initialization (safe to call from [bootstrap]).
class E2eeFoundation {
  static bool _initialized = false;

  static Future<void> ensureInitialized() async {
    if (_initialized) return;
    await LibSignal.init();
    _initialized = true;
  }

  static void requireInitialized() {
    if (!_initialized) {
      throw const E2eeNotInitializedException();
    }
  }

  static final LibSignalE2eeProtocol protocol = LibSignalE2eeProtocol();
}
