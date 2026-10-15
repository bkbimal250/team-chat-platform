import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../components/ui/gc_empty_state.dart';
import '../../../components/ui/gc_loading.dart';
import '../application/contacts_controller.dart';

class ContactsTabScreen extends ConsumerWidget {
  const ContactsTabScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contacts = ref.watch(contactsControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Contacts'),
        actions: [
          IconButton(
            onPressed: () =>
                ref.read(contactsControllerProvider.notifier).refresh(),
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: contacts.when(
        loading: () => const GcLoading(),
        error: (e, _) => GcEmptyState(
          icon: Icons.cloud_off_outlined,
          title: 'Could not load contacts',
          message: e.toString(),
          actionLabel: 'Retry',
          onAction: () =>
              ref.read(contactsControllerProvider.notifier).refresh(),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const GcEmptyState(
              icon: Icons.people_outline_rounded,
              title: 'No contacts yet',
              message:
                  'Saved contacts with registered users appear here for chat and groups.',
            );
          }
          return ListView.separated(
            itemCount: items.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final contact = items[index];
              return ListTile(
                leading: CircleAvatar(
                  child: Text(
                    contact.title.isNotEmpty ? contact.title[0] : '?',
                  ),
                ),
                title: Text(contact.title),
                subtitle: contact.contactIdentityId == null
                    ? const Text('Not on GlobalChat')
                    : Text(contact.subtitle ?? 'Registered'),
                onTap: contact.contactIdentityId == null
                    ? null
                    : () => context.push('/new-chat'),
              );
            },
          );
        },
      ),
    );
  }
}
