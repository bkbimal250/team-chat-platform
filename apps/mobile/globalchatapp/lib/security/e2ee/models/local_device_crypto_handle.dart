import 'package:libsignal/libsignal.dart';

import '../storage/persistent_identity_key_store.dart';
import '../storage/persistent_pre_key_stores.dart';
import '../storage/persistent_sender_key_store.dart';
import '../storage/persistent_session_store.dart';
import '../storage/secure_blob_store.dart';
import 'e2ee_protocol_address.dart';

/// All libsignal stores for one physical device installation.
class LocalDeviceCryptoHandle {
  LocalDeviceCryptoHandle({
    required this.userIdentityId,
    required this.deviceId,
    required this.localAddress,
    required this.identityKeyStore,
    required this.sessionStore,
    required this.preKeyStore,
    required this.signedPreKeyStore,
    required this.kyberPreKeyStore,
    required this.senderKeyStore,
  });

  final String userIdentityId;
  final int deviceId;
  final E2eeProtocolAddress localAddress;
  final IdentityKeyStore identityKeyStore;
  final SessionStore sessionStore;
  final PreKeyStore preKeyStore;
  final SignedPreKeyStore signedPreKeyStore;
  final KyberPreKeyStore kyberPreKeyStore;
  final SenderKeyStore senderKeyStore;

  static Future<LocalDeviceCryptoHandle> open({
    required SecureBlobStore blobs,
    required String userIdentityId,
    required int deviceId,
  }) async {
    final identity = await PersistentIdentityKeyStore.loadOrCreate(
      blobs: blobs,
      userIdentityId: userIdentityId,
      localDeviceId: deviceId,
    );
    return LocalDeviceCryptoHandle(
      userIdentityId: userIdentityId,
      deviceId: deviceId,
      localAddress: E2eeProtocolAddress(
        userIdentityId: userIdentityId,
        deviceId: deviceId,
      ),
      identityKeyStore: identity,
      sessionStore: PersistentSessionStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: deviceId,
      ),
      preKeyStore: PersistentPreKeyStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: deviceId,
      ),
      signedPreKeyStore: PersistentSignedPreKeyStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: deviceId,
      ),
      kyberPreKeyStore: PersistentKyberPreKeyStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: deviceId,
      ),
      senderKeyStore: PersistentSenderKeyStore(
        blobs: blobs,
        userIdentityId: userIdentityId,
        localDeviceId: deviceId,
      ),
    );
  }
}
