class E2eeDeviceCiphertextDto {
  const E2eeDeviceCiphertextDto({
    required this.deviceId,
    required this.messageType,
    required this.ciphertextB64,
    this.registrationId,
  });

  final String deviceId;
  final int messageType;
  final String ciphertextB64;
  final int? registrationId;

  Map<String, dynamic> toJson() => {
        'device_id': deviceId,
        'message_type': messageType,
        'ciphertext': ciphertextB64,
        if (registrationId != null) 'registration_id': registrationId,
      };

  factory E2eeDeviceCiphertextDto.fromJson(Map<String, dynamic> json) =>
      E2eeDeviceCiphertextDto(
        deviceId: json['device_id'] as String,
        messageType: (json['message_type'] as num).toInt(),
        ciphertextB64: json['ciphertext'] as String,
        registrationId: (json['registration_id'] as num?)?.toInt(),
      );
}

class E2eeEnvelopeDto {
  const E2eeEnvelopeDto({
    required this.version,
    required this.mode,
    required this.messageType,
    required this.ciphertextB64,
    required this.devicePayloads,
    this.distributionId,
  });

  final int version;
  final String mode;
  final String? distributionId;
  final int messageType;
  final String ciphertextB64;
  final List<E2eeDeviceCiphertextDto> devicePayloads;

  Map<String, dynamic> toJson() => {
        'version': version,
        'mode': mode,
        if (distributionId != null) 'distribution_id': distributionId,
        'message_type': messageType,
        'ciphertext': ciphertextB64,
        'device_payloads':
            devicePayloads.map((e) => e.toJson()).toList(growable: false),
      };

  factory E2eeEnvelopeDto.fromJson(Map<String, dynamic> json) =>
      E2eeEnvelopeDto(
        version: (json['version'] as num?)?.toInt() ?? 1,
        mode: json['mode'] as String,
        distributionId: json['distribution_id'] as String?,
        messageType: (json['message_type'] as num).toInt(),
        ciphertextB64: json['ciphertext'] as String,
        devicePayloads: (json['device_payloads'] as List<dynamic>)
            .map(
              (e) => E2eeDeviceCiphertextDto.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
      );
}

class MessageDto {
  const MessageDto({
    required this.id,
    required this.conversationId,
    required this.senderUserId,
    required this.senderMemberId,
    required this.senderDeviceId,
    required this.type,
    required this.sequence,
    required this.clientMessageId,
    required this.createdAt,
    this.text,
    this.e2ee,
    this.replyToMessageId,
    this.editedAt,
    this.status,
    this.reactions = const [],
  });

  final String id;
  final String conversationId;
  final String senderUserId;
  final String senderMemberId;
  final String senderDeviceId;
  final String type;
  final int sequence;
  final String clientMessageId;
  final DateTime createdAt;
  final String? text;
  final E2eeEnvelopeDto? e2ee;
  final String? replyToMessageId;
  final DateTime? editedAt;
  final String? status;
  final List<MessageReactionDto> reactions;

  bool get isDeleted => status == 'DELETED';

  factory MessageDto.fromJson(Map<String, dynamic> json) => MessageDto(
        id: json['id'] as String,
        conversationId: json['conversation_id'] as String,
        senderUserId: json['sender_user_id'] as String,
        senderMemberId: json['sender_member_id'] as String,
        senderDeviceId: json['sender_device_id'] as String,
        type: json['type'] as String,
        sequence: (json['sequence'] as num).toInt(),
        clientMessageId: json['client_message_id'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        text: json['text'] as String?,
        e2ee: json['e2ee'] != null
            ? E2eeEnvelopeDto.fromJson(json['e2ee'] as Map<String, dynamic>)
            : null,
        replyToMessageId: json['reply_to_message_id'] as String?,
        editedAt: json['edited_at'] != null
            ? DateTime.parse(json['edited_at'] as String)
            : null,
        status: json['status'] as String?,
        reactions: (json['reactions'] as List<dynamic>? ?? [])
            .map((e) => MessageReactionDto.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class MessageReactionDto {
  const MessageReactionDto({
    required this.memberId,
    required this.userId,
    required this.reaction,
  });

  final String memberId;
  final String userId;
  final String reaction;

  factory MessageReactionDto.fromJson(Map<String, dynamic> json) =>
      MessageReactionDto(
        memberId: json['member_id'] as String,
        userId: json['user_id'] as String,
        reaction: json['reaction'] as String,
      );
}
