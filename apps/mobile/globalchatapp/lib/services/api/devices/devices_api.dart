import '../client/gateway_client.dart';
import '../models/device_list_entry.dart';

class DevicesApi {
  DevicesApi(this._client);

  final GatewayClient _client;

  Future<void> revoke(String deviceId) async {
    await _client.dio.post<void>('/api/v1/devices/$deviceId/revoke');
  }

  Future<List<DeviceListEntryDto>> listDevices() async {
    final response = await _client.dio.get<List<dynamic>>('/api/v1/devices');
    final data = response.data ?? [];
    return data
        .map((e) => DeviceListEntryDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
