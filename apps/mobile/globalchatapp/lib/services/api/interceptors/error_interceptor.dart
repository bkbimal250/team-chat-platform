import 'package:dio/dio.dart';

import '../errors/api_exception.dart';

class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final response = err.response;
    if (response?.data is Map<String, dynamic>) {
      final body = response!.data as Map<String, dynamic>;
      final error = body['error'];
      if (error is Map<String, dynamic>) {
        handler.reject(
          DioException(
            requestOptions: err.requestOptions,
            response: response,
            type: err.type,
            error: ApiException(
              message: error['message'] as String? ?? 'Request failed',
              code: error['code'] as String?,
              statusCode: response.statusCode,
              correlationId: error['correlation_id'] as String?,
            ),
          ),
        );
        return;
      }
    }
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        response: response,
        type: err.type,
        error: ApiException(
          message: err.message ?? 'Network error',
          statusCode: response?.statusCode,
        ),
      ),
    );
  }
}

ApiException? apiExceptionFromDio(DioException err) {
  final inner = err.error;
  return inner is ApiException ? inner : null;
}
