import 'dart:math';
import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import '../models/encrypted_attachment_descriptor.dart';

/// Per-file random keys + AES-256-GCM-SIV (libsignal primitive).
///
/// Upload **encrypted** bytes to object storage; wrap the file key for each
/// recipient device inside the Signal message payload in a later integration phase.
class AttachmentCryptoService {
  static const _nonceLength = 12;
  static const _keyLength = 32;

  EncryptedAttachmentPayload encryptBytes(List<int> plaintext) {
    final key = PrivateKey.generate().serialize().sublist(0, _keyLength);
    final nonce = _randomNonce();
    final cipher = Aes256GcmSiv(key: key.toList());
    final ciphertext = cipher.encrypt(
      plaintext: plaintext,
      nonce: nonce,
      associatedData: const [],
    );
    return EncryptedAttachmentPayload(
      ciphertext: ciphertext,
      fileKey: key.toList(),
      nonce: nonce,
    );
  }

  List<int> decryptBytes({
    required List<int> fileKey,
    required List<int> nonce,
    required List<int> ciphertext,
  }) {
    final cipher = Aes256GcmSiv(key: fileKey);
    return cipher
        .decrypt(
          ciphertext: ciphertext,
          nonce: nonce,
          associatedData: const [],
        )
        .toList();
  }

  EncryptedAttachmentDescriptor describeUpload({
    required EncryptedAttachmentPayload payload,
    required String objectKey,
    required String contentType,
    required List<int> wrappedFileKey,
  }) =>
      EncryptedAttachmentDescriptor(
        objectKey: objectKey,
        contentType: contentType,
        byteLength: payload.ciphertext.length,
        nonce: payload.nonce,
        wrappedFileKey: wrappedFileKey,
      );

  List<int> _randomNonce() {
    final random = Random.secure();
    return List.generate(_nonceLength, (_) => random.nextInt(256));
  }
}

class EncryptedAttachmentPayload {
  const EncryptedAttachmentPayload({
    required this.ciphertext,
    required this.fileKey,
    required this.nonce,
  });

  final Uint8List ciphertext;
  final List<int> fileKey;
  final List<int> nonce;
}
