/// HTTP API shapes for Phase 2B+ (documentation + typed client stubs).
///
/// See `docs/E2EE-BACKEND-CONTRACT.md` for full semantics.
library;

/// `PUT /v1/identities/{identityId}/devices/{deviceId}/keys`
class UploadDeviceKeysRequest {
  const UploadDeviceKeysRequest({
    required this.registrationId,
    required this.identityKey,
    required this.signedPreKey,
    required this.kyberPreKey,
    this.oneTimePreKeys = const [],
  });

  final int registrationId;
  final EncodedPublicKey identityKey;
  final SignedPreKeyUpload signedPreKey;
  final KyberPreKeyUpload kyberPreKey;
  final List<OneTimePreKeyUpload> oneTimePreKeys;
}

class EncodedPublicKey {
  const EncodedPublicKey({required this.bytesBase64});

  final String bytesBase64;
}

class SignedPreKeyUpload {
  const SignedPreKeyUpload({
    required this.keyId,
    required this.publicKey,
    required this.signature,
  });

  final int keyId;
  final String publicKey;
  final String signature;
}

class KyberPreKeyUpload {
  const KyberPreKeyUpload({
    required this.keyId,
    required this.publicKey,
    required this.signature,
  });

  final int keyId;
  final String publicKey;
  final String signature;
}

class OneTimePreKeyUpload {
  const OneTimePreKeyUpload({required this.keyId, required this.publicKey});

  final int keyId;
  final String publicKey;
}

/// `GET /v1/identities/{identityId}/devices/{deviceId}/prekey-bundle`
class PreKeyBundleResponse {
  const PreKeyBundleResponse({
    required this.registrationId,
    required this.deviceId,
    required this.identityKey,
    required this.signedPreKey,
    required this.kyberPreKey,
    this.oneTimePreKey,
  });

  final int registrationId;
  final int deviceId;
  final String identityKey;
  final SignedPreKeyUpload signedPreKey;
  final KyberPreKeyUpload kyberPreKey;
  final OneTimePreKeyUpload? oneTimePreKey;
}

/// `GET /v1/identities/{identityId}/devices`
class DeviceListEntry {
  const DeviceListEntry({
    required this.deviceId,
    required this.createdAt,
    required this.lastSeenAt,
    this.name,
  });

  final int deviceId;
  final DateTime createdAt;
  final DateTime lastSeenAt;
  final String? name;
}

/// Ciphertext message accepted by messaging (no plaintext body field).
class MessagingCiphertextPayload {
  const MessagingCiphertextPayload({
    required this.recipientDeviceIds,
    required this.messageType,
    required this.ciphertextBase64,
    this.senderRegistrationId,
  });

  final List<int> recipientDeviceIds;
  final int messageType;
  final String ciphertextBase64;
  final int? senderRegistrationId;
}
