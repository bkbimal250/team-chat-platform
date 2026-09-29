import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class LocalNotificationService {
  static const channelId = 'globalchat_messages';
  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  Future<void> initialize() async {
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      ),
    );
    await _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(
          const AndroidNotificationChannel(
            channelId,
            'Chat Messages',
            description: 'New GlobalChat messages',
            importance: Importance.high,
          ),
        );
  }
}
