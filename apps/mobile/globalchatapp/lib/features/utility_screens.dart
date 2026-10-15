import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../components/ui/gc_empty_state.dart';

class ListScreen extends StatelessWidget {
  const ListScreen({super.key, required this.title, required this.items});
  final String title;
  final List<String> items;
  @override
  Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: items.isEmpty
        ? GcEmptyState(
            icon: Icons.inbox_outlined,
            title: 'Nothing here yet',
            message: 'This screen will load data from GlobalChat when connected.',
          )
        : ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      separatorBuilder: (_, _) => const Divider(),
      itemBuilder: (_, i) => ListTile(
        leading: CircleAvatar(child: Text(items[i][0])),
        title: Text(items[i]),
        subtitle: const Text('Available in your workspace'),
        trailing: const Icon(Icons.chevron_right),
        onTap: items.isEmpty
            ? null
            : () {
                if (title == 'New chat') {
                  c.go('/chat/${items[i]}');
                }
              },
      ),
    ),
  );
}

class QrScreen extends StatelessWidget {
  const QrScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(title: const Text('Link a device')),
    body: const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.qr_code_scanner, size: 96),
          SizedBox(height: 16),
          Text('Scan a GlobalChat QR code'),
        ],
      ),
    ),
  );
}
