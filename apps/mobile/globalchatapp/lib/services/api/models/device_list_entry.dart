class DeviceListEntryDto {
  const DeviceListEntryDto({
    required this.id,
    required this.platform,
    required this.deviceName,
    required this.status,
    required this.isCurrent,
  });

  final String id;
  final String platform;
  final String deviceName;
  final String status;
  final bool isCurrent;

  factory DeviceListEntryDto.fromJson(Map<String, dynamic> json) =>
      DeviceListEntryDto(
        id: json['id'] as String,
        platform: json['platform'] as String,
        deviceName: json['device_name'] as String,
        status: json['status'] as String,
        isCurrent: json['is_current'] as bool? ?? false,
      );
}
