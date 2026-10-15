class ContactDto {
  const ContactDto({
    required this.id,
    required this.title,
    this.subtitle,
    this.contactIdentityId,
  });

  final String id;
  final String title;
  final String? subtitle;
  final String? contactIdentityId;

  factory ContactDto.fromJson(Map<String, dynamic> json) {
    final matched = json['matched_user'] as Map<String, dynamic>?;
    return ContactDto(
      id: json['id'] as String,
      title: (matched?['display_name'] ?? json['local_label'] ?? 'Contact')
          as String,
      subtitle: json['local_label'] as String?,
      contactIdentityId:
          matched != null ? matched['user_id']?.toString() : null,
    );
  }
}
