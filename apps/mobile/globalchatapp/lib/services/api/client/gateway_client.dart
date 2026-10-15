import 'package:dio/dio.dart';

import '../../../config/app_config.dart';
import '../../auth/session_storage.dart';
import '../interceptors/auth_interceptor.dart';
import '../interceptors/correlation_interceptor.dart';
import '../interceptors/error_interceptor.dart';

class GatewayClient {
  GatewayClient({
    required SessionStorage sessionStorage,
    Dio? dio,
  }) : _sessionStorage = sessionStorage,
       _dio = dio ??
           Dio(
             BaseOptions(
               baseUrl: AppConfig.apiBaseUrl,
               connectTimeout: const Duration(seconds: 20),
               receiveTimeout: const Duration(seconds: 30),
               sendTimeout: const Duration(seconds: 30),
               contentType: Headers.jsonContentType,
               responseType: ResponseType.json,
             ),
           ) {
    _dio.interceptors.addAll([
      CorrelationInterceptor(),
      AuthInterceptor(readAccessToken: _sessionStorage.readAccessToken),
      ErrorInterceptor(),
    ]);
  }

  final SessionStorage _sessionStorage;
  final Dio _dio;

  Dio get dio => _dio;

  Options idempotentPost({String? idempotencyKey}) => Options(
        headers: {
          if (idempotencyKey != null) 'Idempotency-Key': idempotencyKey,
        },
      );
}
