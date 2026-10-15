class PublicDeviceE2eeDto {
  const PublicDeviceE2eeDto({
    required this.deviceId,
    required this.platform,
    required this.deviceName,
    required this.status,
    this.registrationId,
    this.keyVersion,
    this.identityKeyFingerprint,
    this.rotatedAt,
  });

  final String deviceId;
  final String platform;
  final String deviceName;
  final String status;
  final int? registrationId;
  final int? keyVersion;
  final String? identityKeyFingerprint;
  final DateTime? rotatedAt;

  factory PublicDeviceE2eeDto.fromJson(Map<String, dynamic> json) =>
      PublicDeviceE2eeDto(
        deviceId: json['device_id'] as String,
        platform: json['platform'] as String,
        deviceName: json['device_name'] as String,
        status: json['status'] as String,
        registrationId: (json['registration_id'] as num?)?.toInt(),
        keyVersion: (json['key_version'] as num?)?.toInt(),
        identityKeyFingerprint: json['identity_key_fingerprint'] as String?,
        rotatedAt: json['rotated_at'] != null
            ? DateTime.parse(json['rotated_at'] as String)
            : null,
      );
}

class PreKeyBundleDto {
  const PreKeyBundleDto({
    required this.registrationId,
    required this.deviceId,
    required this.identityId,
    required this.keyVersion,
    required this.identityKeyB64,
    required this.signedPreKey,
    required this.kyberPreKey,
    this.oneTimePreKey,
  });

  final int registrationId;
  final String deviceId;
  final String identityId;
  final int keyVersion;
  final String identityKeyB64;
  final Map<String, dynamic> signedPreKey;
  final Map<String, dynamic> kyberPreKey;
  final Map<String, dynamic>? oneTimePreKey;

  factory PreKeyBundleDto.fromJson(Map<String, dynamic> json) =>
      PreKeyBundleDto(
        registrationId: (json['registration_id'] as num).toInt(),
        deviceId: json['device_id'] as String,
        identityId: json['identity_id'] as String,
        keyVersion: (json['key_version'] as num).toInt(),
        identityKeyB64: json['identity_key'] as String,
        signedPreKey: json['signed_pre_key'] as Map<String, dynamic>,
        kyberPreKey: json['kyber_pre_key'] as Map<String, dynamic>,
        oneTimePreKey: json['one_time_pre_key'] as Map<String, dynamic>?,
      );
}
