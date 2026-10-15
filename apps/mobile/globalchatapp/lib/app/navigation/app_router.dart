import '../../features/settings/presentation/user_settings_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../components/layout/gc_main_shell.dart';
import '../../features/auth/application/auth_controller.dart';
import '../../features/auth/application/auth_state.dart';
import '../../features/auth/presentation/device_setup_screen.dart';
import '../../features/auth/presentation/forgot_password_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/otp_login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/auth/presentation/reset_password_screen.dart';
import '../../features/auth/presentation/session_expired_screen.dart';
import '../../features/auth/presentation/splash_screen.dart';
import '../../features/chats/presentation/chats_tab_screen.dart';
import '../../features/chats/presentation/new_chat_screen.dart';
import '../../features/chat/presentation/conversation_chat_screen.dart';
import '../../features/contacts/presentation/contacts_tab_screen.dart';
import '../../features/groups/presentation/group_info_screen.dart';
import '../../features/groups/presentation/new_group_screen.dart';
import '../../features/notifications/presentation/updates_tab_screen.dart';
import '../../features/settings/presentation/linked_devices_screen.dart';
import '../../features/settings/presentation/settings_tab_screen.dart';
import '../../features/search/presentation/search_screen.dart';
import '../../features/utility_screens.dart';
import '../../features/workspace/presentation/workspace_tab_screen.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');
final _shellNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'shell');

const _authRoutes = {
  '/login',
  '/register',
  '/otp-login',
  '/forgot-password',
  '/reset-password',
  '/session-expired',
};

final goRouterProvider = Provider<GoRouter>((ref) {
  final refresh = ref.watch(authRouterRefreshProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ProviderScope.containerOf(context).read(authControllerProvider);
      final loc = state.matchedLocation;

      if (loc == '/splash') return null;

      if (auth.status == AuthStatus.sessionExpired) {
        return loc == '/session-expired' ? null : '/session-expired';
      }

      if (auth.status == AuthStatus.unauthenticated ||
          auth.status == AuthStatus.authenticating) {
        if (_authRoutes.contains(loc) || loc == '/device-setup') {
          return loc == '/device-setup' ? '/login' : null;
        }
        return '/login';
      }

      if (auth.status == AuthStatus.authenticated) {
        if (!auth.canUseMessaging) {
          if (loc == '/device-setup') return null;
          if (_authRoutes.contains(loc)) return '/device-setup';
          if (loc.startsWith('/home')) return '/device-setup';
        } else {
          if (_authRoutes.contains(loc) || loc == '/device-setup') {
            return '/home/chats';
          }
        }
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/otp-login',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const OtpLoginScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/reset-password',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, s) => ResetPasswordScreen(
          initialToken: s.extra as String?,
        ),
      ),
      GoRoute(
        path: '/session-expired',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const SessionExpiredScreen(),
      ),
      GoRoute(
        path: '/device-setup',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const DeviceSetupScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (_, _, navigationShell) =>
            GcMainShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            navigatorKey: _shellNavigatorKey,
            routes: [
              GoRoute(
                path: '/home/chats',
                builder: (_, _) => const ChatsTabScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/updates',
                builder: (_, _) => const UpdatesTabScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/contacts',
                builder: (_, _) => const ContactsTabScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/workspace',
                builder: (_, _) => const WorkspaceTabScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home/settings',
                builder: (_, _) => const SettingsTabScreen(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: '/chats',
        redirect: (_, _) => '/home/chats',
      ),
      GoRoute(
        path: '/chat/:id',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, s) => ConversationChatScreen(
          conversationId: s.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/new-chat',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const NewChatScreen(),
      ),
      GoRoute(
        path: '/new-group',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const NewGroupScreen(),
      ),
      GoRoute(
        path: '/group/:id/info',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, s) => ListScreen(
          title: s.pathParameters['id']!,
          items: const [],
        ),
      ),
      GoRoute(
        path: '/search',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const SearchScreen(),
      ),
      GoRoute(
        path: '/profile',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const UserSettingsScreen(),
      ),
      GoRoute(
        path: '/settings',
        redirect: (_, _) => '/home/settings',
      ),
      GoRoute(
        path: '/privacy',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const UserSettingsScreen(privacy: true),
      ),
      GoRoute(
        path: '/notifications',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) =>
            const ListScreen(title: 'Notifications', items: []),
      ),
      GoRoute(
        path: '/devices',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const LinkedDevicesScreen(),
      ),
      GoRoute(
        path: '/qr-login',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, _) => const QrScreen(),
      ),
      GoRoute(
        path: '/chat/:id/group-info',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (_, s) => GroupInfoScreen(
          conversationId: s.pathParameters['id']!,
        ),
      ),
    ],
  );
});
