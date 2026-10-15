import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../components/ui/gc_empty_state.dart';
import '../../../components/ui/gc_loading.dart';
import '../../../config/app_config.dart';
import '../../../theme/tokens/gc_spacing.dart';
import '../application/chats_controller.dart';
import '../application/chats_filter.dart';
import 'widgets/chat_list_tile.dart';

class ChatsTabScreen extends ConsumerStatefulWidget {
  const ChatsTabScreen({super.key});

  @override
  ConsumerState<ChatsTabScreen> createState() => _ChatsTabScreenState();
}

class _ChatsTabScreenState extends ConsumerState<ChatsTabScreen> {
  ChatListFilter _filter = ChatListFilter.all;

  @override
  Widget build(BuildContext context) {
    final chats = ref.watch(chatsControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(AppConfig.appName),
        actions: [
          IconButton(
            onPressed: () => context.push('/search'),
            icon: const Icon(Icons.search_rounded),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/new-chat'),
        child: const Icon(Icons.chat_rounded),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
              GcSpacing.md,
              GcSpacing.xs,
              GcSpacing.md,
              GcSpacing.sm,
            ),
            child: SegmentedButton<ChatListFilter>(
              segments: const [
                ButtonSegment(value: ChatListFilter.all, label: Text('All')),
                ButtonSegment(value: ChatListFilter.unread, label: Text('Unread')),
                ButtonSegment(value: ChatListFilter.groups, label: Text('Groups')),
              ],
              selected: {_filter},
              onSelectionChanged: (value) {
                setState(() => _filter = value.first);
                ref.read(chatsControllerProvider.notifier).setFilter(_filter);
              },
            ),
          ),
          Expanded(
            child: chats.when(
              loading: () => const GcLoading(),
              error: (e, _) => GcEmptyState(
                icon: Icons.cloud_off_outlined,
                title: 'Could not load chats',
                message: e.toString(),
                actionLabel: 'Retry',
                onAction: () =>
                    ref.read(chatsControllerProvider.notifier).refresh(),
              ),
              data: (items) {
                if (items.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: () =>
                        ref.read(chatsControllerProvider.notifier).refresh(),
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                          height: MediaQuery.sizeOf(context).height * 0.5,
                          child: GcEmptyState(
                            icon: Icons.chat_bubble_outline_rounded,
                            title: 'No conversations',
                            message:
                                'Start a direct chat or create a group from your contacts.',
                            actionLabel: 'New chat',
                            onAction: () => context.push('/new-chat'),
                          ),
                        ),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () =>
                      ref.read(chatsControllerProvider.notifier).refresh(),
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final c = items[index];
                      return ChatListTile(
                        conversation: c,
                        onTap: () => context.push('/chat/${c.id}'),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
