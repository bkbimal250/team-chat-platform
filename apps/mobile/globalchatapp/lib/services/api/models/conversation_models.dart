class ConversationDto {
  const ConversationDto({
    required this.id,
    required this.scope,
    required this.type,
    this.title,
    this.description,
    this.status,
    this.role,
    this.memberCount,
    this.lastMessagePreview,
    this.lastMessageAt,
    this.unreadCount = 0,
    this.avatarMediaId,
    this.displayTitle,
  });

  final String id;
  final String scope;
  final String type;
  final String? title;
  final String? description;
  final String? status;
  final String? role;
  final int? memberCount;
  final String? lastMessagePreview;
  final DateTime? lastMessageAt;
  final int unreadCount;
  final String? avatarMediaId;
  final String? displayTitle;

  bool get isGroup => type == 'GROUP';
  bool get isPersonal => scope == 'PERSONAL';
  bool get isWorkspace => scope == 'WORKSPACE';

  String get listTitle => displayTitle ?? title ?? 'Conversation';

  factory ConversationDto.fromJson(Map<String, dynamic> json) => ConversationDto(
        id: json['id'] as String,
        scope: json['scope'] as String,
        type: json['type'] as String,
        title: json['title'] as String?,
        description: json['description'] as String?,
        status: json['status'] as String?,
        role: json['role'] as String?,
        memberCount: (json['member_count'] as num?)?.toInt(),
        lastMessagePreview: json['last_message_preview'] as String?,
        lastMessageAt: json['last_message_at'] != null
            ? DateTime.parse(json['last_message_at'] as String)
            : null,
        unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
        avatarMediaId: json['avatar_media_id'] as String?,
        displayTitle: (json['title'] as String?)?.isNotEmpty == true
            ? json['title'] as String
            : null,
      );
}
