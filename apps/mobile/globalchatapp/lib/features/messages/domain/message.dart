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
  });
  final String id, conversationId, senderMemberId;
  final MessageType type;
  final DateTime createdAt;
  final bool isMine;
  final String? text;
  final MessageStatus status;
  final ReplyReference? replyTo;
  final MediaAttachment? attachment;
  final List<MessageReaction> reactions;
  final DateTime? editedAt;
}
