import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';

/// Sender-key group encryption (Signal-style, per-sender ratchet).
///
/// A **group conversation id** maps to a stable `distributionId` (UUID string).
/// Each member device maintains sender-key state per (sender, distributionId).
class GroupE2eeService {
  GroupCipher _cipher(LocalDeviceCryptoHandle device) => GroupCipher(
        senderKeyStore: device.senderKeyStore,
        identityKeyStore: device.identityKeyStore,
      );

  Future<Uint8List> createSenderKeyDistributionMessage({
    required LocalDeviceCryptoHandle local,
    required String distributionId,
  }) async {
    final cipher = _cipher(local);
    return cipher.createDistributionMessage(
      local.localAddress.toLibsignal(),
      distributionId,
    );
  }

  Future<void> processSenderKeyDistributionMessage({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress sender,
    required String distributionId,
    required List<int> distributionBytes,
  }) async {
    final cipher = _cipher(local);
    await cipher.processDistributionMessage(
      sender.toLibsignal(),
      distributionId,
      Uint8List.fromList(distributionBytes),
    );
  }

  Future<Uint8List> encryptGroupPayload({
    required LocalDeviceCryptoHandle local,
    required String distributionId,
    required List<int> plaintext,
  }) async {
    final cipher = _cipher(local);
    return cipher.encrypt(
      local.localAddress.toLibsignal(),
      distributionId,
      plaintext,
    );
  }

  Future<List<int>> decryptGroupPayload({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress sender,
    required String distributionId,
    required List<int> ciphertext,
  }) async {
    final cipher = _cipher(local);
    final plaintext = await cipher.decrypt(
      sender.toLibsignal(),
      distributionId,
      ciphertext,
    );
    return plaintext.toList();
  }
}
