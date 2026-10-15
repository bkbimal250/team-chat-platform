import 'dart:async';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../security/e2ee/services/device_identity_service.dart';
import '../../../services/api/messaging/messaging_models.dart';
import '../../../services/api/providers/api_providers.dart';
import '../../../services/auth/session_storage.dart';
import '../../../services/devices/signal_device_id.dart';
import '../../../services/realtime/realtime_client.dart';
import '../../auth/application/auth_controller.dart';
import '../../messages/domain/message.dart';
import 'encrypted_messaging_service.dart';

class ChatState {
  const ChatState({
    this.loading = true,
    this.title = 'Chat',
    this.isGroup = false,
    this.messages = const [],
    this.error,
    this.sending = false,
    this.conversationId,
    this.typingMemberIds = const {},
    this.actionInProgress = false,
    this.connected = false,
  });

  final bool loading;
  final String title;
  final bool isGroup;
  final List<ChatMessage> messages;
  final String? error;
  final bool sending;
  final String? conversationId;
  final Set<String> typingMemberIds;
  final bool actionInProgress;
  final bool connected;

  int get maxSequence => messages.fold<int>(
        0,
        (a, m) => m.sequence > a ? m.sequence : a,
      );
}

class ChatController extends Notifier<ChatState> {
  RealtimeEventHandler? _realtimeHandler;
  Timer? _typingTimer;

  @override
  ChatState build() {
    ref.onDispose(_detachRealtime);
    return const ChatState(loading: false);
  }

  EncryptedMessagingService get _messaging => EncryptedMessagingService(
        messaging: ref.read(messagingApiProvider),
        conversations: ref.read(conversationsApiProvider),
        e2eeApi: ref.read(e2eeApiProvider),
        sessionStorage: ref.read(sessionStorageProvider),
        deviceIdentity: DeviceIdentityService(),
        signalIds: SignalDeviceIdRegistry(),
        mediaApi: ref.read(mediaApiProvider),
      );

  void mount(String conversationId) {
    if (state.conversationId == conversationId &&
        state.messages.isNotEmpty &&
        !state.loading) {
      return;
    }
    _detachRealtime();
    state = ChatState(loading: true, conversationId: conversationId);
    _bootstrap(conversationId);
  }

  void _attachRealtime(String conversationId) {
    final realtime = ref.read(realtimeClientProvider);
    _realtimeHandler = (frame) => onRealtimeFrame(frame);
    realtime.addListener(_realtimeHandler!);
    realtime.subscribe(conversationId);
  }

  void _detachRealtime() {
    final id = state.conversationId;
    final handler = _realtimeHandler;
    if (handler != null) {
      ref.read(realtimeClientProvider).removeListener(handler);
      _realtimeHandler = null;
    }
    if (id != null) {
      ref.read(realtimeClientProvider).unsubscribe(id);
    }
    _typingTimer?.cancel();
    _typingTimer = null;
  }

