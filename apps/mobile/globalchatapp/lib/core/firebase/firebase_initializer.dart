import 'package:firebase_core/firebase_core.dart';

class FirebaseInitializer {
  static bool _initialized = false;
  static Future<void> initialize() async {
    if (_initialized) return;
    try {
      await Firebase.initializeApp();
      _initialized = true;
    } catch (_) {}
  }
}
