import 'package:flutter/material.dart';

import '../domain/message.dart';

class ReplyPreview extends StatelessWidget {
  const ReplyPreview(this.reply, {super.key});
  final ReplyReference reply;
  @override
  Widget build(BuildContext c) => InkWell(
    onTap: () {},
    child: Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        border: Border(
          left: BorderSide(color: Theme.of(c).colorScheme.primary, width: 3),
        ),
        color: Theme.of(c).colorScheme.surfaceContainerHighest,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            reply.senderName,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          Text(reply.preview, maxLines: 1, overflow: TextOverflow.ellipsis),
        ],
      ),
    ),
  );
}

class ReactionBar extends StatelessWidget {
  const ReactionBar(this.reactions, {super.key});
  final List<MessageReaction> reactions;
  @override
  Widget build(BuildContext c) => Wrap(
    children: reactions
        .map(
          (r) => Chip(
            label: Text('${r.emoji} ${r.count}'),
            backgroundColor: r.currentUserReacted
                ? Theme.of(c).colorScheme.primaryContainer
                : null,
          ),
        )
        .toList(),
  );
}

class MessageBubble extends StatelessWidget {
  const MessageBubble(this.message, {super.key});
  final ChatMessage message;
  @override
  Widget build(BuildContext c) {
    final content = switch (message.type) {
      MessageType.text => Text(message.text ?? ''),
      MessageType.deleted => const Text('🚫 This message was deleted'),
      MessageType.image => Column(
        children: [Icon(Icons.image, size: 100), Text(message.text ?? 'Image')],
      ),
      MessageType.video => const ListTile(
        leading: Icon(Icons.play_circle_fill),
        title: Text('Video'),
        subtitle: Text('00:24'),
      ),
      MessageType.document => ListTile(
        leading: const Icon(Icons.description),
        title: Text(
          message.attachment?.name ?? 'Document',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Text(message.attachment?.mimeType ?? ''),
      ),
      MessageType.audio || MessageType.voiceNote => const ListTile(
        leading: Icon(Icons.play_arrow),
        title: LinearProgressIndicator(value: .35),
        subtitle: Text('00:18'),
      ),
    };
    return Align(
      alignment: message.isMine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(c).width * .78),
        margin: const EdgeInsets.all(6),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: message.isMine
              ? Theme.of(c).colorScheme.primaryContainer
              : Theme.of(c).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (message.replyTo != null) ReplyPreview(message.replyTo!),
            content,
            if (message.reactions.isNotEmpty) ReactionBar(message.reactions),
            Text(
              '${message.editedAt != null ? 'edited ' : ''}${message.status.name}',
              style: Theme.of(c).textTheme.labelSmall,
            ),
          ],
        ),
      ),
    );
  }
}
