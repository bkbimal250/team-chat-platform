import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import 'widgets/auth_scaffold.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _email = TextEditingController();
  String? _devToken;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    if (email.isEmpty) return;
    final repo = ref.read(authRepositoryProvider);
    try {
      final dev = await repo.forgotPassword(email: email);
      setState(() => _devToken = dev);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'If an account exists, reset instructions were sent.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);

    return AuthScaffold(
      title: 'Forgot password',
      subtitle: 'We never reveal whether an email is registered.',
      child: Column(
        children: [
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          if (_devToken != null) ...[
            const SizedBox(height: GcSpacing.sm),
            Text(
              'Development reset token (local only):',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            SelectableText(_devToken!),
            TextButton(
              onPressed: () => context.push('/reset-password', extra: _devToken),
              child: const Text('Continue to reset'),
            ),
          ],
          const SizedBox(height: GcSpacing.md),
          FilledButton(
            onPressed: auth.status == AuthStatus.authenticating ? null : _submit,
            child: const Text('Send reset link'),
          ),
        ],
      ),
      footer: TextButton(
        onPressed: () => context.pop(),
        child: const Text('Back to sign in'),
      ),
    );
  }
}
