import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/app_config.dart';
import '../../../theme/tokens/gc_colors.dart';
import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future<void>.delayed(const Duration(milliseconds: 400), _bootstrap);
  }

  Future<void> _bootstrap() async {
    await ref.read(authControllerProvider.notifier).restoreFromStorage();
    if (!mounted) return;
    final auth = ref.read(authControllerProvider);
    switch (auth.status) {
      case AuthStatus.authenticated:
        if (auth.canUseMessaging) {
          context.go('/home/chats');
        } else {
          context.go('/device-setup');
        }
      case AuthStatus.sessionExpired:
        context.go('/session-expired');
      case AuthStatus.unauthenticated:
      case AuthStatus.authenticating:
        context.go('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.forum_rounded,
                size: 64,
                color: GcColors.primary,
              ),
              const SizedBox(height: GcSpacing.md),
              Text(
                AppConfig.appName,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: GcSpacing.lg),
              const CircularProgressIndicator(),
            ],
          ),
        ),
      ),
    );
  }
}
