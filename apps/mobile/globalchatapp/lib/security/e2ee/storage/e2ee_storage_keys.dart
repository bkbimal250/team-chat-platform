/// Namespaced secure-storage keys. Version segment allows future migrations.
abstract final class E2eeStorageKeys {
  static const _root = 'gc_e2ee/v1';

  static String deviceRoot(String userIdentityId, int deviceId) =>
      '$_root/device/$userIdentityId/$deviceId';

  static String localIdentityKeyPair(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/identity_key_pair';

  static String localRegistrationId(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/registration_id';

  static String sessionRecord(String userIdentityId, int deviceId, String remoteName, int remoteDeviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/sessions/$remoteName:$remoteDeviceId';

  static String sessionIndex(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/sessions/_index';

  static String remoteIdentity(String userIdentityId, int deviceId, String remoteName, int remoteDeviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/remote_identities/$remoteName:$remoteDeviceId';

  static String remoteIdentityVerified(String userIdentityId, int deviceId, String remoteName, int remoteDeviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/remote_verified/$remoteName:$remoteDeviceId';

  static String preKeyRecord(String userIdentityId, int deviceId, int preKeyId) =>
      '${deviceRoot(userIdentityId, deviceId)}/prekeys/$preKeyId';

  static String preKeyIndex(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/prekeys/_index';

  static String signedPreKeyRecord(String userIdentityId, int deviceId, int signedPreKeyId) =>
      '${deviceRoot(userIdentityId, deviceId)}/signed_prekeys/$signedPreKeyId';

  static String signedPreKeyIndex(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/signed_prekeys/_index';

  static String kyberPreKeyRecord(String userIdentityId, int deviceId, int kyberPreKeyId) =>
      '${deviceRoot(userIdentityId, deviceId)}/kyber_prekeys/$kyberPreKeyId';

  static String kyberPreKeyIndex(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/kyber_prekeys/_index';

  static String senderKeyRecord(
    String userIdentityId,
    int deviceId,
    String senderName,
    int senderDeviceId,
    String distributionId,
  ) =>
      '${deviceRoot(userIdentityId, deviceId)}/sender_keys/$senderName:$senderDeviceId/$distributionId';

  static String senderKeyIndex(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/sender_keys/_index';

  static String preKeyCounter(String userIdentityId, int deviceId) =>
      '${deviceRoot(userIdentityId, deviceId)}/prekey_counters';

  static String devicePrefix(String userIdentityId, int deviceId) =>
      deviceRoot(userIdentityId, deviceId);
}
