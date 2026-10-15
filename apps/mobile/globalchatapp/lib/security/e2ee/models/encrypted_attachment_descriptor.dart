/// Metadata embedded in the encrypted message for attachment decryption.
///
/// The per-file key is wrapped for each recipient device via the Signal session
/// (or group sender-key distribution) in a later phase; Phase 2A defines shape only.
class EncryptedAttachmentDescriptor {
  const EncryptedAttachmentDescriptor({
    required this.objectKey,
    required this.contentType,
    required this.byteLength,
    required this.nonce,
    required this.wrappedFileKey,
    this.sha256Ciphertext,
  });

  final String objectKey;
  final String contentType;
  final int byteLength;

  /// 12-byte AES-GCM-SIV nonce used for the file blob.
  final List<int> nonce;

  /// Opaque key material encrypted to recipients (not plaintext file key).
  final List<int> wrappedFileKey;

  final List<int>? sha256Ciphertext;
}
