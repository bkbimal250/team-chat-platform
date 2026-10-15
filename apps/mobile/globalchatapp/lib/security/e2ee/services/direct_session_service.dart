import 'package:libsignal/libsignal.dart';

import '../models/ciphertext_envelope.dart';
import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import '../protocol/e2ee_protocol.dart';
import 'e2ee_foundation.dart';

/// 1:1 Signal sessions (personal or workspace **conversations**, not org ids).
class DirectSessionService {
  DirectSessionService({E2eeProtocol? protocol})
      : _protocol = protocol ?? E2eeFoundation.protocol;

  final E2eeProtocol _protocol;

  Future<void> processRemoteBundle({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required PreKeyBundle bundle,
  }) =>
      _protocol.establishSession(
        local: local,
        remote: remote,
        remoteBundle: bundle,
      );

  Future<CiphertextEnvelope> encrypt({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> plaintext,
  }) =>
      _protocol.encryptDirect(
        local: local,
        remote: remote,
        plaintext: plaintext,
      );

  Future<List<int>> decrypt({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required CiphertextEnvelope envelope,
  }) =>
      _protocol.decryptDirect(
        local: local,
        remote: remote,
        envelope: envelope,
      );

  Future<String> safetyNumber({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> remoteIdentityKeyPublic,
  }) =>
      _protocol.safetyNumber(
        local: local,
        remote: remote,
        remoteIdentityKeyPublic: remoteIdentityKeyPublic,
      );
}
