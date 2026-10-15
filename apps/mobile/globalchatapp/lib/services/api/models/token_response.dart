class TokenResponseDto {
  const TokenResponseDto({
    required this.accessToken,
    required this.expiresIn,
    required this.sessionId,
    required this.deviceId,
    this.refreshToken,
    this.organizationId,
    this.memberId,
  });

  final String accessToken;
  final int expiresIn;
  final String sessionId;
  final String deviceId;
  final String? refreshToken;
  final String? organizationId;
  final String? memberId;

  factory TokenResponseDto.fromJson(Map<String, dynamic> json) =>
      TokenResponseDto(
        accessToken: json['access_token'] as String,
        expiresIn: (json['expires_in'] as num).toInt(),
        sessionId: json['session_id'] as String,
        deviceId: json['device_id'] as String,
        refreshToken: json['refresh_token'] as String?,
        organizationId: json['organization_id'] as String?,
        memberId: json['member_id'] as String?,
      );
}
