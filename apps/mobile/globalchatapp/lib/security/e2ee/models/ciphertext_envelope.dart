/// Wire payload the messaging service carries (no plaintext body).
class CiphertextEnvelope {
  const CiphertextEnvelope({
    required this.messageType,
    required this.ciphertext,
    this.registrationId,
  });

  /// libsignal [CiphertextMessageType] numeric value.
  final int messageType;

  final List<int> ciphertext;

  /// Present for pre-key messages when the sender's registration id is needed.
  final int? registrationId;
}
