import 'package:dio/dio.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';
import '../models/conversation_models.dart';

class ConversationsApi {
  ConversationsApi(this._client);

  final GatewayClient _client;

  Future<List<ConversationDto>> list({
    String? type,
    bool? archived,
    bool? pinned,
  }) async {
    try {
      final response = await _client.dio.get<List<dynamic>>(
        '/api/v1/conversations',
        queryParameters: {
          if (type != null) 'type': type,
          if (archived != null) 'archived': archived,
          if (pinned != null) 'pinned': pinned,
        },
      );
      return (response.data ?? [])
          .map((e) => ConversationDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<ConversationDto> createPersonalDirect(String savedContactId) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/conversations/personal/direct',
        data: {'contact_id': savedContactId},
      );
      return ConversationDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<ConversationDto> createPersonalGroup({
    required String title,
    required List<String> memberIds,
    String? description,
  }) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/conversations/personal/groups',
        data: {
          'title': title,
          'member_ids': memberIds,
          if (description != null) 'description': description,
        },
      );
      return ConversationDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<ConversationDto> createWorkspaceGroup({
    required String title,
    required List<String> memberIds,
    String? description,
  }) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/conversations/groups',
        data: {
          'title': title,
          'member_ids': memberIds,
          if (description != null) 'description': description,
        },
      );
      return ConversationDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<ConversationDto> getConversation(String id) async {
    try {
      final response = await _client.dio.get<Map<String, dynamic>>(
        '/api/v1/conversations/$id',
      );
      return ConversationDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<List<ConversationMemberDto>> listMembers(String conversationId) async {
    try {
      final response = await _client.dio.get<List<dynamic>>(
        '/api/v1/conversations/$conversationId/members',
      );
      return (response.data ?? [])
          .map((e) => ConversationMemberDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> addMembers(String conversationId, List<String> memberIds) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/members',
        data: {'member_ids': memberIds},
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> removeMember(String conversationId, String memberId) async {
    try {
      await _client.dio.delete<void>(
        '/api/v1/conversations/$conversationId/members/$memberId',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> leaveConversation(String conversationId) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/leave',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> deleteGroup(String conversationId) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/delete',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> promoteMember(String conversationId, String memberId) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/members/$memberId/promote',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<void> demoteMember(String conversationId, String memberId) async {
    try {
      await _client.dio.post<void>(
        '/api/v1/conversations/$conversationId/members/$memberId/demote',
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }
}

class ConversationMemberDto {
  const ConversationMemberDto({
    required this.memberId,
    this.userId,
    required this.role,
    required this.status,
  });

  final String memberId;
  final String? userId;
  final String role;
  final String status;

  factory ConversationMemberDto.fromJson(Map<String, dynamic> json) =>
      ConversationMemberDto(
        memberId: json['member_id'] as String,
        userId: json['user_id'] as String?,
        role: json['role'] as String,
        status: json['status'] as String,
      );
}
