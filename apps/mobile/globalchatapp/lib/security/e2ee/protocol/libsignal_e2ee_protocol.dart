import 'dart:convert';
import 'dart:typed_data';

import 'package:libsignal/libsignal.dart';

import '../exceptions/e2ee_exception.dart';
import '../models/ciphertext_envelope.dart';
import '../models/device_public_key_bundle.dart';
import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import '../storage/e2ee_storage_keys.dart';
import '../storage/int_list_codec.dart';
import '../storage/secure_blob_store.dart';
import 'e2ee_protocol.dart';
import 'session_operation_lock.dart';

class LibSignalE2eeProtocol implements E2eeProtocol {
  LibSignalE2eeProtocol({
    SecureBlobStore? blobStore,
    SessionOperationLock? sessionLock,
  })  : _blobs = blobStore ?? SecureBlobStore(),
        _sessionLock = sessionLock ?? SessionOperationLock();

  final SecureBlobStore _blobs;
  final SessionOperationLock _sessionLock;

  static const defaultOneTimePreKeyBatch = 50;

  @override
  Future<LocalDeviceCryptoHandle> openDevice({
    required String userIdentityId,
    required int deviceId,
  }) =>
      LocalDeviceCryptoHandle.open(
        blobs: _blobs,
        userIdentityId: userIdentityId,
        deviceId: deviceId,
      );

  @override
  Future<DevicePublicKeyBundle> ensurePreKeys({
    required LocalDeviceCryptoHandle device,
    int oneTimePreKeyCount = defaultOneTimePreKeyBatch,
  }) async {
    final identityPair = await device.identityKeyStore.getIdentityKeyPair();
    final registrationId =
        await device.identityKeyStore.getLocalRegistrationId();

    const signedPreKeyId = 1;
    const kyberPreKeyId = 1;

    SignedPreKeyRecord? signed =
        await device.signedPreKeyStore.loadSignedPreKey(signedPreKeyId);
    KyberPreKeyRecord? kyber =
        await device.kyberPreKeyStore.loadKyberPreKey(kyberPreKeyId);

    final timestamp = BigInt.from(DateTime.now().millisecondsSinceEpoch);

    if (signed == null) {
      final signedPrivate = PrivateKey.generate();
      final signedPublic = signedPrivate.getPublicKey();
      final signature = identityPair.sign(
        message: signedPublic.serialize().toList(),
      );
      signed = SignedPreKeyRecord(
        id: signedPreKeyId,
        publicKey: signedPublic,
        privateKey: signedPrivate,
        signature: signature.toList(),
        timestamp: timestamp,
      );
      await device.signedPreKeyStore.storeSignedPreKey(signedPreKeyId, signed);
    }

    if (kyber == null) {
      final kyberKeyPair = KyberKeyPair.generate();
      final kyberPublic = kyberKeyPair.getPublicKey();
      final kyberSignature = identityPair.sign(
        message: kyberPublic.serialize().toList(),
      );
      kyber = KyberPreKeyRecord.create(
        id: kyberPreKeyId,
        keyPair: kyberKeyPair,
        signature: kyberSignature.toList(),
        timestamp: timestamp,
      );
      await device.kyberPreKeyStore.storeKyberPreKey(kyberPreKeyId, kyber);
    }

    final existingIds = await device.preKeyStore.getAllPreKeyIds();
    final oneTimePublic = <OneTimePreKeyPublic>[];
    var nextId = await _nextPreKeyId(device);

    while (existingIds.length < oneTimePreKeyCount) {
      final preKeyPrivate = PrivateKey.generate();
      final preKeyPublic = preKeyPrivate.getPublicKey();
      final record = PreKeyRecord(
        id: nextId,
        publicKey: preKeyPublic,
        privateKey: preKeyPrivate,
      );
      await device.preKeyStore.storePreKey(nextId, record);
      oneTimePublic.add(
        OneTimePreKeyPublic(
          preKeyId: nextId,
          publicKey: preKeyPublic.serialize().toList(),
        ),
      );
      existingIds.add(nextId);
      nextId++;
      await _persistPreKeyCounter(device, nextId);
    }

    final kyberPublic = kyber.getPublicKey();

    return DevicePublicKeyBundle(
      userIdentityId: device.userIdentityId,
      deviceId: device.deviceId,
      registrationId: registrationId,
      identityKeyPublic: identityPair.publicKey.toList(),
      signedPreKeyId: signedPreKeyId,
      signedPreKeyPublic: signed.publicKey().toList(),
      signedPreKeySignature: signed.signature().toList(),
      kyberPreKeyId: kyberPreKeyId,
      kyberPreKeyPublic: kyberPublic.serialize().toList(),
      kyberPreKeySignature: kyber.signature().toList(),
      oneTimePreKeys: oneTimePublic,
    );
  }