  Future<void> _bootstrap(String conversationId) async {
    final auth = ref.read(authControllerProvider);
    final user = auth.user;
    if (user == null) return;
    try {
      final conversation =
          await ref.read(conversationsApiProvider).getConversation(conversationId);
      final history = await ref.read(messagingApiProvider).history(
            conversationId: conversationId,
          );
      final messages = await _mapHistory(history, user.identityId, user.memberId);
      final realtime = ref.read(realtimeClientProvider);
      await realtime.connect();
      _attachRealtime(conversationId);
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        title: conversation.listTitle,
        isGroup: conversation.isGroup,
        messages: messages,
        connected: true,
      );
      await _markRead(conversationId, state.maxSequence);
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        error: 'Could not load conversation.',
      );
    }
  }

  Future<List<ChatMessage>> _mapHistory(
    List<MessageDto> history,
    String identityId,
    String? memberId,
  ) async {
    final messages = <ChatMessage>[];
    for (final dto in history) {
      final decrypted = await _messaging.decryptMessage(
        dto: dto,
        identityId: identityId,
      );
      messages.add(
        _messaging.toChatMessage(
          dto: dto,
          identityId: identityId,
          memberId: memberId,
          decrypted: decrypted,
        ),
      );
    }
    return messages;
  }

  Future<void> refresh() async {
    final id = state.conversationId;
    if (id == null) return;
    try {
      final user = ref.read(authControllerProvider).user;
      if (user == null) return;
      final history = await ref.read(messagingApiProvider).history(
            conversationId: id,
          );
      final messages =
          await _mapHistory(history, user.identityId, user.memberId);
      state = ChatState(
        loading: false,
        conversationId: id,
        title: state.title,
        isGroup: state.isGroup,
        messages: messages,
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: id,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Could not refresh messages.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> onRealtimeFrame(Map<String, dynamic> frame) async {
    final type = frame['type'] as String?;
    final payload = frame['payload'];
    final map = payload is Map<String, dynamic> ? payload : null;
    final conversationId = map?['conversation_id'] as String?;

    if (type == 'connection.resync_required.v1' || type == 'resync_required') {
      await refresh();
      return;
    }

    if (conversationId != null && conversationId != state.conversationId) {
      return;
    }

    if (type == 'typing.updated.v1' && map != null) {
      final memberId = map['member_id'] as String?;
      final active = map['active'] as bool? ?? false;
      if (memberId == null) return;
      final typing = {...state.typingMemberIds};
      if (active) {
        typing.add(memberId);
      } else {
        typing.remove(memberId);
      }
      state = ChatState(
        loading: state.loading,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        typingMemberIds: typing,
        connected: state.connected,
      );
      return;
    }

    if (type == 'e2ee.sender_key_distribution.v1' && map != null) {
      final user = ref.read(authControllerProvider).user;
      final session = await ref.read(sessionStorageProvider).readSession();
      if (user == null || session == null) return;
      try {
        await _messaging.handleSenderKeyRealtime(
          identityId: user.identityId,
          payload: map,
          localBackendDeviceId: session.deviceId,
        );
      } catch (_) {
        // Distribution may arrive before message; history refresh retries decrypt.
      }
      return;
    }

    if (type == 'message.read.v1' && map != null) {
      final seq = (map['sequence'] as num?)?.toInt();
      if (seq != null) _applyReadReceipts(seq);
      return;
    }

    if (type == 'message.delivered.v1' && map != null) {
      final seq = (map['sequence'] as num?)?.toInt();
      if (seq != null) _applyDeliveredReceipts(seq);
      return;
    }

    if (type != null && type.startsWith('message.')) {
      await refresh();
      final seq = (map?['sequence'] as num?)?.toInt();
      if (seq != null && type == 'message.created.v1') {
        await _markDelivered(conversationId!, seq);
        await _markRead(conversationId, seq);
      }
    }
  }

  void _applyReadReceipts(int sequence) {
    state = ChatState(
      loading: state.loading,
      conversationId: state.conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: [
        for (final m in state.messages)
          if (m.isMine && m.sequence <= sequence && m.sequence > 0)
            m.copyWith(status: MessageStatus.read)
          else
            m,
      ],
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
  }

  void _applyDeliveredReceipts(int sequence) {
    state = ChatState(
      loading: state.loading,
      conversationId: state.conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: [
        for (final m in state.messages)
          if (m.isMine &&
              m.sequence <= sequence &&
              m.sequence > 0 &&
              m.status != MessageStatus.read)
            m.copyWith(status: MessageStatus.delivered)
          else
            m,
      ],
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
  }

  void onComposerTextChanged(String text) {
    final id = state.conversationId;
    if (id == null) return;
    _typingTimer?.cancel();
    if (text.isEmpty) {
      ref.read(realtimeClientProvider).typing(id, false);
      return;
    }
    ref.read(realtimeClientProvider).typing(id, true);
    _typingTimer = Timer(const Duration(seconds: 4), () {
      ref.read(realtimeClientProvider).typing(id, false);
    });
  }

  Future<void> send(String text, {String? replyToId, String? replyPreview}) async {
    final conversationId = state.conversationId;
    if (conversationId == null) return;
    final trimmed = text.trim();
    if (trimmed.isEmpty || state.sending) return;
    final auth = ref.read(authControllerProvider).user;
    if (auth == null) return;
    final clientId = const Uuid().v4();
    await _sendOptimistic(
      clientId: clientId,
      conversationId: conversationId,
      text: trimmed,
      authMemberId: auth.memberId ?? auth.identityId,
      send: () => _messaging.sendText(
        conversationId: conversationId,
        identityId: auth.identityId,
        plaintext: trimmed,
        isGroup: state.isGroup,
        replyToMessageId: replyToId,
        replyPreview: replyPreview,
        clientMessageId: clientId,
      ),
      identityId: auth.identityId,
      memberId: auth.memberId,
    );
    ref.read(realtimeClientProvider).typing(conversationId, false);
  }

  Future<void> retrySend(ChatMessage failed) async {
    if (failed.status != MessageStatus.failed || failed.text == null) return;
    await send(failed.text!);
  }

  Future<void> sendAttachment({
    required Uint8List bytes,
    required String filename,
    required String mimeType,
    String? caption,
  }) async {
    final conversationId = state.conversationId;
    if (conversationId == null || state.sending) return;
    final auth = ref.read(authControllerProvider).user;
    if (auth == null) return;
    final clientId = const Uuid().v4();
    state = ChatState(
      loading: false,
      conversationId: conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: state.messages,
      sending: true,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    try {
      final dto = await _messaging.sendMedia(
        conversationId: conversationId,
        identityId: auth.identityId,
        isGroup: state.isGroup,
        filename: filename,
        contentType: mimeType,
        plaintextBytes: bytes,
        caption: caption,
        clientMessageId: clientId,
      );
      await _confirmMessage(dto, clientId, auth.identityId, auth.memberId);
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        sending: false,
        error: 'Attachment failed to send.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> editMessage(ChatMessage message, String newText) async {
    if (!message.isMine || message.decryptFailed) return;
    final auth = ref.read(authControllerProvider).user;
    final conversationId = state.conversationId;
    if (auth == null || conversationId == null) return;
    state = ChatState(
      loading: state.loading,
      conversationId: conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: state.messages,
      actionInProgress: true,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    try {
      final dto = await _messaging.editText(
        messageId: message.id,
        conversationId: conversationId,
        identityId: auth.identityId,
        isGroup: state.isGroup,
        plaintext: newText.trim(),
      );
      final decrypted = await _messaging.decryptMessage(
        dto: dto,
        identityId: auth.identityId,
      );
      final updated = _messaging.toChatMessage(
        dto: dto,
        identityId: auth.identityId,
        memberId: auth.memberId,
        decrypted: decrypted,
      );
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: [
          for (final m in state.messages)
            if (m.id == message.id) updated else m,
        ],
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Edit failed.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> deleteMessage(ChatMessage message) async {
    if (!message.isMine) return;
    state = ChatState(
      loading: state.loading,
      conversationId: state.conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: state.messages,
      actionInProgress: true,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    try {
      await ref.read(messagingApiProvider).deleteMessage(message.id);
      state = ChatState(
        loading: false,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: [
          for (final m in state.messages)
            if (m.id == message.id)
              m.copyWith(type: MessageType.deleted, text: null)
            else
              m,
        ],
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Delete failed.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> toggleReaction(ChatMessage message, String emoji) async {
    final auth = ref.read(authControllerProvider).user;
    if (auth == null) return;
    final existing = message.reactions
        .where((r) => r.emoji == emoji && r.currentUserReacted)
        .toList();
    try {
      if (existing.isNotEmpty) {
        await ref.read(messagingApiProvider).removeReaction(
              messageId: message.id,
              reaction: emoji,
            );
      } else {
        await ref.read(messagingApiProvider).addReaction(
              messageId: message.id,
              reaction: emoji,
            );
      }
      await refresh();
    } catch (_) {
      state = ChatState(
        loading: state.loading,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Reaction failed.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> trustSenderDevice({
    required String remoteIdentityId,
    required String backendDeviceId,
  }) async {
    final user = ref.read(authControllerProvider).user;
    if (user == null) return;
    state = ChatState(
      loading: state.loading,
      conversationId: state.conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: state.messages,
      actionInProgress: true,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    try {
      await _messaging.trustIdentity(
        localIdentityId: user.identityId,
        remoteIdentityId: remoteIdentityId,
        remoteBackendDeviceId: backendDeviceId,
      );
      await refresh();
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Could not verify identity.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<Uint8List?> downloadAttachment(ChatMessage message) async {
    final media = message.mediaPayload;
    if (media == null) return null;
    try {
      return await _messaging.downloadAndDecryptAttachment(
        mediaMeta: media,
        mediaApi: ref.read(mediaApiProvider),
      );
    } catch (_) {
      state = ChatState(
        loading: state.loading,
        conversationId: state.conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: state.messages,
        error: 'Could not download attachment.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
      return null;
    }
  }

  void _fanOutGroupSenderKeys(String conversationId, E2eeEnvelopeDto envelope) {
    if (!state.isGroup) return;
    final realtime = ref.read(realtimeClientProvider);
    _messaging.publishGroupSenderKeyDistribution(
      conversationId: conversationId,
      envelope: envelope,
      send: ({
        required String conversationId,
        required String distributionId,
        required int messageType,
        required String ciphertextB64,
        String? targetDeviceId,
      }) {
        realtime.sendSenderKeyDistribution(
          conversationId: conversationId,
          distributionId: distributionId,
          messageType: messageType,
          ciphertextB64: ciphertextB64,
          targetDeviceId: targetDeviceId,
        );
      },
    );
  }

  Future<void> _sendOptimistic({
    required String clientId,
    required String conversationId,
    required String text,
    required String authMemberId,
    required Future<MessageDto> Function() send,
    required String identityId,
    required String? memberId,
  }) async {
    final optimistic = ChatMessage(
      id: clientId,
      conversationId: conversationId,
      senderMemberId: authMemberId,
      type: MessageType.text,
      createdAt: DateTime.now(),
      isMine: true,
      text: text,
      status: MessageStatus.sending,
    );
    state = ChatState(
      loading: false,
      conversationId: conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: [...state.messages, optimistic],
      sending: true,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    try {
      final dto = await send();
      await _confirmMessage(dto, clientId, identityId, memberId);
    } catch (_) {
      state = ChatState(
        loading: false,
        conversationId: conversationId,
        title: state.title,
        isGroup: state.isGroup,
        messages: [
          for (final m in state.messages)
            if (m.id == clientId)
              m.copyWith(status: MessageStatus.failed)
            else
              m,
        ],
        sending: false,
        error: 'Message failed to send.',
        typingMemberIds: state.typingMemberIds,
        connected: state.connected,
      );
    }
  }

  Future<void> _confirmMessage(
    MessageDto dto,
    String clientId,
    String identityId,
    String? memberId,
  ) async {
    final decrypted = await _messaging.decryptMessage(
      dto: dto,
      identityId: identityId,
    );
    final confirmed = _messaging.toChatMessage(
      dto: dto,
      identityId: identityId,
      memberId: memberId,
      decrypted: decrypted,
      status: MessageStatus.sent,
    );
    state = ChatState(
      loading: false,
      conversationId: state.conversationId,
      title: state.title,
      isGroup: state.isGroup,
      messages: [
        for (final m in state.messages)
          if (m.id == clientId) confirmed else m,
      ],
      sending: false,
      typingMemberIds: state.typingMemberIds,
      connected: state.connected,
    );
    if (dto.e2ee != null) {
      _fanOutGroupSenderKeys(state.conversationId!, dto.e2ee!);
    }
    await _markDelivered(state.conversationId!, confirmed.sequence);
    await _markRead(state.conversationId!, confirmed.sequence);
  }

  Future<void> _markRead(String conversationId, int sequence) async {
    if (sequence <= 0) return;
    try {
      await ref.read(messagingApiProvider).markRead(
            conversationId: conversationId,
            sequence: sequence,
          );
    } catch (_) {}
  }

  Future<void> _markDelivered(String conversationId, int sequence) async {
    if (sequence <= 0) return;
    try {
      await ref.read(messagingApiProvider).markDelivered(
            conversationId: conversationId,
            sequence: sequence,
          );
    } catch (_) {}
  }
}

final chatControllerProvider =
    NotifierProvider.autoDispose<ChatController, ChatState>(ChatController.new);
