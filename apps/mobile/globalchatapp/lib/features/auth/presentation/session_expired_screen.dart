import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'widgets/auth_scaffold.dart';

class SessionExpiredScreen extends StatelessWidget {
  const SessionExpiredScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      title: 'Session expired',
      subtitle: 'Sign in again to continue.',
      child: FilledButton(
        onPressed: () => context.go('/login'),
        child: const Text('Sign in'),
      ),
    );
  }
}
