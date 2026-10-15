import 'package:libsignal/libsignal.dart';

/// Maps a GlobalChat **user identity** (never an organization id) and device id
/// to a libsignal [ProtocolAddress].
class E2eeProtocolAddress {
  const E2eeProtocolAddress({
    required this.userIdentityId,
    required this.deviceId,
  });

  final String userIdentityId;
  final int deviceId;

  ProtocolAddress toLibsignal() =>
      ProtocolAddress(name: userIdentityId, deviceId: deviceId);

  static E2eeProtocolAddress fromLibsignal(ProtocolAddress address) =>
      E2eeProtocolAddress(
        userIdentityId: address.name(),
        deviceId: address.deviceId(),
      );

  String get label => '$userIdentityId:$deviceId';
}
