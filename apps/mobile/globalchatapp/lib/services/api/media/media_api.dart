import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';

class MediaApi {
  MediaApi(this._client);

  final GatewayClient _client;

  Future<MediaUploadSession> initiateUpload({
    required String conversationId,
    required String mediaType,
    required String filename,
    required String mimeType,
    required int sizeBytes,
  }) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/media/uploads',
        data: {
          'conversation_id': conversationId,
          'media_type': mediaType,
          'filename': filename,
          'mime_type': mimeType,
          'size_bytes': sizeBytes,
        },
      );
      return MediaUploadSession.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<String> downloadUrl(String mediaId) async {
    try {
      final response = await _client.dio.get<Map<String, dynamic>>(
        '/api/v1/media/$mediaId/download',
      );
      return response.data!['download_url'] as String;
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> completeUpload(String mediaId) async {
    try {
      await _client.dio.post<void>('/api/v1/media/$mediaId/complete');
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> putEncryptedBytes({
    required String uploadUrl,
    required Uint8List bytes,
    required String contentType,
    Map<String, String>? requiredHeaders,
  }) async {
    final dio = Dio();
    await dio.put<void>(
      uploadUrl,
      data: bytes,
      options: Options(
        headers: {
          'Content-Type': contentType,
          ...?requiredHeaders,
        },
      ),
    );
  }

  Future<Uint8List> fetchBytes(String url) async {
    final dio = Dio();
    final response = await dio.get<List<int>>(
      url,
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data ?? []);
  }
}

class MediaUploadSession {
  const MediaUploadSession({
    required this.mediaId,
    required this.uploadUrl,
    this.requiredHeaders = const {},
  });

  final String mediaId;
  final String uploadUrl;
  final Map<String, String> requiredHeaders;

  factory MediaUploadSession.fromJson(Map<String, dynamic> json) {
    final headers = json['required_headers'] as Map<String, dynamic>? ?? {};
    return MediaUploadSession(
      mediaId: json['media_id'] as String,
      uploadUrl: json['upload_url'] as String,
      requiredHeaders: headers.map(
        (k, v) => MapEntry(k.toString(), v.toString()),
      ),
    );
  }
}
