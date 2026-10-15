import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import 'widgets/auth_scaffold.dart';

class ResetPasswordScreen extends ConsumerStatefulWidget {
  const ResetPasswordScreen({super.key, this.initialToken});

  final String? initialToken;

  @override
  ConsumerState<ResetPasswordScreen> createState() =>
      _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends ConsumerState<ResetPasswordScreen> {
  late final _token = TextEditingController(text: widget.initialToken);
  final _password = TextEditingController();
  var _obscure = true;

  @override
  void dispose() {
    _token.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final ok = await ref.read(authControllerProvider.notifier).resetPassword(
          _token.text.trim(),
          _password.text,
        );
    if (!mounted || !ok) return;
    context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.status == AuthStatus.authenticating;

    return AuthScaffold(
      title: 'Reset password',
      subtitle: 'Choose a new password (12+ characters).',
      child: Column(
        children: [
          if (auth.errorMessage != null)
            Text(
              auth.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          TextField(
            controller: _token,
            decoration: const InputDecoration(labelText: 'Reset token'),
          ),
          const SizedBox(height: GcSpacing.sm),
          TextField(
            controller: _password,
            obscureText: _obscure,
            decoration: InputDecoration(
              labelText: 'New password',
              suffixIcon: IconButton(
                icon: Icon(
                  _obscure ? Icons.visibility_outlined : Icons.visibility_off,
                ),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
          ),
          const SizedBox(height: GcSpacing.md),
          FilledButton(
            onPressed: loading ? null : _submit,
            child: const Text('Update password'),
          ),
        ],
      ),
    );
  }
}
