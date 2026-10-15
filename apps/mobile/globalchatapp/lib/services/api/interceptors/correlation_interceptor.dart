import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

class CorrelationInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers.putIfAbsent('X-Correlation-ID', () => const Uuid().v4());
    handler.next(options);
  }
}
