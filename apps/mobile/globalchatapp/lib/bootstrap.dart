import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'app/app.dart';
import 'core/firebase/firebase_initializer.dart';
import 'core/firebase/firebase_messaging_service.dart';
import 'core/notifications/local_notification_service.dart';

Future<void> bootstrap() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FirebaseInitializer.initialize();
  await LocalNotificationService().initialize();
  try {
    final token = await FirebaseMessagingService(FirebaseMessaging.instance)
        .initialize();
    if (token != null) {
      debugPrint('FCM token obtained');
    }
  } catch (error) {
    debugPrint('FCM initialization failed: $error');
  }
  runApp(const ProviderScope(child: GlobalChatApp()));
}
