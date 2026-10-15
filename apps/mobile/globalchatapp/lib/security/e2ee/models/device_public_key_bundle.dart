/// Public key material uploaded to the backend for one device.
///
/// Server stores **public** keys only; private keys never leave secure storage.
class DevicePublicKeyBundle {
  const DevicePublicKeyBundle({
    required this.userIdentityId,
    required this.deviceId,
    required this.registrationId,
    required this.identityKeyPublic,
    required this.signedPreKeyId,
    required this.signedPreKeyPublic,
    required this.signedPreKeySignature,
    required this.kyberPreKeyId,
    required this.kyberPreKeyPublic,
    required this.kyberPreKeySignature,
    this.oneTimePreKeys = const [],
  });

  final String userIdentityId;
  final int deviceId;
  final int registrationId;
  final List<int> identityKeyPublic;
  final int signedPreKeyId;
  final List<int> signedPreKeyPublic;
  final List<int> signedPreKeySignature;
  final int kyberPreKeyId;
  final List<int> kyberPreKeyPublic;
  final List<int> kyberPreKeySignature;
  final List<OneTimePreKeyPublic> oneTimePreKeys;
}

class OneTimePreKeyPublic {
  const OneTimePreKeyPublic({required this.preKeyId, required this.publicKey});

  final int preKeyId;
  final List<int> publicKey;
}
