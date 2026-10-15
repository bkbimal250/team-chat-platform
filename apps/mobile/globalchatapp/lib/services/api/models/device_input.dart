import 'dart:io';

import '../../auth/session_storage.dart';

class DeviceInputDto {
  const DeviceInputDto({
    required this.installationId,
    required this.platform,
    required this.deviceName,
    this.deviceModel,
    this.osVersion,
    this.appVersion,
  });

  final String installationId;
  final String platform;
  final String deviceName;
  final String? deviceModel;
  final String? osVersion;
  final String? appVersion;

  Map<String, dynamic> toJson() => {
        'installation_id': installationId,
        'platform': platform,
        'device_name': deviceName,
        if (deviceModel != null) 'device_model': deviceModel,
        if (osVersion != null) 'os_version': osVersion,
        if (appVersion != null) 'app_version': appVersion,
      };

  static Future<DeviceInputDto> current({
    required SessionStorage storage,
    String appVersion = '1.0.0',
  }) async {
    final installationId = await storage.getOrCreateInstallationId();
    final platform = Platform.isIOS ? 'IOS' : 'ANDROID';
    return DeviceInputDto(
      installationId: installationId,
      platform: platform,
      deviceName: Platform.isIOS ? 'iPhone' : 'Android device',
      deviceModel: Platform.operatingSystemVersion,
      osVersion: Platform.operatingSystemVersion,
      appVersion: appVersion,
    );
  }
}
