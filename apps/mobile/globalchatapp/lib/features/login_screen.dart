import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final controller = TextEditingController();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext c) => Scaffold(
    body: SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(
                  Icons.forum_rounded,
                  size: 56,
                  color: Theme.of(c).colorScheme.primary,
                ),
                const SizedBox(height: 20),
                Text(
                  'GlobalChat',
                  textAlign: TextAlign.center,
                  style: Theme.of(c).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Private conversations for your team.',
                  textAlign: TextAlign.center,
                  style: Theme.of(c).textTheme.bodyLarge,
                ),
                const SizedBox(height: 32),
                TextField(
                  controller: controller,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Work email or phone',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => c.go('/chats'),
                  child: const Text('Continue'),
                ),
                TextButton(
                  onPressed: () => c.go('/chats'),
                  child: const Text('Use demo workspace'),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
