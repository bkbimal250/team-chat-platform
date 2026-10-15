import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../components/ui/gc_avatar.dart';
import '../../../../components/ui/gc_badge.dart';
import '../../../../components/ui/gc_scope_chip.dart' show GcConversationScope, GcScopeChip;
import '../../../../services/api/models/conversation_models.dart';
import '../../../../theme/tokens/gc_spacing.dart';

class ChatListTile extends StatelessWidget {
  const ChatListTile({
    super.key,
    required this.conversation,
    required this.onTap,
  });

  final ConversationDto conversation;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final time = conversation.lastMessageAt != null
        ? DateFormat.jm().format(conversation.lastMessageAt!.toLocal())
        : '';

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(
        horizontal: GcSpacing.md,
        vertical: GcSpacing.xxs,
      ),
      leading: GcAvatar(label: conversation.listTitle),
      title: Row(
        children: [
          Expanded(
            child: Text(
              conversation.listTitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.titleMedium,
            ),
          ),
          if (time.isNotEmpty)
            Text(
              time,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 2),
          GcScopeChip(
            scope: conversation.isPersonal
                ? GcConversationScope.personal
                : GcConversationScope.workspace,
          ),
          const SizedBox(height: 4),
          Text(
            conversation.lastMessagePreview ?? 'No messages yet',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
      trailing: conversation.unreadCount > 0
          ? GcBadge(count: conversation.unreadCount)
          : null,
      onTap: onTap,
    );
  }
}
