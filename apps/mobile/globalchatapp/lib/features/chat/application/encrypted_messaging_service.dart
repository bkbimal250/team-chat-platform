import 'dart:typed_data';

import 'package:uuid/uuid.dart';

import '../../../security/e2ee/exceptions/e2ee_exception.dart';
import '../../../security/e2ee/models/local_device_crypto_handle.dart';
import '../../../security/e2ee/services/attachment_crypto_service.dart';
import '../../../security/e2ee/services/device_identity_service.dart';
import '../../../security/e2ee/services/e2ee_recipient_coordinator.dart';
import '../../../security/e2ee/services/e2ee_trust_guard.dart';
import '../../../security/e2ee/util/e2ee_message_codec.dart';
import '../../../services/api/conversations/conversations_api.dart';
import '../../../services/api/e2ee/e2ee_api.dart';
import '../../../services/api/media/media_api.dart';
import '../../../services/api/messaging/messaging_api.dart';
import '../../../services/api/messaging/messaging_models.dart';
import '../../../services/auth/session_storage.dart';
import '../../../services/devices/signal_device_id.dart';
import '../../media/encrypted_media_upload.dart';
import '../../messages/domain/message.dart';

class DecryptResult {
  const DecryptResult({
    required this.body,
    this.failed = false,
    this.trustWarning,
    this.payload,
  });

  final String body;
  final bool failed;
  final String? trustWarning;
  final E2eeMessagePayload? payload;
}

class EncryptedMessagingService {
  EncryptedMessagingService({
    required MessagingApi messaging,
    required ConversationsApi conversations,
    required E2eeApi e2eeApi,
    required SessionStorage sessionStorage,
    required DeviceIdentityService deviceIdentity,
    required SignalDeviceIdRegistry signalIds,
    MediaApi? mediaApi,
    E2eeRecipientCoordinator? coordinator,
    E2eeTrustGuard? trustGuard,
  })  : _messaging = messaging,
        _conversations = conversations,
        _e2eeApi = e2eeApi,
        _sessionStorage = sessionStorage,
        _deviceIdentity = deviceIdentity,
        _signalIds = signalIds,
        _backendDeviceId = '',
        _trust = trustGuard ?? E2eeTrustGuard(signalIds: signalIds),
        _coordinator = coordinator ??
            E2eeRecipientCoordinator(
              e2eeApi: e2eeApi,
              signalIds: signalIds,
              trustGuard: trustGuard,
            ),
        _mediaUpload = mediaApi != null
            ? EncryptedMediaUpload(mediaApi: mediaApi)
            : null;

  final MessagingApi _messaging;
  final ConversationsApi _conversations;
  final E2eeApi _e2eeApi;
  final SessionStorage _sessionStorage;
  final DeviceIdentityService _deviceIdentity;
  final SignalDeviceIdRegistry _signalIds;
  final E2eeRecipientCoordinator _coordinator;
  final E2eeTrustGuard _trust;
  final EncryptedMediaUpload? _mediaUpload;
  String _backendDeviceId;

  Future<LocalDeviceCryptoHandle> _localHandle(String identityId) async {
    final session = await _sessionStorage.readSession();
    final backendDeviceId = session?.deviceId ?? '';
    _backendDeviceId = backendDeviceId;
    final signalDeviceId =
        await _sessionStorage.readSignalDeviceId() ??
        await _signalIds.resolve(backendDeviceId);
    return _deviceIdentity.openOrCreateDevice(
      userIdentityId: identityId,
      deviceId: signalDeviceId,
    );
  }

  Future<List<({String identityId, String deviceId})>> _deviceTargets(
    String conversationId,
    String selfIdentityId,
    bool isGroup,
  ) async {
    final members = await _conversations.listMembers(conversationId);
    final targets = <({String identityId, String deviceId})>[];
    for (final member in members.where((m) => m.status == 'ACTIVE')) {
      final identity = member.userId ?? member.memberId;
      final devices = await _e2eeApi.listUserDevices(identity);
      for (final device in devices.where((d) => d.status == 'ACTIVE')) {
        targets.add((identityId: identity, deviceId: device.deviceId));
      }
    }
    if (!isGroup) {
      final selfDevices = await _e2eeApi.listUserDevices(selfIdentityId);
      for (final device in selfDevices.where((d) => d.status == 'ACTIVE')) {
        targets.add((identityId: selfIdentityId, deviceId: device.deviceId));
      }
    }
    return targets;
  }

