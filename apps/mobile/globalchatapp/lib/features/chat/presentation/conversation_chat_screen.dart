import 'package:image_picker/image_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../components/ui/gc_loading.dart';
import '../../messages/domain/message.dart';
import '../../messages/presentation/composer_controller.dart';
import '../application/chat_controller.dart';

class ConversationChatScreen extends ConsumerStatefulWidget {
  const ConversationChatScreen({super.key, required this.conversationId});

  final String conversationId;

  @override
  ConsumerState<ConversationChatScreen> createState() =>
      _ConversationChatScreenState();
}

class _ConversationChatScreenState extends ConsumerState<ConversationChatScreen> {
  final _input = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(chatControllerProvider.notifier).mount(widget.conversationId),
    );
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatControllerProvider);
    final composer = ref.watch(composerProvider);
    final chatNotifier = ref.read(chatControllerProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: InkWell(
          onTap: chat.isGroup
              ? () => context.push('/chat/${widget.conversationId}/group-info')
              : null,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(chat.title, overflow: TextOverflow.ellipsis),
              if (chat.typingMemberIds.isNotEmpty)
                Text(
                  'Typing…',
                  style: Theme.of(context).textTheme.labelSmall,
                ),
            ],
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (chat.error != null)
              MaterialBanner(
                content: Text(chat.error!),
                actions: [
                  TextButton(
                    onPressed: () => chatNotifier.refresh(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            if (composer.reply != null)
              _ReplyBar(
                preview: composer.reply!.text ?? '',
                onCancel: () =>
                    ref.read(composerProvider.notifier).cancelReply(),
              ),
            if (composer.editing != null)
              _EditBar(
                onCancel: () => ref.read(composerProvider.notifier).cancelEdit(),
              ),
            Expanded(
              child: chat.loading
                  ? const GcLoading()
                  : chat.messages.isEmpty
                      ? const Center(child: Text('No messages yet'))
                      : ListView.builder(
                          reverse: true,
                          padding: const EdgeInsets.all(16),
                          itemCount: chat.messages.length,
                          itemBuilder: (context, index) {
                            final message =
                                chat.messages[chat.messages.length - 1 - index];
                            return _Bubble(
                              message: message,
                              onOpenAttachment: message.mediaPayload != null
                                  ? () => _openAttachment(
                                        context,
                                        message,
                                        chatNotifier,
                                      )
                                  : null,
                              onLongPress: () =>
                                  _showActions(context, message, chatNotifier),
                              onRetry: message.status == MessageStatus.failed
                                  ? () => chatNotifier.retrySend(message)
                                  : null,
                            );
                          },
                        ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Row(
                children: [
                  IconButton(
                    onPressed: chat.sending ? null : () => _pickAttachment(chatNotifier),
                    icon: const Icon(Icons.attach_file_rounded),
                  ),
                  Expanded(
                    child: TextField(
                      controller: _input,
                      onChanged: (value) {
                        ref.read(composerProvider.notifier).setText(value);
                        chatNotifier.onComposerTextChanged(value);
                      },
                      decoration: InputDecoration(
                        hintText: composer.editing != null
                            ? 'Edit message'
                            : 'Message',
                        border: const OutlineInputBorder(),
                      ),
                      minLines: 1,
                      maxLines: 4,
                    ),
                  ),
                  IconButton(
                    onPressed: chat.sending
                        ? null
                        : () async {
                            if (composer.editing != null) {
                              final ok = ref
                                  .read(composerProvider.notifier)
                                  .saveEdit();
                              if (ok) {
                                await chatNotifier.editMessage(
                                  composer.editing!,
                                  _input.text,
                                );
                                ref.read(composerProvider.notifier).cancelEdit();
                                _input.clear();
                              }
                              return;
                            }
                            final text = _input.text;
                            _input.clear();
                            ref.read(composerProvider.notifier).setText('');
                            await chatNotifier.send(
                              text,
                              replyToId: composer.reply?.id,
                              replyPreview: composer.reply?.text,
                            );
                            if (composer.reply != null) {
                              ref.read(composerProvider.notifier).cancelReply();
                            }
                          },
                    icon: Icon(
                      composer.editing != null
                          ? Icons.check_rounded
                          : Icons.send_rounded,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openAttachment(
    BuildContext context,
    ChatMessage message,
    ChatController notifier,
  ) async {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    final bytes = await notifier.downloadAttachment(message);
    if (!context.mounted) return;
    Navigator.of(context).pop();
    if (bytes == null) return;
    final mime =
        message.mediaPayload?['content_type'] as String? ?? 'image/jpeg';
    if (mime.startsWith('image/')) {
      await showDialog<void>(
        context: context,
        builder: (ctx) => Dialog(
          child: InteractiveViewer(
            child: Image.memory(bytes, fit: BoxFit.contain),
          ),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Downloaded ${message.mediaPayload?['filename'] ?? 'attachment'} (${bytes.length} bytes)',
          ),
        ),
      );
    }
  }

  Future<void> _pickAttachment(ChatController notifier) async {
    final picked = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (picked == null) return;
    final bytes = await picked.readAsBytes();
    await notifier.sendAttachment(
      bytes: bytes,
      filename: picked.name,
      mimeType: 'image/jpeg',
    );
  }

  void _showActions(
    BuildContext context,
    ChatMessage message,
    ChatController notifier,
  ) {
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Wrap(
          children: [
            if (message.trustWarning != null)
              ListTile(
                leading: const Icon(Icons.warning_amber_rounded),
                title: const Text('Identity changed'),
                subtitle: Text(message.trustWarning!),
              ),
            if (!message.isMine &&
                message.trustWarning != null &&
                message.senderUserId != null &&
                message.senderDeviceId != null)
              ListTile(
                leading: const Icon(Icons.verified_user_outlined),
                title: const Text('Trust identity and reload'),
                onTap: () {
                  Navigator.pop(ctx);
                  notifier.trustSenderDevice(
                    remoteIdentityId: message.senderUserId!,
                    backendDeviceId: message.senderDeviceId!,
                  );
                },
              ),
            if (message.type != MessageType.deleted)
              ListTile(
                leading: const Icon(Icons.reply_rounded),
                title: const Text('Reply'),
                onTap: () {
                  ref.read(composerProvider.notifier).startReply(message);
                  Navigator.pop(ctx);
                },
              ),
            if (message.isMine && message.type != MessageType.deleted)
              ListTile(
                leading: const Icon(Icons.edit_rounded),
                title: const Text('Edit'),
                onTap: () {
                  ref.read(composerProvider.notifier).startEdit(message);
                  _input.text = message.text ?? '';
                  Navigator.pop(ctx);
                },
              ),
            if (message.isMine)
              ListTile(
                leading: const Icon(Icons.delete_outline),
                title: const Text('Delete'),
                onTap: () {
                  Navigator.pop(ctx);
                  notifier.deleteMessage(message);
                },
              ),
            ListTile(
              leading: const Icon(Icons.add_reaction_outlined),
              title: const Text('React 👍'),
              onTap: () {
                Navigator.pop(ctx);
                notifier.toggleReaction(message, '👍');
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ReplyBar extends StatelessWidget {
  const _ReplyBar({required this.preview, required this.onCancel});
  final String preview;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) => Material(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        child: ListTile(
          dense: true,
          title: Text('Replying to: $preview', maxLines: 1, overflow: TextOverflow.ellipsis),
          trailing: IconButton(icon: const Icon(Icons.close), onPressed: onCancel),
        ),
      );
}

class _EditBar extends StatelessWidget {
  const _EditBar({required this.onCancel});
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context) => Material(
        color: Theme.of(context).colorScheme.secondaryContainer,
        child: ListTile(
          dense: true,
          title: const Text('Editing message'),
          trailing: IconButton(icon: const Icon(Icons.close), onPressed: onCancel),
        ),
      );
}

class _Bubble extends StatelessWidget {
  const _Bubble({
    required this.message,
    this.onLongPress,
    this.onRetry,
    this.onOpenAttachment,
  });

  final ChatMessage message;
  final VoidCallback? onLongPress;
  final VoidCallback? onRetry;
  final VoidCallback? onOpenAttachment;

  @override
  Widget build(BuildContext context) {
    final outgoing = message.isMine;
    final label = message.decryptFailed
        ? (message.trustWarning ?? 'Unable to decrypt')
        : (message.text ??
            (message.mediaPayload != null ? 'Encrypted attachment' : 'Encrypted message'));
    return Align(
      alignment: outgoing ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: onLongPress,
        onTap: onOpenAttachment,
        child: Container(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.sizeOf(context).width * .78,
          ),
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: message.decryptFailed
                ? Theme.of(context).colorScheme.errorContainer
                : outgoing
                    ? Theme.of(context).colorScheme.primaryContainer
                    : Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(label),
              if (message.reactions.isNotEmpty)
                Wrap(
                  spacing: 4,
                  children: message.reactions
                      .map((r) => Chip(
                            label: Text('${r.emoji} ${r.count}'),
                            visualDensity: VisualDensity.compact,
                          ))
                      .toList(),
                ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (message.editedAt != null)
                    Text(
                      'Edited',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  const SizedBox(width: 6),
                  Text(
                    _statusLabel(message.status),
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                  if (onRetry != null) ...[
                    const SizedBox(width: 8),
                    TextButton(onPressed: onRetry, child: const Text('Retry')),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _statusLabel(MessageStatus status) {
    switch (status) {
      case MessageStatus.sending:
        return 'Sending…';
      case MessageStatus.failed:
        return 'Failed';
      case MessageStatus.delivered:
        return 'Delivered';
      case MessageStatus.read:
        return 'Read';
      case MessageStatus.sent:
        return 'Sent';
    }
  }
}
