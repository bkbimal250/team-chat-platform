import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../components/ui/gc_loading.dart';
import '../application/group_providers.dart';
import '../domain/group.dart';
import 'group_info_controller.dart';

class GroupInfoScreen extends ConsumerStatefulWidget {
  const GroupInfoScreen({super.key, required this.conversationId});

  final String conversationId;

  @override
  ConsumerState<GroupInfoScreen> createState() => _GroupInfoScreenState();
}

class _GroupInfoScreenState extends ConsumerState<GroupInfoScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(groupInfoProvider.notifier).mount(widget.conversationId),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(groupInfoProvider);
    final controller = ref.read(groupInfoProvider.notifier);
    if (state.loading && state.group == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Group Info')),
        body: const GcLoading(),
      );
    }
    final group = state.group;
    if (group == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Group Info')),
        body: Center(child: Text(state.error ?? 'Group unavailable')),
      );
    }
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
                group.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            Center(child: Text('${group.members.length} members')),
            if (state.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  state.error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            const SizedBox(height: 12),
            Text('Members · ${group.members.length}'),
            ...group.members.map(
              (member) => ListTile(
                title: Text(member.name, overflow: TextOverflow.ellipsis),
                subtitle: Text(member.role.name),
                onLongPress: group.myRole == GroupRole.owner &&
                        member.role == GroupRole.member
                    ? () => controller.promote(member)
                    : null,
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
              ListTile(
                leading: const Icon(Icons.person_add),
                title: const Text('Add members'),
                onTap: () => _addMembers(context),
              ),
            if (group.myRole == GroupRole.owner)
              OutlinedButton(
                onPressed: state.isMutating
                    ? null
                    : () => _deleteGroup(context),
                child: const Text('Delete group'),
              ),
            OutlinedButton(
              key: const Key('group_info_leave_group'),
              onPressed: state.isMutating ? null : () => _leave(context),
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

  Future<void> _addMembers(BuildContext context) async {
    final repo = ref.read(groupRepositoryProvider);
    final candidates = await repo.searchMembers('');
    final existing =
        ref.read(groupInfoProvider).group?.members.map((m) => m.id).toSet() ??
            {};
    final picked = <GroupMember>[];
    if (!context.mounted) return;
    await showDialog<void>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Add members'),
          content: SizedBox(
            width: double.maxFinite,
            child: ListView(
              shrinkWrap: true,
              children: candidates
                  .where((c) => !existing.contains(c.id))
                  .map(
                    (c) => CheckboxListTile(
                      value: picked.any((p) => p.id == c.id),
                      onChanged: (v) {
                        setState(() {
                          if (v == true) {
                            picked.add(c);
                          } else {
                            picked.removeWhere((p) => p.id == c.id);
                          }
                        });
                      },
                      title: Text(c.name),
                    ),
                  )
                  .toList(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialog),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: picked.isEmpty
                  ? null
                  : () async {
                      await ref
                          .read(groupInfoProvider.notifier)
                          .addMembers(picked);
                      if (dialog.mounted) Navigator.pop(dialog);
                    },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _deleteGroup(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Delete group?'),
        content: const Text('This cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    final deleted =
        await ref.read(groupInfoProvider.notifier).deleteGroup();
    if (deleted && context.mounted) context.go('/home/chats');
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
              final ok =
                  await ref.read(groupInfoProvider.notifier).leaveGroup();
              if (dialog.mounted) Navigator.pop(dialog);
              if (!context.mounted) return;
              if (ok) {
                context.go('/home/chats');
              }
            },
            child: const Text('Leave'),
          ),
        ],
      ),
    );
  }
}