  Future<int> _nextPreKeyId(LocalDeviceCryptoHandle device) async {
    final raw = await _blobs.readBytes(
      E2eeStorageKeys.preKeyCounter(device.userIdentityId, device.deviceId),
    );
    if (raw == null) return 100;
    final list = IntListCodec.decode(raw);
    return list.isEmpty ? 100 : list.first;
  }

  Future<void> _persistPreKeyCounter(
    LocalDeviceCryptoHandle device,
    int nextId,
  ) async {
    await _blobs.writeBytes(
      E2eeStorageKeys.preKeyCounter(device.userIdentityId, device.deviceId),
      IntListCodec.encode([nextId]),
    );
  }

  @override
  Future<void> establishSession({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required PreKeyBundle remoteBundle,
  }) async {
    final builder = SessionBuilder(
      localAddress: local.localAddress.toLibsignal(),
      sessionStore: local.sessionStore,
      identityKeyStore: local.identityKeyStore,
    );
    await builder.processPreKeyBundle(remote.toLibsignal(), remoteBundle);
  }

  SessionCipher _cipher(LocalDeviceCryptoHandle local) => SessionCipher(
        localAddress: local.localAddress.toLibsignal(),
        sessionStore: local.sessionStore,
        identityKeyStore: local.identityKeyStore,
        preKeyStore: local.preKeyStore,
        signedPreKeyStore: local.signedPreKeyStore,
        kyberPreKeyStore: local.kyberPreKeyStore,
      );

  @override
  Future<CiphertextEnvelope> encryptDirect({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> plaintext,
  }) {
    return _sessionLock.run(remote.label, () async {
      final cipher = _cipher(local);
      final message = await cipher.encrypt(
        remote.toLibsignal(),
        Uint8List.fromList(plaintext),
      );
      return CiphertextEnvelope(
        messageType: message.type.value,
        ciphertext: message.ciphertext.toList(),
      );
    });
  }

  @override
  Future<List<int>> decryptDirect({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required CiphertextEnvelope envelope,
  }) {
    return _sessionLock.run(remote.label, () async {
      final cipher = _cipher(local);
      try {
        final ciphertext = CiphertextMessage.fromRaw(
          messageType: envelope.messageType,
          ciphertext: Uint8List.fromList(envelope.ciphertext),
        );
        final bytes = await cipher.decrypt(remote.toLibsignal(), ciphertext);
        return bytes.toList();
      } on LibSignalException catch (e) {
        if (e.code == LibSignalErrorCode.untrustedIdentity) {
          throw E2eeUntrustedIdentityException(remote.label);
        }
        throw E2eeSessionException('Decrypt failed');
      }
    });
  }

  @override
  Future<String> safetyNumber({
    required LocalDeviceCryptoHandle local,
    required E2eeProtocolAddress remote,
    required List<int> remoteIdentityKeyPublic,
  }) async {
    final localPair = await local.identityKeyStore.getIdentityKeyPair();
    final fingerprint = Fingerprint(
      iterations: 5200,
      version: 2,
      localIdentifier: utf8.encode(local.userIdentityId),
      localPublicKey: localPair.publicKey.toList(),
      remoteIdentifier: utf8.encode(remote.userIdentityId),
      remotePublicKey: remoteIdentityKeyPublic,
    );
    return fingerprint.displayString();
  }
}
