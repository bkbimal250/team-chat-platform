import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class ChatsScreen extends StatelessWidget {
  const ChatsScreen({super.key});
  static const chats = [
    ('Design team', 'Maya: The updated prototype is ready', '2m', 3),
    ('Alex Morgan', 'Sounds good, I will review it.', '12m', 0),
    ('Release planning', 'Sam sent a document', 'Yesterday', 0),
    ('Engineering', 'Nora is typing…', 'Yesterday', 1),
  ];
  @override
  Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(
      title: const Text('GlobalChat'),
      actions: [
        IconButton(
          onPressed: () => c.go('/settings'),
          icon: const Icon(Icons.search),
          tooltip: 'Search',
        ),
        IconButton(
          onPressed: () {},
          icon: const Icon(Icons.more_vert),
          tooltip: 'Menu',
        ),
      ],
    ),
    body: RefreshIndicator(
      onRefresh: () async =>
          Future<void>.delayed(const Duration(milliseconds: 500)),
      child: ListView.separated(
        itemCount: chats.length,
        separatorBuilder: (_, _) => const Divider(indent: 76),
        itemBuilder: (_, i) {
          final x = chats[i];
          return ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 5,
            ),
            leading: CircleAvatar(
              radius: 26,
              child: Text(x.$1.substring(0, 1)),
            ),
            title: Text(x.$1, maxLines: 1, overflow: TextOverflow.ellipsis),
            subtitle: Text(x.$2, maxLines: 1, overflow: TextOverflow.ellipsis),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(x.$3, style: Theme.of(c).textTheme.labelSmall),
                if (x.$4 > 0)
                  Container(
                    margin: const EdgeInsets.only(top: 5),
                    padding: const EdgeInsets.all(5),
                    decoration: BoxDecoration(
                      color: Theme.of(c).colorScheme.primary,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '${x.$4}',
                      style: TextStyle(
                        color: Theme.of(c).colorScheme.onPrimary,
                        fontSize: 10,
                      ),
                    ),
                  ),
              ],
            ),
            onTap: () => c.go('/chat/${x.$1}'),
          );
        },
      ),
    ),
    floatingActionButton: FloatingActionButton(
      onPressed: () => c.go('/new-chat'),
      tooltip: 'New chat',
      child: const Icon(Icons.chat),
    ),
  );
}
