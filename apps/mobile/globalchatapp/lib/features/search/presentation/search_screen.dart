import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../chats/application/chats_controller.dart';
import '../../contacts/application/contacts_controller.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final chats = ref.watch(chatsControllerProvider).value ?? [];
    final contacts = ref.watch(contactsControllerProvider).value ?? [];
    final q = _query.trim().toLowerCase();
    final chatHits = chats
        .where((c) => q.isEmpty || c.listTitle.toLowerCase().contains(q))
        .toList();
    final contactHits = contacts
        .where((c) => q.isEmpty || c.title.toLowerCase().contains(q))
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Search chats & contacts'),
          onChanged: (value) => setState(() => _query = value),
        ),
      ),
      body: ListView(
        children: [
          if (chatHits.isNotEmpty) ...[
            const ListTile(title: Text('Chats')),
            ...chatHits.map(
              (c) => ListTile(
                title: Text(c.listTitle),
                onTap: () => context.push('/chat/${c.id}'),
              ),
            ),
          ],
          if (contactHits.isNotEmpty) ...[
            const ListTile(title: Text('Contacts')),
            ...contactHits.map(
              (c) => ListTile(
                title: Text(c.title),
                subtitle: Text(c.subtitle ?? ''),
                onTap: () => context.push('/new-chat'),
              ),
            ),
          ],
          if (q.isNotEmpty && chatHits.isEmpty && contactHits.isEmpty)
            const ListTile(title: Text('No results')),
        ],
      ),
    );
  }
}
