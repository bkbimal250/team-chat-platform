import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';
import 'messaging_models.dart';

class MessagingApi {
  MessagingApi(this._client);

  final GatewayClient _client;

  Future<MessageDto> sendE2ee({
    required String conversationId,
    required E2eeEnvelopeDto envelope,
    String? replyToMessageId,
    String? clientMessageId,
  }) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/conversations/$conversationId/messages',
        data: {
          'client_message_id': clientMessageId ?? const Uuid().v4(),
          'type': 'E2EE',
          'e2ee': envelope.toJson(),
          if (replyToMessageId != null) 'reply_to_message_id': replyToMessageId,
        },
        options: _client.idempotentPost(
          idempotencyKey: clientMessageId ?? const Uuid().v4(),
        ),
      );
      return MessageDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<List<MessageDto>> history({
    required String conversationId,
    int? beforeSequence,
    int? afterSequence,
    int limit = 50,
  }) async {
    try {
      final response = await _client.dio.get<List<dynamic>>(
        '/api/v1/conversations/$conversationId/messages',
        queryParameters: {
          if (beforeSequence != null) 'before_sequence': beforeSequence,
          if (afterSequence != null) 'after_sequence': afterSequence,
          'limit': limit,
        },
      );
      return (response.data ?? [])
          .map((e) => MessageDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<MessageDto> editE2ee({
    required String messageId,
    required E2eeEnvelopeDto envelope,
  }) async {
    try {
      final response = await _client.dio.patch<Map<String, dynamic>>(
        '/api/v1/messages/$messageId',
        data: {'e2ee': envelope.toJson()},
      );
      return MessageDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> deleteMessage(String messageId) async {
    try {
      await _client.dio.delete<void>('/api/v1/messages/$messageId');
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> addReaction({
    required String messageId,
    required String reaction,
  }) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/messages/$messageId/reactions',
        data: {'reaction': reaction},
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> removeReaction({
    required String messageId,
    required String reaction,
  }) async {
    try {
      await _client.dio.delete<void>(
        '/api/v1/messages/$messageId/reactions/$reaction',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> markDelivered({
    required String conversationId,
    required int sequence,
  }) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/delivered',
        data: {'sequence': sequence},
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> markRead({
    required String conversationId,
    required int sequence,
  }) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/read',
        data: {'sequence': sequence},
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }
}
