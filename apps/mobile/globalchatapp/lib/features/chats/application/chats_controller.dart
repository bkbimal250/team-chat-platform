import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../services/api/models/conversation_models.dart';
import '../../../services/api/providers/api_providers.dart';
import '../data/conversations_repository.dart';
import 'chats_filter.dart';

final conversationsRepositoryProvider = Provider(
  (ref) => ConversationsRepository(ref.watch(conversationsApiProvider)),
);

final chatsControllerProvider =
    AsyncNotifierProvider<ChatsController, List<ConversationDto>>(
  ChatsController.new,
);

class ChatsController extends AsyncNotifier<List<ConversationDto>> {
  ChatListFilter _filter = ChatListFilter.all;

  void setFilter(ChatListFilter filter) {
    _filter = filter;
    ref.invalidateSelf();
  }

  @override
  Future<List<ConversationDto>> build() async {
    final repo = ref.read(conversationsRepositoryProvider);
    final all = await repo.listConversations();
    switch (_filter) {
      case ChatListFilter.all:
        return all;
      case ChatListFilter.unread:
        return all.where((c) => c.unreadCount > 0).toList();
      case ChatListFilter.groups:
        return all.where((c) => c.isGroup).toList();
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => build());
  }
}
