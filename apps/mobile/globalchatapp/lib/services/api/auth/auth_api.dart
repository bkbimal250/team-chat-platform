import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';
import '../models/device_input.dart';
import '../models/me_response.dart';
import '../models/token_response.dart';

class AuthApi {
  AuthApi(this._client);

  final GatewayClient _client;

  Dio get _dio => _client.dio;

  Future<TokenResponseDto> loginWithPassword({
    required String email,
    required String password,
    required DeviceInputDto device,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {
        'email': email,
        'password': password,
        'device': device.toJson(),
      },
      options: _client.idempotentPost(idempotencyKey: const Uuid().v4()),
    );
    return TokenResponseDto.fromJson(response.data!);
  }

  Future<TokenResponseDto> registerPersonal({
    required String displayName,
    required String email,
    required String phone,
    required String password,
    required DeviceInputDto device,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/registration/personal',
      data: {
        'display_name': displayName,
        'email': email,
        'phone': phone,
        'password': password,
        'device': device.toJson(),
      },
      options: _client.idempotentPost(idempotencyKey: const Uuid().v4()),
    );
    return TokenResponseDto.fromJson(response.data!);
  }

  Future<Map<String, dynamic>> requestOtp({
    required String phoneNumber,
    required String purpose,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/otp/request',
      data: {
        'phone_number': phoneNumber,
        'purpose': purpose,
      },
    );
    return response.data!;
  }

  Future<TokenResponseDto> verifyOtp({
    required String challengeId,
    required String code,
    required DeviceInputDto device,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/otp/verify',
      data: {
        'challenge_id': challengeId,
        'code': code,
        'device': device.toJson(),
      },
      options: _client.idempotentPost(idempotencyKey: const Uuid().v4()),
    );
    return TokenResponseDto.fromJson(response.data!);
  }

  Future<Map<String, dynamic>> forgotPassword({required String email}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/password/forgot',
      data: {'email': email},
    );
    return response.data!;
  }

  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    await _dio.post<void>(
      '/api/v1/auth/password/reset',
      data: {
        'token': token,
        'new_password': newPassword,
      },
    );
  }

  Future<TokenResponseDto> refresh({required String refreshToken}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return TokenResponseDto.fromJson(response.data!);
  }

  Future<void> logout() async {
    await _dio.post<void>('/api/v1/auth/logout');
  }

  Future<MeResponseDto> me() async {
    final response = await _dio.get<Map<String, dynamic>>('/api/v1/auth/me');
    return MeResponseDto.fromJson(response.data!);
  }

  Future<TokenResponseDto> switchContext({String? organizationId}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/context',
      data: {
        if (organizationId != null) 'organization_id': organizationId,
      },
      options: _client.idempotentPost(idempotencyKey: const Uuid().v4()),
    );
    return TokenResponseDto.fromJson(response.data!);
  }

  static Never rethrowApi(DioException e) {
    throw apiExceptionFromDio(e) ?? e;
  }
}
