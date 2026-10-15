import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../security/e2ee/models/device_public_key_bundle.dart';
import '../client/gateway_client.dart';
import '../interceptors/error_interceptor.dart';
import '../models/e2ee_models.dart';

class E2eeApi {
  E2eeApi(this._client);

  final GatewayClient _client;

  Future<void> uploadDeviceKeys({
    required String backendDeviceId,
    required DevicePublicKeyBundle bundle,
  }) async {
    try {
      await _client.dio.put<void>(
        '/api/v1/devices/$backendDeviceId/keys',
        data: _bundleToJson(bundle),
      );
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<int> replenishPreKeys({
    required String backendDeviceId,
    required List<OneTimePreKeyPublic> keys,
  }) async {
    try {
      final response = await _client.dio.post<Map<String, dynamic>>(
        '/api/v1/devices/$backendDeviceId/prekeys/replenish',
        data: {
          'one_time_pre_keys': keys
              .map(
                (k) => {
                  'pre_key_id': k.preKeyId,
                  'public_key': base64Encode(k.publicKey),
                },
              )
              .toList(),
        },
      );
      return (response.data?['added'] as num?)?.toInt() ?? keys.length;
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<List<PublicDeviceE2eeDto>> listUserDevices(String identityId) async {
    try {
      final response = await _client.dio.get<List<dynamic>>(
        '/api/v1/users/$identityId/devices',
      );
      return (response.data ?? [])
          .map((e) => PublicDeviceE2eeDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Future<PreKeyBundleDto> fetchPreKeyBundle({
    required String identityId,
    required String deviceId,
  }) async {
    try {
      final response = await _client.dio.get<Map<String, dynamic>>(
        '/api/v1/e2ee/prekey-bundle/$identityId/$deviceId',
      );
      return PreKeyBundleDto.fromJson(response.data!);
    } on DioException catch (e) {
      throw apiExceptionFromDio(e) ?? e;
    }
  }

  Map<String, dynamic> _bundleToJson(DevicePublicKeyBundle bundle) => {
        'registration_id': bundle.registrationId,
        'identity_key': base64Encode(bundle.identityKeyPublic),
        'signed_pre_key': {
          'key_id': bundle.signedPreKeyId,
          'public_key': base64Encode(bundle.signedPreKeyPublic),
          'signature': base64Encode(bundle.signedPreKeySignature),
        },
        'kyber_pre_key': {
          'key_id': bundle.kyberPreKeyId,
          'public_key': base64Encode(bundle.kyberPreKeyPublic),
          'signature': base64Encode(bundle.kyberPreKeySignature),
        },
        'one_time_pre_keys': bundle.oneTimePreKeys
            .map(
              (k) => {
                'pre_key_id': k.preKeyId,
                'public_key': base64Encode(k.publicKey),
              },
            )
            .toList(),
      };
}
