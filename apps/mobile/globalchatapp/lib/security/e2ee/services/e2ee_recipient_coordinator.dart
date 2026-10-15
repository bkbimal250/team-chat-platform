import 'dart:convert';

import 'package:libsignal/libsignal.dart';

import '../../../services/api/e2ee/e2ee_api.dart';
import '../../../services/api/models/e2ee_models.dart';
import '../../../services/api/messaging/messaging_models.dart';
import '../../../services/devices/signal_device_id.dart';
import '../exceptions/e2ee_exception.dart';
import '../models/ciphertext_envelope.dart';
import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import '../util/prekey_bundle_mapper.dart';
import 'direct_session_service.dart';
import 'e2ee_trust_guard.dart';
import 'group_e2ee_service.dart';

class E2eeRecipientCoordinator {
  E2eeRecipientCoordinator({
    required E2eeApi e2eeApi,
    required SignalDeviceIdRegistry signalIds,
    DirectSessionService? directSessions,
    GroupE2eeService? groupE2ee,
    E2eeTrustGuard? trustGuard,
  })  : _e2eeApi = e2eeApi,
        _signalIds = signalIds,
        _direct = directSessions ?? DirectSessionService(),
        _group = groupE2ee ?? GroupE2eeService(),
        _trust = trustGuard ?? E2eeTrustGuard(signalIds: signalIds);

  final E2eeApi _e2eeApi;
  final SignalDeviceIdRegistry _signalIds;
  final DirectSessionService _direct;
  final GroupE2eeService _group;
  final E2eeTrustGuard _trust;

  Future<PreKeyBundleDto> _fetchBundleOrThrow(
    ({String identityId, String deviceId}) target,
  ) async {
    try {
      return await _e2eeApi.fetchPreKeyBundle(
        identityId: target.identityId,
        deviceId: target.deviceId,
      );
    } catch (_) {
      throw E2eeSessionException(
        'Pre-keys missing or rotated for device ${target.deviceId}. '
        'The recipient must open GlobalChat to refresh keys.',
      );
    }
  }

  Future<E2eeEnvelopeDto> encryptDirectForDevices({
    required LocalDeviceCryptoHandle local,
    required String localBackendDeviceId,
    required List<({String identityId, String deviceId})> targets,
    required List<int> plaintext,
  }) async {
    final payloads = <E2eeDeviceCiphertextDto>[];
    for (final target in targets) {
      final bundleDto = await _fetchBundleOrThrow(target);
      await _trust.establishSession(local: local, bundleDto: bundleDto);
      final signalDeviceId = await _signalIds.resolve(target.deviceId);
      final remote = E2eeProtocolAddress(
        userIdentityId: target.identityId,
        deviceId: signalDeviceId,
      );
      final envelope = await _direct.encrypt(
        local: local,
        remote: remote,
        plaintext: plaintext,
      );
      payloads.add(
        E2eeDeviceCiphertextDto(
          deviceId: target.deviceId,
          messageType: envelope.messageType,
          ciphertextB64: base64Encode(envelope.ciphertext),
          registrationId: envelope.registrationId,
        ),
      );
    }
    final selfPayload = payloads.firstWhere(
      (p) => p.deviceId == localBackendDeviceId,
      orElse: () => payloads.first,
    );
    return E2eeEnvelopeDto(
      version: 1,
      mode: 'direct',
      messageType: selfPayload.messageType,
      ciphertextB64: selfPayload.ciphertextB64,
      devicePayloads: payloads,
    );
  }

  Future<E2eeEnvelopeDto> encryptGroup({
    required LocalDeviceCryptoHandle local,
    required String conversationId,
    required List<int> plaintext,
    required String localBackendDeviceId,
    required List<({String identityId, String deviceId})> memberDevices,
  }) async {
    final distributionId = conversationId;
    final groupCipherText = await _group.encryptGroupPayload(
      local: local,
      distributionId: distributionId,
      plaintext: plaintext,
    );
    final directPlain = utf8.encode(
      jsonEncode({
        'kind': 'sender_key_distribution',
        'distribution_id': distributionId,
        'bytes': base64Encode(
          await _group.createSenderKeyDistributionMessage(
            local: local,
            distributionId: distributionId,
          ),
        ),
      }),
    );
    final devicePayloads = <E2eeDeviceCiphertextDto>[];
    for (final target in memberDevices) {
      if (target.identityId == local.userIdentityId &&
          target.deviceId == localBackendDeviceId) {
        continue;
      }
      final bundleDto = await _fetchBundleOrThrow(target);
      await _trust.establishSession(local: local, bundleDto: bundleDto);
      final signalDeviceId = await _signalIds.resolve(target.deviceId);
      final remote = E2eeProtocolAddress(
        userIdentityId: target.identityId,
        deviceId: signalDeviceId,
      );
      final envelope = await _direct.encrypt(
        local: local,
        remote: remote,
        plaintext: directPlain,
      );
      devicePayloads.add(
        E2eeDeviceCiphertextDto(
          deviceId: target.deviceId,
          messageType: envelope.messageType,
          ciphertextB64: base64Encode(envelope.ciphertext),
        ),
      );
    }
    return E2eeEnvelopeDto(
      version: 1,
      mode: 'group',
      distributionId: distributionId,
      messageType: 6,
      ciphertextB64: base64Encode(groupCipherText),
      devicePayloads: devicePayloads.isEmpty
          ? [
              E2eeDeviceCiphertextDto(
                deviceId: localBackendDeviceId,
                messageType: 6,
                ciphertextB64: base64Encode(groupCipherText),
              ),
            ]
          : devicePayloads,
    );
  }