  Future<E2eeEnvelopeDto> _encryptPayload({
    required String conversationId,
    required String identityId,
    required bool isGroup,
    required List<int> payload,
  }) async {
    final handle = await _localHandle(identityId);
    final targets = await _deviceTargets(conversationId, identityId, isGroup);
    return isGroup
        ? _coordinator.encryptGroup(
            local: handle,
            conversationId: conversationId,
            plaintext: payload,
            localBackendDeviceId: _backendDeviceId,
            memberDevices: targets,
          )
        : _coordinator.encryptDirectForDevices(
            local: handle,
            localBackendDeviceId: _backendDeviceId,
            targets: targets,
            plaintext: payload,
          );
  }

  Future<MessageDto> sendText({
    required String conversationId,
    required String identityId,
    required String plaintext,
    required bool isGroup,
    String? replyToMessageId,
    String? replyPreview,
    String? clientMessageId,
  }) async {
    final payload = E2eeMessagePayload(
      body: plaintext,
      replyPreview: replyPreview,
    ).encode();
    final envelope = await _encryptPayload(
      conversationId: conversationId,
      identityId: identityId,
      isGroup: isGroup,
      payload: payload,
    );
    return _messaging.sendE2ee(
      conversationId: conversationId,
      envelope: envelope,
      replyToMessageId: replyToMessageId,
      clientMessageId: clientMessageId ?? const Uuid().v4(),
    );
  }

  Future<MessageDto> sendMedia({
    required String conversationId,
    required String identityId,
    required bool isGroup,
    required String filename,
    required String contentType,
    required Uint8List plaintextBytes,
    String? caption,
    String? clientMessageId,
  }) async {
    if (_mediaUpload == null) {
      throw StateError('Media API is not configured');
    }
    final uploaded = await _mediaUpload.upload(
      conversationId: conversationId,
      mediaType: _mediaTypeFromMime(contentType),
      filename: filename,
      contentType: contentType,
      plaintext: plaintextBytes,
    );
    final payload = E2eeMessagePayload(
      body: caption ?? '',
      media: uploaded.mediaMeta,
    ).encode();
    final envelope = await _encryptPayload(
      conversationId: conversationId,
      identityId: identityId,
      isGroup: isGroup,
      payload: payload,
    );
    return _messaging.sendE2ee(
      conversationId: conversationId,
      envelope: envelope,
      clientMessageId: clientMessageId ?? const Uuid().v4(),
    );
  }

  Future<MessageDto> editText({
    required String messageId,
    required String conversationId,
    required String identityId,
    required bool isGroup,
    required String plaintext,
  }) async {
    final payload =
        E2eeMessagePayload(body: plaintext, edited: true).encode();
    final envelope = await _encryptPayload(
      conversationId: conversationId,
      identityId: identityId,
      isGroup: isGroup,
      payload: payload,
    );
    return _messaging.editE2ee(messageId: messageId, envelope: envelope);
  }

  Future<DecryptResult> decryptMessage({
    required MessageDto dto,
    required String identityId,
  }) async {
    if (dto.type != 'E2EE' || dto.e2ee == null) {
      return DecryptResult(body: dto.text ?? '');
    }
    try {
      final handle = await _localHandle(identityId);
      final bytes = await _coordinator.decryptEnvelope(
        local: handle,
        localBackendDeviceId: _backendDeviceId,
        message: dto,
      );
      final payload = E2eeMessagePayload.decode(bytes);
      return DecryptResult(body: payload.body, payload: payload);
    } on E2eeUntrustedIdentityException catch (e) {
      return DecryptResult(
        body: '',
        failed: true,
        trustWarning: e.message,
      );
    } catch (_) {
      return const DecryptResult(body: '', failed: true);
    }
  }

  Future<void> handleSenderKeyRealtime({
    required String identityId,
    required Map<String, dynamic> payload,
    required String? localBackendDeviceId,
  }) async {
    final target = payload['target_device_id'] as String?;
    if (target != null && target != localBackendDeviceId) return;
    final handle = await _localHandle(identityId);
    await _coordinator.processSenderKeyDistribution(
      local: handle,
      senderUserId: payload['sender_user_id'] as String,
      senderBackendDeviceId: payload['sender_device_id'] as String,
      distributionId: payload['distribution_id'] as String,
      messageType: (payload['message_type'] as num).toInt(),
      ciphertextB64: payload['ciphertext'] as String,
    );
  }

