import 'dart:convert';
import 'dart:typed_data';

import '../exceptions/e2ee_exception.dart';
import '../models/e2ee_protocol_address.dart';
import '../models/local_device_crypto_handle.dart';
import '../../../services/api/models/e2ee_models.dart';
import 'direct_session_service.dart';
import 'identity_trust_service.dart';
import '../util/prekey_bundle_mapper.dart';
import '../../../services/devices/signal_device_id.dart';

/// Pre-session trust checks and explicit verification before accepting new keys.
class E2eeTrustGuard {
  E2eeTrustGuard({
    IdentityTrustService? trust,
    DirectSessionService? direct,
    SignalDeviceIdRegistry? signalIds,
  })  : _trust = trust ?? IdentityTrustService(),
        _direct = direct ?? DirectSessionService(),
        _signalIds = signalIds ?? SignalDeviceIdRegistry();

  final IdentityTrustService _trust;
  final DirectSessionService _direct;
  final SignalDeviceIdRegistry _signalIds;

  Future<String?> fingerprintForBundle(PreKeyBundleDto dto) async {
    final bytes = base64Decode(dto.identityKeyB64);
    return _formatFingerprint(bytes);
  }

  Future<void> establishSession({
    required LocalDeviceCryptoHandle local,
    required PreKeyBundleDto bundleDto,
  }) async {
    final bundle = await preKeyBundleFromDto(bundleDto, _signalIds);
    final signalDeviceId = await _signalIds.resolve(bundleDto.deviceId);
    final remote = E2eeProtocolAddress(
      userIdentityId: bundleDto.identityId,
      deviceId: signalDeviceId,
    );
    final identityBytes = base64Decode(bundleDto.identityKeyB64);
    final stored =
        await local.identityKeyStore.getIdentity(remote.toLibsignal());
    final changed = stored != null &&
        !_identityKeysEqual(stored.serialize(), identityBytes);
    if (changed) {
      final verified = await _trust.isExplicitlyVerified(
        device: local,
        remote: remote,
      );
      if (!verified) {
        throw E2eeUntrustedIdentityException(remote.label);
      }
    }
    await _direct.processRemoteBundle(
      local: local,
      remote: remote,
      bundle: bundle,
    );
  }

  Future<void> markVerified({
    required LocalDeviceCryptoHandle local,
    required String identityId,
    required String backendDeviceId,
  }) async {
    final signalDeviceId = await _signalIds.resolve(backendDeviceId);
    final remote = E2eeProtocolAddress(
      userIdentityId: identityId,
      deviceId: signalDeviceId,
    );
    await _trust.markVerified(device: local, remote: remote);
  }

  bool _identityKeysEqual(List<int> a, List<int> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  String _formatFingerprint(List<int> identityKey) {
    final digest = identityKey.length >= 32 ? identityKey.sublist(0, 32) : identityKey;
    final hex = digest.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return hex.replaceAllMapped(RegExp(r'.{4}'), (m) => '${m[0]} ').trim();
  }
}
