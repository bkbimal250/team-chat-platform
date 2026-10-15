import 'dart:convert';
import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import '../../../services/api/models/e2ee_models.dart';
import '../../../services/devices/signal_device_id.dart';

Future<PreKeyBundle> preKeyBundleFromDto(
  PreKeyBundleDto dto,
  SignalDeviceIdRegistry registry,
) async {
  final signalDeviceId = await registry.resolve(dto.deviceId);
  final signed = dto.signedPreKey;
  final kyber = dto.kyberPreKey;
  final otp = dto.oneTimePreKey;

  return PreKeyBundle(
    registrationId: dto.registrationId,
    deviceId: signalDeviceId,
    preKeyId: otp != null ? (otp['pre_key_id'] as num).toInt() : null,
    preKeyPublic: otp != null
        ? base64Decode(otp['public_key'] as String)
        : null,
    signedPreKeyId: (signed['key_id'] as num).toInt(),
    signedPreKeyPublic: base64Decode(signed['public_key'] as String),
    signedPreKeySignature: base64Decode(signed['signature'] as String),
    identityKey: base64Decode(dto.identityKeyB64),
    kyberPreKeyId: (kyber['key_id'] as num).toInt(),
    kyberPreKeyPublic: base64Decode(kyber['public_key'] as String),
    kyberPreKeySignature: base64Decode(kyber['signature'] as String),
  );
}
