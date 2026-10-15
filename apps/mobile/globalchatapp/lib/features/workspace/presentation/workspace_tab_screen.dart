import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../components/ui/gc_empty_state.dart';
import '../../../theme/tokens/gc_spacing.dart';
import '../../auth/application/auth_controller.dart';
import '../application/workspace_controller.dart';

class WorkspaceTabScreen extends ConsumerWidget {
  const WorkspaceTabScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final workspace = ref.watch(workspaceControllerProvider);
    final auth = ref.watch(authControllerProvider);
    final orgId = auth.user?.organizationId;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Workspace'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(GcSpacing.md),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.person_outline_rounded),
              title: const Text('Personal mode'),
              subtitle: const Text(
                'Use a personal login session (no organization in your token). '
                'Workspace context does not remove personal conversations.',
              ),
              trailing: orgId == null
                  ? const Icon(Icons.check_circle_outline)
                  : null,
            ),
          ),
          if (workspace.organizations.isNotEmpty) ...[
            const SizedBox(height: GcSpacing.md),
            Text('Organizations', style: Theme.of(context).textTheme.titleSmall),
            ...workspace.organizations.map(
              (org) => Card(
                child: ListTile(
                  leading: const Icon(Icons.apartment_rounded),
                  title: Text(org.label),
                  subtitle: Text(org.organizationId),
                  trailing: orgId == org.organizationId
                      ? const Icon(Icons.check_circle_outline)
                      : null,
                  onTap: orgId == org.organizationId
                      ? null
                      : () => ref
                          .read(workspaceControllerProvider.notifier)
                          .switchOrganization(org.organizationId),
                ),
              ),
            ),
          ],
          if (workspace.error != null)
            Padding(
              padding: const EdgeInsets.only(top: GcSpacing.sm),
              child: Text(
                workspace.error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          const SizedBox(height: GcSpacing.lg),
          const GcEmptyState(
            icon: Icons.groups_outlined,
            title: 'Workspace hub',
            message:
                'Use organization context for workspace groups and members. Personal chats stay available when no organization is selected.',
          ),
        ],
      ),
    );
  }
}
