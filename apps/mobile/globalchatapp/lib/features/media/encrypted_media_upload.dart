import 'dart:typed_data';

import '../../security/e2ee/services/attachment_crypto_service.dart';
import '../../services/api/media/media_api.dart';
/// Encrypt locally, upload ciphertext bytes, return media id for E2EE payload JSON.
class EncryptedMediaUpload {
  EncryptedMediaUpload({
    AttachmentCryptoService? attachmentCrypto,
    required MediaApi mediaApi,
  })  : _attachmentCrypto = attachmentCrypto ?? AttachmentCryptoService(),
        _mediaApi = mediaApi;

  final AttachmentCryptoService _attachmentCrypto;
  final MediaApi _mediaApi;

  Future<({String mediaId, Map<String, dynamic> mediaMeta})> upload({
    required String conversationId,
    required String mediaType,
    required String filename,
    required String contentType,
    required Uint8List plaintext,
  }) async {
    final encrypted = _attachmentCrypto.encryptBytes(plaintext);
    final session = await _mediaApi.initiateUpload(
      conversationId: conversationId,
      mediaType: mediaType,
      filename: filename,
      mimeType: 'application/octet-stream',
      sizeBytes: encrypted.ciphertext.length,
    );
    await _mediaApi.putEncryptedBytes(
      uploadUrl: session.uploadUrl,
      bytes: Uint8List.fromList(encrypted.ciphertext),
      contentType: 'application/octet-stream',
      requiredHeaders: session.requiredHeaders,
    );
    await _mediaApi.completeUpload(session.mediaId);
    return (
      mediaId: session.mediaId,
      mediaMeta: {
        'media_id': session.mediaId,
        'content_type': contentType,
        'filename': filename,
        'nonce': encrypted.nonce,
        'file_key': encrypted.fileKey,
        'encrypted': true,
      },
    );
  }
}
