import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../components/ui/gc_loading.dart';
import '../../../services/api/models/e2ee_models.dart';
import '../../../services/api/providers/api_providers.dart';
import '../../auth/application/auth_controller.dart';

class LinkedDevicesScreen extends ConsumerStatefulWidget {
  const LinkedDevicesScreen({super.key});

  @override
  ConsumerState<LinkedDevicesScreen> createState() =>
      _LinkedDevicesScreenState();
}

class _LinkedDevicesScreenState extends ConsumerState<LinkedDevicesScreen> {
  var _loading = true;
  bool _revoking = false;
  String? _error;
  List<PublicDeviceE2eeDto> _devices = const [];

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final identityId = ref.read(authControllerProvider).user?.identityId;
    if (identityId == null) {
      setState(() {
        _loading = false;
        _error = 'Not signed in.';
      });
      return;
    }
    try {
      final devices =
          await ref.read(e2eeApiProvider).listUserDevices(identityId);
      if (!mounted) return;
      setState(() {
        _devices = devices;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Could not load devices.';
      });
    }
  }

  Widget? deviceAction(PublicDeviceE2eeDto device) => device.status == 'REVOKED' ? null :
    TextButton(onPressed: _revoking ? null : () => _revoke(device), child: const Text('Revoke'));

  Future<void> _revoke(PublicDeviceE2eeDto device) async {
    if (_revoking) return;
    final confirmed = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('Revoke device?'),
      content: Text('Sign out ${device.deviceName} and revoke its encryption key bundle?'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Revoke'))]));
    if (confirmed != true || !mounted) return;
    setState(() => _revoking = true);
    try {
      await ref.read(devicesApiProvider).revoke(device.deviceId);
      if (mounted) await _load();
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not revoke device. Please retry.');
    } finally { if (mounted) setState(() => _revoking = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Linked devices'),
        actions: [
          IconButton(
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: _loading
          ? const GcLoading()
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!),
                      TextButton(onPressed: _load, child: const Text('Retry')),
                    ],
                  ),
                )
              : _devices.isEmpty
                  ? const Center(child: Text('No devices registered'))
                  : ListView.separated(
                      itemCount: _devices.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final d = _devices[index];
                        final user = ref.read(authControllerProvider).user;
                        final isCurrent = user?.deviceId == d.deviceId;
                        return ListTile(
                          leading: Icon(
                            isCurrent
                                ? Icons.phone_android_rounded
                                : Icons.devices_other_rounded,
                          ),
                          title: Text(d.deviceName),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('${d.platform} Â· ${d.status}'),
                              if (d.identityKeyFingerprint != null)
                                Text(
                                  'Fingerprint: ${d.identityKeyFingerprint}',
                                  style:
                                      Theme.of(context).textTheme.labelSmall,
                                ),
                              if (d.rotatedAt != null)
                                Text(
                                  'Keys rotated ${d.rotatedAt}',
                                  style:
                                      Theme.of(context).textTheme.labelSmall,
                                ),
                            ],
                          ),
                          trailing: isCurrent
                              ? const Chip(label: Text('This device'))
                              : deviceAction(d),
                        );
                      },
                    ),
    );
  }
}
