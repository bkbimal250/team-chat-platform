import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../theme/gc_theme.dart';
import '../theme/theme_mode_controller.dart';
import 'navigation/app_router.dart';

class GlobalChatApp extends ConsumerWidget {
  const GlobalChatApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final router = ref.watch(goRouterProvider);
    return MaterialApp.router(
      title: 'GlobalChat',
      debugShowCheckedModeBanner: false,
      themeMode: themeMode,
      theme: GcTheme.light(),
      darkTheme: GcTheme.dark(),
      routerConfig: router,
    );
  }
}