  Future<List<int>> decryptEnvelope({
    required LocalDeviceCryptoHandle local,
    required String localBackendDeviceId,
    required MessageDto message,
  }) async {
    if (message.e2ee == null) {
      throw StateError('Message is not encrypted');
    }
    final env = message.e2ee!;
    E2eeDeviceCiphertextDto? devicePayload;
    for (final payload in env.devicePayloads) {
      if (payload.deviceId == localBackendDeviceId) {
        devicePayload = payload;
        break;
      }
    }
    if (env.mode == 'group') {
      await _ingestEmbeddedSenderKeyDistribution(
        local: local,
        localBackendDeviceId: localBackendDeviceId,
        message: message,
        env: env,
      );
      final bytes = base64Decode(env.ciphertextB64);
      final senderSignalId =
          await _signalIds.resolve(message.senderDeviceId);
      final sender = E2eeProtocolAddress(
        userIdentityId: message.senderUserId,
        deviceId: senderSignalId,
      );
      try {
        return await _group.decryptGroupPayload(
          local: local,
          sender: sender,
          distributionId: env.distributionId ?? message.conversationId,
          ciphertext: bytes,
        );
      } catch (_) {
        await _ingestEmbeddedSenderKeyDistribution(
          local: local,
          localBackendDeviceId: localBackendDeviceId,
          message: message,
          env: env,
        );
        return _group.decryptGroupPayload(
          local: local,
          sender: sender,
          distributionId: env.distributionId ?? message.conversationId,
          ciphertext: bytes,
        );
      }
    }

    final ciphertextB64 = devicePayload?.ciphertextB64 ?? env.ciphertextB64;
    final messageType = devicePayload?.messageType ?? env.messageType;
    final bytes = base64Decode(ciphertextB64);
    final senderSignalId = await _signalIds.resolve(message.senderDeviceId);
    final remote = E2eeProtocolAddress(
      userIdentityId: message.senderUserId,
      deviceId: senderSignalId,
    );
    return _direct.decrypt(
      local: local,
      remote: remote,
      envelope: CiphertextEnvelope(
        messageType: messageType,
        ciphertext: bytes,
      ),
    );
  }

  Future<void> _ingestEmbeddedSenderKeyDistribution({
    required LocalDeviceCryptoHandle local,
    required String localBackendDeviceId,
    required MessageDto message,
    required E2eeEnvelopeDto env,
  }) async {
    E2eeDeviceCiphertextDto? devicePayload;
    for (final payload in env.devicePayloads) {
      if (payload.deviceId == localBackendDeviceId) {
        devicePayload = payload;
        break;
      }
    }
    if (devicePayload == null) return;
    try {
      await processSenderKeyDistribution(
        local: local,
        senderUserId: message.senderUserId,
        senderBackendDeviceId: message.senderDeviceId,
        distributionId: env.distributionId ?? message.conversationId,
        messageType: devicePayload.messageType,
        ciphertextB64: devicePayload.ciphertextB64,
      );
    } catch (_) {
      // Distribution may already be installed; decrypt retry handles missing keys.
    }
  }

  /// Realtime `e2ee.sender_key_distribution.v1` — ciphertext is a direct Signal payload.
  Future<void> processSenderKeyDistribution({
    required LocalDeviceCryptoHandle local,
    required String senderUserId,
    required String senderBackendDeviceId,
    required String distributionId,
    required int messageType,
    required String ciphertextB64,
  }) async {
    final senderSignalId = await _signalIds.resolve(senderBackendDeviceId);
    final sender = E2eeProtocolAddress(
      userIdentityId: senderUserId,
      deviceId: senderSignalId,
    );
    final plaintext = await _direct.decrypt(
      local: local,
      remote: sender,
      envelope: CiphertextEnvelope(
        messageType: messageType,
        ciphertext: base64Decode(ciphertextB64),
      ),
    );
    final json = jsonDecode(utf8.decode(plaintext)) as Map<String, dynamic>;
    if (json['kind'] != 'sender_key_distribution') return;
    final bytes = base64Decode(json['bytes'] as String);
    await _group.processSenderKeyDistributionMessage(
      local: local,
      sender: sender,
      distributionId: distributionId,
      distributionBytes: bytes,
    );
  }
}
