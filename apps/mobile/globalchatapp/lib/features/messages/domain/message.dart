enum MessageType { text, image, video, document, audio, voiceNote, deleted }

enum MessageStatus { sending, sent, delivered, read, failed }

class MediaAttachment {
  const MediaAttachment({
    required this.name,
    required this.mimeType,
    required this.sizeBytes,
    this.duration,
  });
  final String name, mimeType;
  final int sizeBytes;
  final Duration? duration;
}

class ReplyReference {
  const ReplyReference({
    required this.messageId,
    required this.senderName,
    required this.preview,
  });
  final String messageId, senderName, preview;
}

class MessageReaction {
  const MessageReaction(
    this.emoji,
    this.count, {
    this.currentUserReacted = false,
  });
  final String emoji;
  final int count;
  final bool currentUserReacted;
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderMemberId,
    required this.type,
    required this.createdAt,
    required this.isMine,
    this.text,
    this.status = MessageStatus.sent,
    this.replyTo,
    this.attachment,
    this.reactions = const [],
    this.editedAt,
    this.sequence = 0,
    this.decryptFailed = false,
    this.trustWarning,
    this.replyToMessageId,
    this.mediaPayload,
    this.senderUserId,
    this.senderDeviceId,
  });

  final String id, conversationId, senderMemberId;
  final String? senderUserId;
  final String? senderDeviceId;
  final MessageType type;
  final DateTime createdAt;
  final bool isMine;
  final String? text;
  final MessageStatus status;
  final ReplyReference? replyTo;
  final MediaAttachment? attachment;
  final List<MessageReaction> reactions;
  final DateTime? editedAt;
  final int sequence;
  final bool decryptFailed;
  final String? trustWarning;
  final String? replyToMessageId;
  final Map<String, dynamic>? mediaPayload;

  ChatMessage copyWith({
    String? id,
    String? text,
    MessageStatus? status,
    List<MessageReaction>? reactions,
    DateTime? editedAt,
    MessageType? type,
    bool? decryptFailed,
    String? trustWarning,
  }) =>
      ChatMessage(
        id: id ?? this.id,
        conversationId: conversationId,
        senderMemberId: senderMemberId,
        type: type ?? this.type,
        createdAt: createdAt,
        isMine: isMine,
        text: text ?? this.text,
        status: status ?? this.status,
        replyTo: replyTo,
        attachment: attachment,
        reactions: reactions ?? this.reactions,
        editedAt: editedAt ?? this.editedAt,
        sequence: sequence,
        decryptFailed: decryptFailed ?? this.decryptFailed,
        trustWarning: trustWarning ?? this.trustWarning,
        replyToMessageId: replyToMessageId,
        mediaPayload: mediaPayload,
        senderUserId: senderUserId,
        senderDeviceId: senderDeviceId,
      );
}
