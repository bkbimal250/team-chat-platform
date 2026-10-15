import 'package:dio/dio.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';
import '../models/contact_models.dart';

class ContactsApi {
  ContactsApi(this._client);

  final GatewayClient _client;

  Future<List<ContactDto>> list() async {
    try {
      final response = await _client.dio.get<Map<String, dynamic>>(
        '/api/v1/contacts',
      );
      final items = response.data?['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => ContactDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }
}
