import 'package:dio/dio.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';

class OrgMemberDto {
  const OrgMemberDto({
    required this.id,
    required this.displayName,
    this.userId,
  });

  final String id;
  final String displayName;
  final String? userId;

  factory OrgMemberDto.fromJson(Map<String, dynamic> json) => OrgMemberDto(
        id: json['id'] as String,
        displayName: (json['display_name'] ?? json['name'] ?? 'Member') as String,
        userId: json['user_id'] as String?,
      );
}

class MembersApi {
  MembersApi(this._client);

  final GatewayClient _client;

  Future<List<OrgMemberDto>> list() async {
    try {
      final response = await _client.dio.get<Map<String, dynamic>>(
        '/api/v1/members/',
      );
      final results = response.data?['results'] as List<dynamic>? ?? [];
      return results
          .map((e) => OrgMemberDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }
}
