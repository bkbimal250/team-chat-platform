import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'group_info_controller.dart';

class GroupInfoScreen extends ConsumerWidget {
  const GroupInfoScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(groupInfoProvider);
    final controller = ref.read(groupInfoProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('Group Info')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Center(
              child: CircleAvatar(
                radius: 40,
                child: Icon(Icons.group, size: 40),
              ),
            ),
            const SizedBox(height: 12),
            Center(
              child: Text(
                state.group.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            Center(child: Text('${state.group.members.length} members')),
            const SizedBox(height: 12),
            const ListTile(
              title: Text('Media, Links & Docs'),
              trailing: Icon(Icons.chevron_right),
            ),
            Text('Members · ${state.group.members.length}'),
            ...state.group.members.map(
              (member) => ListTile(
                title: Text(member.name, overflow: TextOverflow.ellipsis),
                subtitle: Text(member.role.name),
                trailing: state.canRemove(member)
                    ? IconButton(
                        tooltip: 'Remove member',
                        icon: const Icon(Icons.person_remove),
                        onPressed: () => _remove(context, controller, member),
                      )
                    : null,
              ),
            ),
            if (state.canAdd)
              const ListTile(
                leading: Icon(Icons.person_add),
                title: Text('Add member'),
              ),
            OutlinedButton(
              key: const Key('group_info_leave_group'),
              onPressed: () => _leave(context),
              child: const Text('Leave group'),
            ),
          ],
        ),
      ),
    );
  }

  void _remove(
    BuildContext context,
    GroupInfoController controller,
    dynamic member,
  ) {
    showDialog<void>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: Text('Remove ${member.name}?'),
        content: const Text('This member will no longer be in this group.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              controller.remove(member);
              Navigator.pop(dialog);
            },
            child: const Text('Remove'),
          ),
        ],
      ),
    );
  }

  void _leave(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Leave group?'),
        content: const Text(
          'You will stop receiving messages from this group.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog),
            child: const Text('Cancel'),
          ),
          FilledButton(
            key: const Key('group_info_confirm_leave'),
            onPressed: () async {
              final ok = await ProviderScope.containerOf(context)
                  .read(groupInfoProvider.notifier)
                  .leaveGroup();
              if (dialog.mounted) Navigator.pop(dialog);
              if (!context.mounted) return;
              if (ok) {
                context.go('/chats');
              } else {
                final error = ProviderScope.containerOf(context)
                    .read(groupInfoProvider)
                    .error;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      error ?? 'Unable to leave this group right now.',
                    ),
                  ),
                );
              }
            },
            child: const Text('Leave'),
          ),
        ],
      ),
    );
  }
}
