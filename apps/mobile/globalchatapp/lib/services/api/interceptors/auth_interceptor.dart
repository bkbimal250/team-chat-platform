import 'package:dio/dio.dart';

typedef AccessTokenReader = Future<String?> Function();

class AuthInterceptor extends Interceptor {
  AuthInterceptor({required this.readAccessToken});

  final AccessTokenReader readAccessToken;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}
