import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'new_group_controller.dart';

class NewGroupScreen extends ConsumerWidget {
  const NewGroupScreen({super.key});
  @override
  Widget build(BuildContext c, WidgetRef r) {
    final s = r.watch(newGroupProvider);
    final ctl = r.read(newGroupProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: Text(s.step == 0 ? 'New Group' : 'Group Details')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: s.step == 0
            ? Column(
                children: [
                  TextField(
                    onChanged: ctl.search,
                    decoration: const InputDecoration(
                      hintText: 'Search members',
                    ),
                  ),
                  Wrap(
                    children: s.selected
                        .map(
                          (m) => Chip(
                            label: Text(m.name),
                            onDeleted: () => ctl.toggle(m),
                          ),
                        )
                        .toList(),
                  ),
                  Expanded(
                    child: ListView(
                      children: s.members
                          .map(
                            (m) => CheckboxListTile(
                              value: s.selected.any((x) => x.id == m.id),
                              onChanged: (_) => ctl.toggle(m),
                              title: Text(m.name),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                  FilledButton(
                    onPressed: s.selected.isEmpty ? null : ctl.details,
                    child: Text('Next · ${s.selected.length} selected'),
                  ),
                ],
              )
            : Column(
                children: [
                  const CircleAvatar(radius: 36, child: Icon(Icons.group)),
                  TextField(
                    onChanged: ctl.setName,
                    decoration: const InputDecoration(labelText: 'Group name'),
                  ),
                  const SizedBox(height: 12),
                  Text('Participants · ${s.selected.length}'),
                  Expanded(
                    child: ListView(
                      children: s.selected
                          .map((m) => ListTile(title: Text(m.name)))
                          .toList(),
                    ),
                  ),
                  FilledButton(
                    onPressed: s.name.trim().isEmpty
                        ? null
                        : () async {
                            await ctl.create();
                            if (c.mounted) Navigator.pop(c);
                          },
                    child: const Text('Create Group'),
                  ),
                ],
              ),
      ),
    );
  }
}
