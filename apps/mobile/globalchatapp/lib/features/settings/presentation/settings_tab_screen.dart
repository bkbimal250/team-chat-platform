import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/application/auth_controller.dart';
import '../../../theme/theme_mode_controller.dart';
import '../../../theme/tokens/gc_spacing.dart';

class SettingsTabScreen extends ConsumerWidget {
  const SettingsTabScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(GcSpacing.md),
        children: [
          _SectionHeader(title: 'Account'),
          ListTile(
            leading: const Icon(Icons.person_outline_rounded),
            title: const Text('Profile'),
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => context.push('/profile'),
          ),
          ListTile(
            leading: const Icon(Icons.apartment_outlined),
            title: const Text('Organization memberships'),
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => context.go('/home/workspace'),
          ),
          const SizedBox(height: GcSpacing.md),
          _SectionHeader(title: 'Preferences'),
          ListTile(
            leading: const Icon(Icons.lock_outline_rounded),
            title: const Text('Privacy'),
            onTap: () => context.push('/privacy'),
          ),
          ListTile(
            leading: const Icon(Icons.notifications_none_rounded),
            title: const Text('Notifications'),
            onTap: () => context.push('/notifications'),
          ),
          ListTile(
            leading: const Icon(Icons.palette_outlined),
            title: const Text('Appearance'),
            subtitle: Text(_appearanceLabel(themeMode)),
            onTap: () => _showAppearanceSheet(context, ref),
          ),
          ListTile(
            leading: const Icon(Icons.devices_other_rounded),
            title: const Text('Linked devices'),
            onTap: () => context.push('/devices'),
          ),
          const SizedBox(height: GcSpacing.md),
          ListTile(
            leading: Icon(Icons.logout_rounded, color: Theme.of(context).colorScheme.error),
            title: Text(
              'Log out',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            onTap: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
    );
  }

  static String _appearanceLabel(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.light:
        return 'Light';
      case ThemeMode.dark:
        return 'Dark';
      case ThemeMode.system:
        return 'System default';
    }
  }

  static void _showAppearanceSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final mode in ThemeMode.values)
              ListTile(
                title: Text(_appearanceLabel(mode)),
                trailing: ref.watch(themeModeProvider) == mode
                    ? const Icon(Icons.check_rounded)
                    : null,
                onTap: () {
                  ref.read(themeModeProvider.notifier).setMode(mode);
                  Navigator.pop(context);
                },
              ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: GcSpacing.xs, top: GcSpacing.xs),
      child: Text(
        title,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: Theme.of(context).colorScheme.primary,
            ),
      ),
    );
  }
}