  Future<void> trustIdentity({
    required String localIdentityId,
    required String remoteIdentityId,
    required String remoteBackendDeviceId,
  }) async {
    final handle = await _localHandle(localIdentityId);
    await _trust.markVerified(
      local: handle,
      identityId: remoteIdentityId,
      backendDeviceId: remoteBackendDeviceId,
    );
  }

  /// Fan-out per-device sender-key ciphertexts over realtime (server stamps sender ids).
  void publishGroupSenderKeyDistribution({
    required void Function({
      required String conversationId,
      required String distributionId,
      required int messageType,
      required String ciphertextB64,
      String? targetDeviceId,
    }) send,
    required String conversationId,
    required E2eeEnvelopeDto envelope,
  }) {
    if (envelope.mode != 'group') return;
    final distributionId = envelope.distributionId ?? conversationId;
    for (final payload in envelope.devicePayloads) {
      send(
        conversationId: conversationId,
        distributionId: distributionId,
        messageType: payload.messageType,
        ciphertextB64: payload.ciphertextB64,
        targetDeviceId: payload.deviceId,
      );
    }
  }

  ChatMessage toChatMessage({
    required MessageDto dto,
    required String identityId,
    required String? memberId,
    required DecryptResult decrypted,
    MessageStatus status = MessageStatus.sent,
  }) {
    final mine = dto.senderMemberId == (memberId ?? identityId) ||
        dto.senderUserId == identityId;
    final reactions = _mapReactions(dto.reactions, memberId ?? identityId);
    MessageType type = MessageType.text;
    if (dto.isDeleted) {
      type = MessageType.deleted;
    } else if (decrypted.payload?.media != null) {
      type = MessageType.image;
    }
    return ChatMessage(
      id: dto.id,
      conversationId: dto.conversationId,
      senderMemberId: dto.senderMemberId,
      type: type,
      createdAt: dto.createdAt,
      isMine: mine,
      text: dto.isDeleted
          ? null
          : decrypted.failed
              ? null
              : decrypted.body,
      status: status,
      editedAt: dto.editedAt,
      sequence: dto.sequence,
      decryptFailed: decrypted.failed,
      trustWarning: decrypted.trustWarning,
      replyToMessageId: dto.replyToMessageId,
      mediaPayload: decrypted.payload?.media,
      reactions: reactions,
      senderUserId: dto.senderUserId,
      senderDeviceId: dto.senderDeviceId,
    );
  }

  List<MessageReaction> _mapReactions(
    List<MessageReactionDto> dtos,
    String selfMemberId,
  ) {
    final counts = <String, int>{};
    var mine = <String>{};
    for (final r in dtos) {
      counts[r.reaction] = (counts[r.reaction] ?? 0) + 1;
      if (r.memberId == selfMemberId) mine.add(r.reaction);
    }
    return counts.entries
        .map(
          (e) => MessageReaction(
            e.key,
            e.value,
            currentUserReacted: mine.contains(e.key),
          ),
        )
        .toList();
  }

  Future<Uint8List?> downloadAndDecryptAttachment({
    required Map<String, dynamic> mediaMeta,
    required MediaApi mediaApi,
  }) async {
    final mediaId = mediaMeta['media_id'] as String?;
    final nonce = (mediaMeta['nonce'] as List<dynamic>?)
        ?.map((e) => (e as num).toInt())
        .toList();
    final fileKey = (mediaMeta['file_key'] as List<dynamic>?)
        ?.map((e) => (e as num).toInt())
        .toList();
    if (mediaId == null || nonce == null || fileKey == null) return null;
    final url = await mediaApi.downloadUrl(mediaId);
    final cipher = await mediaApi.fetchBytes(url);
    final plain = AttachmentCryptoService().decryptBytes(
      fileKey: fileKey,
      nonce: nonce,
      ciphertext: cipher,
    );
    return Uint8List.fromList(plain);
  }

  String _mediaTypeFromMime(String mime) {
    if (mime.startsWith('image/')) return 'image';
    if (mime.startsWith('video/')) return 'video';
    if (mime.startsWith('audio/')) return 'audio';
    return 'document';
  }
}
