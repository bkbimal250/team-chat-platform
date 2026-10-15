class MeResponseDto {
  const MeResponseDto({
    required this.identityId,
    this.email,
    this.phoneNumber,
    required this.phoneVerified,
    required this.emailVerified,
    required this.sessionId,
    required this.deviceId,
    this.organizationId,
    this.memberId,
  });

  final String identityId;
  final String? email;
  final String? phoneNumber;
  final bool phoneVerified;
  final bool emailVerified;
  final String sessionId;
  final String deviceId;
  final String? organizationId;
  final String? memberId;

  factory MeResponseDto.fromJson(Map<String, dynamic> json) {
    final identity = json['identity'] as Map<String, dynamic>;
    final session = json['session'] as Map<String, dynamic>;
    final context = json['context'] as Map<String, dynamic>;
    return MeResponseDto(
      identityId: identity['id'] as String,
      email: identity['email'] as String?,
      phoneNumber: identity['phone_number'] as String?,
      phoneVerified: identity['phone_verified'] as bool? ?? false,
      emailVerified: identity['email_verified'] as bool? ?? false,
      sessionId: session['id'] as String,
      deviceId: session['device_id'] as String,
      organizationId: context['organization_id'] as String?,
      memberId: context['member_id'] as String?,
    );
  }
}
