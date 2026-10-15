import '../models/ciphertext_envelope.dart';
import '../models/device_public_key_bundle.dart';
import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import 'package:libsignal/libsignal.dart';

/// Port between GlobalChat and the Signal implementation (libsignal).
abstract interface class E2eeProtocol {
  Future<LocalDeviceCryptoHandle> openDevice({
    required String userIdentityId,
    required int deviceId,
  });

  Future<DevicePublicKeyBundle> ensurePreKeys({
    required LocalDeviceCryptoHandle device,
    int oneTimePreKeyCount,
  });

  Future<void> establishSession({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required PreKeyBundle remoteBundle,
  });

  Future<CiphertextEnvelope> encryptDirect({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> plaintext,
  });

  Future<List<int>> decryptDirect({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required CiphertextEnvelope envelope,
  });

  Future<String> safetyNumber({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> remoteIdentityKeyPublic,
  });
}
