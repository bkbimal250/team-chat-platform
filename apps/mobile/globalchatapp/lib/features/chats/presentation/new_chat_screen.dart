import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../components/ui/gc_empty_state.dart';
import '../../../components/ui/gc_loading.dart';
import '../../../services/api/models/contact_models.dart';
import '../../../services/api/providers/api_providers.dart';
import '../../../theme/tokens/gc_spacing.dart';
import '../data/conversations_repository.dart';
import '../application/chats_controller.dart';

final _contactsProvider = FutureProvider<List<ContactDto>>((ref) async {
  return ref.read(contactsApiProvider).list();
});

class NewChatScreen extends ConsumerStatefulWidget {
  const NewChatScreen({super.key});

  @override
  ConsumerState<NewChatScreen> createState() => _NewChatScreenState();
}

class _NewChatScreenState extends ConsumerState<NewChatScreen> {
  String _query = '';
  var _busy = false;

  Future<void> _openDirect(ContactDto contact) async {
    if (contact.contactIdentityId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Contact is not on GlobalChat yet.')),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      final conv = await ref
          .read(conversationsRepositoryProvider)
          .startPersonalDirect(contact.id);
      await ref.read(chatsControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go('/chat/${conv.id}');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final contacts = ref.watch(_contactsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('New chat'),
        actions: [
          IconButton(
            onPressed: _busy ? null : () => context.push('/new-group'),
            icon: const Icon(Icons.group_add_outlined),
            tooltip: 'New group',
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(GcSpacing.md),
            child: SearchBar(
              hintText: 'Search contacts',
              onChanged: (v) => setState(() => _query = v.trim().toLowerCase()),
            ),
          ),
          if (_busy) const LinearProgressIndicator(minHeight: 2),
          Expanded(
            child: contacts.when(
              loading: () => const GcLoading(),
              error: (e, _) => GcEmptyState(
                icon: Icons.contacts_outlined,
                title: 'Contacts unavailable',
                message: e.toString(),
              ),
              data: (items) {
                final filtered = items
                    .where(
                      (c) =>
                          _query.isEmpty ||
                          c.title.toLowerCase().contains(_query),
                    )
                    .toList();
                if (filtered.isEmpty) {
                  return const GcEmptyState(
                    icon: Icons.person_search_outlined,
                    title: 'No contacts',
                    message: 'Add contacts in the Contacts tab first.',
                  );
                }
                return ListView.builder(
                  itemCount: filtered.length,
                  itemBuilder: (_, i) {
                    final c = filtered[i];
                    return ListTile(
                      leading: CircleAvatar(
                        child: Text(
                          c.title.isNotEmpty ? c.title[0].toUpperCase() : '?',
                        ),
                      ),
                      title: Text(c.title),
                      subtitle: c.subtitle != null ? Text(c.subtitle!) : null,
                      onTap: () => _openDirect(c),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
