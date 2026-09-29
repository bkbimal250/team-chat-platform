import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/chats_screen.dart';
import '../features/chat_screen.dart';
import '../features/login_screen.dart';
import '../features/utility_screens.dart';
import '../features/groups/presentation/new_group_screen.dart';
import '../features/groups/presentation/group_info_screen.dart';

class GlobalChatApp extends StatelessWidget {
  const GlobalChatApp({super.key});
  static final router = GoRouter(
    initialLocation: '/login',
    routes: [
      GoRoute(path: '/', redirect: (_, _) => '/login'),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/chats', builder: (_, _) => const ChatsScreen()),
      GoRoute(
        path: '/chat/:id',
        builder: (_, s) => ChatScreen(name: s.pathParameters['id']!),
      ),
      GoRoute(
        path: '/new-chat',
        builder: (_, _) => const ListScreen(
          title: 'New chat',
          items: ['Avery Chen', 'Maya Patel', 'Sam Rivera'],
        ),
      ),
      GoRoute(path: '/new-group', builder: (_, _) => const NewGroupScreen()),
      GoRoute(
        path: '/group/:id/info',
        builder: (_, s) => ListScreen(
          title: s.pathParameters['id']!,
          items: const [
            'Media, links & docs',
            'Members',
            'Add member',
            'Leave group',
          ],
        ),
      ),
      GoRoute(
        path: '/search',
        builder: (_, _) => const ListScreen(
          title: 'Search',
          items: ['Chats', 'Messages', 'People'],
        ),
      ),
      GoRoute(
        path: '/profile',
        builder: (_, _) => const ListScreen(
          title: 'Profile',
          items: ['Jordan Lee', 'About', 'Organization member'],
        ),
      ),
      GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
      GoRoute(
        path: '/privacy',
        builder: (_, _) => const ListScreen(
          title: 'Privacy',
          items: ['Discoverability', 'Blocked users'],
        ),
      ),
      GoRoute(
        path: '/notifications',
        builder: (_, _) => const ListScreen(
          title: 'Notifications',
          items: ['Message notifications', 'Preview messages'],
        ),
      ),
      GoRoute(
        path: '/devices',
        builder: (_, _) => const ListScreen(
          title: 'Linked devices',
          items: ['This device', 'GlobalChat Web', 'Link a device'],
        ),
      ),
      GoRoute(path: '/qr-login', builder: (_, _) => const QrScreen()),
      GoRoute(
        path: '/chat/:id/group-info',
        builder: (_, _) => const GroupInfoScreen(),
      ),
    ],
  );
  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: 'GlobalChat',
    routerConfig: router,
    themeMode: ThemeMode.system,
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF08786B)),
    ),
    darkTheme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF42C9B7),
        brightness: Brightness.dark,
      ),
    ),
  );
}
