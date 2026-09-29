import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.name});
  final String name;
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final input = TextEditingController();
  final messages = <String>[
    'Welcome to GlobalChat.',
    'The project update is ready for review.',
  ];
  @override
  void dispose() {
    input.dispose();
    super.dispose();
  }

  void send() {
    if (input.text.trim().isEmpty) return;
    setState(() => messages.add(input.text.trim()));
    input.clear();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: InkWell(
        onTap: () => context.go('/chat/${widget.name}/group-info'),
        child: Text(widget.name, overflow: TextOverflow.ellipsis),
      ),
    ),
    body: SafeArea(
      child: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              padding: const EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final outgoing = index.isEven;
                final text = messages[messages.length - 1 - index];
                return Align(
                  alignment: outgoing
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.sizeOf(context).width * .78,
                    ),
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: outgoing
                          ? Theme.of(context).colorScheme.primaryContainer
                          : Theme.of(context)
                                .colorScheme
                                .surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(text),
                        Text(
                          outgoing ? 'Delivered' : '09:42',
                          style: Theme.of(context).textTheme.labelSmall,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                IconButton(
                  onPressed: () => showModalBottomSheet(
                    context: context,
                    builder: (context) => const _Attachments(),
                  ),
                  icon: const Icon(Icons.add_circle_outline),
                  tooltip: 'Attach',
                ),
                Expanded(
                  child: TextField(
                    controller: input,
                    minLines: 1,
                    maxLines: 4,
                    onChanged: (_) => setState(() {}),
                    onSubmitted: (_) => send(),
                    decoration: const InputDecoration(hintText: 'Message'),
                  ),
                ),
                IconButton(
                  onPressed: input.text.trim().isEmpty ? () {} : send,
                  icon: Icon(
                    input.text.trim().isEmpty ? Icons.mic_none : Icons.send,
                  ),
                  tooltip: 'Send message',
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}

class _Attachments extends StatelessWidget {
  const _Attachments();
  @override
  Widget build(BuildContext context) => const SafeArea(
    child: Padding(
      padding: EdgeInsets.all(24),
      child: Wrap(
        spacing: 20,
        children: [
          Text('Gallery'),
          Text('Camera'),
          Text('Document'),
          Text('Audio'),
        ],
      ),
    ),
  );
}
