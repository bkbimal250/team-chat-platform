import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../config/app_config.dart';
import '../api/providers/api_providers.dart';
import '../auth/session_storage.dart';

typedef RealtimeEventHandler = void Function(Map<String, dynamic> frame);

class RealtimeClient {
  RealtimeClient({required SessionStorage sessionStorage})
      : _sessionStorage = sessionStorage;

  final SessionStorage _sessionStorage;
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  final _handlers = <RealtimeEventHandler>[];
  final _subscriptions = <String>{};
  Timer? _pingTimer;
  bool _connecting = false;

  void addListener(RealtimeEventHandler handler) => _handlers.add(handler);

  void removeListener(RealtimeEventHandler handler) => _handlers.remove(handler);

  Future<void> connect() async {
    if (_channel != null || _connecting) return;
    _connecting = true;
    final token = await _sessionStorage.readAccessToken();
    if (token == null) {
      _connecting = false;
      return;
    }
    final uri = Uri.parse(
      '${AppConfig.realtimeWssUrl}?token=${Uri.encodeQueryComponent(token)}',
    );
    _channel = WebSocketChannel.connect(uri);
    _subscription = _channel!.stream.listen(
      _onData,
      onDone: _scheduleReconnect,
      onError: (_) => _scheduleReconnect(),
      cancelOnError: true,
    );
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      _send({'version': 1, 'type': 'ping'});
    });
    _connecting = false;
  }

  void _scheduleReconnect() {
    _teardownChannel();
    Future.delayed(const Duration(seconds: 2), connect);
  }

  void _teardownChannel() {
    _subscription?.cancel();
    _subscription = null;
    _channel?.sink.close();
    _channel = null;
  }

  void _onData(dynamic data) {
    try {
      final frame = jsonDecode(data as String) as Map<String, dynamic>;
      final type = frame['type'] as String?;
      if (type == 'connection.ready.v1') {
        for (final id in _subscriptions) {
          subscribe(id);
        }
      } else if (type == 'connection.resync_required.v1') {
        for (final handler in List.of(_handlers)) {
          handler({'type': 'resync_required'});
        }
      } else {
        for (final handler in List.of(_handlers)) {
          handler(frame);
        }
      }
    } catch (_) {
      // Ignore malformed frames — never log payload contents.
    }
  }

  void _send(Map<String, dynamic> frame) {
    final channel = _channel;
    if (channel == null) return;
    try {
      channel.sink.add(jsonEncode(frame));
    } catch (_) {}
  }

  void subscribe(String conversationId) {
    _subscriptions.add(conversationId);
    _send({
      'version': 1,
      'type': 'subscribe',
      'conversation_id': conversationId,
    });
  }

  void unsubscribe(String conversationId) {
    _subscriptions.remove(conversationId);
    _send({
      'version': 1,
      'type': 'unsubscribe',
      'conversation_id': conversationId,
    });
  }

  void sendSenderKeyDistribution({
    required String conversationId,
    required String distributionId,
    required int messageType,
    required String ciphertextB64,
    String? targetDeviceId,
  }) {
    _send({
      'version': 1,
      'type': 'e2ee.sender_key_distribution',
      'conversation_id': conversationId,
      'distribution_id': distributionId,
      'message_type': messageType,
      'ciphertext': ciphertextB64,
      if (targetDeviceId != null) 'target_device_id': targetDeviceId,
    });
  }

  void typing(String conversationId, bool active) {
    _send({
      'version': 1,
      'type': active ? 'typing.start' : 'typing.stop',
      'conversation_id': conversationId,
    });
  }

  Future<void> disconnect() async {
    _pingTimer?.cancel();
    _pingTimer = null;
    _subscriptions.clear();
    _teardownChannel();
  }
}

final realtimeClientProvider = Provider<RealtimeClient>((ref) {
  final client = RealtimeClient(sessionStorage: ref.watch(sessionStorageProvider));
  ref.onDispose(() => client.disconnect());
  return client;
});
