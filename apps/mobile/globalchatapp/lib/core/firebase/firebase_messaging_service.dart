import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';

@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {}

class FirebaseMessagingService {
  FirebaseMessagingService(this.messaging);
  final FirebaseMessaging messaging;

  StreamSubscription<String>? _tokenRefreshSubscription;
  StreamSubscription<RemoteMessage>? _foregroundSubscription;
  StreamSubscription<RemoteMessage>? _openedSubscription;

  Future<String?> initialize() async {
    await messaging.requestPermission();
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);
    _tokenRefreshSubscription ??= tokenRefresh.listen((_) {});
    _foregroundSubscription ??= foreground.listen((_) {});
    _openedSubscription ??= opened.listen((_) {});
    await initialMessage();
    return messaging.getToken();
  }

  Stream<String> get tokenRefresh => messaging.onTokenRefresh;
  Stream<RemoteMessage> get foreground => FirebaseMessaging.onMessage;
  Stream<RemoteMessage> get opened => FirebaseMessaging.onMessageOpenedApp;
  Future<RemoteMessage?> initialMessage() =>
      FirebaseMessaging.instance.getInitialMessage();
}
