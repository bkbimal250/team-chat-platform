import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../client/gateway_client.dart';
class UserApi {
  UserApi(this.client);
  final GatewayClient client;
  Future<Map<String, dynamic>> setPhoto(Uint8List bytes, String mime, int? hours) async {
    if (bytes.length > 2 * 1024 * 1024) throw ArgumentError('Photo exceeds 2 MB');
    final upload = (await client.dio.post<Map<String, dynamic>>('/api/v1/media/profile-photos/uploads',
      data: {'mime_type': mime, 'size_bytes': bytes.length})).data!;
    // Never forward the authenticated Gateway client's headers to object storage.
    final storage = Dio(BaseOptions(connectTimeout: const Duration(seconds: 20), sendTimeout: const Duration(seconds: 60), receiveTimeout: const Duration(seconds: 30)));
    try {
      await storage.put<void>(upload['upload_url'] as String, data: bytes,
        options: Options(headers: Map<String, dynamic>.from(upload['required_headers'] as Map), followRedirects: false));
    } finally { storage.close(); }
    final id = upload['media_id'] as String;
    await client.dio.post<void>('/api/v1/media/profile-photos/$id/complete');
    return (await client.dio.put<Map<String, dynamic>>('/api/v1/users/me/photo',
      data: {'media_id': id, 'duration_hours': hours})).data!;
  }
  Future<void> removePhoto() async { await client.dio.delete<void>('/api/v1/users/me/photo'); }
  Future<String> photoUrl(String mediaId) async =>
    (await client.dio.get<Map<String, dynamic>>('/api/v1/users/profile-photos/$mediaId')).data!['download_url'] as String;
  Future<Map<String, dynamic>> get(String section) async =>
    (await client.dio.get<Map<String, dynamic>>('/api/v1/users/me$section')).data!;
  Future<Map<String, dynamic>> update(String section, Map<String, dynamic> values) async =>
    (await client.dio.patch<Map<String, dynamic>>('/api/v1/users/me$section', data: values)).data!;
}
