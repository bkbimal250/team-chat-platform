import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';

class DeviceSetupScreen extends ConsumerStatefulWidget {
  const DeviceSetupScreen({super.key});

  @override
  ConsumerState<DeviceSetupScreen> createState() => _DeviceSetupScreenState();
}

class _DeviceSetupScreenState extends ConsumerState<DeviceSetupScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeBootstrap());
  }

  Future<void> _maybeBootstrap() async {
    final auth = ref.read(authControllerProvider);
    if (auth.cryptoStatus == DeviceCryptoStatus.needsBootstrap) {
      await ref.read(authControllerProvider.notifier).runDeviceCryptoBootstrap();
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(authControllerProvider, (prev, next) {
      if (next.cryptoStatus == DeviceCryptoStatus.ready && mounted) {
        context.go('/home/chats');
      }
    });
    final auth = ref.watch(authControllerProvider);
    final crypto = auth.cryptoStatus;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(GcSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: GcSpacing.xl),
              Icon(
                Icons.phonelink_lock_rounded,
                size: 56,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: GcSpacing.md),
              Text(
                'Secure this device',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: GcSpacing.sm),
              Text(
                'GlobalChat generates encryption keys on this device. '
                'Private keys never leave secure storage.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: GcSpacing.lg),
              if (crypto == DeviceCryptoStatus.bootstrapping)
                const Center(child: CircularProgressIndicator())
              else if (crypto == DeviceCryptoStatus.ready)
                FilledButton(
                  onPressed: () => context.go('/home/chats'),
                  child: const Text('Continue to GlobalChat'),
                )
              else if (crypto == DeviceCryptoStatus.blockedNoBackend) ...[
                Text(
                  auth.cryptoMessage ?? 'Server key upload is not available.',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                  ),
                ),
                const SizedBox(height: GcSpacing.md),
                FilledButton(
                  onPressed: () => ref
                      .read(authControllerProvider.notifier)
                      .retryKeyPublish(),
                  child: const Text('Retry key upload'),
                ),
                TextButton(
                  onPressed: () async {
                    await ref.read(authControllerProvider.notifier).logout();
                    if (context.mounted) context.go('/login');
                  },
                  child: const Text('Sign out'),
                ),
              ] else if (crypto == DeviceCryptoStatus.failed) ...[
                if (auth.cryptoMessage != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: GcSpacing.md),
                    child: Text(
                      auth.cryptoMessage!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                FilledButton(
                  onPressed: () => ref
                      .read(authControllerProvider.notifier)
                      .runDeviceCryptoBootstrap(),
                  child: const Text('Try again'),
                ),
                TextButton(
                  onPressed: () async {
                    await ref.read(authControllerProvider.notifier).logout();
                    if (context.mounted) context.go('/login');
                  },
                  child: const Text('Sign out'),
                ),
              ]
              else
                FilledButton(
                  onPressed: () => ref
                      .read(authControllerProvider.notifier)
                      .runDeviceCryptoBootstrap(),
                  child: const Text('Set up encryption'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
